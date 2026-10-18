"""Independent decimal oracle, dimensional conversion and real CLI checks."""
from decimal import (Decimal, localcontext, ROUND_HALF_EVEN, ROUND_HALF_UP,
                     ROUND_DOWN, ROUND_FLOOR, ROUND_CEILING)
from fractions import Fraction
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

import round_flint as rf


class RoundingTests(unittest.TestCase):
    def test_documented_speed(self):
        r = rf.calculate("10 km / 2 h", "m/s", 2, expect="1.39")
        self.assertEqual(r["exact_value"], "25/18")
        self.assertEqual(r["rounded"], "1.39")
        self.assertEqual(r["error"], "1/900")
        self.assertTrue(r["check"]["matches"])
        self.assertFalse(r["halfway"])

    def test_decimal_not_binary_ties(self):
        for expr, even, away in (("2.675", "2.68", "2.68"),
                                 ("2.665", "2.66", "2.67"),
                                 ("-2.665", "-2.66", "-2.67")):
            self.assertEqual(rf.calculate(expr, "1", 2)["rounded"], even)
            r = rf.calculate(expr, "1", 2, "half-away")
            self.assertEqual(r["rounded"], away)
            self.assertTrue(r["halfway"])

    def test_signed_direction_and_zero(self):
        for mode, expected in (("floor", "-1.24"), ("ceiling", "-1.23"),
                               ("toward-zero", "-1.23")):
            self.assertEqual(rf.calculate("-1.231", "1", 2, mode)["rounded"], expected)
        self.assertEqual(rf.calculate("-0.004", "1", 2)["rounded"], "0.00")
        self.assertEqual(rf.calculate("9.995", "1", 2)["rounded"], "10.00")
        self.assertEqual(rf.calculate("-0.5", "1", 0)["rounded"], "0")
        self.assertEqual(rf.calculate("0", "1", 18)["rounded"], "0.000000000000000000")

    def test_independent_decimal_oracle(self):
        rng = random.Random(2704)
        modes = dict(zip(rf.MODES, (ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_DOWN,
                                   ROUND_FLOOR, ROUND_CEILING)))
        # Denominators have only factors 2 and 5: all oracle inputs terminate
        # exactly, so Decimal's context cannot perturb a tie decision.
        for _ in range(500):
            n, denominator, places = rng.randint(-10**12, 10**12), 10**rng.randrange(7), rng.randrange(7)
            value = Fraction(n, denominator)
            for mode, decimal_mode in modes.items():
                with localcontext() as ctx:
                    ctx.prec = 100
                    exact = Decimal(n) / Decimal(denominator)
                    expected = exact.quantize(Decimal(1).scaleb(-places), rounding=decimal_mode)
                integer, _ = rf.rounded_integer(value * 10**places, mode)
                self.assertEqual(Fraction(integer, 10**places), Fraction(expected))

    def test_fraction_error_and_nearest_bound(self):
        rng = random.Random(2705)
        for _ in range(200):
            n, d, places = rng.randint(-10000, 10000), rng.randint(1, 999), rng.randrange(5)
            r = rf.calculate(f"{n} m / {d}", "cm", places)
            exact = Fraction(n * 100, d)
            error = Fraction(r["rounded"]) - exact
            self.assertEqual(Fraction(r["error"]), error)
            self.assertEqual(Fraction(r["error_base_value"]), error / 100)
            self.assertLessEqual(abs(error), Fraction(1, 2 * 10**places))

    def test_dimensions_and_scaled_target(self):
        r = rf.calculate("1 in", "cm", 1)
        self.assertEqual((r["exact_value"], r["rounded"], r["error_base_value"]),
                         ("2.54", "2.5", "-0.0004"))
        self.assertEqual(rf.calculate("3 m", "2*m", 0)["rounded"], "2")
        for expr, target in (("0 m", "s"), ("1 m", "0*m"),
                             ("1 m", "-m"), ("1 m + 1 s", "m"),
                             ("1 m / 0", "m"), ("1 m", "m+s")):
            with self.assertRaises((ValueError, rf.UnitError)):
                rf.calculate(expr, target)

    def test_display_claim_validation(self):
        for claim in ("1.2", "01.20", "+1.20", "1.20 m", "1.2e0", " 1.20",
                      "1.20\n", "١.٢٠", "-0.00", "9" * 701, "", 1.2):
            with self.assertRaises(ValueError, msg=repr(claim)):
                rf.calculate("1.2 m", "m", 2, expect=claim)
        self.assertFalse(rf.calculate("1.2 m", "m", 2, expect="1.21")["check"]["matches"])
        self.assertTrue(rf.calculate("1.2 m", "m", 2, expect="1.20")["check"]["matches"])

    def test_budgets(self):
        for places in (-1, 19, True, 2.0):
            with self.assertRaises(ValueError):
                rf.calculate("1 m", "m", places)
        for expr in ("-" * 1100 + "1", "(" * 40 + "1" + ")" * 40,
                     "1e201", "(1e100)^12", "1" * 4097):
            with self.assertRaises(rf.UnitError):
                rf.calculate(expr, "1")
        with self.assertRaises(rf.UnitError):
            rf.calculate("(1e100)^6", "1", 18)
        with self.assertRaises(ValueError):
            rf.calculate("1", "1", mode="guess")

    def test_real_cli_statuses_and_streams(self):
        script = str(Path(__file__).with_name("round_flint.py"))
        cases = [(["10 km / 2 h", "--to", "m/s", "--expect", "1.39"], 0),
                 (["10 km / 2 h", "--to", "m/s", "--expect", "1.38"], 1),
                 (["0 m", "--to", "s"], 2),
                 (["1", "--to", "1", "--expect", "1.0"], 2),
                 (["--to", "1", "--expect=-1.24", "--mode", "floor", "--", "-1.231"], 0)]
        for args, status in cases:
            p = subprocess.run([sys.executable, "-B", script, *args],
                               capture_output=True, text=True, timeout=10)
            self.assertEqual(p.returncode, status, p.stderr)
            if status == 2:
                self.assertEqual(p.stdout, "")
                self.assertIn("round-flint:", p.stderr)
            else:
                self.assertEqual(p.stderr, "")
                self.assertEqual(json.loads(p.stdout)["check"]["matches"], status == 0)


if __name__ == "__main__":
    unittest.main()
