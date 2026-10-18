import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import policy_benchmark as app


class PolicyBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.raw = (app.HERE / 'cases.json').read_bytes()
        self.pack = app.freeze_cases(self.raw)
        self.pin = self.pack['seal_sha256']
        self.packed = app.canonical(self.pack)

    def test_real_execution_and_recheck(self):
        receipt, rows = app.measure(self.packed, self.pin)
        self.assertEqual([sum(r['passed'][n] for r in rows) for n in app.policies.NAMES], [10, 14, 18])
        self.assertEqual(len(rows), 18)
        result = app.recheck(app.canonical(receipt), self.pin, receipt['receipt_sha256'])
        self.assertEqual(result['status'], 'replayed_and_reexecuted')

    def test_freeze_does_not_execute_policies(self):
        with patch.object(app.policies, 'accepts', side_effect=AssertionError('ran too early')):
            self.assertEqual(app.freeze_cases(self.raw), self.pack)

    def test_pin_rejected_before_execution(self):
        with patch.object(app.policies, 'accepts', side_effect=AssertionError('ran too early')):
            with self.assertRaisesRegex(ValueError, 'seal mismatch'):
                app.measure(self.packed, 'f' * 64)

    def test_rehashed_replacement_against_original_pin(self):
        altered = copy.deepcopy(self.pack)
        case = json.loads(app.seal.decode_blob(altered['content']['cases'][0]['data_b64']))
        case['expected_accept'] = False
        altered['content']['cases'][0]['data_b64'] = app.seal.encode(app.canonical(case))
        altered['seal_sha256'] = app.frozen.digest(app.canonical(altered['content']))
        with self.assertRaisesRegex(ValueError, 'seal mismatch'):
            app.measure(app.canonical(altered), self.pin)

    def test_foreign_policy_pack_rejected_even_with_matching_new_pin(self):
        altered = copy.deepcopy(self.pack)
        altered['content']['systems'][0]['data_b64'] = app.seal.encode(b'print("do not execute")')
        altered['seal_sha256'] = app.frozen.digest(app.canonical(altered['content']))
        with patch.object(app.policies, 'accepts', side_effect=AssertionError('ran too early')):
            with self.assertRaisesRegex(ValueError, 'fixed policies'):
                app.measure(app.canonical(altered), altered['seal_sha256'])

    def test_forged_but_algebraically_valid_outcomes_fail_reexecution(self):
        receipt, _ = app.measure(self.packed, self.pin)
        csv = app.evidence.unblob(receipt['body']['results_b64'])
        forged = app.evidence.make(self.packed, csv.replace(b'empty-object,1,1,1', b'empty-object,0,1,1'), self.pin)
        # A valid analytical receipt need not represent what was actually run.
        app.evidence.replay(app.canonical(forged), self.pin, forged['receipt_sha256'])
        with self.assertRaisesRegex(ValueError, 'fresh execution differs'):
            app.recheck(app.canonical(forged), self.pin, forged['receipt_sha256'])

    def test_handoff_pin_rejected(self):
        receipt, _ = app.measure(self.packed, self.pin)
        with self.assertRaisesRegex(ValueError, 'handoff pin'):
            app.recheck(app.canonical(receipt), self.pin, 'f' * 64)

    def test_runtime_change_rejected_before_execution(self):
        with patch.object(app, 'runtime', return_value={'changed': True}):
            with self.assertRaisesRegex(ValueError, 'runtime'):
                app.measure(self.packed, self.pin)

    def test_case_ids_and_booleans_are_strict(self):
        for change in ('duplicate', 'integer', 'unknown_field', 'text_type'):
            data = json.loads(self.raw)
            if change == 'duplicate':
                data['cases'][1]['id'] = data['cases'][0]['id']
            elif change == 'integer':
                data['cases'][0]['expected_accept'] = 1
            elif change == 'unknown_field':
                data['cases'][0]['execute'] = 'untrusted'
            else:
                data['cases'][0]['text'] = 7
            with self.subTest(change=change), self.assertRaises(ValueError):
                app.freeze_cases(app.canonical(data))

    def test_duplicate_json_and_budgets(self):
        with self.assertRaises(ValueError):
            app.freeze_cases(b'{"schema":"json-policy-cases-v1","cases":[],"cases":[]}')
        for cases in ([], [{'id': 'x', 'text': 'a' * 8193, 'expected_accept': True}],
                      [{'id': str(i), 'text': '{}', 'expected_accept': True} for i in range(257)]):
            with self.assertRaises(ValueError):
                app.freeze_cases(app.canonical({'schema': 'json-policy-cases-v1', 'cases': cases}))

    def test_custom_labels_are_scored_not_replaced_with_policy_oracle(self):
        custom = {'schema': 'json-policy-cases-v1', 'cases': [
            {'id': 'caller-label', 'text': '{}', 'expected_accept': False}]}
        pack = app.freeze_cases(app.canonical(custom))
        _, rows = app.measure(app.canonical(pack), pack['seal_sha256'])
        self.assertEqual(list(rows[0]['passed'].values()), [0, 0, 0])

    def test_policy_edge_cases(self):
        strict = app.policies.NAMES[2]
        for text in ('{"x":{"a":1,"\\u0061":2}}', '-1e400', '[NaN]', '[1,]'):
            self.assertFalse(app.policies.accepts(strict, text), text)
        for text in ('[{"a":1},{"a":2}]', '"Infinity"', '1e-400', 'null'):
            self.assertTrue(app.policies.accepts(strict, text), text)
        with self.assertRaises(ValueError):
            app.policies.accepts('unknown', '{}')

    def test_inputs_not_mutated_and_deterministic(self):
        before = self.packed
        first, _ = app.measure(self.packed, self.pin)
        second, _ = app.measure(self.packed, self.pin)
        self.assertEqual(app.canonical(first), app.canonical(second))
        self.assertEqual(before, app.canonical(self.pack))

    def test_snapshot_identity(self):
        entries = json.loads((app.HERE / 'provenance.json').read_text())
        for entry in entries:
            raw = (app.HERE / entry['file']).read_bytes()
            self.assertEqual(app.frozen.digest(raw), entry['sha256'])
            original = Path(entry['source'])
            if original.is_file():
                self.assertEqual(raw, original.read_bytes())

    def test_standalone_cli_and_empty_stdout_on_error(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary).resolve()
            target = root / 'tool'
            shutil.copytree(app.HERE, target)
            def cli(*args):
                return subprocess.run([sys.executable, '-B', 'tool/policy_benchmark.py', *args],
                                      cwd=root, capture_output=True, check=False)
            frozen = cli('freeze', '--cases', 'tool/cases.json')
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            pack = json.loads(frozen.stdout)
            (root / 'pack.json').write_bytes(frozen.stdout)
            measured = cli('run', '--pack', 'pack.json', '--expected-seal-sha256', pack['seal_sha256'])
            self.assertEqual(measured.returncode, 0, measured.stderr)
            receipt = json.loads(measured.stdout)
            (root / 'receipt.json').write_bytes(measured.stdout)
            checked = cli('recheck', '--receipt', 'receipt.json', '--expected-seal-sha256', pack['seal_sha256'],
                          '--expected-receipt-sha256', receipt['receipt_sha256'])
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)['status'], 'replayed_and_reexecuted')
            failed = cli('run', '--pack', 'pack.json', '--expected-seal-sha256', 'f' * 64)
            self.assertEqual(failed.returncode, 2)
            self.assertEqual(failed.stdout, b'')
            # The parent workspace file exists, but is outside this workspace.
            outside = cli('freeze', '--cases', str(app.HERE / 'cases.json'))
            self.assertEqual(outside.returncode, 2)
            self.assertEqual(outside.stdout, b'')


if __name__ == '__main__':
    unittest.main()
