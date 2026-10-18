#!/usr/bin/env python3
"""Render replayed binary benchmark counts with exact, explicit rounding."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'engines/policy-benchmark'))
sys.path.insert(0, str(HERE / 'engines/round-flint'))
import policy_benchmark as policy
import round_flint as rounding

evidence = policy.evidence


def ratio(numerator, denominator, places, mode):
    value = Fraction(numerator, denominator)
    result = rounding.calculate(f'({numerator}) / ({denominator})', '1', places, mode)
    return {'exact_fraction': f'{value.numerator}/{value.denominator}',
            'display': result['rounded'], 'rounding_error': result['error'],
            'halfway': result['halfway']}


def summarize(raw, seal_pin, receipt_pin, places=2, mode='half-even'):
    # Reject invalid display options and replay the complete evidence before
    # building any view. Rounded displays never participate in a test decision.
    rounding.calculate('0', '1', places, mode)
    receipt = evidence.replay(raw, seal_pin, receipt_pin)
    analysis = receipt['body']['analysis']
    check = receipt['body']['seal_check']
    count, baseline = analysis['paired_cases'], analysis['baseline_passes']
    systems = [{'name': check['observations']['baseline'], 'role': 'baseline',
                'passes': baseline, 'cases': count,
                'pass_percent': ratio(100 * baseline, count, places, mode)}]
    comparisons = []
    for item in analysis['candidates']:
        passes = item['candidate_passes']
        systems.append({'name': item['name'], 'role': 'candidate', 'passes': passes,
                        'cases': count, 'pass_percent': ratio(100 * passes, count, places, mode)})
        p = item['holm_adjusted_p']
        comparisons.append({'candidate': item['name'],
                            'candidate_only_pass': item['candidate_only_pass'],
                            'baseline_only_pass': item['baseline_only_pass'],
                            'effect_percentage_points': ratio(100 * (passes - baseline), count, places, mode),
                            'holm_adjusted_p': {'numerator': p['numerator'], 'denominator': p['denominator']},
                            'familywise_reject_equal_discordance': item['familywise_reject_equal_discordance'],
                            'observed_direction': item['observed_direction']})
    return {'schema': 'benchmark-display/1', 'verification': 'complete_analytical_replay',
            'seal_sha256': check['seal_sha256'], 'receipt_sha256': receipt['receipt_sha256'],
            'data_kind_from_receipt': receipt['body']['data_kind'],
            'rounding': {'places': places, 'mode': mode, 'error_means': 'display minus exact'},
            'familywise_alpha': analysis['familywise_alpha'],
            'systems': systems, 'comparisons': comparisons,
            'limits': ['Reading view only; retain the original receipt and independently trusted pins.',
                       'Displayed percentages are rounded; p-values remain exact fractions and decisions use the original exact analysis.',
                       'A non-rejection is not equivalence.',
                       'Analytical replay proves consistency, not execution, honest labels, independence or representativeness.',
                       'When using curated JSON policy cases, population inference is unsupported even if a conditional test rejects.',
                       'Engine source identity is checked; version metadata and hashes do not establish trusted authorship.',
                       'No measurement uncertainty, confidence interval or significant-figure claim is added.']}


def demo(places=2, mode='half-even'):
    raw = evidence.read_workspace(HERE / 'engines/policy-benchmark/cases.json')
    pack = policy.freeze_cases(raw)
    receipt, _ = policy.measure(policy.canonical(pack), pack['seal_sha256'])
    policy.recheck(policy.canonical(receipt), pack['seal_sha256'], receipt['receipt_sha256'])
    result = summarize(policy.canonical(receipt), pack['seal_sha256'], receipt['receipt_sha256'], places, mode)
    result['verification'] = 'local_policy_execution_and_reexecution_plus_analytical_replay'
    result['fixture'] = '18 curated JSON acceptance cases; actual local execution, not a representative sample'
    result['pin_note'] = 'Demo pins were created in this run, not independently authenticated or timestamped.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    example = sub.add_parser('demo')
    review = sub.add_parser('receipt')
    review.add_argument('--file', required=True)
    review.add_argument('--expected-seal-sha256', required=True)
    review.add_argument('--expected-receipt-sha256', required=True)
    for command in (example, review):
        command.add_argument('--places', type=int, default=2)
        command.add_argument('--mode', choices=rounding.MODES, default='half-even')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo(args.places, args.mode)
        else:
            result = summarize(evidence.read_workspace(args.file), args.expected_seal_sha256,
                               args.expected_receipt_sha256, args.places, args.mode)
        rendered = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
        if len(rendered) > 4 * 1024 * 1024:
            raise ValueError('reading view exceeds 4 MiB')
    except (ValueError, OSError, TypeError, RecursionError, OverflowError, rounding.UnitError) as exc:
        parser.exit(2, 'benchmark-display: ' + ascii(str(exc))[:240] + '\n')
    sys.stdout.write(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
