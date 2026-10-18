# Unicode Text Window

Inspect source code, plain text or logs for the existing Unicode Lantern's
covered patterns without printing active terminal controls. This fills the
plain-text gap in Unicode Window, which reviews JSON. It does not execute the
input or decode language/JSON escape syntax.

From the repository root, with Python 3.10+ and no installation or network:

```sh
python3 -B line-2/tools/unicode-text-window/unicode_text_window.py --demo --max-findings 2
```

The synthetic example reports **7 findings, 2 retained, 5 omitted**. Its first
two findings expose a Cyrillic letter in an identifier and cite both original
spellings of a lookalike collision. Each retained span has an exact original
byte range, SHA-256, line/byte-column, up to 64 preview bytes and 16 context
bytes per side. Long spans keep their full digest and explicit omitted-byte
count. Output is printable ASCII and LF only. Byte notation doubles backslashes
and represents other nonprintable/non-ASCII bytes as `\xHH`; evidence objects
have one additional JSON quoting layer. Do not interpret escaped evidence as
terminal instructions.

To inspect a real explicit file (the command only reads it):

```sh
python3 -B line-2/tools/unicode-text-window/unicode_text_window.py --file line-1/tools/paired-verdict/paired_verdict.py
```

Tried this actual source: **8,674 bytes, zero covered patterns**, SHA-256
`ed7f2e286ceb08a9dd88de1b77b4a8858a7856eda5dc9e47d32d0bc3d19ebbe1`.
This is an offline source review, not a safety endorsement or real incident.

Exit status: 0 for no findings or the demo, 1 for findings in a selected file,
2 for invalid input/error (empty stdout). Inputs must resolve within the current
working directory, be regular UTF-8 files and fit 2 MiB. The limit is 1–1000
retained findings, default 100; the complete input is still scanned for counts.
Rendering is capped at 4 MiB. No recursive discovery, environment access,
network access, modification, signing or sending occurs.

Run the focused regression tests:

```sh
python3 -B -m unittest discover -s line-2/tools/unicode-text-window -p 'test_*.py' -v
```

All 14 tests passed, covering original multibyte/CRLF coordinates, collision
references, inert terminal output, literal escapes, omission counts, long
identifiers, input/output bounds, CLI status and two-folder portable use.
The 12 unchanged Unicode Lantern tests also passed.

For portable use, copy this folder and sibling `unicode-lantern/` together
under the same parent. Both contain ordinary standard-library Python source.
The other five line tools are not dependencies of this viewer.

Limitations: the inherited detector uses a small Latin/Greek/Cyrillic heuristic,
not full Unicode confusables or a language parser. Comments and strings count;
legitimate multilingual text may be flagged. Literal `\u202e` is not a direction
control in raw-text mode; use Unicode Window/JSON Citations for decoded JSON.
No cross-file collisions, automatic rewriting, redaction, authentication or
replay bundle is supplied. Digests bind bytes, not their author. Reading-view
excerpts can split a multibyte character; coordinates and hashes still refer to
the complete original span. The printable-ASCII contract is for terminal output,
not HTML/Markdown escaping. The Python Unicode database version is reported.
