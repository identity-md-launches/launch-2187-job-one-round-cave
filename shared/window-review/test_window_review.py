import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import window_review as w

START = '2026-10-18T10:00:02Z'
END = '2026-10-18T10:00:04Z'
HERE = Path(__file__).resolve().parent


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.pack = w.demo_pack()
        self.raw = w.window.replay.canonical(self.pack)

    def render(self, raw=None, **kwargs):
        return w.render(self.raw if raw is None else raw, START, END, **kwargs)

    def test_query_and_decoded_hidden_evidence(self):
        view = self.render()
        self.assertIn('"matching": 2', view)
        self.assertIn('"outside": 1', view)
        self.assertIn('"omitted_lines_total": 1', view)
        self.assertIn('U+202E', view)
        self.assertIn('duplicate-key', view)
        self.assertIn('undated; time unknown', view)
        self.assertNotIn('"message": "outside"', view)
        self.assertIn('Independent digest checked: false', view)

    def test_bom_crlf_coordinates_match_original_bytes(self):
        wanted = {('queue.jsonl', 1), ('queue.jsonl', 2)}
        spans = w.original_lines(self.pack, wanted)
        data = base64.b64decode(self.pack['inputs'][0]['base64'])
        for _, (offset, physical, start, payload, _) in spans.items():
            self.assertEqual(data[offset:offset+len(physical)], physical)
            self.assertEqual(data[start:start+len(payload)], payload)
            self.assertTrue(physical.endswith(b'\r'))
            self.assertFalse(payload.endswith(b'\r'))
        self.assertEqual(spans['queue.jsonl', 1][2], 3)
        self.assertEqual(spans['queue.jsonl', 2][0], data.index(b'\n')+1)

    def test_half_open_window_does_not_include_adjacent_event(self):
        pack = w.window.replay.make_pack([('x',
            b'2026-10-18T10:00:01Z before\n2026-10-18T10:00:02Z inside\n2026-10-18T10:00:04Z after\n')])
        text = self.render(w.window.replay.canonical(pack))
        self.assertIn('"contained": 1', text)
        self.assertNotIn('"message": "before"', text)
        self.assertNotIn('"message": "after"', text)

    def test_forgery_rejected_before_scanning(self):
        self.pack['timeline']['events'][0]['message'] = 'forged'
        with patch.object(w.unicode.replay, 'pack', side_effect=AssertionError('scanned too soon')):
            with self.assertRaises(w.window.replay.ReplayError):
                self.render(w.window.replay.canonical(self.pack))

    def test_external_pin_and_exact_whitespace_domain(self):
        pin = hashlib.sha256(self.raw).hexdigest()
        self.assertIn('Independent digest checked: true', self.render(expected=pin))
        with self.assertRaises(ValueError):
            self.render(self.raw+b'\n', expected=pin)
        replacement = w.window.replay.make_pack([('x', b'2026-10-18T10:00:02Z replacement\n')])
        with self.assertRaises(ValueError):
            self.render(w.window.replay.canonical(replacement), expected=pin)

    def test_all_terminal_controls_are_inert(self):
        pack = w.window.replay.make_pack([('inert\x1b\u202e',
            '2026-10-18T10:00:02Z \x1b]52;c;X\x07\t\u202e\u200b\n'.encode())])
        view = self.render(w.window.replay.canonical(pack))
        self.assertTrue(all(c == '\n' or 32 <= ord(c) <= 126 for c in view))
        self.assertIn('bidi-control', view)
        self.assertNotIn('\x1b', view)

    def test_omitted_malformed_json_stays_incomplete(self):
        pack = w.window.replay.make_pack([('x', b'{"broken":\n')], ignore_unmatched=True)
        text = self.render(w.window.replay.canonical(pack))
        self.assertIn('JSON REVIEW INCOMPLETE', text)
        self.assertIn('undated; time unknown', text)

    def test_limits_keep_exact_totals(self):
        text = self.render(limit=0)
        self.assertIn('"not_shown": 2', text)
        self.assertIn('"omitted_lines_not_shown": 1', text)
        self.assertNotIn('CITATION ', text)
        for limit in (-1, 51, True):
            with self.assertRaises(ValueError):
                self.render(limit=limit)
        with patch.object(w, 'MAX_OUTPUT', 1), self.assertRaises(ValueError):
            self.render()

    def test_long_preview_and_findings_are_explicitly_truncated(self):
        pack = w.window.replay.make_pack([('x',
            ('2026-10-18T10:00:02Z ' + 'a'*300 + '\u202e'*30 + '\n').encode())])
        text = self.render(w.window.replay.canonical(pack))
        self.assertRegex(text, 'Original preview bytes omitted: [1-9][0-9]+')
        self.assertIn('"finding_count": 30', text)
        self.assertIn('"truncated": true', text)

    def test_strict_input_invalid_windows_and_immutability(self):
        before = copy.deepcopy(self.pack)
        self.render()
        self.assertEqual(self.pack, before)
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'null'):
            with self.assertRaises(ValueError):
                self.render(raw)
        with self.assertRaises(ValueError):
            w.render(self.raw, END, START)

    def test_source_provenance(self):
        root = HERE.parents[1]
        for row in json.loads((HERE/'provenance.json').read_text()):
            data = (root/row['snapshot']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            if 'source_status' in row:
                self.assertEqual(row['source_status'], 'historical_snapshot_before_source_and_message_filters')
                self.assertEqual(row['source'], 'line-3/tools/timeline-window/timeline_window.py')
                self.assertEqual(row['sha256'], 'fb937ce1d04728255a796320f1277c5a67043df0b738551536c021229e6a0385')
            else:
                self.assertEqual(data, (root/row['source']).read_bytes())

    def test_standalone_cli_and_no_partial_output(self):
        scratch = Path('test/scratch').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary)
            shutil.copytree(HERE, root/'tool')
            command = [sys.executable, '-B', str(root/'tool/window_review.py')]
            demo = subprocess.run(command+['demo'], cwd=root, capture_output=True)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            self.assertIn(b'U+202E', demo.stdout)
            (root/'pack.json').write_bytes(self.raw)
            args = ['review', 'pack.json', '--start', START, '--end', END]
            good = subprocess.run(command+args, cwd=root, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            bad = subprocess.run(command+args+['--expect-sha256', hashlib.sha256(b'different').hexdigest()],
                                 cwd=root, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, b'')
            escaped = subprocess.run(command+['review', str(HERE/'README.md'), '--start', START, '--end', END],
                                     cwd=root, capture_output=True)
            self.assertEqual(escaped.returncode, 2)
            self.assertEqual(escaped.stdout, b'')


if __name__ == '__main__':
    unittest.main()
