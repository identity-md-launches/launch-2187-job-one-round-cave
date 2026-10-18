#!/usr/bin/env python3
"""Measure fixed JSON policies against sealed labeled cases; export evidence."""
import argparse
import csv
import io
import json
from pathlib import Path
import sys

import evidence_receipt as evidence
import policies

frozen = evidence.frozen
seal = evidence.seal
canonical = frozen.canonical
InputError = frozen.InputError
HERE = Path(__file__).resolve().parent
RULE = ('Pass iff the fixed policy accepts the case text exactly when expected_accept '
        'is true. Rejection includes parser ValueError or RecursionError. '
        'Curated acceptance checks, not a representative performance sample.')
MAX_CASES = 256
MAX_TEXT = 8192


def cases_from(raw):
    data = frozen.parse_json(raw)
    seal.shape(data, {'schema', 'cases'}, 'case set')
    if data['schema'] != 'json-policy-cases-v1':
        raise InputError('unknown case-set schema')
    values = data['cases']
    if not isinstance(values, list) or not 1 <= len(values) <= MAX_CASES:
        raise InputError('case set requires 1 to 256 cases')
    seen = set()
    for case in values:
        seal.shape(case, {'id', 'text', 'expected_accept'}, 'case')
        name = frozen.label(case['id'], 'case ID')
        if name in seen:
            raise InputError('duplicate case ID')
        seen.add(name)
        if (not isinstance(case['text'], str)
                or len(case['text'].encode('utf-8', errors='surrogatepass')) > MAX_TEXT):
            raise InputError('case text must be a string of at most 8192 UTF-8 bytes')
        if type(case['expected_accept']) is not bool:
            raise InputError('expected_accept must be a JSON boolean')
    return values


def runtime():
    # Version metadata only; no environment, host details or library files read.
    return {'implementation': sys.implementation.name,
            'python_version': list(sys.version_info[:3]),
            'integer_string_limit': sys.get_int_max_str_digits() if hasattr(sys, 'get_int_max_str_digits') else None,
            'recursion_limit': sys.getrecursionlimit()}


def system_assets():
    source = evidence.read_workspace(HERE / 'policies.py', frozen.MAX_BYTES)
    runner = evidence.read_workspace(HERE / 'policy_benchmark.py', frozen.MAX_BYTES)
    common = {'policy_source_b64': seal.encode(source), 'runner_source_b64': seal.encode(runner),
              'evidence_engines': evidence.engines(), 'runtime': runtime(),
              'limits': 'Python standard library and interpreter bytes are not embedded or hashed.'}
    return [{'id': name, 'data_b64': seal.encode(canonical(dict(common, policy=name)))}
            for name in policies.NAMES]


def freeze_cases(raw):
    cases = cases_from(raw)
    plan = {'schema': frozen.SCHEMA, 'baseline': policies.NAMES[0],
            'candidates': list(policies.NAMES[1:]), 'cases': [c['id'] for c in cases],
            'pass_rule': RULE, 'alpha': '0.05'}
    manifest = frozen.freeze(canonical(plan))
    content = {'manifest': manifest, 'systems': system_assets(),
               'cases': [{'id': c['id'], 'data_b64': seal.encode(canonical(c))} for c in cases]}
    return seal.seal(canonical(content), manifest['plan_sha256'])


def admit_pack(raw, expected_seal):
    # Validate the entire pack before invoking any policy.
    seal.verify(raw, expected_seal)
    pack = frozen.parse_json(raw)
    content = pack['content']
    cases = []
    for asset in content['cases']:
        case = frozen.parse_json(seal.decode_blob(asset['data_b64']))
        if not isinstance(case, dict) or case.get('id') != asset['id']:
            raise InputError('case payload ID differs from sealed asset ID')
        cases.append(case)
    validated = cases_from(canonical({'schema': 'json-policy-cases-v1', 'cases': cases}))
    expected = freeze_cases(canonical({'schema': 'json-policy-cases-v1', 'cases': validated}))
    if canonical(pack) != canonical(expected):
        raise InputError('pack differs from fixed policies, source bytes, runtime or scoring rule')
    return pack, validated


def measure(raw, expected_seal):
    pack, cases = admit_pack(raw, expected_seal)
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['case', 'baseline'] + list(policies.NAMES[1:]))
    observations = []
    for case in cases:
        accepted = [policies.accepts(name, case['text']) for name in policies.NAMES]
        passed = [int(value == case['expected_accept']) for value in accepted]
        writer.writerow([case['id']] + passed)
        observations.append({'case': case['id'], 'expected_accept': case['expected_accept'],
                             'accepted': dict(zip(policies.NAMES, accepted)),
                             'passed': dict(zip(policies.NAMES, passed))})
    receipt = evidence.make(raw, stream.getvalue().encode('utf-8'), expected_seal)
    # Algebraic replay before returning any artifact.
    evidence.replay(canonical(receipt), expected_seal, receipt['receipt_sha256'])
    return receipt, observations


def recheck(raw, expected_seal, expected_receipt):
    receipt = evidence.replay(raw, expected_seal, expected_receipt)
    pack_raw = evidence.unblob(receipt['body']['pack_b64'])
    measured, _ = measure(pack_raw, expected_seal)
    if canonical(measured) != canonical(receipt):
        raise InputError('fresh execution differs from retained receipt')
    return {'status': 'replayed_and_reexecuted', 'receipt_sha256': receipt['receipt_sha256'],
            'runtime': runtime(), 'limits': 'Local reproduction, not independent execution attestation.'}


def demo():
    raw = evidence.read_workspace(HERE / 'cases.json', frozen.MAX_BYTES)
    pack = freeze_cases(raw)
    receipt, observations = measure(canonical(pack), pack['seal_sha256'])
    recheck(canonical(receipt), pack['seal_sha256'], receipt['receipt_sha256'])
    return {'data_kind': 'measured_local_execution_on_curated_cases',
            'seal_sha256': pack['seal_sha256'], 'receipt_sha256': receipt['receipt_sha256'],
            'runtime': runtime(), 'case_count': len(observations),
            'passes': {name: sum(r['passed'][name] for r in observations) for name in policies.NAMES},
            'observations': observations,
            'conditional_analysis': receipt['body']['analysis'],
            'interpretation': 'These hand-selected related regression cases are not independent random samples. '
                              'The computed p-values do not establish population improvement. '
                              'This demo seals before execution but does not establish preregistration time.',
            'recheck': 'passed'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    freeze = sub.add_parser('freeze')
    freeze.add_argument('--cases', required=True)
    run = sub.add_parser('run')
    run.add_argument('--pack', required=True)
    run.add_argument('--expected-seal-sha256', required=True)
    check = sub.add_parser('recheck')
    check.add_argument('--receipt', required=True)
    check.add_argument('--expected-seal-sha256', required=True)
    check.add_argument('--expected-receipt-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            output = demo()
        elif args.command == 'freeze':
            output = freeze_cases(evidence.read_workspace(args.cases, frozen.MAX_BYTES))
        elif args.command == 'run':
            output, _ = measure(evidence.read_workspace(args.pack, frozen.MAX_BYTES), args.expected_seal_sha256)
        else:
            output = recheck(evidence.read_workspace(args.receipt), args.expected_seal_sha256,
                             args.expected_receipt_sha256)
        rendered = canonical(output).decode('ascii')
    except (ValueError, OSError, TypeError, RecursionError, OverflowError) as exc:
        parser.exit(2, 'error: ' + ascii(str(exc))[:240] + '\n')
    sys.stdout.write(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
