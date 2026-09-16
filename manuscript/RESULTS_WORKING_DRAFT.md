# Results — Working Draft

> **Rule for this file:** each retained subsection follows observation → quantitative result → physical/methodological interpretation. Historical thesis values that have not been independently reproduced are not promoted to final Results claims.

## 7.1 Experimental evidence and provenance

### Observation

The experimental evidence chain is presently asymmetric: the historical downstream PIVlab population is accessible and partially auditable at byte level, whereas the complete canonical MP4 cannot be downloaded through the current ChatGPT Drive connector because its provider-reported size exceeds the connector transfer ceiling. This prevents a complete canonical SHA-256, `ffprobe` audit and strict sequential decode in the current runtime.

### Quantitative result

The exact canonical acquisition object is `vid_2025-08-29_19-28-15.mp4`, Drive ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U`, with provider-reported size 714,939,306 bytes. The M0 implementation is configured to bind this exact object to provider metadata, compute a complete-file SHA-256, persist container metadata, decode to end-of-file and explicitly test historical source labels 4250–4500. The current M0 state is `BLOCKED_EXTERNAL_CANONICAL_EXECUTION_REQUIRED`; it is not a dataset-failure result.

For the downstream PIV evidence, the Drive folder exposes the historical filename sequence `PIVlab_0001.txt` through `PIVlab_0250.txt`. The first recovered export identifies source images 4250/4251 and the last identifies 4499/4500, consistent with 250 consecutive PIV pairs derived from 251 source images. Thirteen complete exports distributed across this interval have been retrieved, parsed from raw bytes and SHA-256 hashed. Every audited checkpoint follows the exact pair rule \(A=4249+i\), \(B=4250+i\), where \(i\) is the PIVlab export index.

### Interpretation

The historical PIVlab data are sufficiently traceable to support scoped forensic statements about the archived measurement domain and to exercise downstream robustness analyses. They do not, however, substitute for verification of the canonical acquisition. Accordingly, no canonical stationarity claim, final publication subset or CFD validation is opened from the downstream files alone. `[RESULT PENDING — M0]`

---

## 7.2 PIV measurement-domain characterization

### Observation

The audited PIVlab fields share the same coordinate support and static masked region, but the composition of direct and interpolated active vectors changes between fields. The archived coordinate lattice also provides an independent constraint on the geometry of the PIV output grid.

### Quantitative result

Each of the 13 complete raw exports contains 3,850 rows on a 70 × 55 coordinate lattice. In every audited field, 2,658 locations are type-0/masked and 1,192 locations contain finite velocity vectors. The coordinate-grid SHA-256 is identical for all 13 audited exports, and the type-0 mask is also invariant within the sample. The stored spatial and velocity conversion factors are respectively 0.00019061 m px⁻¹ and 0.20386 (m s⁻¹)/(px frame⁻¹) in all audited files.

Among the 1,192 active vectors, the direct/type-1 fraction varies from approximately 49.92% to 62.08% across the audited sample. Thus, even when the spatial support remains fixed, the proportion of vectors retained as direct PIVlab observations is not temporally constant. The median spacing of the complete unique-coordinate lattices is 0.00343104452 m, equivalent to 18.00033849 px using the stored spatial conversion.

### Interpretation

The archived fields should not be treated as spatially homogeneous measurements merely because they share an identical output mask. A fixed active domain can contain a changing mixture of direct and interpolated information. This distinction is important for median fields, profiles and any later PIV–CFD validation because interpolation can alter both local variance and spatial smoothness. The final analysis will therefore include direct-observation probability and direct-only versus all-active-vector sensitivity after the complete 250-file freeze.

The approximately 18 px exported lattice pitch also exposes an unresolved processing inconsistency. A nominal final 18 px interrogation window with 50% overlap would imply a 9 px vector step, not the observed ~18 px archived lattice. Together with conflicting documentary first-pass values of 32, 36 and 64 px, this prevents the manuscript from assigning a historical interrogation configuration by assumption. `[BLOCKER — PIV SETTINGS]`

A related metrological issue concerns the earlier `VDP >95%` statement. The current direct/type-1 fraction is not definitionally equivalent to Valid Data Percentage unless the historical VDP denominator and vector classes are reconstructed. The two quantities are therefore kept separate. `[BLOCKER — DEFINITION AND REPRODUCTION REQUIRED]`

---

## 7.3 Temporal robustness and subset-selection analysis

### Observation

The retrospective selector study does not produce a stable single-method preference across the predeclared decision lenses. Instead, different defensible criteria select different approaches from the same recovered historical PIVlab population.

### Quantitative result

The retrospective tournament used 250 historical PIVlab fields and an active spatial domain of 1,192 cells. Eleven algorithms were evaluated at subset sizes \(N=25, 50, 100, 150\), using five spatial folds and three random seeds. The run comprised 60 scenarios and 660 algorithm evaluations with zero algorithm errors, and the associated real-data software test suite passed 9/9 checks. The mean direct-vector fraction across the loaded 250-field population was 0.5542080537.

Under the predefined decision framework, the uniform baseline received three decision-lens votes, temporal-quality stratified sampling received two and the spatial lower-tail method received one. The resulting consensus fraction was 0.60, below the required 0.80 threshold. The recorded outcome was `UNRESOLVED_DECISION_RULE_DISAGREEMENT`, with `publication_selector = null` and no numerical candidate frozen.

### Interpretation

The result does not justify describing a more complex temporal selector as superior to uniform sampling, nor does it justify declaring the uniform baseline the publication winner. Rather, selector preference depends materially on how representativeness is defined. Preserving the unresolved outcome avoids converting methodological uncertainty into an unsupported claim. Uniform sampling remains a competitive baseline, but the final publication subset must be selected only after canonical source verification, stationarity and sample-size convergence have been established.

This result is explicitly retrospective. It demonstrates that the selection machinery can be exercised on real downstream PIV data and that rule disagreement is substantive; it does not establish representativeness outside the historical 4250–4500 interval and cannot replace `[RESULT PENDING — M1 STATIONARITY]`.

---

## 7.4 Sample-size convergence

`[RESULT PENDING — SAMPLE-SIZE CONVERGENCE]`

Required evidence before writing this subsection as Results:

- canonical admissible interval after M1;
- repeated subsampling over candidate \(N\);
- convergence of median velocity statistics;
- convergence of direct-vector support/probability;
- stability of vortex-center position and any retained profile metrics;
- predeclared tolerance and robustness criterion.

The existing 11-field regression is retained only as a software/data sanity check and is not used to define publication convergence.

---

## 7.5 Experimental vortex hydrodynamics

`[RESULT PENDING — EXPERIMENTAL HYDRODYNAMICS]`

The final subsection will report only quantities reproducible from the frozen experimental subset. Priority outputs are the median vector/velocity field, vortex-center location, radial and tangential velocity profiles and, if sensitivity tests support them, vorticity and circulation. These quantities must be evaluated with the final mask, vector-class treatment and spatial calibration.

---

## 7.6 Measurement uncertainty

`[RESULT PENDING — UNCERTAINTY REPRODUCTION]`

The final subsection will report the reproduced uncertainty budget and spatial uncertainty distribution. The historically documented expanded uncertainty near ±0.0408 m/s and median relative expanded uncertainty near 12.63% remain reproduction targets only and are deliberately excluded from the current quantitative Results narrative.

---

## 7.7 CFD numerical verification

`[RESULT PENDING — CFD GCI]`

CFD remains locked until the experimental subset is frozen. The historically documented fine-grid GCI near 4.05% is not treated as a reproduced result. The final subsection will report the authoritative mesh hierarchy, refinement relation, monitored quantity, apparent order, extrapolated value, GCI and other numerical-convergence evidence from executable data.

---

## 7.8 Common-coordinate PIV–CFD validation

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

Historical analysis documents spatial acceptance fractions near 60.41% for a 10% relative-error threshold and 78.67% for a 15% threshold. These values remain deliberately excluded as final Results claims until the PIV/CFD arrays, registration transform, mask, interpolation procedure, error denominator and area calculation are independently reproduced. The final subsection will include registered local discrepancy together with RMSE, MAE and a carefully defined normalized metric before any threshold-area statistic is interpreted.

---

## 7.9 Spatial localization of discrepancy and uncertainty

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

The final analysis will determine whether regions of elevated PIV–CFD discrepancy co-locate with large experimental uncertainty, intermittent direct-vector coverage, strong velocity gradients, the air-core boundary or registration-sensitive regions. Association will be reported descriptively unless a causal test is available. The purpose of this subsection is to identify where the validation is measurement-limited, numerically discrepant or jointly uncertain rather than compress the comparison into a single global percentage.
