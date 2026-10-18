# Round Flint

Check whether a displayed decimal follows from a calculation, its units, a
specified number of decimal places and an explicit rounding rule. Calculations
and conversion use exact fractions throughout, so `2.675` rounded to two places
is `2.68` with the default nearest, ties-to-even rule. No binary floating point
or decimal context precision participates in the decision.

One command from the repository root shows it working offline:

```sh
python3 -B line-4/tools/round-flint/round_flint.py '10 km / 2 h' --to m/s --places 2 --expect 1.39
```

Tried locally: exit **0**, exact value `25/18 m/s`, rounded display `1.39`,
`check.matches: true`, and error `1/900 m/s`. Changing `--expect` to `1.38`
produced exit **1** with `matches: false`. Converting `0 m` to `s` produced
exit **2**, a diagnostic on stderr and no stdout. These are supplied arithmetic
examples, not measured speed or accuracy claims.

The output is one JSON object. `exact_value`, `rounded`, `quantum`, and `error`
are in the requested target unit; `error_base_value` is in `base_unit`.
Error always means **rounded minus exact**. `halfway` identifies an exact
midpoint between adjacent multiples of the quantum, even with a directed mode.
Without `--expect`, a valid calculation exits 0. Invalid inputs exit 2; a valid
but unequal display claim exits 1. Output includes the original expression,
target unit expression, places, mode, and schema `round-flint/v1`.

`--places` is an integer from 0 through 18 (default 2). The quantum is
`10^-places` target units. The supported `--mode` choices are:

| Mode | Rule |
| --- | --- |
| `half-even` (default) | Nearest quantum; at a tie choose the even scaled integer. |
| `half-away` | Nearest quantum; ties go away from zero. |
| `toward-zero` | Drop the fractional part of the scaled value. |
| `floor` | Round toward negative infinity. |
| `ceiling` | Round toward positive infinity. |

For example, `-1.231` becomes `-1.24` with `floor`, and `-1.23` with
`ceiling` or `toward-zero`, at two places. Rounded zero is always `0.00`
at two places; no negative zero is emitted.

`--expect` is a **display claim in the target unit**, not a quantity expression.
It must be a plain ASCII decimal with exactly the requested number of decimal
places, no leading zeros except the single zero before the decimal point,
no leading plus, no exponent, no surrounding whitespace, and no negative zero.
At zero places it must be an integer. Thus `1.20` is valid at two places;
`1.2`, `1.20 m`, and `1.2e0` are invalid. This deliberately checks both value
and declared display precision. For a negative claim use `--expect=-1.24`.
For a negative positional expression, put options first and then `--`:

```sh
python3 -B line-4/tools/round-flint/round_flint.py --to 1 --mode floor --places 2 --expect=-1.24 -- '-1.231'
```

The inherited Unit Flint grammar accepts quantities, unit arithmetic,
parentheses, signs and integer powers. `--to` is required and accepts a positive
unit scale expression, including `1` for dimensionless results and `2*m` for
a scaled unit. Dimensions must match even for zero. Rounding happens **after**
conversion. As in Unit Flint, `2 m^2` means `(2 m)^2`; write `2 * m^2` for
two square metres.

Copy this whole folder to use it independently. Python 3.10+ and its standard
library are the only dependencies. The adjacent `engine.py` is a byte-identical
snapshot of the inherited Unit Flint at mark 24, SHA-256
`c683e558cdbdf6cf73d4b32572b6fa498b80e7816483b882bf2d51adfff3062e`.
No network, configuration, environment, wallet, or data-file access is used.
The formula/target parser retains its 4,096-character, 256-token, 32-level,
2,048-bit exact value and bounded-dimension limits. New scaled values and
error calculations share the exact-value budget. Claims are limited to 700
characters. Deliberately over-budget calculations can fail even when their
final mathematical result would be small.

Run the regression suite:

```sh
python3 -B -m unittest discover -s line-4/tools/round-flint -v
```

Tried locally: all **nine tests passed**, including 2,500 seeded comparisons
with an independent `decimal` oracle (exact terminating oracle inputs), 200
rational conversion/error checks, signed ties, decimal `2.675`, carry into
the integer part, all five modes, precision validation, dimension/resource
errors and actual subprocess exit/stream behavior. These are local checks,
not exhaustive verification or independent certification.

Limits: this checks rounding of supplied arithmetic; it does not establish
measurement accuracy, significant figures, uncertainty, source honesty, or
whether the selected units and rounding policy suit a particular application.
No currency value or coin is needed for rounding, so no ZTO or IMD exchange
rate is inferred. The existing exact and interval tools are unchanged.
