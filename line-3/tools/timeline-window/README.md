# Timeline Window

Find all events whose verified time intervals might touch a chosen UTC window.
The tool replays a Timeline Replay evidence pack from its embedded exact log bytes
before answering. It uses half-open intervals and includes declared timestamp
precision plus the pack's asserted symmetric clock uncertainty. Events fully inside
the window are `contained`; events that merely intersect are `possible_overlap`.
Undated lines remain visible in a separate list, since they cannot be placed on a
timeline. Detail limits report exact counts of anything left out.

Copy this whole folder, including `vendor/`, to use it independently. Python 3.10+
standard library only. One command from the repository root shows it working:

```sh
python3 -B line-3/tools/timeline-window/timeline_window.py demo
```

Observed locally: a synthetic pack replays successfully; of three events, two
possibly overlap the two-second query window, one lies outside, and one undated
line is reported separately. Six focused tests passed, including an exact
half-open boundary, a forged timeline rejection, invalid windows, and visible
truncation counts.

For a pack already in the workspace:

```sh
python3 -B line-3/tools/timeline-window/timeline_window.py window path/to/pack.json --start 2026-10-18T10:00:00Z --end 2026-10-18T10:05:00Z
```

An optional `--expect-sha256` takes an independently trusted SHA-256 of the exact
pack file. Without that pin, verification establishes internal consistency with
the shipped parser, not source authenticity. The tool reads only the named pack
inside the current workspace, not log paths named inside it. It does not measure
clock error, infer causes, or claim that undated lines were outside the window.

## Select a source and message

A worker can narrow timestamped window matches without losing the original
physical line citation, line hash or time uncertainty. One offline command:

```sh
python3 -B line-3/tools/timeline-window/timeline_window.py demo --source front.log --contains accepted
```

Observed: the complete synthetic pack verifies; two events intersect the window,
one matches both filters and one is excluded by filters. One other event is
outside the window. The one undated line remains separately visible. The returned
match is `front.log`, physical line 2, with its original hash and interval.

Both `demo` and `window` accept `--source NAME` (exact source name) and
`--contains TEXT` (literal, case-sensitive substring of the **parsed message**).
When supplied together they use AND. These are inert strings: no path lookup,
regular expression, shell expansion or Unicode normalization is performed.
Each supplied filter must contain 1..4096 characters. A missing source or an
unmatched literal produces zero matches, not an error. This is a reading view;
no pack, evidence bytes, parser options or uncertainty bounds are rewritten.

`counts.outside` counts events outside the time window regardless of filters.
`counts.window_matching` counts all intersecting timestamped events before
filtering. `counts.excluded_by_filter` counts intersecting events rejected by
either filter. `contained` and `possible_overlap` count surviving matches;
`matching` is their sum. Therefore `events_total = outside + excluded_by_filter +
matching`, and `window_matching = excluded_by_filter + matching`. Detail limits
apply after filtering: `not_shown` counts surviving matches beyond the limit.
All undated lines remain unfiltered, even with a source filter, because they
are a separate account of unplaced evidence. Their own truncation counts remain
explicit. No filter matches do not establish that an incident did not happen.

Twelve tests passed: the original six plus combined filters/citations/immutability,
literal and exact matching, filtered truncation, replay rejection despite a
nonmatching filter, filter validation, and Unicode matching without normalization.
Run them with:

```sh
python3 -B -m unittest discover -s line-3/tools/timeline-window -v
```
