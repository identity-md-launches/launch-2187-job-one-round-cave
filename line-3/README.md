# Line 3 — incident timelines

The first piece, [Time Flint](tools/time-flint/README.md), merges plain UTF-8 logs
and JSONL into a reproducible UTC timeline. It preserves source citations and
marks timestamp intervals whose order cannot be established from their stated
precision. `GOAL.md` is the line's one thing.

## Mark 01: Pebbles in Time

Pepe arranges scattered pebbles into a trail on the illuminated cave wall. The
frog and trail were added to the supplied bare cave for this first round. The
wall's square framing, roots, cracks, rough rock, and torchlit color remain.

Output inspection: `artifacts/line-3/wall.png` is a 1254 × 1254 PNG at the supplied
cave's dimensions; `dist/line-3/01.jpg` is a 512 × 512 JPEG preview. The JSON
record contains the finished PNG's SHA-256. Visual review found a wide mouth,
heavy-lidded eyes, worn ochre and charcoal pigments, and no text or symbols.
The hands are concealed and no handprints appear, so there are no visible digits
to miscount. Unmet visual requirements observed: none.

## Mark 22: Bounded Time

Time Flint now handles calendar extremes as validation errors, bounds workspace
input reads, and lets an analyst assert a symmetric clock uncertainty bound.
Original timestamp evidence remains visible beside broadened intervals. See
[the tool README](tools/time-flint/README.md) for a working one-command example,
the precise assumptions and the regression suite.

Two ochre pebbles enclosed by overlapping chalk arcs, with charcoal pebbles at
the outer edges, mark the difference between an observed timestamp and an
uncertain interval. No earlier record was changed. The new number is 22 because
21 numbered records, including reserved slots, already existed.

The built-in image tool edited the existing wall with this prompt:

> Keep the square cave, its rock, roots, cracks, torchlight, existing Pepe and
> pebble trail. Add only two small ochre pebbles in the blank upper-right rock,
> each enclosed by an uneven overlapping chalk arc, with charcoal pebbles at
> the outer ends. Use worn earth pigments. No new hands, text, digits, logos,
> signatures, borders, photographs or 3D rendering.

The complete generation prompt is retained in [wall-review.json](wall-review.json).
For preservation, only the new mark's empty-rock patch was composited into the
original. Every original pixel outside x=710..1044, y=355..554 is unchanged,
including the whole earlier Pepe and pebble trail. This was checked against the
original PNG's decoded pixels. A 12-pixel join lies inside that rectangle.

The finished `artifacts/line-3/wall.png` and required named output
`artifacts/line-3/wall-v2.png` contain identical 1254 × 1254 RGB8 PNG bytes.
`dist/line-3/22.jpg` is a 512 × 512 baseline JPEG under 100 KB.
`dist/line-3/22.json` references the finished PNG's SHA-256.

Visual review of the final PNG: the earlier Pepe's wide mouth and heavy-lidded
eyes remain intact; the new arcs use chalk, charcoal, red and yellow ochre.
No letters, numbers, captions, logos, watermarks, borders or frames were seen.
No hands or handprints were added; the earlier hands remain concealed, so there
are no visible hand digits to count. The square size, cave framing and light
are preserved. Unmet visual requirements observed: none. This inspection does
not claim automatic visual certification. Raster formats, checks, prompt and
file properties are recorded in `wall-review.json`.

## Mark 23: Retraced Time

[Timeline Replay](tools/timeline-replay/README.md) gives a worker a portable JSON
pack of exact log bytes, parser identity, assumptions and the resulting timeline.
It replays without the original files and rejects inconsistent evidence or reports.
An optional independently trusted pack digest binds all file bytes. A matching
replay alone establishes consistency, not authentic or complete logs.

Try it from the repository root:

```sh
python3 -B line-3/tools/timeline-replay/timeline_replay.py demo
```

Observed: two synthetic events and one omission replayed successfully at an
asserted ±750 ms clock bound, and an altered message was rejected. Twenty new
tests and the original 28 Time Flint tests passed. CLI checks also replayed a
pack after deleting the scratch source copies. Results are recorded in
`cli-check-23.json` and `round-23-review.json`.

The new mark is two short matching pebble trails between the older chalk arcs
and the original trail. The image tool supplied the pigments; only the empty-rock
patch x=735..909, y=580..694 was composited into the inherited wall. Every pixel
outside that patch, including every earlier painted mark and the entire Pepe,
is unchanged. `image-check-23.json` records the decoded-pixel comparison.

`artifacts/line-3/wall-v3.png` is the required 1254 × 1254 RGB8 PNG;
`artifacts/line-3/wall.png` aliases it. `dist/line-3/23.jpg` is a 512 × 512 JPEG
of 66,664 bytes. `dist/line-3/23.json` references the PNG's SHA-256.
Visual inspection of both final images found no text or numbers and no unmet
visual requirements. No hands or handprints were added, and the ancestral
hands remain concealed, so there are no visible hand digits to count. Rock,
roots, cracks, lighting and framing remain unchanged outside the small patch.

## Mark 25: The Narrowing Gap

[Clock Margin](tools/clock-margin/README.md) checks how much total symmetric clock
uncertainty a verified event pair can tolerate. Its exact interval calculation is
checked by full evidence replays at the last ordered millisecond and the next.
It preserves source citations and reports calendar/pack failures explicitly.

```sh
python3 -B line-3/tools/clock-margin/clock_margin.py demo
```

Observed: the synthetic pair remains ordered at ±500 ms and becomes unresolved
at ±501 ms. Its original ±750 ms assumption is already unresolved. Thirteen new
tests, twenty Replay tests and thirteen Order Witness tests passed. A copied
standalone tool analyzed a pack after the scratch logs were removed and rejected
changed report content and a wrong pinned digest. No real incident is claimed;
the tool tests asserted bounds, not measured clocks or causal relationships.

The new wall mark is two red ochre dots beside inward-facing chalk arcs above
Pepe, showing a gap that uncertainty can close. The tool generated the new pigment;
only x=520..684, y=300..397 was blended into the inherited wall. All pixels outside
that rectangle are identical, preserving every older painting, the rock, roots,
cracks, torchlight and framing. No new hands or stencils appear; ancestral hands
remain concealed, with no visible digits to count. No words, numbers or other
prohibited imagery were observed. Unmet visual requirements observed: none.

`artifacts/line-3/wall-v5.png` is a **1254 × 1254 RGB8 PNG**, also reached through
`wall.png`. `dist/line-3/25.jpg` is a **512 × 512 JPEG** of 66,593 bytes, and
`25.json` binds the whole wall's SHA-256. The image tool's one generated draft
was used; no other draft was required. Full byte counts, hash and local visual
review are in [round-25-review.json](round-25-review.json).

## Mark 26: Two Readings

[Timeline Diff](tools/timeline-diff/README.md) verifies two offline evidence packs,
then reports changed source and line evidence, changed clock assumptions, and the
before/after order of a selected cited pair. It distinguishes a changed relation
on the same line evidence from a comparison whose evidence itself changed.

```sh
python3 -B line-3/tools/timeline-diff/timeline_diff.py demo
```

Observed: two synthetic lines change from ordered to unresolved under an asserted
±750 ms bound, with both line hashes unchanged. Eight new tests passed. This does
not measure clock error or establish a real incident. The new cave mark is two
parallel short pebble trails above Pepe. The final edit changes only pixels in
x=305..474, y=335..459; every earlier painted mark, including Pepe, remains
outside that patch. The finished wall is a 1254 × 1254 RGB8 PNG at
`artifacts/line-3/wall-v6.png`, reached through `wall.png`; the 512 × 512 JPEG is
`dist/line-3/26.jpg`. The image hash is in `26.json` and file details are in
[round-26-review.json](round-26-review.json). Local visual review found no words,
symbols or other prohibited additions. No hands or handprints were added; Pepe's
ancestral hands are concealed, so there are no visible digits to count. Unmet
visual requirements observed: none.

## Mark 27: Windowed Pebble

[Timeline Window](tools/timeline-window/README.md) replays an evidence pack, then
finds events whose uncertainty intervals can touch a chosen half-open UTC window.
It distinguishes fully contained events from possible overlaps and separately
reports undated lines and any truncated details. The one-command synthetic demo
and six focused tests passed.

The added ochre pebble between chalk arcs lies on previously unpainted lower-right
rock. The final PNG changes only x=995..1149, y=900..1004; all ancestor pixels
outside that rectangle, including Pepe, remain identical. The 1254-square PNG is
`artifacts/line-3/wall-v7.png`, reached by `wall.png`; the 512-square JPEG is
`dist/line-3/27.jpg`. Exact formats, hashes, dimensions and visual review are in
[round-27-review.json](round-27-review.json). No hands or handprints were added,
and no words, numbers or prohibited symbols were observed. Unmet visual
requirements observed: none.

## Mark 28: Chosen Pebble

[Timeline Window](tools/timeline-window/README.md) now narrows verified time-window
matches by exact source name and literal parsed message text. It retains original
citations, hashes and uncertainty intervals, reports excluded and truncated counts,
and keeps all undated lines separately visible. Twelve tests and this demo passed:

```sh
python3 -B line-3/tools/timeline-window/timeline_window.py demo --source front.log --contains accepted
```

The synthetic pack has two intersecting events: one matches and one is excluded.
This does not establish a real incident or measured clock error.

The mark is a chosen ochre pebble between charcoal pebbles and short chalk strokes
on unused lower rock. Built-in imagegen supplied the pigment; only the patch
[720,925,835,995) was retained. Every ancestral pixel outside it is identical.
The required output `artifacts/line-3/wall-v8.png` is a 1254 × 1254 RGB8 PNG,
reached also by `wall.png`; `dist/line-3/28.jpg` is a 512 × 512 JPEG. Local visual
review found no letters, numbers or prohibited additions. No new hands or
handprints appear; the older hands remain concealed, so no digits are visible.
Unmet visual requirements observed: none. Dimensions, hash, preservation check,
full prompt and review limits are in [round-28-review.json](round-28-review.json).
