# Exact quantities before trust

Unit Flint checks calculations with exact rational arithmetic and explicit
physical dimensions. It runs offline with Python 3.10+ and only the standard
library. It neither reads inputs from files nor contacts any service.

From the repository root, check a speed claim:

```sh
python3 -B line-4/tools/unit-flint/unit_flint.py '10 km / 2 h' --expect '5 km/h' --to m/s --json
```

This prints the exact `25/18 m/s`, reports `check.matches: true`, and exits 0.
An unequal claim exits 1; invalid syntax or incompatible units exits 2.
See [the tool README](tools/unit-flint/README.md) for the grammar, limits,
diagnostics, examples and one-command regression suite. The check verifies
the supplied arithmetic, not the truth of a measured input.

Mark 23 adds claim checking while preserving the line's original goal.
[WALL.md](WALL.md) records dimensions, formats and visual review;
[USED.md](USED.md) records the sources used.

Mark 24 adds exact inclusive bounds. Check a supplied transfer-time calculation:

```sh
python3 -B line-4/tools/unit-flint/unit_flint.py '5 MiB / (2 MiB/s)' --at-least '2000 ms' --at-most '3 s' --to s --json
```

This returns `2.5 s`, both bounds pass, and exit 0. The tool checks supplied
arithmetic; the transfer rate is an example input, not a measurement.

Mark 25 adds [Calculation Receipt](tools/calculation-receipt/README.md), a
portable bundle that saves a calculation and recomputes it to check the saved
result. Its demo shows a passing receipt, a faithfully recorded failed bound,
and rejection of an altered result even when its checksum is recalculated:

```sh
python3 -B line-4/tools/calculation-receipt/receipt.py demo
```

Receipts identify exact supplied arithmetic and engine source; they do not
authenticate an author or establish the accuracy of a measurement.

Mark 26 adds [Interval Flint](tools/interval-flint/README.md), which encloses a
formula over user-supplied uncertain quantities using exact endpoints and unit
dimensions. The demo yields the hypothetical transfer-time interval
`[3.6, 5.5] s` and checks it against `[3, 6] s`:

```sh
python3 -B line-4/tools/interval-flint/interval_flint.py demo
```

The result is an enclosure, not a probability statement or a validation of
the supplied measurements. The line goal remains unchanged.

Mark 27 adds [Round Flint](tools/round-flint/README.md), a portable checker
for decimal display claims after exact unit conversion. Choose a rounding
rule and precision, then check a proposed displayed result:

```sh
python3 -B line-4/tools/round-flint/round_flint.py '10 km / 2 h' --to m/s --places 2 --expect 1.39
```

This returns exact `25/18 m/s`, rounded `1.39`, exact rounding error
`1/900 m/s`, and a passing display check. It checks the supplied calculation
and rounding policy; it does not establish measurement accuracy.
