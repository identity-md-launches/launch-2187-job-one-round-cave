import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('text_window', HERE / 'unicode_text_window.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class TextWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (Path.cwd() / 'test/scratch').mkdir(parents=True, exist_ok=True)

    def test_multibyte_crlf_original_ranges(self):
        raw = 'é\r\nhello\u202e!'.encode()
        item = w.review(raw)['findings'][0]['source']
        self.assertEqual((item['byte_start'], item['byte_end']), (9, 12))
        self.assertEqual((item['line'], item['byte_column']), (2, 6))
        self.assertEqual(item['sha256'], hashlib.sha256(raw[9:12]).hexdigest())

    def test_collision_keeps_first_original_spelling(self):
        raw = 'owner\nоwner'.encode()
        item = next(f for f in w.review(raw)['findings'] if f['rule'] == 'lookalike-collision')
        self.assertEqual((item['source']['byte_start'], item['source']['byte_end']), (6, 12))
        self.assertEqual((item['first_source']['byte_start'], item['first_source']['byte_end']), (0, 5))
        self.assertEqual(item['first_source']['preview']['bytes'], 'owner')

    def test_hostile_terminal_and_source_label(self):
        text, count = w.render(b'\x1b]52;c;payload\x07\r\t', '\x1b\u202e')
        self.assertGreater(count, 0)
        self.assertTrue(all(c == '\n' or 32 <= ord(c) <= 126 for c in text))
        self.assertNotIn('\x1b', text)

    def test_literal_escapes_not_decoded(self):
        self.assertEqual(w.review(br'hello\u202e')['finding_count'], 0)
        self.assertEqual(w.review('hello\u202e'.encode())['finding_count'], 1)

    def test_omissions_are_explicit(self):
        raw = '\u202e\u200b\x1b'.encode()
        report = w.review(raw, max_findings=1)
        self.assertEqual((report['finding_count'], report['retained_findings'], report['omitted_findings']), (3, 1, 2))
        self.assertTrue(report['truncated'])

    def test_large_identifier_bounded_without_losing_full_hash(self):
        raw = ('a' * 10000 + 'а').encode()
        report = w.review(raw)
        span = report['findings'][0]['source']
        self.assertEqual(span['byte_end'], len(raw))
        self.assertEqual(span['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(span['omitted_span_bytes'], len(raw) - 64)
        self.assertLess(len(w.render(raw)[0]), 4000)

    def test_invalid_utf8_and_bounds(self):
        for raw, limit in ((b'\xff', 1), (b'a', 0), (b'a', True), (b'a', 1001),
                           (b'a' * (w.lantern.MAX_BYTES + 1), 1)):
            with self.subTest(limit=limit, size=len(raw)):
                with self.assertRaises(ValueError):
                    w.review(raw, max_findings=limit)

    def test_output_budget(self):
        with patch.object(w, 'MAX_OUTPUT', 1):
            with self.assertRaisesRegex(ValueError, 'output budget'):
                w.render(b'abc')

    def test_no_findings_not_safety(self):
        text, count = w.render(b'normal text')
        self.assertEqual(count, 0)
        self.assertIn('Not a safety verdict', text)

    def test_byte_notation(self):
        self.assertEqual(w.byte_text(b'\\x1b\x1b\n\xff'), r'\\x1b\x1b\x0a\xff')

    def test_all_scanner_values_match_source_bytes(self):
        raw = ('é\nＡowner\nAowner\nоwner\nowner\n\u034f\ufe0f\U000e0100\u200b\x00').encode()
        for item in w.review(raw)['findings']:
            for key in ('source', 'first_source'):
                if key in item:
                    span = item[key]
                    self.assertEqual(span['sha256'], hashlib.sha256(raw[span['byte_start']:span['byte_end']]).hexdigest())

    def test_cli_status_and_empty_stdout_on_error(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd() / 'test/scratch') as tmp:
            p = Path(tmp) / 'source.txt'
            for raw, status in ((b'hello', 0), (b'\x1b', 1), (b'\xff', 2)):
                p.write_bytes(raw)
                result = subprocess.run([sys.executable, '-B', str(HERE / 'unicode_text_window.py'),
                                         '--file', str(p)], capture_output=True)
                self.assertEqual(result.returncode, status, result.stderr)
                if status == 2:
                    self.assertEqual(result.stdout, b'')
                    self.assertTrue(all(b == 10 or 32 <= b <= 126 for b in result.stderr))

    def test_workspace_escape_rejected_before_read(self):
        with self.assertRaisesRegex(ValueError, 'workspace'):
            w.lantern.workspace_file(Path.cwd().parent / 'not-an-input')

    def test_portable_two_folder_copy(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd() / 'test/scratch') as tmp:
            root = Path(tmp)
            for name in ('unicode-text-window', 'unicode-lantern'):
                shutil.copytree(HERE.parent / name, root / name)
            result = subprocess.run([sys.executable, '-B', str(root / 'unicode-text-window/unicode_text_window.py'),
                                     '--demo'], cwd=root, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b'lookalike-collision', result.stdout)


if __name__ == '__main__':
    unittest.main()
