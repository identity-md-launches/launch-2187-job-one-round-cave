import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import benchmark_display as app


class DisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = app.evidence.demo_receipt()
        cls.raw = app.evidence.canonical(cls.receipt)
        cls.seal = cls.receipt['body']['seal_check']['seal_sha256']
        cls.pin = cls.receipt['receipt_sha256']

    def test_actual_policies_and_exact_percentages(self):
        report = app.demo()
        self.assertEqual([r['passes'] for r in report['systems']], [10, 14, 18])
        self.assertEqual([r['pass_percent']['display'] for r in report['systems']], ['55.56', '77.78', '100.00'])
        self.assertIn('reexecution', report['verification'])
        self.assertIn('not a representative sample', report['fixture'])

    def test_fraction_oracle_for_rates_and_errors(self):
        for numerator in range(-18, 19):
            for denominator in (1, 3, 7, 18):
                for mode in app.rounding.MODES:
                    result = app.ratio(numerator, denominator, 2, mode)
                    exact = Fraction(numerator, denominator)
                    self.assertEqual(Fraction(result['exact_fraction']), exact)
                    self.assertEqual(Fraction(result['rounding_error']), Fraction(result['display']) - exact)
                    error = Fraction(result['rounding_error'])
                    if mode in ('half-even', 'half-away'):
                        self.assertLessEqual(abs(error), Fraction(1, 200))
                    elif mode == 'floor':
                        self.assertTrue(-Fraction(1, 100) < error <= 0)
                    elif mode == 'ceiling':
                        self.assertTrue(0 <= error < Fraction(1, 100))
                    else:
                        self.assertLess(abs(error), Fraction(1, 100))
                        self.assertLessEqual(abs(Fraction(result['display'])), abs(exact))

    def test_signed_ties_and_precision(self):
        self.assertEqual(app.ratio(-5, 2, 0, 'half-even')['display'], '-2')
        self.assertEqual(app.ratio(-5, 2, 0, 'half-away')['display'], '-3')
        self.assertEqual(app.ratio(1, 3, 18, 'half-even')['display'], '0.333333333333333333')

    def test_exact_decisions_and_pvalues_survive_all_displays(self):
        original = self.receipt['body']['analysis']['candidates']
        for mode in app.rounding.MODES:
            report = app.summarize(self.raw, self.seal, self.pin, 0, mode)
            for before, after in zip(original, report['comparisons']):
                self.assertEqual(after['familywise_reject_equal_discordance'], before['familywise_reject_equal_discordance'])
                self.assertEqual(after['holm_adjusted_p'], {k: before['holm_adjusted_p'][k] for k in ('numerator', 'denominator')})

    def test_wrong_pins_fail(self):
        for seal, pin in (('f'*64, self.pin), (self.seal, 'f'*64)):
            with self.assertRaises(ValueError):
                app.summarize(self.raw, seal, pin)

    def test_rehashed_forged_analysis_fails(self):
        forged = copy.deepcopy(self.receipt)
        forged['body']['analysis']['baseline_passes'] += 1
        forged['receipt_sha256'] = app.evidence.digest(app.evidence.canonical(forged['body']))
        with self.assertRaises(ValueError):
            app.summarize(app.evidence.canonical(forged), self.seal, forged['receipt_sha256'])

    def test_bad_options_fail_and_inputs_stay_exact(self):
        for places, mode in ((True, 'half-even'), (-1, 'floor'), (19, 'floor'), (2, 'other')):
            with self.assertRaises(ValueError):
                app.summarize(self.raw, self.seal, self.pin, places, mode)
        before = bytes(self.raw)
        self.assertEqual(app.summarize(self.raw, self.seal, self.pin), app.summarize(self.raw, self.seal, self.pin))
        self.assertEqual(before, self.raw)

    def test_source_snapshots(self):
        root = app.HERE.parents[1]
        for entry in json.loads((app.HERE/'provenance.json').read_text()):
            source = (root/entry['source']).read_bytes()
            snapshot = (root/entry['snapshot']).read_bytes()
            self.assertEqual(source, snapshot)
            self.assertEqual(hashlib.sha256(snapshot).hexdigest(), entry['sha256'])

    def test_copied_folder_offline_cli_and_no_partial_stdout(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary).resolve()
            shutil.copytree(app.HERE, root/'tool')
            command = [sys.executable, '-B', 'tool/benchmark_display.py']
            run = subprocess.run(command+['demo'], cwd=root, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(all(c == 10 or 32 <= c <= 126 for c in run.stdout))
            (root/'receipt.json').write_bytes(self.raw)
            args = ['receipt', '--file', 'receipt.json', '--expected-seal-sha256', self.seal,
                    '--expected-receipt-sha256', self.pin]
            run = subprocess.run(command+args, cwd=root, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['verification'], 'complete_analytical_replay')
            for extra in (['--places', '19'], ['--expected-receipt-sha256', 'f'*64],
                          ['--file', str(app.HERE/'README.md')]):
                bad = subprocess.run(command+args+extra, cwd=root, capture_output=True)
                self.assertEqual(bad.returncode, 2)
                self.assertEqual(bad.stdout, b'')


if __name__ == '__main__':
    unittest.main()
