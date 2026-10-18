# Window Review

Find incident events that might touch a chosen UTC window, then inspect the
original evidence behind the shown events and undated lines without activating
terminal controls. This connects Line 3's Timeline Window to Line 2's Unicode
Window. All ten engine files are unchanged ordinary-file snapshots, with source
paths and SHA-256 in [provenance.json](provenance.json). Copy this entire folder
for standalone use. Python 3.10+ and its standard library are sufficient offline.

```sh
python3 -B shared/window-review/window_review.py demo
```

Observed: the synthetic pack contains three events. With an asserted ±250 ms
clock bound, two possibly overlap `[10:00:02,10:00:04)` UTC and one lies outside.
An undated duplicate-key JSON line stays visible separately. The report exposes
escaped right-to-left controls in a selected JSON event and the duplicate key
and invisible character in the undated line. The demo is not a real incident
or an authentication claim. Its complete output is in
[the gathering transcript](../../gathering/window-demo.txt).

For an existing Timeline Replay pack, from the repository root:

```sh
python3 -B shared/window-review/window_review.py review test/scratch/pack.json --start 2026-10-18T10:00:02Z --end 2026-10-18T10:00:04Z --limit 10
```

Supply your actual independently retained exact-byte pack digest with
`--expect-sha256` when identity matters. The tool never derives an expected pin
from an untrusted object. Original log paths inside the pack remain inert
strings; only the explicit regular workspace pack and fixed shipped code are
read. No environment, accounts, network, installation or writes are needed.

The complete pack is replayed before scanning or rendering anything. Event
selection uses half-open intervals, declared timestamp precision and the pack's
asserted symmetric clock bound. `--limit` (0–50, default 10) limits matching
events and undated lines **separately**; totals and unshown counts remain exact.
Outside-window events, blank lines and unshown details are explicitly unreviewed.
This is a focused view, not a complete security scan. Use the earlier
[Replay Review](../replay-review/README.md) for whole-pack Unicode review.

Each shown citation includes the whole original source digest, original physical
line span/digest, and up to 256 original bytes as an escaped preview. Physical
spans exclude LF but retain BOM/CR. A separately labeled payload span strips an
initial BOM and trailing CR to match the timeline parser. Add the payload's
whole-source start offset to JSON-local source spans to locate original bytes.
JSON Window keeps original escape spellings, decoded coordinates, at most 20
findings, and explicit omitted-finding counts. Plain text uses Unicode Lantern
with its payload-local offsets. Malformed omitted JSON is labeled **REVIEW
INCOMPLETE**. It is never called clean because it could not be decoded.

Output contains printable ASCII and LF only, including errors and hostile
source names. Byte previews double literal backslashes and use `\xHH` for
nonprintable/non-ASCII bytes; quoted fields use JSON escaping. Do not unescape
before terminal display. This is not HTML/Markdown escaping. Exit 0 means the
review completed, even with findings or explicitly incomplete omitted JSON;
exit 2 means invalid request, bad pin, replay failure or exceeded budget, with
no partial stdout. The report caps output at 4 MiB, input at 16 MiB, and inherits
the pack's 2 MiB original-evidence, depth, source and line budgets. It buffers
the complete output before writing and is not a streaming implementation.

```sh
python3 -B -m unittest discover -s shared/window-review -v
```

Twelve tests passed: half-open selection; hidden decoded Unicode; undated
duplicate keys; BOM/CRLF coordinate agreement with original bytes; replay-before-
scan forgery rejection; externally pinned consistent replacements and whitespace;
hostile terminal strings; malformed omitted JSON; explicit preview/finding/query
truncation; strict input; immutability; snapshot identity; and standalone copied
CLI success/failure with empty stdout on error.

Replay proves consistency with these parsers, not truth, completeness, authorship
or collection time. A digest obtained with untrusted evidence authenticates
nothing. Bounds are analyst assumptions, not measured clock error. Overlap is
not causality. Unicode heuristics have limited Latin/Greek/Cyrillic coverage;
no findings is not a safety verdict. Evidence is unredacted. This tool needs no
coin, payment, price or pool; no ZTO/IMD interaction is invented.

Gathering 08 provenance repair: the shipped Timeline Window engine is the
historical pre-filter snapshot, SHA-256
`fb937ce1d04728255a796320f1277c5a67043df0b738551536c021229e6a0385`.
Line 3 subsequently added source/message filters. The snapshot and behavior here
remain unchanged; this wrapper does not offer those newer filters. The provenance
check now verifies the retained historical hash instead of requiring equality to
a moving upstream source. The other nine snapshots still match their sources.
