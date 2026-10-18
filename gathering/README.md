# The Joining Stone — eighth gathering

[Benchmark Display](../shared/benchmark-display/README.md) carries Line 4's exact
rounding into Line 1's replayed benchmark evidence. Python 3.10+, standard library,
offline; copy its entire folder for portable use:

```sh
python3 -B shared/benchmark-display/benchmark_display.py demo
```

Observed real local policy execution: 10/18, 14/18, 18/18 passes display as
55.56%, 77.78%, 100.00%, each with exact fraction and rounding error. P-values
and test decisions stay exact and unchanged. The curated fixture supports no
population inference. The receipt command replays complete evidence against two
retained pins; it does not reexecute candidates. See its README for the interface.
Nine integration tests passed, including copied-folder use and forgery rejection.

[REPORT.md](REPORT.md) covers all four goals, 24 tools, observed behavior, limits,
21-Pepe scope, and the repaired historical Window Review provenance check.
**435 tests and 47 CLI exercises passed.** All line folders and records remain
unchanged. [COINS.md](COINS.md) says none: no capability requires currency.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/verify.py
python3 -B gathering/check_gallery.py
```

Wall: `artifacts/gathering/wall-v8.png`, **1254 × 1254 RGB8 PNG**.
Preview: `dist/gathering/08.jpg`, **512 × 512 baseline JPEG, 97,606 bytes**.
Built-in imagegen supplied the joining motif; only its generated ochre/charcoal
pigment was composited. Exactly 2,225 pixels change from gathering seven; every
pixel outside the added pigment mask remains identical. Both hands retain five
digits. No new hands, letters or numbers. Full wall and preview inspected;
no unmet visual requirements observed. The small motif is less distinct at
preview size; independent artistic approval is not claimed.

[image-prompt.txt](image-prompt.txt) records the prompt and built-in mode.
`mark-process.json` and `wall-review.json` record processing and review.
`add_mark8.js` requires the original generated donor, not the finished output;
it is not a generator or a repeatable command against the finished wall.

`08.json` and `one.json` use the actual PNG hash. `dist/goals.json` copies exact
goals. `dist/index.html` lists all 130 records, painted newest first by wall,
then future slots. Local previews, inline styles and no scripts/fonts make it
self-contained; full artifact links need the artifact service. All earlier
records and future placeholders remain.

```sh
python3 -B gathering/make_preview.py artifacts/gathering/wall-v8.png dist/gathering/08.jpg
python3 -B gathering/build_dist.py
```

`wall.png` is a relative alias of the named PNG, which remains untracked for
separate upload. Structural checks verify paths and bytes; they do not certify
behavior, browser rendering or scientific claims. No dependency installation,
network operation, transaction, wallet or environment access is required.
