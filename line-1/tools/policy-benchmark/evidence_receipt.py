#!/usr/bin/env python3
"""Replayable, readable receipts for sealed fixed paired binary benchmarks."""
import argparse
import base64
import binascii
import json
from pathlib import Path
import re
import sys

import frozen_engine as frozen
import seal_engine as seal
import ladder_engine as ladder

SCHEMA = 'benchmark-evidence-receipt-v1'
MAX_RECEIPT = 12 * 1024 * 1024
InputError = frozen.InputError
canonical = frozen.canonical
digest = frozen.digest
ENGINE_FILES = ('evidence_receipt.py', 'seal_engine.py', 'frozen_engine.py', 'ladder_engine.py')


def read_workspace(name, limit=MAX_RECEIPT):
    path = Path(name).resolve()
    if not path.is_relative_to(Path.cwd().resolve()) or not path.is_file():
        raise InputError('input must be a regular file inside the current workspace')
    with path.open('rb') as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise InputError('input exceeds byte limit')
    return raw


def engines():
    here = Path(__file__).resolve().parent
    return {name: digest(read_workspace(here / name, frozen.MAX_BYTES)) for name in ENGINE_FILES}


def pin(value, what):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise InputError(what + ' must be 64 lowercase hexadecimal characters')
    return value


def unblob(value):
    if not isinstance(value, str):
        raise InputError('embedded bytes must be canonical base64 strings')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise InputError('invalid embedded base64') from exc
    if len(raw) > frozen.MAX_BYTES or base64.b64encode(raw).decode('ascii') != value:
        raise InputError('embedded input exceeds 2 MiB or is not canonical base64')
    return raw


def make(pack_raw, results_raw, expected_seal, data_kind='user_supplied_benchmark'):
    if len(pack_raw) > frozen.MAX_BYTES or len(results_raw) > frozen.MAX_BYTES:
        raise InputError('pack and results must each be at most 2 MiB')
    if data_kind not in ('user_supplied_benchmark', 'synthetic_demonstration'):
        raise InputError('unknown data kind')
    checked, normalized = seal.verify(pack_raw, pin(expected_seal, 'seal pin'), results_raw)
    names, rows = ladder.read_csv_bytes(normalized)
    analysis = ladder.analyze(normalized, names, rows, ladder.parse_alpha(checked['observations']['alpha']))
    if analysis['input_sha256'] != checked['observations']['normalized_csv_sha256']:
        raise InputError('admission and analysis disagree on normalized CSV')
    body = {'schema': SCHEMA, 'data_kind': data_kind, 'engines': engines(),
            'pack_b64': seal.encode(pack_raw), 'results_b64': seal.encode(results_raw),
            'pack_bytes_sha256': digest(pack_raw), 'results_bytes_sha256': digest(results_raw),
            'seal_check': checked, 'analysis': analysis}
    receipt = {'body': body, 'receipt_sha256': digest(canonical(body))}
    if len(canonical(receipt)) > MAX_RECEIPT:
        raise InputError('receipt exceeds 12 MiB')
    return receipt


def parse_receipt(raw):
    if len(raw) > MAX_RECEIPT:
        raise InputError('receipt exceeds 12 MiB')
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=frozen.unique_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(InputError('nonfinite number')))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise InputError('invalid receipt JSON: ' + str(exc)[:160]) from exc


def replay(raw, expected_seal, expected_receipt):
    receipt = parse_receipt(raw)
    seal.shape(receipt, {'body', 'receipt_sha256'}, 'receipt')
    body = receipt['body']
    seal.shape(body, {'schema', 'data_kind', 'engines', 'pack_b64', 'results_b64',
                      'pack_bytes_sha256', 'results_bytes_sha256', 'seal_check', 'analysis'}, 'body')
    if body['schema'] != SCHEMA:
        raise InputError('unknown receipt schema')
    actual = digest(canonical(body))
    if receipt['receipt_sha256'] != actual or actual != pin(expected_receipt, 'receipt pin'):
        raise InputError('receipt mismatch against independently retained handoff pin')
    if canonical(body['engines']) != canonical(engines()):
        raise InputError('engine identity differs; use the original shipped engine sources')
    recomputed = make(unblob(body['pack_b64']), unblob(body['results_b64']), expected_seal, body['data_kind'])
    # Canonical comparison distinguishes bool/int and other Python equality aliases.
    if canonical(recomputed) != canonical(receipt):
        raise InputError('receipt disagrees with replayed admission or analysis')
    return recomputed


def literal(value):
    """Render user labels as visible ASCII, inert in Markdown and HTML tables."""
    text = json.dumps(value, ensure_ascii=True)[1:-1]
    return ''.join(c if c.isascii() and (c.isalnum() or c in ' .-') else '&#%d;' % ord(c)
                   for c in text)


def markdown(receipt):
    body = receipt['body']
    checked, analysis = body['seal_check'], body['analysis']
    observed = checked['observations']
    lines = ['# Benchmark evidence receipt', '',
             'Data: ' + body['data_kind'] + '.', '',
             'Complete paired observations admitted and exact McNemar/Holm analysis replayed.', '',
             'Baseline: ' + literal(observed['baseline']) + '.',
             'Pass rule: ' + literal(observed['pass_rule']), '',
             'Cases: %d. Baseline passes: %d. Planned family: %d. Alpha: %s.' %
             (analysis['paired_cases'], analysis['baseline_passes'], analysis['candidate_count'], observed['alpha']), '',
             '| Candidate | Passes | Wins | Losses | Effect (percentage points) | Holm p (exact) | Conclusion |',
             '| --- | ---: | ---: | ---: | ---: | --- | --- |']
    for item in analysis['candidates']:
        reject = item['familywise_reject_equal_discordance']
        direction = item['observed_direction']
        conclusion = ('Evidence favors candidate' if direction == 'candidate' else 'Evidence favors baseline') if reject else 'No rejection; equivalence not established'
        p = item['holm_adjusted_p']
        lines.append('| %s | %d | %d | %d | %s | %s/%s | %s |' %
                     (literal(item['name']), item['candidate_passes'], item['candidate_only_pass'],
                      item['baseline_only_pass'], item['candidate_minus_baseline_percentage_points'],
                      p['numerator'], p['denominator'], conclusion))
    lines += ['', '## Retained pins and byte identity', '',
              '- Pre-outcome seal: `' + checked['seal_sha256'] + '`',
              '- Plan: `' + checked['plan_sha256'] + '`',
              '- Handoff receipt: `' + receipt['receipt_sha256'] + '`',
              '- Raw pack: `' + body['pack_bytes_sha256'] + '`',
              '- Raw observations: `' + body['results_bytes_sha256'] + '`',
              '- Admitted CSV: `' + analysis['input_sha256'] + '`', '',
              '## Bound assets', '', '| Kind | ID | Bytes | SHA-256 |', '| --- | --- | ---: | --- |']
    for kind in ('cases', 'systems'):
        for asset in checked['assets'][kind]:
            lines.append('| %s | %s | %d | %s |' % (kind, literal(asset['id']), asset['bytes'], asset['sha256']))
    lines += ['', '## Limits', '',
              'The pre-outcome seal must be independently retained before collection. The receipt pin is retained at handoff; it does not preregister outcomes.', '',
              'This receipt verifies consistency and recomputation, not honest scoring, execution of the sealed code, complete dependencies, case independence, representativeness, or the absence of repeated looks. A non-rejection is not equivalence. Practical value is not established.', '',
              'The embedded pack and observations are unredacted. Markdown is a reading aid; use the JSON receipt and original independent pins for replay. Engine hashes identify code, not trusted authorship.']
    return '\n'.join(lines) + '\n'


def demo_receipt():
    # Reuse the predecessor fixture; no observed performance is invented.
    previous = seal.demo()
    pack = previous['pack']
    return make(canonical(pack), previous['normalized_csv'].encode(), pack['seal_sha256'],
                'synthetic_demonstration')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo')
    demo.add_argument('--json', action='store_true', help='emit replayable receipt instead of Markdown')
    create = sub.add_parser('create')
    create.add_argument('--pack', required=True)
    create.add_argument('--results', required=True)
    create.add_argument('--expected-seal-sha256', required=True)
    verify = sub.add_parser('replay')
    verify.add_argument('--receipt', required=True)
    verify.add_argument('--expected-seal-sha256', required=True)
    verify.add_argument('--expected-receipt-sha256', required=True)
    verify.add_argument('--markdown', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            receipt = demo_receipt()
            replay(canonical(receipt), receipt['body']['seal_check']['seal_sha256'], receipt['receipt_sha256'])
            output = canonical(receipt).decode() if args.json else markdown(receipt)
        elif args.command == 'create':
            receipt = make(read_workspace(args.pack, frozen.MAX_BYTES),
                           read_workspace(args.results, frozen.MAX_BYTES), args.expected_seal_sha256)
            output = canonical(receipt).decode()
        else:
            receipt = replay(read_workspace(args.receipt), args.expected_seal_sha256, args.expected_receipt_sha256)
            output = markdown(receipt) if args.markdown else canonical({'status': 'replayed', 'receipt_sha256': receipt['receipt_sha256']}).decode()
    except (ValueError, OSError, TypeError, RecursionError, OverflowError) as exc:
        parser.exit(2, 'error: ' + str(exc)[:240] + '\n')
    sys.stdout.write(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
