#!/usr/bin/env python3
"""Compare several paired binary candidates with exact tests and Holm correction."""

import argparse
import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from pathlib import Path


MAX_BYTES = 2 * 1024 * 1024
MAX_CASES = 10_000
MAX_CANDIDATES = 16


class InputError(ValueError):
    """Input cannot support the claimed paired comparison."""


def parse_alpha(value):
    if len(value) > 64:
        raise InputError('alpha must contain at most 64 characters')
    try:
        alpha = Decimal(value)
    except InvalidOperation as exc:
        raise InputError('alpha must be a decimal number') from exc
    if not alpha.is_finite() or not Decimal('0.000001') <= alpha <= Decimal('0.2'):
        raise InputError('alpha must be between 0.000001 and 0.2 inclusive')
    return alpha


def valid_id(value):
    return bool(value) and value == value.strip() and not any(ord(c) < 32 or ord(c) == 127 for c in value)


def read_csv_bytes(raw):
    """Return named, complete observations on a shared, uniquely identified case set."""
    if len(raw) > MAX_BYTES:
        raise InputError(f'CSV exceeds {MAX_BYTES} bytes')
    try:
        decoded = raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise InputError('CSV must be UTF-8') from exc
    if '\x00' in decoded:
        raise InputError('CSV contains a NUL byte')
    reader = csv.reader(io.StringIO(decoded, newline=''), strict=True)
    try:
        header = next(reader, None)
        if (header is None or len(header) < 4 or len(header) > MAX_CANDIDATES + 2
                or header[:2] != ['case', 'baseline']):
            raise InputError('header must be case,baseline followed by 2 to 16 candidate names')
        names = header[2:]
        if (any(not valid_id(name) or name in ('case', 'baseline') for name in names)
                or len(set(names)) != len(names)):
            raise InputError('candidate names must be distinct, nonempty IDs without edge whitespace or controls')
        seen = set()
        rows = []
        for row in reader:
            line = reader.line_num
            if len(row) != len(header):
                raise InputError(f'line {line}: expected exactly {len(header)} fields')
            case, *outcomes = row
            if not valid_id(case):
                raise InputError(f'line {line}: case ID must be nonempty without edge whitespace or controls')
            if case in seen:
                raise InputError(f'line {line}: duplicate case ID')
            if any(value not in ('0', '1') for value in outcomes):
                raise InputError(f'line {line}: all outcomes must be exactly 0 or 1')
            seen.add(case)
            rows.append(tuple(int(value) for value in outcomes))
            if len(rows) > MAX_CASES:
                raise InputError(f'CSV exceeds {MAX_CASES} paired cases')
    except csv.Error as exc:
        raise InputError(f'invalid CSV near line {reader.line_num}: {exc}') from exc
    if not rows:
        raise InputError('CSV must contain at least one paired case')
    return names, rows


def load_workspace_input(name):
    root = Path.cwd().resolve()
    path = Path(name).resolve()
    if not path.is_relative_to(root):
        raise InputError('input must resolve inside the current workspace directory')
    if not path.is_file():
        raise InputError('input must be a regular workspace file')
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    names, rows = read_csv_bytes(raw)
    return raw, names, rows


def exact_mcnemar(wins, losses):
    """Exact two-sided conditional McNemar p-value as an integer fraction."""
    if min(wins, losses) < 0 or wins + losses > MAX_CASES:
        raise InputError('invalid discordant counts')
    discordant = wins + losses
    term = total = 1
    for k in range(1, min(wins, losses) + 1):
        term = term * (discordant - k + 1) // k
        total += term
    return min(Fraction(1), Fraction(2 * total, 1 << discordant))


def decimal_display(value):
    with localcontext() as context:
        context.prec = 16
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def analyze(raw, names, rows, alpha):
    """Apply Holm's step-down rule to all prespecified candidate comparisons."""
    count = len(rows)
    if not 1 <= count <= MAX_CASES or not 2 <= len(names) <= MAX_CANDIDATES:
        raise InputError('invalid case or candidate count')
    if any(len(row) != len(names) + 1 or any(value not in (0, 1) for value in row) for row in rows):
        raise InputError('incomplete or nonbinary observation')
    alpha_fraction = Fraction(*alpha.as_integer_ratio())
    baseline_passes = sum(row[0] for row in rows)
    candidates = []
    for index, name in enumerate(names, 1):
        wins = sum(row[0] == 0 and row[index] == 1 for row in rows)
        losses = sum(row[0] == 1 and row[index] == 0 for row in rows)
        passes = baseline_passes + wins - losses
        p = exact_mcnemar(wins, losses)
        candidates.append({'name': name, 'wins': wins, 'losses': losses,
                           'passes': passes, 'p': p})
    order = sorted(range(len(candidates)), key=lambda i: (candidates[i]['p'], i))
    running_adjusted = Fraction(0)
    for rank, index in enumerate(order):
        item = candidates[index]
        running_adjusted = max(running_adjusted, min(Fraction(1), (len(names) - rank) * item['p']))
        item['adjusted'] = running_adjusted
        item['rank'] = rank + 1
    report_candidates = []
    for item in candidates:
        p, adjusted = item['p'], item['adjusted']
        report_candidates.append({
            'name': item['name'],
            'candidate_passes': item['passes'],
            'candidate_only_pass': item['wins'],
            'baseline_only_pass': item['losses'],
            'candidate_minus_baseline_percentage_points': 100 * (item['wins'] - item['losses']) / count,
            'exact_two_sided_p': {'numerator': str(p.numerator), 'denominator': str(p.denominator),
                                  'decimal_16_digits': decimal_display(p)},
            'holm_rank': item['rank'],
            'holm_adjusted_p': {'numerator': str(adjusted.numerator), 'denominator': str(adjusted.denominator),
                                'decimal_16_digits': decimal_display(adjusted)},
            'familywise_reject_equal_discordance': adjusted <= alpha_fraction,
            'observed_direction': ('candidate' if item['wins'] > item['losses'] else
                                   'baseline' if item['losses'] > item['wins'] else 'tie'),
        })
    return {
        'schema_version': 1,
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'paired_cases': count,
        'baseline_passes': baseline_passes,
        'candidate_count': len(names),
        'familywise_alpha': str(alpha),
        'method': 'exact two-sided conditional McNemar per candidate; Holm step-down familywise correction',
        'candidates': report_candidates,
        'assumptions': [
            'Every row is one independent case evaluated once by the baseline and every candidate.',
            'Case set, pass rule, candidate family and alpha were fixed before inspecting results.',
            'All planned candidate comparisons against this baseline are included in this family.',
            'These tests address equal discordance probabilities, not equivalence or practical value.',
            'Repeated looks, case selection and correlated cases are not corrected here.'
        ],
    }


def demo_csv():
    """Explicitly synthetic 40-case family with one clear improvement."""
    lines = ['case,baseline,swift,steady,noisy']
    for i in range(40):
        baseline = int(i < 20)
        swift = int(i < 20 or 20 <= i < 32)
        steady = int(2 <= i < 20 or 20 <= i < 28)
        noisy = int(5 <= i < 20 or 20 <= i < 25)
        lines.append(f'synthetic-{i + 1:03},{baseline},{swift},{steady},{noisy}')
    return ('\n'.join(lines) + '\n').encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', help='UTF-8 CSV inside the current workspace')
    source.add_argument('--demo', action='store_true', help='run a labeled synthetic example')
    parser.add_argument('--alpha', default='0.05', help='prespecified familywise alpha, 0.000001 through 0.2')
    args = parser.parse_args(argv)
    try:
        alpha = parse_alpha(args.alpha)
        if args.demo:
            raw = demo_csv()
            names, rows = read_csv_bytes(raw)
        else:
            raw, names, rows = load_workspace_input(args.input)
        result = analyze(raw, names, rows, alpha)
        result['data_kind'] = 'synthetic_demonstration' if args.demo else 'user_supplied_benchmark'
    except (InputError, OSError, ValueError) as exc:
        parser.exit(2, f'error: {exc}\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
