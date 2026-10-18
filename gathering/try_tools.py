#!/usr/bin/env python3
"""Run bounded documented CLI examples and preserve compact observed results."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
CASES = [
 ('shared exact benchmark display', ['shared/benchmark-display/benchmark_display.py', 'demo'], 0),
 ('executed policy benchmark', ['line-1/tools/policy-benchmark/policy_benchmark.py', 'demo'], 0),
 ('plain Unicode window', ['line-2/tools/unicode-text-window/unicode_text_window.py', '--demo', '--max-findings', '2'], 0),
 ('plain Unicode actual policy source', ['line-2/tools/unicode-text-window/unicode_text_window.py', '--file', 'line-1/tools/policy-benchmark/policies.py'], 0),
 ('filtered timeline', ['line-3/tools/timeline-window/timeline_window.py', 'demo', '--source', 'front.log', '--contains', 'accepted'], 0),
 ('exact rounding match', ['line-4/tools/round-flint/round_flint.py', '10 km / 2 h', '--to', 'm/s', '--places', '2', '--expect', '1.39'], 0),
 ('exact rounding mismatch', ['line-4/tools/round-flint/round_flint.py', '10 km / 2 h', '--to', 'm/s', '--places', '2', '--expect', '1.38'], 1),
 ('invalid rounded dimension', ['line-4/tools/round-flint/round_flint.py', '0 m', '--to', 's'], 2),
 ('evidence receipt JSON', ['line-1/tools/evidence-receipt/evidence_receipt.py', 'demo', '--json'], 0),
 ('evidence receipt readable demo', ['line-1/tools/evidence-receipt/evidence_receipt.py', 'demo'], 0),
 ('evidence receipt shipped replay', ['line-1/tools/evidence-receipt/evidence_receipt.py', 'replay', '--receipt', 'line-1/tools/evidence-receipt/example-receipt.json', '--expected-seal-sha256', '0d18499d7dcb9150785724d7121ffeafa8607ace1612900920b715c4f85b3947', '--expected-receipt-sha256', 'a48b052b69deb57fe5919d28cbc0ea5d33c65fcf69befaba3dfab2c8d4d0594d', '--markdown'], 0),
 ('Unicode window demo', ['line-2/tools/unicode-window/unicode_window.py', 'demo'], 0),
 ('Unicode window actual record', ['line-2/tools/unicode-window/unicode_window.py', 'source', '--file', 'dist/line-2/26.json'], 0),
 ('timeline window demo', ['line-3/tools/timeline-window/timeline_window.py', 'demo'], 0),
 ('shared window review', ['shared/window-review/window_review.py', 'demo'], 0),
 ('interval clock', ['shared/interval-clock/interval_clock.py', 'demo'], 0),
 ('benchmark seal', ['line-1/tools/benchmark-seal/benchmark_seal.py', 'demo'], 0),
 ('Unicode seal', ['line-2/tools/unicode-seal/unicode_seal.py', 'demo'], 0),
 ('timeline diff', ['line-3/tools/timeline-diff/timeline_diff.py', 'demo'], 0),
 ('interval arithmetic', ['line-4/tools/interval-flint/interval_flint.py', 'demo'], 0),
 ('shared clock receipt', ['shared/clock-receipt/clock_receipt.py', 'demo'], 0),
 ('Unicode replay', ['line-2/tools/unicode-replay/unicode_replay.py', 'demo'], 0),
 ('clock sensitivity', ['line-3/tools/clock-margin/clock_margin.py', 'demo'], 0),
 ('calculation receipt', ['line-4/tools/calculation-receipt/receipt.py', 'demo'], 0),
 ('paired verdict demo', ['line-1/tools/paired-verdict/paired_verdict.py', '--demo'], 0),
 ('paired verdict CSV', ['line-1/tools/paired-verdict/paired_verdict.py', '--input', 'line-1/tools/paired-verdict/example.csv'], 0),
 ('candidate ladder', ['line-1/tools/candidate-ladder/candidate_ladder.py', '--demo'], 0),
 ('prospective power', ['line-1/tools/paired-power/paired_power.py', '--demo'], 0),
 ('raw Unicode', ['line-2/tools/unicode-lantern/unicode_lantern.py', '--demo'], 0),
 ('decoded JSON', ['line-2/tools/json-lantern/json_lantern.py', '--demo'], 0),
 ('actual record JSON', ['line-2/tools/json-lantern/json_lantern.py', '--file', 'dist/line-2/22.json'], 0),
 ('timeline demo', ['line-3/tools/time-flint/time_flint.py', '--demo', '--json'], 0),
 ('timeline supplied fixtures', ['line-3/tools/time-flint/time_flint.py', '--json', '--clock-uncertainty-ms', '750', 'line-3/tools/time-flint/examples/client.txt', 'line-3/tools/time-flint/examples/server.jsonl'], 0),
 ('timeline replay', ['line-3/tools/timeline-replay/timeline_replay.py', 'demo'], 0),
 ('exact distance', ['line-4/tools/unit-flint/unit_flint.py', '1.5 km + 350 m', '--to', 'm', '--json'], 0),
 ('exact matching claim', ['line-4/tools/unit-flint/unit_flint.py', '10 km / 2 h', '--expect', '5 km/h', '--to', 'm/s', '--json'], 0),
 ('exact mismatching claim', ['line-4/tools/unit-flint/unit_flint.py', '10 km / 2 h', '--expect', '6 km/h', '--to', 'm/s', '--json'], 1),
 ('invalid dimension claim', ['line-4/tools/unit-flint/unit_flint.py', '0 m', '--expect', '0 s', '--json'], 2),
 ('frozen benchmark', ['line-1/tools/frozen-benchmark/frozen_benchmark.py', 'demo'], 0),
 ('JSON citations', ['line-2/tools/json-citations/json_citations.py', '--demo'], 0),
 ('actual record citations', ['line-2/tools/json-citations/json_citations.py', '--file', 'dist/line-2/23.json'], 0),
 ('event order witness', ['line-3/tools/order-witness/order_witness.py', 'demo'], 0),
 ('inclusive duration bounds', ['line-4/tools/unit-flint/unit_flint.py', '5 MiB / (2 MiB/s)', '--at-least', '2000 ms', '--at-most', '3 s', '--to', 's', '--json'], 0),
 ('duration bound failed', ['line-4/tools/unit-flint/unit_flint.py', '5 MiB / (2 MiB/s)', '--at-most', '2400 ms', '--json'], 1),
 ('reversed duration bounds', ['line-4/tools/unit-flint/unit_flint.py', '2.5 s', '--at-least', '3 s', '--at-most', '2 s', '--json'], 2),
 ('shared reviewed timeline', ['shared/reviewed-timeline/reviewed_timeline.py', '--demo', '--clock-bound', '0.75 s'], 0),
 ('shared replay review', ['shared/replay-review/replay_review.py', 'demo'], 0),
]


def main():
    results = []
    for name, args, expected in CASES:
        command = [sys.executable, '-B', *args]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        row = {'name': name, 'command': ['python3', '-B', *args],
               'expected_exit': expected, 'exit_code': run.returncode,
               'passed': run.returncode == expected}
        if run.stdout:
            try:
                value = json.loads(run.stdout)
            except json.JSONDecodeError:
                value = {}
                row['text'] = {'bytes': len(run.stdout.encode()),
                    'sha256': hashlib.sha256(run.stdout.encode()).hexdigest(),
                    'printable_ascii_and_lf': all(c == '\n' or 32 <= ord(c) <= 126 for c in run.stdout),
                    'opening_lines': run.stdout.splitlines()[:7]}
                row['passed'] &= row['text']['printable_ascii_and_lf']
            # Small numeric/evidence summaries; full reports are reproducible.
            keys = ['passes', 'case_count', 'recheck', 'rounded', 'exact_value', 'error', 'filters', 'comparison', 'lower', 'upper', 'within', 'pair', 'line_changes', 'consistent_replacement_rejected', 'runtime_mismatch_rejected', 'rejected_rehashed_replacement', 'analysis', 'asserted_total_bound_ms', 'different_valid_bound_rejected', 'matching_receipt', 'failed_bound_verified', 'failed_bound_calculation_exit', 'rehashed_altered_result_rejected', 'verified', 'retained_findings', 'truncated', 'altered_citation_rejected', 'paired_cases', 'table', 'test', 'candidates', 'comparison_threshold',
                    'smallest_evaluated_size_meeting_target', 'sizes', 'finding_count',
                    'assessment', 'sha256', 'value', 'unit', 'check', 'replay',
                    'tampered_report_rejected', 'tampered_timeline_rejected', 'review_errors',
                    'json_lines_checked', 'digest_pin_checked', 'bounds', 'rejected',
                    'same_group_certain_order', 'overlap', 'widened', 'normalized_csv']
            row['observed'] = {k: value[k] for k in keys if k in value}
            if 'counts' in value:
                row['observed']['counts'] = value['counts']
            if 'events' in value and 'omitted' in value:
                row['observed'].update(events=len(value['events']), omitted=len(value['omitted']),
                                       overlap_groups=[e['overlap_group'] for e in value['events']])
        if run.stderr:
            row['diagnostic'] = run.stderr[:2000]
        results.append(row)
    result = {'checks_passed': all(r['passed'] for r in results),
              'examples': results, 'note': 'Demos and fixtures are synthetic; the actual record scan checks real workspace bytes. No live system performance or incident is claimed.'}
    print(json.dumps(result, indent=2))
    return 0 if result['checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
