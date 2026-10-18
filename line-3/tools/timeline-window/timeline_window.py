#!/usr/bin/env python3
"""Find every event that might touch a time window in a verified evidence pack."""

import argparse
from datetime import datetime
import re
import sys

import replay

FORMAT = "timeline-window/1"
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_SHOWN = 200


def boundary(value):
    """Read a strict ISO timestamp as an exact instant, without precision widening."""
    if not isinstance(value, str):
        raise replay.ReplayError("window boundaries must be ISO 8601 text")
    match = replay.engine.ISO.fullmatch(value)
    if match is None:
        raise replay.ReplayError("window boundaries need T and explicit Z or ±HH:MM offset")
    body, offset = match.groups()
    if offset != "Z" and (int(offset[1:3]) > 23 or int(offset[4:]) > 59):
        raise replay.ReplayError("UTC offset is outside ±23:59")
    try:
        instant = datetime.fromisoformat(body + ("+00:00" if offset == "Z" else offset))
        value = replay.engine.micros(instant)
    except (OverflowError, ValueError) as exc:
        raise replay.ReplayError("window boundary is outside the UTC calendar") from exc
    if not replay.engine.MIN_MICROS <= value <= replay.engine.MAX_MICROS:
        raise replay.ReplayError("window boundary is outside the UTC calendar")
    return value


def inspect(pack, start_text, end_text, limit=100, *, source=None, contains=None):
    if type(limit) is not int or not 0 <= limit <= MAX_SHOWN:
        raise replay.ReplayError(f"limit must be an integer in 0..{MAX_SHOWN}")
    for name, value in (("source", source), ("contains", contains)):
        if value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 4096):
            raise replay.ReplayError(f"{name} filter must be text of 1..4096 characters")
    checked = replay.verify_pack(pack)
    start, end = boundary(start_text), boundary(end_text)
    if start >= end:
        raise replay.ReplayError("window start must precede end")

    selected = []
    counts = {"contained": 0, "possible_overlap": 0, "outside": 0}
    excluded_by_filter = 0
    for event in pack["timeline"]["events"]:
        left = boundary(event["start_utc"])
        right = boundary(event["end_utc_exclusive"])
        if right <= start or end <= left:
            counts["outside"] += 1
            continue
        if ((source is not None and event["source"] != source) or
                (contains is not None and contains not in event["message"])):
            excluded_by_filter += 1
            continue
        classification = "contained" if start <= left and right <= end else "possible_overlap"
        counts[classification] += 1
        if len(selected) < limit:
            selected.append({"classification": classification, "event": event})

    omitted = pack["timeline"]["omitted"]
    shown_omitted = omitted[:limit]
    match_count = counts["contained"] + counts["possible_overlap"]
    return {
        "format": FORMAT,
        "replay": checked,
        "query": {"start_utc_inclusive": replay.engine.utc_text(start),
                  "end_utc_exclusive": replay.engine.utc_text(end)},
        "counts": {"events_total": len(pack["timeline"]["events"]),
                   **counts, "excluded_by_filter": excluded_by_filter,
                   "window_matching": match_count + excluded_by_filter, "matching": match_count,
                   "shown": len(selected), "not_shown": match_count - len(selected),
                   "omitted_lines_total": len(omitted),
                   "omitted_lines_shown": len(shown_omitted),
                   "omitted_lines_not_shown": len(omitted) - len(shown_omitted)},
        "filters": {"source_exact": source, "message_contains_literal": contains,
                    "case_sensitive": True, "undated_lines_filtered": False},
        "events": selected,
        "undated_lines": shown_omitted,
        "source_sha256": [{"source": item["source"], "sha256": item["sha256"]}
                          for item in pack["inputs"]],
        "engine_sha256": pack["engine_sha256"],
        "options": pack["options"],
        "interpretation": "Intervals include stated precision and asserted symmetric clock uncertainty. Contained means the entire event interval lies within the half-open query window. Possible overlap means only part intersects. Filters apply only to timestamped events intersecting the window. Source matching is exact; message matching is a case-sensitive literal substring, without regex or Unicode normalization. Undated lines remain unfiltered and cannot be placed in time; truncation counts are explicit. Neither temporal overlap nor order proves causality. Independent authenticity requires a trusted pack digest."
    }


def read_checked_pack(path, expected):
    raw = replay.read_workspace(path, replay.MAX_PACK_BYTES)
    actual = replay.digest(raw)
    if expected is not None:
        if HEX.fullmatch(expected) is None:
            raise replay.ReplayError("expected digest must be 64 lowercase hex digits")
        if expected != actual:
            raise replay.ReplayError("pack does not match expected SHA-256")
    return replay.load_pack(raw), actual


def demo(*, source=None, contains=None):
    # Synthetic log lines. One 2-second uncertainty interval crosses the window edge.
    pack = replay.make_pack([
        ("front.log", b"2026-10-18T10:00:00Z began\n2026-10-18T10:00:02Z accepted\nunknown diagnostic\n"),
        ("back.log", b"2026-10-18T10:00:04Z finished\n"),
    ], ignore_unmatched=True, clock_uncertainty_ms=250)
    result = inspect(pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:04Z", source=source, contains=contains)
    result["example"] = "synthetic, not a real incident"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    example = sub.add_parser("demo", help="query a synthetic verified evidence pack")
    window = sub.add_parser("window", help="query a workspace evidence pack")
    window.add_argument("pack")
    window.add_argument("--start", required=True, help="inclusive ISO 8601 instant")
    window.add_argument("--end", required=True, help="exclusive ISO 8601 instant")
    window.add_argument("--limit", type=int, default=100)
    window.add_argument("--expect-sha256", help="independently trusted exact pack digest")
    for command in (example, window):
        command.add_argument("--source", help="exact source name (inert text)")
        command.add_argument("--contains", help="case-sensitive literal substring of parsed message")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo(source=args.source, contains=args.contains)
        else:
            pack, digest = read_checked_pack(args.pack, args.expect_sha256)
            result = inspect(pack, args.start, args.end, args.limit,
                             source=args.source, contains=args.contains)
            result["pack_sha256"] = digest
        sys.stdout.buffer.write(replay.canonical(result) + b"\n")
        return 0
    except (OSError, ValueError, RecursionError, OverflowError) as exc:
        print("timeline-window: " + replay.engine.visible(str(exc)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
