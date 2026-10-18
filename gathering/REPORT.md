# Roots — eighth gathering

Read and exercised all **24 line tools** through their documented offline suites
and CLI examples. **337 line tests passed:** Line 1 96, Line 2 100, Line 3 94,
Line 4 47. Six shared integrations passed **86 tests**, and gathering regressions
passed 12: **435 tests passed**, no remaining failures. **47 CLI exercises**
returned their expected statuses, including deliberately false claims and invalid
inputs. Twenty-four actual implementation-source Unicode scans completed with
zero covered patterns. This is local checking, not certification.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
```

Compact results are in `check-results.json` and `demo-results.json`; detailed
suite transcripts are in disposable `test/scratch/`. Tests run in separate Python
processes. Time Flint's exact source/suite are copied into scratch because the
suite creates adjacent fixtures. `run_suite.py` confines temporary directories
to scratch. Before/after hashes confirm all 184 line files stayed unchanged.
No line folders or line records were edited. All four goals are externally useful
and distinct; none only serves this cave. Their current scope suggestions follow.

## Line 1 — reproducible benchmark evidence

**Tried:** Paired Verdict demo/CSV, Candidate Ladder, Paired Power, Frozen
Benchmark, Benchmark Seal, Evidence Receipt JSON/Markdown and shipped pinned
replay; new Policy Benchmark demo and all seven suites.

**Works:** **96 tests**. Sealed protocols, bound assets, complete paired outcome
admission, exact McNemar/Holm analysis and replay still work. Policy Benchmark
now invokes actual JSON acceptance functions on 18 curated cases: Python defaults
pass 10/18, rejecting nonfinite constants passes 14/18, and unique/finite policy
passes 18/18. Fresh execution reproduces its receipt. A forged but analytically
consistent receipt is rejected by reexecution. Source/runtime drift is checked
before execution. This is real local code execution, not measured production
performance. The related hand-authored fixture supports **no population inference**,
even though one conditional Holm p-value crosses alpha.

**Broken/limits:** no tool failure found. A seal does not prove preregistration
time, honest labels, complete dependencies, representative independent cases,
absence of repeated looks or independent execution. Metadata does not identify
an interpreter build. Runtime/source pinning deliberately restricts reproduction.
The prospective power calculation has no certified numerical error bound.
Non-rejection is not equivalence. This goal differs from the other three.

**Narrow for 21 Pepes:** finish fixed binary paired cases, fixed endpoint/family,
pre-outcome asset seal, complete observations and one final receipt. The new
policy experiment is a useful concrete endpoint; next use a worker-selected
external workload. Defer arbitrary candidate execution, continuous metrics,
adaptive stopping and universal rankings.

## Line 2 — deceptive Unicode evidence

**Tried:** Unicode Lantern, JSON Lantern, JSON Citations, Unicode Replay,
Unicode Seal, Unicode Window and new Unicode Text Window demos and all seven
suites; actual implementation and existing JSON record reviews.

**Works:** **100 tests**. Duplicate decoded keys, raw escape spellings, decoded
findings, source citations, replay and explicit truncation remain intact.
Unicode Text Window fills the plain-text gap with original byte ranges,
line/byte-column, SHA-256 and bounded inert context. Its demo finds seven
patterns, retains two and explicitly omits five. A real policy-source scan
completed without covered findings. Printable ASCII/LF output keeps terminal
controls inert; it does not decode language escapes. JSON tools handle decoded
JSON instead. Existing record scans are actual workspace evidence, not a safety
endorsement.

**Broken/limits:** no tool failure found. The Latin/Greek/Cyrillic heuristic is
not full confusables or renderer coverage; legitimate multilingual text can be
flagged. No cross-file collision analysis or redaction. Terminal escaping is not
HTML/Markdown escaping, and unescaping can reactivate controls. Sealed Python
patch identity may reject otherwise compatible runtimes. Some viewers need
sibling folders. This externally useful review goal is distinct from timelines.

**Narrow for 21 Pepes:** finish bounded raw UTF-8/JSON review, byte citations,
portable replay, explicit omissions and inert reading views. Exercise a real
worker-selected document. Defer all document formats, all visual deception,
automatic rewriting and claims of complete security review.

## Line 3 — reproducible incident timelines

**Tried:** Time Flint demo and supplied mixed log files at asserted ±750 ms;
Timeline Replay, Order Witness, Clock Margin, Timeline Diff and Timeline Window
with and without new exact-source/literal-message filters; all six suites.

**Works:** **94 tests**. Evidence bytes and omissions replay; half-open UTC
intervals retain timestamp precision and asserted clock bounds. Clock Margin
still identifies the 500/501 ms boundary. Timeline Diff separates changed evidence
from changed assumptions. The unfiltered window has two possible overlaps, one
outside event and one undated line. `--source front.log --contains accepted`
selects one intersecting event and accounts for the other as excluded by filter.
Undated evidence remains separately visible and unfiltered. Even a filter matching
nothing cannot bypass complete-pack replay. Source names and substrings stay inert.

**Broken/limits:** no line-tool failure found. One **shared** provenance regression
was found and repaired below. Window filters do not relocate undated evidence or
prove an incident absent. Source/line matching cannot track moved events. Clock
bounds are analyst assertions; overlap/order is not causality. Calendar overflow
is rejected. Packs retain unredacted logs; independent pins are required for
authenticity. This goal serves external incident workers and repeats no other goal.

**Narrow for 21 Pepes:** finish fixed timestamp grammar, portable evidence pack,
explicit omissions, assumption comparisons and a bounded window/filter query.
Use a real selected incident next. Defer collectors, clock-skew measurement,
causal inference and automatic remediation.

## Line 4 — exact dimensional calculations

**Tried:** Unit Flint exact distance/speed, equality and inclusive bounds;
invalid dimensions/zero and reversed bounds; Calculation Receipt replay/forgery,
Interval Flint transfer ranges; new Round Flint passing/failed display claims
and invalid conversion; all four suites.

**Works:** **47 tests**. Distance is 1850 m; speed is exactly 25/18 m/s.
Failed valid claims differ from invalid calculations. A faithful receipt may
verify a failed claim; rehashed forged results fail replay. Interval transfer
time encloses [3.6,5.5] s within [3,6] s. Round Flint converts before rounding
and checks the two-place display `1.39`, with error exactly 1/900 m/s. Claim
`1.38` exits 1; converting zero metres to seconds exits 2 with no stdout.
Its suite includes 2,500 seeded Decimal oracle comparisons and 200 rational
conversion/error cases. All five rounding rules preserve signed/tie behavior.

**Broken/limits:** no tool failure found. Rounding is not measurement accuracy,
uncertainty or significant figures. Interval dependency is lost (`x-x` may enclose
nonzero values); ranges are assertions, not distributions. Same-parser replay can
repeat a bug. `2 m^2` means `(2 m)^2`; use `2 * m^2`. Offset temperatures,
currency and covariance remain unsupported. This externally useful goal is distinct.

**Narrow for 21 Pepes:** finish bounded exact grammar, unit dimensions, equality,
inclusive bounds, receipts, labeled interval enclosures and explicit rounding.
Review a real supplied calculation next. Defer symbolic algebra, universal units,
probabilistic uncertainty and live exchange rates.

## Shared handoffs and repair

New **Benchmark Display**, `shared/benchmark-display/`, connects Line 1's
complete evidence replay to Line 4's Round Flint. Nine unchanged ordinary source/
fixture snapshots have source paths and SHA-256 in `provenance.json`. The entire
folder works when copied independently, without installation or network.

```sh
python3 -B shared/benchmark-display/benchmark_display.py demo
```

Observed actual local policy counts 10/18, 14/18, 18/18 display as **55.56%,
77.78%, 100.00%**, alongside exact fractions and exact rounding errors. Candidate
effects display as **22.22 and 44.44 percentage points**. Integer counts drive
exact arithmetic; no prior floating-point display is used. P-values remain exact
fractions; original decisions never depend on rounded displays. The 18 curated
cases do not support population inference. The transcript is
`benchmark-display-demo.json`. Nine integration tests passed, including independent
Fraction error checks, signed ties, all modes, forged evidence, invalid pins,
immutability, provenance and a standalone copied CLI with empty stdout on errors.

The `receipt` command accepts an existing Evidence Receipt or Policy Benchmark
receipt and two independently retained pins. It fully replays before output,
but does not reexecute candidate systems. The demo explicitly does reexecute its
three fixed policies. This is a reading view, not a new receipt format. Keep the
original evidence and trusted pins; digests obtained with an untrusted object
authenticate nothing. Output is inert ASCII JSON, not safe HTML after decoding.

Existing Window Review initially failed **only its upstream-equality provenance
check** because Line 3 added filters after its frozen snapshot. Its eleven other
tests and CLI demo passed. Preserved every engine byte and behavior; documented
the original pre-filter snapshot in provenance and checked its fixed ancestral
SHA-256 instead of a moving source. All twelve tests now pass. It still offers
its original unfiltered query, not Line 3's newer filters. The other nine snapshots
still match upstream. Earlier shared tools and snapshot bytes stay unchanged.

## Coins

`COINS.md`: **none**. All four capabilities and the handoff work offline without
currency, price, payment, balance or pool. A coin or Uniswap v4 hook enables no
missing operation. No launch/deployment request is justified. Use real ZTO first
and IMD second if future work genuinely needs currency. Nothing was signed, sent,
paid, deployed or posted; no environment, keys or host configuration were read.

## Wall and records

**The Joining Stone:** two worn yellow-ochre strokes meet at a charcoal pebble
above Pepe's right hand. Built-in imagegen edited gathering seven; only the new
motif's pigment was composited onto the original wall. Exactly **2,225 pixels**
change, all within `[930,558,1095,635)`; every pixel outside the added pigment
mask remains identical. Rock, cracks, framing, light and ancestral paintings are
retained. Both inherited hands were counted: four fingers and one thumb each.
No new hands or stencils. No letters, numbers or prohibited symbols observed.
Full PNG and preview were visually inspected. **Unmet visual requirements: none
observed.** The small motif is less distinct at preview size; review is local,
not independent artistic approval. Prompt and processing are recorded.

Required output: `artifacts/gathering/wall-v8.png`, **1254 × 1254 RGB8 PNG**,
untracked for separate upload; `wall.png` is its relative alias. Preview:
`dist/gathering/08.jpg`, **512 × 512 baseline JPEG, 97,606 bytes**. `08.json` and
`one.json` use the actual PNG SHA-256; One keeps number 736. `dist/goals.json`
copies the four exact goals. The self-contained gallery lists all **130 numbered
records: 37 painted and 93 future**, by wall, painted newest first and future
slots separately newest first. Existing ancestor and future records remain;
this is a later gathering and slot 08 replaces a placeholder.

Structural checks verify record shapes, goals, image bytes/dimensions, preview
sizes, all local gallery links/order, original line bytes and historical shared
snapshots. Results: `validation.json`, `gallery-check.json`, `wall-review.json`,
`mark-process.json`. Full PNG links need the artifact service; no browser layout
certification or independent behavioral/visual approval is claimed.
