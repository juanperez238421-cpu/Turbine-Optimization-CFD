# New results obtained on 2026-09-15 — execution update

Only results newly obtained or materially strengthened in the current execution pass are listed here.

## 1. Thirteen complete raw PIVlab exports were downloaded and cryptographically frozen

Complete raw bytes were retrieved from Drive for the stratified indices:

`0001, 0002, 0025, 0050, 0075, 0100, 0125, 0150, 0175, 0200, 0225, 0249, 0250`.

Every file was parsed locally and assigned a complete-file SHA-256. This is stronger than the earlier header-only continuity check.

Across all 13 raw files:

- pair provenance exactly matches `A = 4249 + index`, `B = 4250 + index`;
- calibration metadata are invariant: `xy = 0.00019061 m/px`, `uv = 0.20386 (m/s)/(px/frame)`;
- each file contains exactly **3,850 rows**;
- the grid is exactly **70 × 55** in every file;
- the coordinate-grid hash is identical in all 13 files: `c04e34792866ca52c9c333a5e2412d746a75e8dd327b20dad6ac2f60f2fd1c99`;
- every file has **2,658 type-0/masked locations** and **1,192 finite active vectors**;
- the type-0 mask itself is identical across all 13 files and is the exact complement of the finite-vector mask;
- type-1/direct fraction among the active 1,192 vectors varies from **49.92% to 62.08%**.

This directly corroborates the 1,192-cell active domain used by the retrospective tournament from raw PIVlab files distributed throughout the historical window. It also provides real evidence that direct-versus-interpolated composition changes over time, which makes the planned direct-only versus all-vector sensitivity test scientifically relevant.

This is still a **13/250 raw-byte sample**, not the final full cryptographic freeze.

## 2. The exported-grid pitch was re-estimated from complete raw coordinate lattices

Using all unique coordinates in each complete raw export, the median lattice spacing is:

`0.00343104452 m`

which corresponds to:

`18.00033849 px`

under the stored `0.00019061 m/px` calibration.

This is a more robust estimate than a single adjacent-coordinate difference. The conclusion is unchanged: the exported grid is nominally an **18 px** lattice, whereas a simple 18 px final window at 50% overlap would nominally imply a **9 px** step.

Historical interrogation settings therefore remain **INSUFFICIENT_EVIDENCE**.

## 3. The connector can enumerate the complete historical export namespace

The actual Drive parent folder exposes `PIVlab_0001.txt` through `PIVlab_0250.txt`, and the tested objects are individually raw-downloadable. Therefore the remaining 250-file freeze is no longer a data-access design problem; it is an execution step.

A new Colab downloader now lists the folder by exact parent ID, requires the complete 0001–0250 namespace, downloads every exact Drive file ID, matches provider byte size and MD5, then delegates to the existing `freeze_pivlab_ascii.py` for SHA-256, grid, vector and source-pair checks.

## 4. The canonical M0 Colab route no longer scans the mounted Drive tree

The prior runner recursively searched `MyDrive`/`Shareddrives` for same-name/size candidates before comparing MD5. That can be slow and unnecessarily ambiguous on a large Drive.

The updated runner instead:

`exact Drive file ID -> provider metadata -> exact Drive API media download -> provider size/MD5 match -> complete SHA-256 -> ffprobe -> strict EOF decode -> historical 4250–4500 range audit`.

This preserves the existing fail-closed M0 core while removing whole-Drive pathname discovery from the critical identity chain.

## 5. Software QA added for the 250-file Drive namespace gate

A new pure-core validator requires exactly one `PIVlab_0001.txt` through `PIVlab_0250.txt`, positive provider sizes, Drive file IDs, and valid provider MD5 checksums. Four new unit tests cover:

- exact 250-object namespace;
- missing + duplicate indices;
- absent provider MD5;
- unrelated folder files without masking expected gaps.

The new module/scripts compile locally and the four new unit tests pass. GitHub Actions must still pass after the integrated commit before this software change is considered remotely frozen.
