#!/usr/bin/env python3
"""Review original UTF-8 text with bounded, terminal-inert byte evidence."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ENGINE = Path(__file__).resolve().parents[1] / 'unicode-lantern' / 'unicode_lantern.py'
spec = importlib.util.spec_from_file_location('text_lantern', ENGINE)
lantern = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lantern)
MAX_OUTPUT = 4 * 1024 * 1024
CONTEXT = 16
PREVIEW = 64


def quoted(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)


def byte_text(raw):
    return ''.join(chr(b) if 32 <= b <= 126 and b != 92 else
                   '\\\\' if b == 92 else '\\x%02x' % b for b in raw)


def evidence(raw, position):
    # The scanner produces unicode_escape, not arbitrary user escape syntax.
    value = position['escaped'].encode('ascii').decode('unicode_escape').encode('utf-8')
    start = position['byte_offset']
    end = start + len(value)
    if raw[start:end] != value:
        raise ValueError('scanner location does not match original bytes')
    left, right = max(0, start - CONTEXT), min(len(raw), end + CONTEXT)
    stop = min(end, start + PREVIEW)
    return dict(byte_start=start, byte_end=end,
                line=raw.count(b'\n', 0, start) + 1,
                byte_column=start - raw.rfind(b'\n', 0, start),
                sha256=hashlib.sha256(value).hexdigest(),
                before=dict(byte_start=left, byte_end=start, bytes=byte_text(raw[left:start])),
                preview=dict(byte_start=start, byte_end=stop, bytes=byte_text(raw[start:stop])),
                omitted_span_bytes=end - stop,
                after=dict(byte_start=end, byte_end=right, bytes=byte_text(raw[end:right])))


def review(raw, source='<memory>', max_findings=100):
    """Recompute findings from bytes; do not accept caller-supplied reports."""
    report = lantern.scan(raw, source, max_findings)
    # Avoid duplicating arbitrarily long identifier strings in the reading view.
    findings = []
    for original in report['findings']:
        item = {key: original[key] for key in ('rule', 'explanation')}
        item['source'] = evidence(raw, original)
        for key in ('codepoint', 'unicode_name', 'scripts'):
            if key in original:
                item[key] = original[key]
        if 'first' in original:
            item['first_source'] = evidence(raw, original['first'])
        findings.append(item)
    return dict(tool='unicode-text-window/1', source=source,
                source_sha256=report['sha256'], source_bytes=len(raw),
                unicode_version=report['unicode_version'],
                finding_count=report['finding_count'], retained_findings=len(findings),
                omitted_findings=report['finding_count'] - len(findings),
                truncated=report['truncated'], assessment=report['assessment'],
                findings=findings, limitations=[s for s in report['limitations']
                    if not s.startswith('Columns count')] + [
                    'Viewer columns count original bytes, not Unicode code points or screen cells.',
                    'Raw UTF-8 only: literal backslash escapes are not decoded as JSON or source code.',
                    'Evidence is unredacted; digests identify bytes, not authorship.',
                    'Only retained findings are shown; excerpts may split UTF-8 characters.',
                    'No cross-file collision detection or document-format parsing.'])


def render(raw, source='<memory>', max_findings=100):
    report = review(raw, source, max_findings)
    lines = ['UNICODE TEXT WINDOW / 1', 'Not a safety verdict. Evidence is not redacted.',
             'Source: ' + quoted(source), 'Original SHA-256: ' + report['source_sha256'],
             'Original bytes: ' + str(report['source_bytes']),
             'Unicode database: ' + report['unicode_version'],
             'Findings total: %d; retained: %d; omitted: %d' % (
                 report['finding_count'], report['retained_findings'], report['omitted_findings']),
             'Truncated: ' + str(report['truncated']).lower(),
             'Assessment: ' + report['assessment'],
             'Coordinates: zero-based half-open ORIGINAL byte ranges.',
             'Line/byte-column: one-based; only LF starts a line.',
             'Excerpts: 16 context bytes per side; at most 64 span bytes.',
             'Byte notation: backslash doubled; nonprintable/non-ASCII bytes use \\xHH.',
             'Evidence objects are JSON-quoted; JSON decoding removes one escaping layer.']
    for index, item in enumerate(report['findings'], 1):
        lines.extend(['', 'FINDING %d' % index, quoted(item)])
    lines.extend(['', 'LIMITATIONS'] + [quoted(s) for s in report['limitations']])
    text = '\n'.join(lines) + '\n'
    if len(text) > MAX_OUTPUT:
        raise ValueError('render exceeds output budget; lower max_findings')
    if any(c != '\n' and not 32 <= ord(c) <= 126 for c in text):
        raise ValueError('render violated printable ASCII contract')
    return text, report['finding_count']


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo', action='store_true', help='synthetic source-code example')
    group.add_argument('--file', help='explicit UTF-8 file within current workspace')
    parser.add_argument('--max-findings', type=int, default=100)
    args = parser.parse_args(argv)
    try:
        if args.demo:
            raw, source = lantern.DEMO.encode('utf-8'), '<synthetic-demo>'
        else:
            path = lantern.workspace_file(args.file)
            with path.open('rb') as handle:
                raw = handle.read(lantern.MAX_BYTES + 1)
            source = str(path.relative_to(Path.cwd().resolve()))
        text, count = render(raw, source, args.max_findings)
        sys.stdout.write(text)
        return 0 if args.demo or count == 0 else 1
    except (OSError, ValueError, OverflowError) as error:
        sys.stderr.write('ERROR: ' + quoted(str(error)) + '\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
