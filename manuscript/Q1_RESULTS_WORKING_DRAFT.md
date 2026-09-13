# Working Results Draft — Q1 PIV–CFD Paper

**Working story:** *Uncertainty-aware, spatially resolved PIV–CFD validation of free-surface gravitational vortex hydrodynamics*  
**Status:** active working draft; not submission-ready  
**Rule:** only evidence that has been reproduced or explicitly classified is written as a result. Blocked claims remain blocked.

---

## 7. Results

### 7.1 Experimental vortex hydrodynamics — evidence gate not yet closed

The final description of the experimental vortex field must be generated from the audited PIV population after canonical-source verification, stationarity analysis, final ROI definition, calibration reconciliation, and PIV processing settings are frozen. At present, historical PIVlab exports provide useful downstream evidence, but they cannot substitute for verification of the complete raw-video population.

The manuscript should ultimately report the spatial organization of the measured velocity field using identical physical coordinates across all experimental and numerical comparisons. The principal hydrodynamic observations should be expressed in terms of measured velocity components, spatial gradients, vortex-core location, and, where the raw measurements support them, radial/tangential velocity profiles, vorticity, circulation, and uncertainty bands. No such additional quantity should be promoted to a main result until it is reproducible from the canonical data and the final coordinate system.

**Current manuscript action:** retain this subsection as gated. Do not insert the historical thesis figures as final quantitative evidence.

### 7.2 Statistical robustness and experimental subset selection

A retrospective real-data tournament was executed on 250 historical PIVlab fields corresponding to the legacy consecutive-pair window spanning source frames 4250–4500. The active PIV grid contained 1,192 cells, and the mean fraction of direct PIVlab vectors across the recovered fields was 0.5542. Eleven subset-selection algorithms were evaluated at sample sizes of 25, 50, 100, and 150 fields using five spatial folds and three random seeds. In total, 660 algorithm evaluations were completed across 60 scenarios with no algorithm failures; the associated real-data test suite passed 9/9 tests.

The tournament did not identify a sufficiently robust winner. Under the predefined multi-rule decision framework, the uniform baseline received three votes, temporal-quality stratified sampling received two, and the spatial lower-tail method received one. The resulting consensus fraction was 0.60, below the required threshold of 0.80. Consequently, ASTRA returned `UNRESOLVED_DECISION_RULE_DISAGREEMENT`, with neither a numerical candidate nor a publication selector frozen.

This unresolved outcome is itself informative. First, the evidence does not support presenting a complex selector as intrinsically superior to simple uniform sampling. Second, the disagreement between independent decision lenses indicates that selector ranking is sensitive to the criterion used to define representativeness and spatial information. Third, forcing a single winner at this stage would convert methodological uncertainty into an unsupported publication claim. The scientifically conservative interpretation is therefore that the recovered historical population is sufficient to test the tournament machinery, but insufficient to authorize the final experimental subset.

The retrospective run has important limits. It is based on downstream PIVlab exports rather than an independently verified canonical raw-video population; it evaluates direct-vector validity coverage rather than measured velocity accuracy; the interleaved spatial holdouts originate from one experiment and may remain spatially correlated; raw-image feature representativeness is unavailable in this dataset; and no selection outside the historical 250-pair window is evaluated. These restrictions prevent the present tournament from replacing the canonical stationarity, sensitivity, and convergence analyses required for publication freeze.

A smaller 11-field retrospective regression provides a complementary convergence sanity check rather than a publication result. Relative to the full 11-field direct-only median reference, the measured-cell fraction increased from 0.8070 at N = 3 to 0.9144 at N = 9, while vector RMSE decreased from 0.0690 m/s to 0.0301 m/s. Because N = 11 defines that local reference ensemble, the zero error at N = 11 is tautological and must not be interpreted as independent validation. This diagnostic supports the expected reduction of sampling error with increasing field count, but the small ensemble is too sparse to define the final convergence criterion.

**Current result statement for the paper:** the recovered experimental evidence does not yet justify a privileged temporal-selection algorithm; uniform sampling remains a credible baseline and the selector decision remains intentionally unresolved until canonical-video stationarity and full-population robustness are demonstrated.

### 7.3 CFD prediction — intentionally locked

The CFD results remain outside the experimental selector-development loop. Numerical fields, CFD-derived vortex-core positions, spatial error metrics, and agreement percentages must not influence frame eligibility, subset construction, or selector ranking. This firewall is required to prevent circular validation in which the experimental sample is optimized to resemble the numerical prediction that it is later used to validate.

The final CFD subsection will report the numerical free-surface solution only after the experimental selection is frozen. It should include the final turbulence model, multiphase/free-surface treatment, temporal discretization, convergence evidence, mass balance, mesh hierarchy, and independently reproduced grid-verification result. Historical reported values, including the fine-grid GCI near 4.05%, remain provisional until regenerated from frozen mesh data and the documented verification procedure.

### 7.4 Spatial PIV–CFD validation — publication result blocked pending M11

The core paper contribution is intended to be an uncertainty-aware, spatially resolved validation rather than a qualitative side-by-side comparison. The final analysis will therefore place PIV and CFD data on a common coordinate system and mask, use identical physical units and velocity limits, and compute local discrepancy together with global validation metrics.

Historical results report approximately 60.41% of the comparison domain within a 10% relative-error criterion and approximately 78.67% within a 15% criterion. These values are not yet accepted as final manuscript results because the complete registration, masking, interpolation, denominator treatment, and metric reproduction have not been independently rerun from authoritative arrays. Until that reproduction is complete, wording such as “good agreement” should be avoided.

The final subsection should report, at minimum, the registered spatial discrepancy field, the 10% and 15% acceptance regions if retained after methodological review, RMSE, MAE, an explicitly defined normalized error metric where meaningful, and sensitivity to alignment/registration. Any correlation coefficient must be interpreted carefully because strong spatial autocorrelation can inflate apparent agreement.

### 7.5 Measurement uncertainty

The final validation claims must be interpreted against the spatially varying experimental uncertainty. Historical analysis reports an expanded PIV velocity uncertainty of approximately ±0.0408 m/s and a median relative expanded uncertainty of approximately 12.63%. These values remain working targets for reproduction rather than submission-ready constants.

The final uncertainty subsection should distinguish calibration, timing, displacement estimation, image quality, vector validation/interpolation, spatial registration, and any other retained contributors. It should state the coverage factor and clearly separate uncertainty of directly measured vectors from uncertainty or epistemic limitations introduced by rejected/interpolated vectors. The uncertainty map should be evaluated together with the PIV–CFD discrepancy field so that local numerical differences are not interpreted independently of measurement capability.

---

## 8. Discussion — current argument map

The present evidence supports a conservative methodological argument rather than a performance claim. The main experimental lesson is that temporal subset selection is not yet demonstrably improved by a more elaborate algorithm: several defensible decision lenses disagree, and a uniform baseline remains competitive. For a Q1 paper, this is preferable to overfitting the sampling strategy because the primary contribution is the credibility of the PIV–CFD validation, not the promotion of a selector.

The discussion should ultimately connect four layers: (i) whether the experimental flow population is stationary enough to admit representative subsampling; (ii) whether the selected experimental subset preserves spatial PIV reliability and converged statistics; (iii) whether the CFD solution is independently verified; and (iv) whether observed PIV–CFD differences are small relative to both measurement uncertainty and the spatial variability of the vortex. The paper becomes substantially stronger when these four layers are kept logically separate.

A key negative result should be retained if it survives the canonical study: added algorithmic complexity is not automatically evidence of better experimental representation. If uniform or simple stratified sampling remains statistically equivalent after the complete prospective tournament, the manuscript should state that explicitly rather than force novelty through algorithm selection.

---

## 9. Current limitations to keep explicit

1. Canonical video bytes are not yet accessible in the current runtime; the file digest and complete sequential decode have therefore not been verified.
2. Raw-video stationarity has not yet been established for the canonical population.
3. The final ROI, camera-resolution evidence, calibration value, first-pass interrogation-window size, complete PIVlab settings, and filtering thresholds still require reconciliation.
4. The full uncertainty budget, sample-size convergence, GCI reproduction, coordinate registration, and final PIV–CFD agreement metrics remain open.
5. The 250-field tournament is retrospective and restricted to the historical window spanning frames 4250–4500.
6. CFD remains intentionally locked until the experimental evidence gate is passed and the subset is frozen.

---

## Immediate evidence-to-manuscript dependencies

- **M0:** obtain complete canonical bytes, compute independently bound SHA-256, verify full decode and frames 4250–4500.
- **M1:** establish canonical experimental stationarity and admissible analysis interval.
- **M2–M10:** complete PIV quality characterization, selector robustness, convergence, uncertainty, and publication freeze.
- **M11:** open CFD, reproduce numerical verification, register fields, and compute final spatial validation metrics.

Until these gates pass, Section 7.2 is the most developed defensible Results subsection; Sections 7.1 and 7.3–7.5 remain structured but deliberately gated against unsupported numerical claims.
