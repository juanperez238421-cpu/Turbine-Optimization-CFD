# 250-PIVlab ASCII forensic progress — 2026-09-15

**Evidence class:** downstream historical PIVlab exports; retrospective evidence only.

## New evidence obtained in this session

The accessible Drive folder exposes the complete expected filename namespace `PIVlab_0001.txt` through `PIVlab_0250.txt`. Five strategically spaced files were reopened from Drive and their raw headers checked:

| Export | Source A/B | xy (m/px) | uv ((m/s)/(px/frame)) | Drive size (bytes) |
|---:|---|---:|---:|---:|
| 0001 | 4250 / 4251 | 0.00019061 | 0.20386 | 487196 |
| 0002 | 4251 / 4252 | 0.00019061 | 0.20386 | 487914 |
| 0125 | 4374 / 4375 | 0.00019061 | 0.20386 | 486200 |
| 0249 | 4498 / 4499 | 0.00019061 | 0.20386 | 487884 |
| 0250 | 4499 / 4500 | 0.00019061 | 0.20386 | 486525 |

These samples support the expected pair rule `A = 4249 + export_index`, `B = 4250 + export_index` at the beginning, midpoint and end, and show unchanged calibration metadata in the sampled files. This is **sampled confirmation**, not yet a byte-level freeze of all 250 exports. The committed `ASCII_250_MANIFEST.csv` is therefore intentionally a sampled evidence manifest; the complete 250-row byte/hash manifest is generated only by `scripts/freeze_pivlab_ascii.py` when all files are mounted.

## Exact exported coordinate pitch

Raw coordinate values give, in both axes:

- `dx = dy = 0.0034310519 m`;
- using `0.00019061 m/px`, `dx = dy = 18.00037721 px`;
- an 18 px interrogation window with 50% overlap would nominally give a 9 px step = `0.00171549 m`;
- an 18 px step corresponds to `0.00343098 m`, essentially the exported spacing within coordinate rounding.

Therefore the exported vector-grid pitch is quantitatively consistent with approximately **18 px**, not the **9 px** step expected from a straightforward 18 px final pass with 50% overlap.

## Interrogation-window forensic verdict

**`INSUFFICIENT_EVIDENCE`**

Reason: the PIVlab ASCII headers expose source-frame and calibration metadata but not interrogation settings. Accessible evidence is mutually inconsistent: a reconstruction script uses a 32 px first pass, thesis-oriented prose reports 36 px, and `GVT_Vortex_Analysis_Main.m` comments state 64 px. The exact historical PIVlab `Sett.mat`/session/settings file was not located in the targeted Drive search. The 18 px exported grid pitch proves a processing-configuration inconsistency but does not identify the historical first-pass window or whether later decimation/resampling affected the exported nodes.

## What remains to close the ASCII freeze

Run `scripts/freeze_pivlab_ascii.py` on the complete mounted folder. It will calculate SHA-256, row count, grid dimensions, pitch, vector-type counts, finite-vector count and continuity/calibration/grid flags for every file and will fail on missing/duplicate indices, pair discontinuities, conversion changes or coordinate-grid changes.
