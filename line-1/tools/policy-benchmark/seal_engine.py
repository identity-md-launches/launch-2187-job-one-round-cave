#!/usr/bin/env python3
"""Bind a frozen binary benchmark to portable case and system bytes, offline."""
import argparse
import base64
import binascii
import json
import re
import sys

import frozen_engine as frozen

InputError = frozen.InputError
canonical = frozen.canonical
digest = frozen.digest
SCHEMA = 'benchmark-seal-v1'


def shape(value, fields, what):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise InputError(what + ': unexpected fields')


def decode_blob(value):
    if not isinstance(value, str):
        raise InputError('data_b64 must be a string')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise InputError('invalid base64') from exc
    if base64.b64encode(raw).decode('ascii') != value:
        raise InputError('base64 must use its canonical padded representation')
    if not raw:
        raise InputError('empty asset; represent an empty case with an explicit structured payload')
    return raw


def assets(values, ids, what):
    if not isinstance(values, list) or len(values) != len(ids):
        raise InputError(what + ': must contain every planned ID exactly once')
    allowed = set(ids)
    by_id = {}
    for value in values:
        shape(value, {'id', 'data_b64'}, what)
        name = frozen.label(value['id'], what + ' ID')
        if name not in allowed or name in by_id:
            raise InputError(what + ': unknown or duplicate ID')
        decode_blob(value['data_b64'])
        by_id[name] = dict(value)
    if set(by_id) != set(ids):
        raise InputError(what + ': missing ID')
    return [by_id[name] for name in ids]


def normalize(content, expected_plan):
    shape(content, {'manifest', 'cases', 'systems'}, 'content')
    if not isinstance(expected_plan, str) or not re.fullmatch('[0-9a-f]{64}', expected_plan):
        raise InputError('expected plan SHA-256 must be 64 lowercase hex characters')
    plan = frozen.verify_manifest(canonical(content['manifest']), expected_plan)
    manifest = {'schema': 'frozen-benchmark-manifest-v1', 'plan': plan,
                'plan_sha256': expected_plan}
    return {'manifest': manifest,
            'cases': assets(content['cases'], plan['cases'], 'cases'),
            'systems': assets(content['systems'], [plan['baseline']] + plan['candidates'], 'systems')}


def seal(raw, expected_plan):
    content = normalize(frozen.parse_json(raw), expected_plan)
    pack = {'schema': SCHEMA, 'content': content,
            'seal_sha256': digest(canonical(content))}
    # Guarantee that this tool can read its own pretty-printed output.
    if len((json.dumps(pack, indent=2, ensure_ascii=True) + '\n').encode('ascii')) > frozen.MAX_BYTES:
        raise InputError('sealed pack exceeds 2 MiB; use a smaller fixed benchmark')
    return pack


def verify(raw, expected_seal, results=None):
    if not isinstance(expected_seal, str) or not re.fullmatch('[0-9a-f]{64}', expected_seal):
        raise InputError('expected seal SHA-256 must be 64 lowercase hex characters')
    pack = frozen.parse_json(raw)
    shape(pack, {'schema', 'content', 'seal_sha256'}, 'pack')
    if pack['schema'] != SCHEMA:
        raise InputError('unknown pack schema')
    shape(pack['content'], {'manifest', 'cases', 'systems'}, 'content')
    manifest = pack['content']['manifest']
    shape(manifest, {'schema', 'plan', 'plan_sha256'}, 'manifest')
    content = normalize(pack['content'], manifest['plan_sha256'])
    if pack['content'] != content:
        raise InputError('pack content must already be normalized in planned order')
    actual = digest(canonical(content))
    if pack['seal_sha256'] != actual or actual != expected_seal:
        raise InputError('seal mismatch against independently retained pin')
    summaries = {}
    for kind in ('cases', 'systems'):
        summaries[kind] = [{'id': item['id'], 'bytes': len(decode_blob(item['data_b64'])),
                            'sha256': digest(decode_blob(item['data_b64']))}
                           for item in content[kind]]
    report = {'schema': 'benchmark-seal-check-v1', 'status': 'content_matches_pin',
              'seal_sha256': actual, 'plan_sha256': manifest['plan_sha256'],
              'assets': summaries,
              'limits': ['The independent pin must be retained before outcomes are collected.',
                         'Content consistency proves neither preregistration nor execution of these bytes.',
                         'Assets may contain private data; review before sharing. No redaction is performed.',
                         'Correct scoring, independence, representative cases and fixed stopping remain assertions.']}
    normalized = None
    if results is not None:
        checked, normalized = frozen.check(canonical(manifest), results, manifest['plan_sha256'])
        report['observations'] = checked
    return report, normalized


def encode(raw):
    return base64.b64encode(raw).decode('ascii')


def demo():
    previous = frozen.demo()
    manifest = previous['manifest']
    plan = manifest['plan']
    content = {'manifest': manifest,
               'cases': [{'id': name, 'data_b64': encode(canonical({'synthetic_case': name}))}
                         for name in plan['cases']],
               'systems': [{'id': name, 'data_b64': encode(('synthetic system descriptor: ' + name).encode())}
                           for name in [plan['baseline']] + plan['candidates']]}
    pack = seal(canonical(content), manifest['plan_sha256'])
    report, normalized = verify(canonical(pack), pack['seal_sha256'],
                                previous['normalized_csv'].encode())
    altered = json.loads(json.dumps(pack))
    altered['content']['cases'][0]['data_b64'] = encode(b'changed payload')
    altered['seal_sha256'] = digest(canonical(altered['content']))
    try:
        verify(canonical(altered), pack['seal_sha256'])
    except InputError as exc:
        rejected = str(exc)
    else:
        raise RuntimeError('failed to reject replacement payload and recomputed internal hash')
    return {'data_kind': 'synthetic_demonstration', 'pack': pack, 'check': report,
            'normalized_csv': normalized.decode(), 'rejected_rehashed_replacement': rejected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    create = sub.add_parser('seal')
    create.add_argument('--input', required=True)
    create.add_argument('--expected-plan-sha256', required=True)
    check = sub.add_parser('verify')
    check.add_argument('--pack', required=True)
    check.add_argument('--expected-seal-sha256', required=True)
    check.add_argument('--results')
    check.add_argument('--emit-csv', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            output = demo()
        elif args.command == 'seal':
            output = seal(frozen.read_workspace(args.input), args.expected_plan_sha256)
        else:
            if args.emit_csv and not args.results:
                raise InputError('--emit-csv requires --results')
            output, normalized = verify(frozen.read_workspace(args.pack), args.expected_seal_sha256,
                                        frozen.read_workspace(args.results) if args.results else None)
            if args.emit_csv:
                sys.stdout.buffer.write(normalized)
                return 0
    except (ValueError, OSError, TypeError, RecursionError) as exc:
        parser.exit(2, 'error: ' + str(exc)[:240] + '\n')
    print(json.dumps(output, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
