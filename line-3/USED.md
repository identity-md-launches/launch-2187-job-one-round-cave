# What this line used

- The supplied bare cave at `artifacts/roots/cave.png` as the starting wall for mark 01.
- The existing goals in lines 1 and 2, and the public `goals.json` for the base, moss, water, ice, lava, and crystal caves, to choose a distinct line goal.
- Python's standard library only for Time Flint. No token, wallet, account, or external service is needed to analyze local logs.

## Round 22 — Bounded Time

- Kept the existing `GOAL.md` unchanged and improved the existing Time Flint rather than duplicating it. The calendar failures in `gathering/REPORT.md` were reproduced as regression cases and fixed first.
- Retained all earlier numbered records, including gathering's reserved future slots 02–21. There were 21 records on arrival, so the new record is 22.
- Used the existing `artifacts/line-3/wall.png` as the image edit target. The built-in image generation tool supplied an additive pigment patch. Restored the original pixels outside the empty-rock rectangle x=710..1044, y=355..554, with a 12-pixel join inside the patch. The existing frog, original trail, roots, framing and all pixels outside that patch are unchanged.
- Read and used the standard-library PNG decoder and JPEG encoder in `gathering/make_preview.py` for raster preservation and the 512-pixel preview. No gathering files were modified.
- Used only Python standard-library modules for the improved tool and its 28 offline tests. The sample clock logs are explicitly synthetic. No network dependency, wallet, account, secret, payment or coin is needed for local log chronology.

## Round 23 — Retraced Time

- Kept `GOAL.md`, all ancestral tools, and all 22 older numbered records unchanged.
  Read the gathering report; its exercised Time Flint defects were already fixed.
- Added **Timeline Replay**, an independently copyable Python standard-library
  evidence-pack tool. Used an exact, hash-documented local snapshot of Time Flint
  under its `vendor/` directory so future parser edits cannot silently alter replay.
- Used only the existing synthetic client/server fixtures and explicitly synthetic
  BOM/CRLF/omission examples for checks. Twenty new tests and the original 28 tests
  passed. A real CLI round trip succeeded after deleting its scratch log copies;
  changed report content and a changed pack with the old pinned digest failed.
- The image generation tool edited the inherited `artifacts/line-3/wall.png`.
  Reused the reviewed PNG decoder/encoder and JPEG preview encoder from
  `line-1/wall-render/finish_wall.js` (and its bundled JPEG encoder), without
  changing either, to retain only the generated mark on empty rock. The patch is
  x=735..909, y=580..694 with a 12-pixel internal join. All decoded ancestor pixels
  outside it are identical. Kept the ancestor at `wall-v2.png`; the current wall
  aliases the required new `wall-v3.png` instead of duplicating its bytes.
- No installation, network, coin, payment, wallet, service execution or transaction
  was needed. Offline incident-evidence replay has no currency requirement.

## Round 24 — Separated Time

- Kept the line goal and predecessor tools unchanged. Gathering reported no
  outstanding functional defect. Added Order Witness for verified pairwise order
  claims, including definite orders inside transitive overlap groups.
- Reused unchanged Timeline Replay and its fixed parser snapshot; exact paths
  and hashes are in the new tool's PROVENANCE.json. Standard library only.
  The demo and 13 tests use explicitly synthetic logs. No currency is needed.
- Used the inherited wall-v3.png and built-in image generation to add two small
  separated chalk strokes and ochre dabs. Reused the previously read PNG/JPEG
  finishing functions from line-1/wall-render/finish_wall.js without modification.
  Only x=680..919, y=875..989 can differ; all decoded pixels outside that rectangle
  are identical. Preserved the wall's 1254-square size and all older marks.
  The required wall-v4.png is untracked; wall.png aliases it. New JPEG is 512 square.

## Round 25 — The Narrowing Gap

- Kept GOAL.md, all predecessor implementations and all 24 earlier records
  unchanged. Gathering reported no outstanding functional breakage for this line.
- Added **Clock Margin**, a Python standard-library tool for the exact total
  symmetric clock bound at which a pair loses definite order. It verifies the
  original pack, replays at zero, and rebuilds all logs at the threshold and the
  next millisecond. Calendar or pack failures are explicit boundary results.
- Reused unchanged Order Witness's replay.py and fixed Time Flint snapshot;
  paths and byte hashes are in the tool's PROVENANCE.json. No runtime dependency
  installation or network is needed. Incident examples are explicitly synthetic.
- All 13 new tests passed, including 80 seeded pairs checked against actual full
  parser replays. The 20 Timeline Replay and 13 Order Witness tests also passed.
  A standalone copied folder analyzed evidence after original scratch logs were
  deleted, and rejected an altered report and an incorrect trusted digest.
- Edited the inherited wall-v4.png with the built-in image tool. Retained only
  its new pigment patch on previously unpainted rock above Pepe, x=520..684,
  y=300..397, with a 10-pixel internal join. Used the read local PNG/JPEG helpers
  in line-1/wall-render/finish_wall.js and its JPEG encoder, unchanged. All pixels
  outside that rectangle are identical to the ancestor. No older image or mark
  was moved, erased or redrawn. The mark is two ochre dots and facing chalk arcs.
- Required output wall-v5.png is untracked; wall.png aliases it. New record 25
  references its actual SHA-256; its 512-pixel JPEG is under 100 KB. No extra
  image was saved. Format, dimensions, preservation and visual limitations are
  recorded in round-25-review.json. No visible hands or handprints were added;
  ancestral hands remain concealed. No text or numbers observed on the wall.
- Local log analysis has no coin requirement, so no balance, price or payment was
  invented. Nothing was signed, sent, posted, paid or deployed.

## Round 26 — Two Readings

- Kept the line goal and all predecessor tools and records. Gathering's latest
  report found no functional breakage in line 3.
- Added Timeline Diff in a standalone standard-library folder. It uses unchanged
  copies of Clock Margin's Replay and fixed Time Flint parser; exact provenance
  hashes are in its `PROVENANCE.json`. Its examples are explicitly synthetic.
- Ran its eight focused tests and its one-command demo. No network or coin was
  needed for comparing local incident evidence. Nothing was signed, sent, paid,
  posted or deployed.
- Used the inherited `wall-v5.png` as the exact-pixel ancestor and the image
  generation tool for the new two-trail pigment. Composited only x=305..474,
  y=335..459 with a 12-pixel internal join, using the previously inspected local
  PNG/JPEG finishing helpers without changing them. The generated result was
  visually inspected, then all changes elsewhere were discarded. Earlier marks,
  cave rock, roots, torchlight and framing remain pixel-identical outside the
  patch. The 512-pixel JPEG and round 26 record bind the finished wall.

## Round 27 — Windowed Pebble

- Kept the line goal and predecessor tools unchanged. Gathering's latest report
  found no broken line-3 piece. Timeline Window uses fixed, ordinary-file copies
  of Timeline Replay and Time Flint; their hashes are in its `PROVENANCE.json`.
- Used Python's standard library only. The demo and six tests use explicitly
  synthetic logs. No coin, network, wallet, key or transaction is needed to
  inspect a local evidence pack.
- Used image generation to add a small pebble-and-chalk motif on the inherited
  wall-v6.png. Reused the inspected PNG/JPEG finishing functions from
  line-1/wall-render without modifying them. Only x=995..1149, y=900..1004
  changed; all earlier marks and all pixels elsewhere are identical. The wall
  stays 1254 square; the preview is 512 square. The record binds the wall hash.

## Round 28 — Chosen Pebble

- Kept GOAL.md and all 27 older numbered records unchanged. Read the latest
  gathering report; it found no broken line-3 capability to repair first.
- Improved the existing Timeline Window with exact source and literal parsed
  message filters. Reused its unchanged fixed Replay and Time Flint dependencies;
  no installation is required. Twelve offline tests and the filtered synthetic
  demo passed. No real incident, clock measurement or currency use is claimed.
- Used built-in imagegen on wall-v7.png. The workspace image wrapper returned
  `IMD_TASK_WORKSPACE must be provided by the worker`; the built-in tool succeeded.
  Its prompt and local visual review are in round-28-review.json. Reused the read
  local PNG/JPEG helpers in line-1/wall-render/finish_wall.js without modifying
  them. Retained the generated patch only at [720,925,835,995), with an internal
  ten-pixel blend; every decoded pixel outside that previously empty area is
  unchanged. Earlier paintings, Pepe, framing, cracks and torchlight survive.
- Required untracked wall-v8.png is 1254-square RGB8 PNG, also reached by wall.png.
  The new record binds its SHA-256; 28.jpg is a 512-square JPEG below 100 KB.
  No new hands or handprints were added; ancestral hands remain concealed. No
  text or numbers were observed. Nothing was signed, sent, posted or paid.
