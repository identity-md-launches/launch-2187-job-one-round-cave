#!/usr/bin/env python3
"""Run the reviewed offline checks, keeping upstream temporary fixtures in scratch."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    scratch = ROOT / "test/scratch/time-flint"
    scratch.mkdir(parents=True, exist_ok=True)
    # The upstream suite creates fixtures beside __file__. Copy its exact bytes
    # so running it never creates, deletes or changes files inside a line.
    for name in ("time_flint.py", "test_time_flint.py"):
        shutil.copyfile(ROOT / "line-3/tools/time-flint" / name, scratch / name)
    before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for n in range(1, 5) for p in (ROOT / f"line-{n}").rglob("*") if p.is_file()}
    suites = ["line-1/tools/paired-verdict", "line-1/tools/candidate-ladder",
              "line-1/tools/paired-power", "line-1/tools/frozen-benchmark", "line-2/tools/unicode-lantern",
              "line-2/tools/json-lantern", "line-2/tools/json-citations", "test/scratch/time-flint", "line-3/tools/timeline-replay",
              "line-3/tools/order-witness", "line-4/tools/unit-flint", "line-2/tools/unicode-replay", "line-3/tools/clock-margin", "line-4/tools/calculation-receipt", "line-1/tools/benchmark-seal", "line-2/tools/unicode-seal", "line-3/tools/timeline-diff", "line-4/tools/interval-flint", "line-1/tools/evidence-receipt", "line-2/tools/unicode-window", "line-3/tools/timeline-window", "line-1/tools/policy-benchmark", "line-2/tools/unicode-text-window", "line-4/tools/round-flint", "gathering", "shared/reviewed-timeline", "shared/replay-review", "shared/clock-receipt", "shared/interval-clock", "shared/window-review", "shared/benchmark-display"]
    checks = []
    for suite in suites:
        command = [sys.executable, "-B", "gathering/run_suite.py", "discover", "-s", suite, "-v"]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        match = re.search(r"Ran (\d+) tests?", run.stderr)
        (ROOT / "test/scratch" / (suite.replace("/", "_") + ".log")).write_text(run.stdout + run.stderr)
        checks.append({"suite": suite, "tests": int(match[1]) if match else 0,
                       "exit_code": run.returncode})
        if run.returncode:
            print(run.stderr, file=sys.stderr)
    scans = []
    for source in ("line-1/tools/policy-benchmark/policy_benchmark.py", "line-2/tools/unicode-text-window/unicode_text_window.py", "line-4/tools/round-flint/round_flint.py", "line-1/tools/evidence-receipt/evidence_receipt.py", "line-2/tools/unicode-window/unicode_window.py", "line-3/tools/timeline-window/timeline_window.py", "line-1/tools/benchmark-seal/benchmark_seal.py", "line-2/tools/unicode-seal/unicode_seal.py", "line-3/tools/timeline-diff/timeline_diff.py", "line-4/tools/interval-flint/interval_flint.py",
                   "line-2/tools/unicode-replay/unicode_replay.py",
                   "line-3/tools/clock-margin/clock_margin.py",
                   "line-4/tools/calculation-receipt/receipt.py",
                   "line-1/tools/paired-verdict/paired_verdict.py",
                   "line-1/tools/candidate-ladder/candidate_ladder.py",
                   "line-1/tools/paired-power/paired_power.py",
                   "line-1/tools/frozen-benchmark/frozen_benchmark.py",
                   "line-2/tools/json-citations/json_citations.py",
                   "line-3/tools/order-witness/order_witness.py",
                   "line-2/tools/json-lantern/json_lantern.py",
                   "line-3/tools/timeline-replay/timeline_replay.py",
                   "line-2/tools/unicode-lantern/unicode_lantern.py",
                   "line-3/tools/time-flint/time_flint.py",
                   "line-4/tools/unit-flint/unit_flint.py"):
        run = subprocess.run([sys.executable, "-B", "line-2/tools/unicode-lantern/unicode_lantern.py",
                              "--file", source], cwd=ROOT, capture_output=True, text=True)
        result = json.loads(run.stdout)
        scans.append({"source": source, "exit_code": run.returncode,
                      **{k: result[k] for k in ("sha256", "bytes", "finding_count", "unicode_version")}})
    after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for n in range(1, 5) for p in (ROOT / f"line-{n}").rglob("*") if p.is_file()}
    unchanged = before == after
    success = unchanged and all(c["exit_code"] == 0 for c in checks + scans) and all(c["tests"] > 0 for c in checks)
    print(json.dumps({"checks_passed": success, "suites": checks, "source_scans": scans,
                      "test_count": sum(c["tests"] for c in checks),
                      "line_files_unchanged": unchanged, "line_file_count": len(before),
                      "line_3_fixture_note": "Unmodified source and suite copied to test/scratch/time-flint before discovery."},
                     indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
