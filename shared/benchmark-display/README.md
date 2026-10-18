# Benchmark Display

Show pass rates and candidate effects from a completely replayed binary benchmark
receipt with explicit exact decimal rounding. This connects Line 1's benchmark
evidence to Line 4's Round Flint. Copy this entire folder for offline use with
Python 3.10+ and its standard library; there are no installations or network calls.
Nine unchanged ordinary-file snapshots are listed in [provenance.json](provenance.json).

One command from the repository root:

```sh
python3 -B shared/benchmark-display/benchmark_display.py demo
```

Observed: the three fixed JSON policies actually execute on 18 curated cases,
then reexecute against their retained receipt. Their pass counts are 10, 14, 18;
their exact percentages are `500/9`, `700/9`, `100/1`, displayed as `55.56`,
`77.78`, `100.00`. Rounding errors (display minus exact) are `1/225`, `1/450`,
`0` percentage points. Effects against the baseline are `22.22` and `44.44`
percentage points. The full observed view is in
[the gathering result](../../gathering/benchmark-display-demo.json).

These hand-authored, related regression cases are not a representative sample.
The exact conditional Holm p-values are `1/8` and `1/64`; the latter crosses
alpha 0.05, but **this fixture does not support population inference**. The demo
does not prove preregistration time, independent execution or source honesty.
Its pins are generated in the run, not independently authenticated.

For an existing Evidence Receipt or Policy Benchmark receipt, use the two actual
pins you retained independently (the uppercase tokens below are explanatory):

```sh
python3 -B shared/benchmark-display/benchmark_display.py receipt --file path/to/receipt.json --expected-seal-sha256 YOUR_PRE_OUTCOME_PIN --expected-receipt-sha256 YOUR_HANDOFF_PIN
```

The entire receipt, assets, observation admission and exact analysis replay
before any stdout is emitted. This command performs analytical replay; it does
not execute the candidate systems. Use Policy Benchmark's `recheck` for fresh
execution of its three fixed policies. The reading view is not a replacement
receipt or a new authentication format. Keep the original receipt and pins.
External receipts require the same four evidence-engine source identities.

Both commands accept `--places 0..18` (default 2) and `--mode half-even`,
`half-away`, `toward-zero`, `floor` or `ceiling`. Rates and effects are recomputed
from integer counts through Round Flint's exact fraction arithmetic; they never
use the predecessor's floating point percentage display. Exact fractions,
rounded decimals, halfway flags and exact rounding errors travel together.
P-values stay exact numerator/denominator pairs. All original test decisions
are retained unchanged; rounding never affects a test threshold. A non-rejection
does not establish equivalence. Rounding adds no confidence interval, measurement
uncertainty or significant-figure claim.

Exit 0 means the reading view completed, regardless of the systems' pass counts
or test decisions. Exit 2 means invalid input, options, pins or replay failure,
with empty stdout. Output is ASCII JSON with escaped control characters and one
final LF; do not unescape it before terminal display. JSON escaping is not HTML
escaping. Input must be an explicit regular workspace file, at most 12 MiB;
output is capped at 4 MiB. Only that input and fixed shipped sources/fixtures
are read. Nothing is written, signed, sent, paid or deployed. No environment,
wallet, secret, account or host configuration is accessed. These calculations
need no currency; no invented ZTO/IMD price or interaction is introduced.

```sh
python3 -B -m unittest discover -s shared/benchmark-display -v
```

Nine tests passed: actual policy execution and rates, independent Fraction
checks for error direction/bounds, negative ties and 18-place displays, unchanged
exact decisions/p-values across every rounding mode, bad pins, rehashed forged
analysis, invalid options, deterministic immutable inputs, snapshot identity,
and a copied-folder CLI with successful receipt replay and empty stdout on
errors. These are local checks, not independent certification.
