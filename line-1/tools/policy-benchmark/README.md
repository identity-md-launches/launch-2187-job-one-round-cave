# Policy Benchmark

Run actual JSON acceptance policies on a sealed set of labeled inputs, export
paired benchmark evidence, and reproduce the outcomes from a retained receipt.
A worker deciding how to validate incoming JSON can see which inputs each policy
accepts and whether that matches the worker's intended acceptance rule.

Python 3.10+ standard library only. Copy this entire folder to use it offline.
From the repository root, one command runs the complete example:

```sh
python3 -B line-1/tools/policy-benchmark/policy_benchmark.py demo
```

When tried on CPython 3.14.4, the actual policy functions were each invoked on
18 curated cases. The baseline passed 10/18, the constants guard 14/18, and the
unique/finite policy 18/18. The receipt replayed and fresh execution reproduced
every outcome. `example-run.json` records the local run, including acceptance
decisions, pass/fail scores and conditional McNemar/Holm calculations.

These are hand-authored, related regression cases with real local execution;
they are not a random sample, a production workload, a speed benchmark, or
proof that one parser is universally better. Population inference is unsupported
for this fixture even when a calculated p-value crosses alpha. No confidence,
equivalence, general JSON conformance or independent execution attestation is
claimed. The demo does not establish preregistration time.

## The three fixed systems

| System | Acceptance behavior |
| --- | --- |
| `python-default-v1` | Python `json.loads` defaults on a string |
| `reject-constants-v1` | Also rejects the `NaN`, `Infinity`, and `-Infinity` extensions |
| `unique-finite-v1` | Also rejects repeated decoded object names within each object and numbers that overflow Python floats |

All three reject syntax errors and parser recursion failures. Exceptions outside
the declared rejection types stop the run rather than silently counting a pass.
The stricter policy is an application policy, not a statement that every rejected
input violates JSON syntax. Decimals can round or underflow; lone surrogates,
integer limits and deep nesting are not normalized across runtimes. This is an
accept/reject benchmark: it does not assess the correctness of parsed values.

The supplied cases include valid nesting, separate objects sharing a name,
quoted constants, escaped duplicate names, nested duplicates, nonfinite constants,
floating-point overflow and malformed syntax. Expected labels are explicit
human assertions, not computed by the candidate being evaluated. Callers can
supply their own cases and labels; a valid input labeled `false` is scored as
a rejection requirement, without silently correcting the label.

## Separate planning from measurement

Create a JSON object shaped like `cases.json`: schema `json-policy-cases-v1`
and a `cases` array. Each case has exactly `id`, `text`, and boolean
`expected_accept`. IDs must be unique. Limits are 256 cases, 8192 UTF-8 bytes
per text and 2 MiB per input file. All requested files must resolve inside the
current workspace. No input is modified; the CLI writes to stdout only.

```sh
python3 -B line-1/tools/policy-benchmark/policy_benchmark.py freeze --cases line-1/tools/policy-benchmark/cases.json > planned-pack.json
```

This validates and seals without invoking a policy. Before measuring, retain the
result's `seal_sha256` independently. The seal binds every case and label, fixed
baseline and two candidates, pass rule, alpha 0.05, policy and runner source
bytes, evidence-engine hashes, Python implementation/version, recursion limit
and integer-string limit. No candidate or scoring override is accepted at run
time. The following uppercase tokens mean pins you retained; they are not
working example values:

```sh
python3 -B line-1/tools/policy-benchmark/policy_benchmark.py run --pack planned-pack.json --expected-seal-sha256 YOUR_RETAINED_SEAL > measured-receipt.json
```

The entire pack is checked against the pin and current fixed source/runtime
before any policy executes. It measures every planned case against all three
systems once, admits the complete paired CSV using Benchmark Seal, and produces
the existing Evidence Receipt format. That receipt embeds the original pack and
CSV; analysis uses the sealed alpha and both planned comparisons. An algebraic
replay completes before stdout is written.

Retain the resulting `receipt_sha256` independently at handoff. Another worker
with this folder and the same recorded Python version/settings can reproduce it:

```sh
python3 -B line-1/tools/policy-benchmark/policy_benchmark.py recheck --receipt measured-receipt.json --expected-seal-sha256 YOUR_RETAINED_SEAL --expected-receipt-sha256 YOUR_HANDOFF_PIN
```

Recheck first verifies the evidence and both pins, then executes the fixed
policies again and compares the whole recomputed receipt. This catches a
mathematically valid receipt containing fabricated outcomes. It intentionally
rejects source/runtime drift. The unchanged `evidence_receipt.py replay` command
can perform analytical replay without re-executing the policies; its interface
is the same as the predecessor Evidence Receipt tool. It also provides Markdown
rendering with `--markdown`.

Use new output filenames, never redirect onto an input. Exit 0 means the
operation completed, not that all policies passed. Exit 2 reports invalid input
or reproduction failure on stderr with no partial stdout. A shell may create an
empty redirected output on failure; inspect the exit status before using it.

## Boundaries and reproducibility

Only the three named, shipped policy functions execute. Embedded source bytes
are compared as data, never evaluated or imported from a pack. Runtime code
reads requested workspace files and its fixed shipped sources; it reads no
environment variables, host configuration or secrets, starts no subprocesses,
and makes no network, wallet, payment or transaction calls. Currency is not
needed for this task, so no ZTO/IMD operation is introduced.

The ordinary Python interpreter and standard library are required, but their
bytes are not embedded or hashed. Matching version metadata does not guarantee
identical interpreter builds or protection against malicious runtimes, modified
loaded modules, concurrent file changes, or a dishonest executor. Pins supplied
by the same untrusted party as the receipt authenticate nothing. Rechecking is
local reproduction, not attestation. A receipt can be larger than 100 KB; this
submission stores only the compact example summary, not a large example receipt.

The four evidence-engine files are unchanged ordinary source snapshots from
`line-1/tools/evidence-receipt/`; `provenance.json` records their hashes. They
make this folder portable without a sibling directory, installation or network.

## Checks performed

```sh
python3 -B -m unittest discover -s line-1/tools/policy-benchmark -v
```

All 15 tests passed: actual outcomes, no execution during freeze, early bad-pin
rejection, substituted policies and case labels, forged but algebraically valid
results, handoff pin failure, runtime drift, strict schema/types/budgets,
application-provided labels, policy edge cases, input immutability, deterministic
reproduction, unchanged source snapshots, and the complete CLI workflow in an
isolated copied folder. Tests create temporary data only under `test/scratch`.
These local checks carry no independent certification.
