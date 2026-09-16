# PIVlab 250-ASCII forensic progress — raw-byte upgrade 2026-09-15

**Evidence class:** retrospective downstream PIVlab exports. This report does **not** promote the historical subset to a publication selector and does not use CFD.

## Executed raw-byte evidence in this session

The Drive connector was able to retrieve complete raw bytes for a stratified 13-file sample spanning the beginning, interior, and end of the historical population:

`0001, 0002, 0025, 0050, 0075, 0100, 0125, 0150, 0175, 0200, 0225, 0249, 0250`.

Each downloaded file was parsed from the raw bytes and SHA-256 hashed locally. The Drive folder listing exposes the full expected filename namespace `PIVlab_0001.txt` through `PIVlab_0250.txt`, but the repository manifest below remains explicitly a **13/250 raw-byte sample**, not the final 250-file cryptographic freeze.

## New forensic results

Across all 13 complete raw files:

- pair provenance follows the expected rule `A = 4249 + export_index`, `B = 4250 + export_index`;
- `xy = 0.00019061 m/px` and `uv = 0.20386 (m/s)/(px/frame)` are unchanged;
- every file contains exactly **3,850 rows**;
- every file contains the same **70 × 55** coordinate lattice;
- the coordinate-grid SHA-256 is identical in all 13 files: `c04e34792866ca52c9c333a5e2412d746a75e8dd327b20dad6ac2f60f2fd1c99`;
- the median exported pitch is `0.00343104452 m`, corresponding to `18.00033849 px` using the stored calibration;
- every file has exactly **2,658 type-0/masked locations** and **1,192 finite active vectors**;
- the type-0 mask is byte-identical across the 13 files and is the exact complement of the finite-vector mask;
- type-1 versus type-2 composition changes with time: the direct/type-1 fraction among active vectors ranges from **49.92% to 62.08%** in this sample.

The fixed 1,192-cell active domain is therefore directly corroborated from complete raw ASCII files distributed across the historical 250-field window. The changing type-1/type-2 composition also gives a concrete empirical reason to retain the planned direct-only versus all-vector sensitivity test.

## Raw-byte sample manifest

| Export | A/B | Rows | Grid | Type 0 | Type 1 | Type 2 | Finite | Direct/active | SHA-256 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0001 | 4250/4251 | 3850 | 70×55 | 2658 | 605 | 587 | 1192 | 50.76% | `6caea3f791c717fe8ec02112284ec555be210819d80f55d75305ef174d36aab3` |
| 0002 | 4251/4252 | 3850 | 70×55 | 2658 | 632 | 560 | 1192 | 53.02% | `6cb6c7436c2313a7abfbde2720777515670578f05e9f610b3f61112924ccb41e` |
| 0025 | 4274/4275 | 3850 | 70×55 | 2658 | 642 | 550 | 1192 | 53.86% | `5869eb72dce6de0a3a14da42e4d27616d44230c8fad00ce728607b0dfc023d0e` |
| 0050 | 4299/4300 | 3850 | 70×55 | 2658 | 668 | 524 | 1192 | 56.04% | `3c8ec4dc0a4571f739c7f2840e57b071ac11cf6a264bd19f12aa15904c514e23` |
| 0075 | 4324/4325 | 3850 | 70×55 | 2658 | 722 | 470 | 1192 | 60.57% | `4d2c876c6a1da6c32253b1a4dadb0f5a5153043bf9655c18b5f6725bd8fc4635` |
| 0100 | 4349/4350 | 3850 | 70×55 | 2658 | 677 | 515 | 1192 | 56.80% | `c72291d7b414265b0ead9c1e3fb0346615e43d3ca46061880cccbb7c3f2c4a9c` |
| 0125 | 4374/4375 | 3850 | 70×55 | 2658 | 740 | 452 | 1192 | 62.08% | `4d307c13dcee4384f0d63d46ce6141304cfe02941e932b801050fa47fd4a4829` |
| 0150 | 4399/4400 | 3850 | 70×55 | 2658 | 628 | 564 | 1192 | 52.68% | `f6cc7861b3aadaf142b155d99a1623ea95ab1862d4741d8cec13c1e1ab9b75d7` |
| 0175 | 4424/4425 | 3850 | 70×55 | 2658 | 619 | 573 | 1192 | 51.93% | `3893b312eb98465644d1f7a5a4263d28c8fd8d957d73fba251408375d3f7dafd` |
| 0200 | 4449/4450 | 3850 | 70×55 | 2658 | 646 | 546 | 1192 | 54.19% | `2b6e696dc6106a26f8a34d8d9b0d85fae691ef28d92cf03358f3d3e17f040b75` |
| 0225 | 4474/4475 | 3850 | 70×55 | 2658 | 613 | 579 | 1192 | 51.43% | `0b69e4f7f5e4d6878421b43534399ad7c0fb3b8e024cb8faade836e420bd2699` |
| 0249 | 4498/4499 | 3850 | 70×55 | 2658 | 632 | 560 | 1192 | 53.02% | `56c04ac458dc8e205c506b7a8b55bc094ad944c1c83a8e9f2fcf5932a171927c` |
| 0250 | 4499/4500 | 3850 | 70×55 | 2658 | 595 | 597 | 1192 | 49.92% | `5b6903179d1defcec36533fa685e758f748983a8fbec3180790fe1928d21fe6c` |

## Interrogation-window implication

The measured exported node pitch is approximately 18 px, not the 9 px step expected from a simple final 18 px interrogation window with 50% overlap. This strengthens the processing-configuration contradiction but does not identify the historical first-pass window. The current verdict remains:

**`INSUFFICIENT_EVIDENCE`**

The ASCII header exposes source-frame and calibration metadata, not the PIVlab interrogation/session settings. Conflicting documentary evidence remains 32 px, 36 px, and 64 px for the first pass.

## Full freeze status

**Not yet complete inside this ChatGPT runtime.** Thirteen complete files are byte-level frozen here. The complete Drive namespace is visible and each file is individually downloadable, so a new authenticated Colab runner now automates exact Drive-ID download, provider size/MD5 verification, and delegation to `freeze_pivlab_ascii.py` for all 250 files.

A full PASS requires all 250 exact filenames, no missing/duplicate index, continuous source pairs 4250/4251 through 4499/4500, constant calibration/grid/mask evidence, and SHA-256 for every file.
