#!/usr/bin/env python3
"""Freeze a paired binary benchmark protocol and admit only complete observations."""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_CASES = 10000
SCHEMA = 'frozen-benchmark-v1'
FIELDS = {'schema', 'baseline', 'candidates', 'pass_rule', 'alpha', 'cases'}


class InputError(ValueError):
    pass


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('ascii')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError('duplicate JSON member: ' + key[:80])
        result[key] = value
    return result


def parse_json(raw):
    if len(raw) > MAX_BYTES:
        raise InputError('JSON exceeds 2 MiB')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(InputError('nonfinite JSON number')))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise InputError('invalid JSON: ' + str(exc)[:160]) from exc


def label(value, what, limit=256):
    if (not isinstance(value, str) or not 1 <= len(value) <= limit
            or value != value.strip()
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 or 0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise InputError(what + ': expected nonempty text without edge whitespace or controls')
    return value


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != FIELDS or plan.get('schema') != SCHEMA:
        raise InputError('plan must have exactly schema, baseline, candidates, pass_rule, alpha, cases')
    label(plan['baseline'], 'baseline version')
    label(plan['pass_rule'], 'pass rule', 8192)
    names = plan['candidates']
    if not isinstance(names, list) or not 2 <= len(names) <= 16:
        raise InputError('plan requires 2 to 16 candidate version names')
    for name in names:
        label(name, 'candidate version')
    if len(set(names)) != len(names) or any(n in ('case', 'baseline', plan['baseline']) for n in names):
        raise InputError('candidate versions must be distinct and not reserved or the baseline version')
    cases = plan['cases']
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise InputError('plan requires 1 to 10000 case IDs')
    for case in cases:
        label(case, 'case ID')
    if len(set(cases)) != len(cases):
        raise InputError('duplicate planned case ID')
    alpha = plan['alpha']
    if not isinstance(alpha, str) or len(alpha) > 32 or not re.fullmatch(r'(?:0|1)(?:\.[0-9]{1,18})?', alpha):
        raise InputError('alpha must be a plain decimal string with at most 18 fractional places')
    try:
        number = Decimal(alpha)
    except InvalidOperation as exc:
        raise InputError('invalid alpha') from exc
    if not Decimal('0.000001') <= number <= Decimal('0.2'):
        raise InputError('alpha must be 0.000001 through 0.2')
    # One representation for numerically equal alpha settings.
    result = dict(plan)
    result['alpha'] = format(number.normalize(), 'f')
    return result


def freeze(raw):
    plan = validate_plan(parse_json(raw))
    manifest = {'schema': 'frozen-benchmark-manifest-v1', 'plan': plan,
                'plan_sha256': digest(canonical(plan))}
    if len((json.dumps(manifest, indent=2, ensure_ascii=True) + '\n').encode('ascii')) > MAX_BYTES:
        raise InputError('emitted manifest would exceed 2 MiB; shorten case IDs')
    return manifest


def verify_manifest(raw, expected):
    if not re.fullmatch('[0-9a-f]{64}', expected):
        raise InputError('expected plan SHA-256 must be 64 lowercase hex characters')
    manifest = parse_json(raw)
    if (not isinstance(manifest, dict) or set(manifest) != {'schema', 'plan', 'plan_sha256'}
            or manifest['schema'] != 'frozen-benchmark-manifest-v1'):
        raise InputError('invalid manifest shape')
    plan = validate_plan(manifest['plan'])
    actual = digest(canonical(plan))
    if manifest['plan_sha256'] != actual or expected != actual:
        raise InputError('plan digest mismatch; retain and supply the original independent pin')
    return plan


def observations(raw, plan):
    if len(raw) > MAX_BYTES:
        raise InputError('observations exceed 2 MiB')
    try:
        text = raw.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(text, newline=''), strict=True)
        header = next(reader, None)
        if header != ['case', 'baseline'] + plan['candidates']:
            raise InputError('CSV header differs from complete planned candidate family and order')
        planned = set(plan['cases'])
        rows = {}
        for row in reader:
            if len(rows) >= MAX_CASES:
                raise InputError('too many observation rows')
            if len(row) != len(header):
                raise InputError('CSV row has missing or extra fields')
            case = label(row[0], 'observed case ID')
            if case in rows:
                raise InputError('duplicate observed case ID')
            if case not in planned:
                raise InputError('unplanned observed case ID: ' + case[:80])
            if any(value not in ('0', '1') for value in row[1:]):
                raise InputError('outcomes must be literal 0 or 1')
            rows[case] = row
        if set(rows) != planned:
            raise InputError('missing planned cases: ' + str(len(planned - set(rows))))
    except (UnicodeError, csv.Error) as exc:
        raise InputError('invalid UTF-8 CSV: ' + str(exc)[:120]) from exc
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(header)
    writer.writerows(rows[case] for case in plan['cases'])
    return output.getvalue().encode('utf-8')


def check(manifest_raw, csv_raw, expected):
    plan = verify_manifest(manifest_raw, expected)
    normalized = observations(csv_raw, plan)
    return {'schema': 'frozen-benchmark-check-v1', 'status': 'complete_observations',
            'plan_sha256': expected, 'manifest_bytes_sha256': digest(manifest_raw),
            'observation_bytes_sha256': digest(csv_raw),
            'normalized_csv_sha256': digest(normalized),
            'case_count': len(plan['cases']), 'candidates': plan['candidates'],
            'baseline': plan['baseline'], 'pass_rule': plan['pass_rule'], 'alpha': plan['alpha'],
            'limits': ['Consistency with a pinned plan does not prove preregistration or honest execution.',
                       'Case IDs do not bind case payloads; keep the actual inputs and immutable system versions.',
                       'Independence, pass-rule application and absence of repeated looks are not verified.']}, normalized


def read_workspace(name):
    root = Path.cwd().resolve()
    path = Path(name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise InputError('input must be a regular file inside the current workspace')
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise InputError('input exceeds 2 MiB')
    return raw


def demo():
    plan = {'schema': SCHEMA, 'baseline': 'synthetic-parser-v1',
            'candidates': ['synthetic-fast-v1', 'synthetic-careful-v1'],
            'pass_rule': 'Synthetic fixture only: output equals the case expected value exactly.',
            'alpha': '0.05', 'cases': ['empty', 'unicode', 'truncated']}
    manifest = freeze(canonical(plan))
    raw = b'case,baseline,synthetic-fast-v1,synthetic-careful-v1\ntruncated,0,0,1\nempty,1,1,1\nunicode,0,1,1\n'
    report, normalized = check(canonical(manifest), raw, manifest['plan_sha256'])
    rejected = {}
    variants = {'missing_case': raw.rsplit(b'unicode', 1)[0],
                'unplanned_case': raw + b'extra,0,1,1\n',
                'family_drift': raw.replace(b'synthetic-fast-v1', b'synthetic-fast-v2')}
    for name, value in variants.items():
        try:
            check(canonical(manifest), value, manifest['plan_sha256'])
        except InputError as exc:
            rejected[name] = str(exc)
        else:
            raise RuntimeError('demo failed to reject drift')
    return {'data_kind': 'synthetic_demonstration', 'manifest': manifest,
            'check': report, 'normalized_csv': normalized.decode(), 'rejected': rejected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='run a labeled synthetic complete and rejected-case demonstration')
    create = sub.add_parser('freeze', help='validate a JSON protocol and emit a manifest')
    create.add_argument('--spec', required=True)
    review = sub.add_parser('check', help='verify pinned protocol and complete paired CSV')
    review.add_argument('--manifest', required=True)
    review.add_argument('--results', required=True)
    review.add_argument('--expected-plan-sha256', required=True)
    review.add_argument('--emit-csv', action='store_true', help='emit admitted CSV instead of JSON')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        elif args.command == 'freeze':
            result = freeze(read_workspace(args.spec))
        else:
            result, normalized = check(read_workspace(args.manifest), read_workspace(args.results),
                                       args.expected_plan_sha256)
            if args.emit_csv:
                sys.stdout.buffer.write(normalized)
                return 0
    except (InputError, OSError, ValueError, RecursionError) as exc:
        parser.exit(2, 'error: ' + str(exc)[:240] + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
