# ASTRA PIV Selector SuperStudy v2

ASTRA v2 is an evidence-gated scientific model-selection framework for temporal PIV subsampling. It does **not** assume a preferred tournament score or force a winner. Its question is: which subset of adjacent image pairs preserves the stationary hydrodynamic population while maximizing defensible PIV information and spatial measurement coverage?

## Selector portfolio

**Control/baseline:** historical legacy control, uniform, stratified random, IID random, best contiguous window.  
**Quality:** top PIV quality, quality within temporal strata.  
**Representative design:** cluster medoids, farthest-point/k-center, Kennard–Stone, kernel herding, greedy D-optimal, facility location.  
**Spatial information:** log coverage, saturated coverage, lower-tail/CVaR-like coverage.  
**Hybrid:** Pareto+temporal, QCRC maximin, quality/state/temporal MMR, quality/facility/temporal maximin.

## Scientific safeguards

1. The unit is an adjacent PIV image pair, not an isolated frame.
2. Canonical acquisition provenance is checked before ranking.
3. Stationarity is determined independently of CFD.
4. A common robust PIV-quality gate is applied before algorithms compete.
5. Spatial selectors are trained on only part of the reliability map and evaluated on held-out spatial cells.
6. The tournament uses Pareto fronts, minimax regret, repeated seeds, sample-size variation and sensitivity/ablation scenarios.
7. A Monte-Carlo weight-space analysis is diagnostic only; it cannot alone define the winner.
8. Five independent decision lenses must reach strong consensus. Returning no winner is valid.
9. A separate publication gate blocks selection freeze until provenance, calibration, settings, convergence and robustness evidence are complete.
10. CFD remains sealed until the experimental selection is frozen.

## Sample-size study

Default canonical study evaluates N = 25, 50, 75, 100, 150, 200 and 250 pairs when the stationary population supports them. The historical 250-pair PIVlab selection remains an explicit control.

## Sensitivity matrix

The OAT design tests 32/36/48 px coarse interrogation windows, PCE/PPR normalization ranges, PCE-only/PPR-only/geometric-mean reliability, 3/4/5-MAD quality gates, spatial saturation targets and lower-tail fractions. OAT is used instead of an opaque combinatorial explosion so the source of method sensitivity is interpretable.

## Online canonical run

Start with `../ASTRA_STATE.json` and `../ASTRA_PROGRESS.md`. The current dependency is M0 source evidence. Do not restart the retrospective selector study.

The canonical Drive file was located on 2026-09-13 with ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U` and size **714,939,306 bytes**. The connector could read metadata but rejected the raw download because its limit is **268,435,456 bytes**. No canonical checksum, full decode, stationarity or selector result was obtained in that session.

In a runtime where the original is already accessible through authenticated Drive mounting, run the integrated source audit from this package directory:

```bash
python -m astra_piv source-audit "/content/drive/MyDrive/Maestría/PIV/vid_2025-08-29_19-28-15.mp4" \
  --config configs/publication_q1.yaml \
  --output-dir "/content/drive/MyDrive/ASTRA_M0_CANONICAL"
```

This always attempts a strict FFmpeg decode and records the observed checksum. A checksum observed on the candidate alone does **not** certify source identity. Bind an independently verified digest to its source evidence using `provenance.canonical_sha256` and `canonical_reference`; do not automatically copy the candidate digest into its own expected value. The supplied config intentionally leaves these unresolved. Byte size and basename are supporting metadata only.

Add `--scan-features` for full image/pair-feature coverage, or `--scan-features --max-frames 32` for a partial diagnostic. The independent decode remains a full pass. A stopped feature scan cannot satisfy `full_raw_video_scanned`. Every strict pipeline checks both decoder counts and the source hash before proceeding to stationarity. A source audit runs no selector and creates no selection freeze.

Container fps is playback metadata. Acquisition delta-t requires a positive `provenance.acquisition_dt_s` and a separate `acquisition_dt_reference`; the historical calibration ratio remains a working estimate until resolved.

After the M0 dependency is satisfied, `notebooks/ASTRA_PIV_SUPERSTUDY_Q1.ipynb` is the existing Colab entrypoint for the superstudy. Use an audited ROI for publication mode. Full-frame mode is exploratory only. The publication runner now stops on incomplete or contradictory decode evidence, and unresolved acquisition timing keeps the publication gate closed.

## Local tests

```bash
pip install -e .
# Install FFmpeg through the runtime's package manager if it is absent.
python -m unittest discover -s tests -v
```

Tests using private experimental data skip automatically in public CI. The canonical raw data are intentionally not stored in GitHub Actions.

The M0 real-video diagnostic is persisted in `results/m0_noncanonical_20260913/`. It uses the attached Teams recording solely to test decoding and partial-scan evidence handling. It cannot support PIV selector rankings. To validate these outputs against that actual recording:

```bash
ASTRA_REAL_VIDEO="/absolute/path/to/01-MicrosoftTeams-video.mp4" \
ASTRA_REAL_SOURCE_AUDIT_DIR="results/m0_noncanonical_20260913" \
python -m unittest discover -s tests -p 'test_astra_source_real.py' -v
```

## Interpretation

The selector is a reproducibility/measurement-quality component supporting the broader paper: **Uncertainty-aware, spatially resolved PIV–CFD validation of free-surface gravitational vortex hydrodynamics.** It must not be optimized against CFD agreement.
