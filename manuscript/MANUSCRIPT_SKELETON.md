# Manuscript Skeleton — Main PIV–CFD Paper

**Working story:** *Uncertainty-aware, spatially resolved PIV–CFD validation of free-surface gravitational vortex hydrodynamics*  
**Evidence rule:** final numerical claims require traceable source → script → output → figure/table → manuscript sentence.  
**Current gate:** M0 canonical source audit is blocked by the current transfer environment; M1 and CFD remain locked.

---

## 1. Title

### Working title
**Uncertainty-aware spatially resolved PIV–CFD validation of free-surface gravitational vortex hydrodynamics**

**Purpose:** define the paper as a measurement/validation study rather than a turbine-efficiency study.  
**Can be written now:** yes.  
**Blocked:** final title may be adjusted after the reproduced validation metrics and journal target are frozen.

---

## 2. Highlights

**Purpose:** state only contributions already defensible or explicitly methodological.  
**Central question:** what is novel about the validation workflow beyond a conventional qualitative PIV–CFD comparison?  
**Evidence needed:** reproducible provenance, PIV QA, subset robustness, uncertainty, numerical verification, registered validation.  
**Can be written now:** provisional highlights on evidence traceability, vector-class characterization, unresolved selector result and CFD firewall.  
**Blocked:** uncertainty/GCI/agreement percentages cannot enter the final highlights before reproduction.

---

## 3. Abstract

**Purpose:** concise quantitative synthesis of objective, methods, primary results and implications.  
**Evidence needed:** M0/M1, final experimental subset, uncertainty reproduction, CFD verification, common-coordinate validation.  
**Figures/tables:** none.  
**Can be written now:** structure only.  
**Blocked:** `[RESULT PENDING — M0]`, `[RESULT PENDING — M1 STATIONARITY]`, `[RESULT PENDING — UNCERTAINTY REPRODUCTION]`, `[RESULT PENDING — CFD GCI]`, `[RESULT PENDING — COMMON-COORDINATE VALIDATION]`.

---

## 4. Keywords

Provisional: gravitational water vortex; particle image velocimetry; CFD validation; measurement uncertainty; spatial registration; free-surface flow; grid convergence.

---

# 5. Introduction

## 5.1 Free-surface gravitational vortices as spatially heterogeneous flows

**Purpose:** motivate why a local velocity-field description is necessary.  
**Scientific question:** why are integral performance indicators or surface-profile validation insufficient to characterize the vortex hydrodynamics?  
**Evidence/literature:** primary free-surface/intake-vortex studies using velocity-field measurements; current gravitational-vortex literature.  
**Figures/tables:** none.  
**Writable now:** yes, using verified primary literature and avoiding performance-centric framing.

## 5.2 CFD use and the need for local experimental validation

**Purpose:** distinguish simulation from validation and motivate common-coordinate field comparison.  
**Scientific question:** what experimental evidence is needed to assess a CFD prediction of a free-surface vortex?  
**Evidence/literature:** recent gravitational-vortex CFD study validated mainly with surface profiles; V&V literature.  
**Writable now:** yes.  
**Blocked:** no claims about final CFD accuracy.

## 5.3 PIV capability, vector validity and optical/metrological limitations

**Purpose:** establish PIV as a suitable non-intrusive field method while making its uncertainty and air–water-interface limitations explicit.  
**Scientific question:** which parts of the measured field are direct observations, interpolated estimates or unavailable because of masking/optics?  
**Evidence/literature:** Adrian; Scarano; Westerweel & Scarano; Sciacchitano et al.; hydraulic air-core PIV literature.  
**Writable now:** yes.

## 5.4 Gap, objective and contribution

**Purpose:** state the paper's exact novelty.  
**Scientific question:** can gravitational free-surface vortex CFD be assessed with a traceable PIV workflow that explicitly separates measurement uncertainty, subset robustness and numerical discretization effects?  
**Writable now:** yes as an objective/contribution statement.  
**Blocked:** final quantitative novelty claims await reproduced results.

---

# 6. Experimental and Numerical Methodology

## 6.1 Evidence architecture and reproducibility gates

**Purpose:** formalize source identity, provenance and analysis order.  
**Scientific question:** how is circular validation prevented?  
**Evidence needed:** M0 implementation, manifests, Git commit identity, CFD firewall.  
**Figures/tables:** Figure 2; Supplementary provenance manifest.  
**Writable now:** yes, with M0 status explicitly reported as pending rather than passed.

## 6.2 Hydraulic and optical test section

**Purpose:** describe only hardware/geometry/operating conditions with traceable evidence.  
**Evidence needed:** final prototype-to-CAD identity, run-specific flow condition, camera/lens/laser evidence, acquisition geometry.  
**Figures/tables:** Figure 1; Table 1 experimental configuration.  
**Writable now:** camera model and manufacturer capability can be stated in scoped form; actual encoded video resolution and final operating flow rate remain blocked.  
**Blockers:** `[BLOCKER — CANONICAL VIDEO METADATA]`, `[BLOCKER — OPERATING CONDITION]`, `[BLOCKER — PROTOTYPE/CAD IDENTITY]`.

## 6.3 PIV acquisition, calibration and historical export provenance

**Purpose:** define frame-pair mapping and physical conversion without silently importing disputed processing settings.  
**Scientific question:** what parts of the historical PIV data chain are directly recoverable from the exported data?  
**Evidence needed:** canonical source M0; 250/250 ASCII freeze; calibration reconstruction.  
**Figures/tables:** Figure 2; Table 1.  
**Writable now:** historical pair span, audited xy/uv conversion, derived Δt with explicit scope.  
**Blockers:** full 250-file cryptographic freeze; independent calibration reconstruction; canonical timing verification.

## 6.4 PIV vector domain and data classes

**Purpose:** distinguish type-0/masked, type-1/direct and type-2/interpolated vectors.  
**Scientific question:** how much of the spatial domain is directly measured at each instant, and how stable is the support mask?  
**Evidence needed:** raw PIVlab Vector type columns; 250/250 freeze for population-wide maps.  
**Figures/tables:** Figure 3; Figure 4.  
**Writable now:** 13-file byte-audited results and retrospective 250-field aggregate, each with explicit evidence scope.

## 6.5 PIV interrogation and vector validation

**Purpose:** report the actual historical processing chain only after settings are reconciled.  
**Scientific question:** which interrogation-window, overlap, deformation and filtering settings generated the archived vector fields?  
**Evidence needed:** authoritative PIVlab session/settings or raw-image reproduction matching the export grid.  
**Figures/tables:** Figure 3; Supplementary settings table.  
**Current state:** `[BLOCKER — PIV SETTINGS]` because first-pass evidence is 32 vs 36 vs 64 px and the documented 18 px/50% overlap does not reproduce the observed ~18 px vector-grid pitch.

## 6.6 Temporal robustness and experimental subset selection

**Purpose:** establish a subset-selection rule without using CFD.  
**Scientific question:** does a more complex temporal selector outperform simple uniform sampling robustly enough to freeze a publication subset?  
**Evidence needed:** retrospective tournament now; canonical M1 stationarity and prospective robustness later.  
**Figures/tables:** Figure 5; Table 2.  
**Writable now:** retrospective tournament design and unresolved decision.  
**Blocked:** final publication selector.

## 6.7 Sample-size convergence

**Purpose:** establish the minimum number of fields required for stable spatial statistics.  
**Scientific question:** when do velocity-field statistics and vector-quality maps converge within a predeclared tolerance?  
**Evidence needed:** canonical admissible population and repeated subsampling.  
**Figures/tables:** Figure 5.  
**Current state:** `[RESULT PENDING — SAMPLE-SIZE CONVERGENCE]`.

## 6.8 Measurement uncertainty

**Purpose:** quantify metrological quality independently of CFD.  
**Scientific question:** what uncertainty is associated with the PIV velocity field and how does it vary spatially and by vector class?  
**Evidence needed:** reproduced uncertainty budget, coverage factor, calibration/timing/displacement contributions, treatment of interpolation and registration.  
**Figures/tables:** Figure 6; Table 3.  
**Current state:** `[RESULT PENDING — UNCERTAINTY REPRODUCTION]`.

## 6.9 CFD model and numerical verification

**Purpose:** describe numerical model and establish discretization quality before validation.  
**Scientific question:** is the CFD solution sufficiently grid-converged and internally consistent for comparison with measurements?  
**Evidence needed:** final CFD case files, mesh hierarchy, convergence, mass balance, turbulence/multiphase settings, reproduced Richardson/GCI calculation.  
**Figures/tables:** Figure 7; Table 4; GCI supplementary plot.  
**Current state:** CFD remains intentionally locked. `[RESULT PENDING — CFD GCI]`.

## 6.10 Common-coordinate registration and validation metrics

**Purpose:** define the transformation, interpolation, mask and discrepancy metrics before viewing validation results.  
**Scientific question:** where do PIV and CFD agree/disagree after registration, and are discrepancies resolvable relative to measurement capability?  
**Evidence needed:** frozen PIV subset, verified CFD, registration transform, sensitivity analysis, uncertainty map.  
**Figures/tables:** Figures 7–10.  
**Current state:** `[RESULT PENDING — COMMON-COORDINATE VALIDATION]`.

---

# 7. Results

## 7.1 Experimental evidence and provenance

**Observation → quantitative result → interpretation:** exact canonical object metadata and downstream historical pair provenance are available, but complete canonical byte audit is not yet closed. Report M0 as blocked, not failed.  
**Figures/tables:** Figure 2; Table 1.  
**Writable now:** yes.

## 7.2 PIV measurement-domain characterization

**Observation:** archived exports share a fixed coordinate domain while direct/interpolated composition varies.  
**Quantitative result:** for the 13 byte-audited exports, 70×55 = 3850 nodes, 2658 masked/type-0, 1192 finite active vectors, direct fraction 49.92–62.08%, nominal exported pitch ≈18 px.  
**Interpretation:** spatial support is fixed in the sampled exports but instantaneous direct measurement coverage is not; interpolation sensitivity is therefore mandatory.  
**Figures/tables:** Figures 3–4; Table 1.  
**Writable now:** yes, scoped to audited exports.

## 7.3 Temporal robustness and subset-selection analysis

**Observation:** different defensible decision rules prefer different selectors.  
**Quantitative result:** 660 evaluations/60 scenarios, no algorithm errors, vote split 3/2/1 and consensus 0.60 < 0.80; publication selector remains null.  
**Interpretation:** complexity has not demonstrated robust superiority; no winner is forced.  
**Figures/tables:** Figure 5; Table 2.  
**Writable now:** yes as retrospective evidence.

## 7.4 Sample-size convergence

`[RESULT PENDING — SAMPLE-SIZE CONVERGENCE]`

Required result: convergence curves for median velocity, vector support, vortex-center position and selected profile metrics with repeated-subset uncertainty.

## 7.5 Experimental vortex hydrodynamics

`[RESULT PENDING — EXPERIMENTAL HYDRODYNAMICS]`

Required result: median vector/magnitude field; vortex center; radial/tangential profiles; vorticity/circulation only if stable and physically interpretable from the frozen data.

## 7.6 Measurement uncertainty

`[RESULT PENDING — UNCERTAINTY REPRODUCTION]`

Historical thesis values may be retained in the blocker ledger but are not final Results claims.

## 7.7 CFD numerical verification

`[RESULT PENDING — CFD GCI]`

No CFD-derived metric may influence Sections 7.1–7.6.

## 7.8 Common-coordinate PIV–CFD validation

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

Required result: registered discrepancy field, RMSE, MAE, explicitly defined normalized metric, registration sensitivity and only then any retained relative-error acceptance fractions.

## 7.9 Spatial localization of discrepancy and uncertainty

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

Required result: map disagreement relative to local measurement capability and identify optical/hydrodynamic regions associated with elevated discrepancy without assigning causality beyond the evidence.

---

# 8. Discussion

## 8.1 Experimental credibility before numerical comparison
Interpret consequences of provenance, stationarity and vector-class evidence.

## 8.2 Direct versus interpolated PIV information
Discuss why a nominal field-validity statistic cannot be assumed equivalent to direct-vector coverage; retain the historical VDP >95% claim as a definition/reproduction blocker until reconstructed.

## 8.3 What the unresolved selector result means
Discuss methodological uncertainty and why a null selector decision is preferable to data-driven overfitting.

## 8.4 Numerical verification versus experimental validation
Keep GCI/discretization evidence separate from PIV–CFD comparison.

## 8.5 Spatial disagreement, optical limitations and vortex physics
After validation is reproduced, relate discrepancy localization to free-surface reflections, air-core proximity, velocity gradients, registration and uncertainty with appropriate sensitivity evidence.

---

# 9. Limitations

Writable now. Must include canonical M0, stationarity, PIV settings, full ASCII freeze, operating-condition traceability, uncertainty reproduction, CFD verification and registration as active limitations without implying they have been solved.

---

# 10. Conclusions

**Current state:** do not finalize.  
**Required evidence:** final experimental subset, uncertainty, CFD verification and common-coordinate validation.

---

# 11. Data and Code Availability

**Can be prepared now:** repository/branch and planned frozen evidence packages.  
**Blocked:** permanent archival DOI and final data package identity.

# 12. CRediT Authorship

Pending author list and contribution confirmation.

# 13. Funding

Pending verified funding statement.

# 14. Conflict of Interest

Pending author confirmation.

# 15. References

Build incrementally from verified primary literature only. Current core set: Adrian (1991); Scarano (2002); Westerweel & Scarano (2005); Sciacchitano et al. (2013, 2015); Keller et al. (2014); Menter (1994); Celik et al. (2008); Nayab et al. (2026). Add further gravitational-vortex and VOF sources only when they support text that is actually retained.

# 16. Supplementary Material

Planned contents: canonical M0 manifest; 250-ASCII manifest; PIV settings reconciliation; stationarity tests; convergence tests; uncertainty budget; GCI calculation; registration sensitivity; additional selector robustness; reproducibility environment and hashes.
