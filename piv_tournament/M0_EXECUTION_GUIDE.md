# M0 canonical-source execution guide

This gate is deliberately limited to **source identity and decode integrity**. It must finish with `M0_STATUS.json: status = PASS` before M1 stationarity, temporal selection, CFD access, or final validation is allowed.

## One Colab notebook

Open `notebooks/ASTRA_M0_CANONICAL_AUDIT.ipynb` in Google Colab and run all cells.

### Canonical M0 step

The M0 cell:

1. authenticates to the user's Google Drive;
2. queries the exact canonical file ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U`;
3. requires basename `vid_2025-08-29_19-28-15.mp4`, size `714939306` bytes, and provider `md5Checksum`;
4. downloads the **exact Drive object by file ID** into the Colab runtime using the Drive API (no whole-Drive `rglob`/name search);
5. verifies downloaded byte size and MD5 against provider metadata;
6. computes SHA-256 over the complete local file;
7. persists raw `ffprobe` metadata;
8. performs a strict FFmpeg sequential decode to EOF with decoder errors fatal;
9. explicitly decodes historical labels 4250–4500 under both zero-based and one-based FFmpeg mappings instead of silently assuming an indexing convention;
10. writes JSON, CSV, Markdown, and an execution manifest containing Git HEAD and hashes of critical scripts;
11. executes no stationarity, selector, CFD, or validation code.

M0 outputs are written to:

`MyDrive/ASTRA_M0_EVIDENCE/<UTC timestamp>/`

Required outputs include `drive_provider_metadata.json`, `ffprobe.json`, `M0_STATUS.json`, `M0_STATUS.csv`, `M0_REPORT.md`, and `execution_manifest.json`.

A non-zero exit code or `status != PASS` leaves M0 closed.

## Independent 250-ASCII freeze in the same notebook

The second evidence cell is independent of M0 and may execute even if M0 remains closed. It:

1. lists the exact Drive folder `1UF77fkaEm2NZ2CJCbfADYeAHaoj3PnZO`;
2. requires exactly one `PIVlab_0001.txt` through `PIVlab_0250.txt`;
3. downloads each object by its exact Drive file ID;
4. requires provider size and MD5 and matches both to downloaded bytes;
5. delegates parsing and forensic calculations to the existing `freeze_pivlab_ascii.py`;
6. computes a SHA-256 for every export;
7. verifies source-pair continuity 4250/4251 through 4499/4500, calibration constancy, coordinate-grid constancy, vector-type counts, finite-vector counts, and missing/duplicate indices.

Outputs are written to:

`MyDrive/ASTRA_ASCII_250_EVIDENCE/<UTC timestamp>/`

A PASS here is **retrospective downstream PIVlab provenance evidence only**. It does not authorize a publication selector, does not prove stationarity, and does not unlock CFD.

## One local M0 command

```bash
python piv_tournament/scripts/run_m0_canonical.py \
  --video /absolute/path/vid_2025-08-29_19-28-15.mp4 \
  --provider-metadata drive_provider_metadata.json \
  --out M0_EVIDENCE
```

Do not hand-edit a provider checksum. If local bytes cannot be bound to the exact Drive object by provider ID, name, size and checksum, the audit fails closed.

## One local 250-ASCII command

```bash
python piv_tournament/scripts/freeze_pivlab_ascii.py \
  --ascii-dir /path/to/PIVlab_exports \
  --out ASCII_250_EVIDENCE
```

PASS requires all 250 exact filenames, no missing/duplicate index, continuous source pairs, constant conversion metadata and coordinate grid, and SHA-256 for every file.
