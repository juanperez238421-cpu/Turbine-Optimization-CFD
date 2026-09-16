# M0 canonical-source execution guide

This gate is deliberately limited to **source identity and decode integrity**. It must finish with `M0_STATUS.json: status = PASS` before M1 stationarity, temporal selection, CFD access, or final validation is allowed.

## One Colab route

Open `notebooks/ASTRA_M0_CANONICAL_AUDIT.ipynb` in Google Colab and run all cells. The notebook:

1. mounts the authenticated Google Drive;
2. queries Drive API metadata for file ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U`;
3. requires basename `vid_2025-08-29_19-28-15.mp4` and size `714939306` bytes;
4. requires a provider `md5Checksum` and matches it to the mounted bytes, so a same-name duplicate cannot silently pass;
5. computes SHA-256 over the complete local file;
6. persists raw `ffprobe` metadata;
7. performs a strict FFmpeg sequential decode to EOF with decoder errors fatal;
8. explicitly decodes the historical PIV labels 4250–4500 under both zero-based and one-based FFmpeg mappings rather than silently assuming an indexing convention;
9. writes JSON, CSV, Markdown and an execution manifest containing Git HEAD and hashes of critical scripts;
10. executes no stationarity, selector, CFD, or validation code.

Outputs are written to `MyDrive/ASTRA_M0_EVIDENCE/<UTC timestamp>/`: `drive_provider_metadata.json`, `ffprobe.json`, `M0_STATUS.json`, `M0_STATUS.csv`, `M0_REPORT.md`, and `execution_manifest.json`.

A non-zero exit code or `status != PASS` leaves M0 closed.

## One local command

```bash
python piv_tournament/scripts/run_m0_canonical.py \
  --video /absolute/path/vid_2025-08-29_19-28-15.mp4 \
  --provider-metadata drive_provider_metadata.json \
  --out M0_EVIDENCE
```

Do not hand-edit a provider checksum. If the mounted file cannot be bound to the exact Drive object by provider ID, name, size and checksum, the audit fails closed.

## Optional 250-ASCII freeze

```bash
python piv_tournament/scripts/freeze_pivlab_ascii.py \
  --ascii-dir /path/to/PIVlab_exports \
  --out ASCII_250_EVIDENCE
```

PASS requires exactly one `PIVlab_0001.txt` through `PIVlab_0250.txt`, continuous source pairs 4250/4251 through 4499/4500, constant conversion metadata, a constant coordinate grid, and a SHA-256 for every file.
