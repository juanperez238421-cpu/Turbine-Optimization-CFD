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

Open `notebooks/ASTRA_PIV_SUPERSTUDY_Q1.ipynb` in Google Colab. It mounts Drive, finds `vid_2025-08-29_19-28-15.mp4`, scans the real recording, detects the stationary pool, computes coarse correlation quality, executes the selector portfolio and writes the evidence-gated decision. Use an audited ROI for publication mode. Full-frame mode is exploratory only.

## Local tests

```bash
pip install -e .
python -m unittest discover -s tests -v
```

Tests using private experimental data skip automatically in public CI. The canonical raw data are intentionally not stored in GitHub Actions.

## Interpretation

The selector is a reproducibility/measurement-quality component supporting the broader paper: **Uncertainty-aware, spatially resolved PIV–CFD validation of free-surface gravitational vortex hydrodynamics.** It must not be optimized against CFD agreement.
