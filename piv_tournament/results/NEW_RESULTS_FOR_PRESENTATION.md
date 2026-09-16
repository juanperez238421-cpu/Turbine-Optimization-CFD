# New results obtained on 2026-09-15

Only results newly obtained or materially strengthened in this session are listed here.

## 1. M0 has a concrete one-command route around the ChatGPT transfer ceiling

A second raw-download attempt used Drive streaming/file-reference mode (`download_raw_file=true`, `include_base64=false`). The provider still rejected the 714,939,306-byte canonical MP4 because the connector ceiling is 268,435,456 bytes. Therefore the limitation is confirmed to be connector-side rather than a base64-only issue.

A dedicated M0-only implementation was prepared that binds mounted bytes to the exact Drive object using file ID, exact basename, exact byte size and provider MD5 before computing the complete-file SHA-256. It then persists `ffprobe`, performs strict decode-to-EOF, explicitly tests the historical 4250–4500 range, and records Git/script hashes. It cannot silently open M1.

## 2. Camera-resolution contradiction was materially reduced

The official Chronos 1.4 Rev5 datasheet states a 1280 × 1024 image sensor at 1069 FPS for full-frame operation. Separately, `GVT_Vortex_Analysis_Main.m` explicitly creates a **post-processing bilinear interpolation target** `imgW=1630`, `imgH=1345` and calls `imresize(...,[1345 1630],'bilinear')`.

Therefore **1630 × 1345 is demonstrably an analysis/resampling dimension in at least one project workflow and must not be called camera native resolution on that evidence**. The thesis statement calling 1630 × 1345 “native” conflicts with the manufacturer specification and the project script. The actual encoded resolution of the canonical MP4 remains open until M0 `ffprobe` executes.

## 3. Final-grid inconsistency was quantified exactly

The exported PIVlab coordinate spacing is `0.0034310519 m` in both axes. Dividing by the raw PIVlab calibration `0.00019061 m/px` yields `18.00037721 px` per exported grid step. A final 18 px window at 50% overlap should nominally produce a 9 px step (`0.00171549 m`), not ~18 px.

This turns the prior qualitative concern into a measured contradiction. It does **not** resolve the historical interrogation settings.

## 4. First-pass interrogation setting is now more clearly unresolved

Three project evidence paths conflict:

- reconstruction/figure script: 32 px first pass;
- thesis-oriented method text: 36 px first pass;
- `GVT_Vortex_Analysis_Main.m` comment: 64 px first pass.

No authoritative PIVlab session/`Sett.mat` was found in the targeted Drive search. Verdict: **INSUFFICIENT_EVIDENCE**, not 32 or 36.

## 5. Strategic raw-header continuity checks extended

In addition to the known endpoint files, raw Drive exports 0002, 0125 and 0249 were reopened. Their headers report 4251/4252, 4374/4375 and 4498/4499 respectively, with the same `xy=0.00019061 m/px` and `uv=0.20386 (m/s)/(px/frame)`. Beginning/middle/end sampled provenance is therefore internally consistent. Full 250-file byte/hash verification remains pending external mounted-Drive execution.
