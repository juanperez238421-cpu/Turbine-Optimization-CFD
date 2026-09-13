# ASTRA selector methodology — publication design specification

## 1. Selection unit and firewall
ASTRA selects adjacent image pairs, \(P_i=(I_i,I_{i+1})\). CFD information is prohibited from provenance, stationarity, quality gating, subset construction, ablation and winner selection. CFD is opened only after an experimental `selection_freeze.json` is scientifically authorized.

## 2. Stages
A. Canonical provenance and SHA-256.  
B. Raw-image QA with illumination normalization.  
C. Stationary-population detection.  
D. Common PIV-native quality gate.  
E. Multi-family selector tournament.  
F. Held-out spatial validation.  
G. Sample-size, seed, temporal and parameter sensitivity.  
H. Multi-rule decision uncertainty.  
I. Independent publication evidence gate.

## 3. Spatial PIV information
For pair i and spatial cell j, let q_ij in [0,1] denote a PIV correlation-reliability proxy. For selected subset S, C_j(S)=sum_i q_ij.

Log coverage uses F_log(S)=sum_j log(1+C_j). Saturated coverage uses F_sat(S)=sum_j min(C_j,C*). A lower-tail criterion maximizes performance of the least-observed cells rather than only the spatial mean. These objectives are designed to avoid repeatedly sampling the same optically easy region.

## 4. Representative selectors
Kennard–Stone provides maximin space filling using actual observations. Kernel herding targets the stationary population kernel mean. Greedy D-optimal selection targets state-space information volume. Facility location maximizes representative similarity coverage. Cluster-medoid and k-center approaches are retained as transparent comparators.

## 5. Hybrid selectors
QCRC/MMR variants use rank-based maximin compromises. A candidate must be simultaneously non-poor in measurement quality, state representativeness, spatial coverage and temporal novelty; no criterion can be compensated by an arbitrarily large fixed weight assigned to another.

## 6. Common quality gate
Correlation-derived quality is primarily an eligibility constraint. Robust low-tail PCE/PPR thresholds reject catastrophic candidates before algorithms compete. The final tournament therefore asks which eligible subset is spatially informative, representative and temporally nonredundant rather than rewarding a single scalar quality score twice.

## 7. Held-out spatial validation
Spatial reliability cells are partitioned into folds. Spatial selectors optimize only training cells. All methods are evaluated on held-out cells using log coverage, 10th-percentile coverage and coverage inequality. This separates construction from evaluation and reduces overfitting to the specific interrogation locations used by the selector.

## 8. Population/temporal evaluation
Selected-state distributions are compared with the complete stationary population using scale-normalized Wasserstein discrepancies. Temporal span, adjacent-pair fraction and inter-pair gaps quantify redundancy. Temporal-block jackknife analysis is required before publication freeze.

## 9. Decision uncertainty
No single weighted score defines the winner. Five independent lenses are used: Pareto-front frequency, median scenario rank, 90th-percentile regret, scenario-win frequency and Monte-Carlo unknown-weight win probability. Default numerical consensus requirement is 80%. Below that threshold ASTRA returns an unresolved decision.

## 10. Full-field retrospective validation
When PIVlab fields are available, direct type-1 measurements are analyzed separately from type-2 interpolated vectors. Direct-only convergence and spatial observation counts can validate the selector retrospectively. These downstream measurement fields must not silently leak into prospective raw-image selection.

## 11. Publication gate
A numerical leader is not a manuscript selector. Freeze additionally requires canonical-video identity, complete scan, stationarity, explicit ROI, resolved calibration/dt/PIVlab settings, PIV-native evidence, spatial holdout validation, sample-size convergence, temporal-dependence analysis, temporal jackknife, ablation stability and winner stability. CFD must still be locked.
