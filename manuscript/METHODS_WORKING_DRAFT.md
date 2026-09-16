# Experimental and Numerical Methodology — Working Draft

> **Status:** only methodology supported by the present evidence gate is written as operative text. Unresolved historical PIV settings, canonical-video properties, uncertainty and CFD verification remain explicit placeholders.

## 6.1 Evidence architecture and analysis order

The study was organized as an evidence-gated validation workflow. Raw experimental and numerical data were assigned the highest evidential priority, followed by executable analysis outputs, frozen forensic manifests, the final thesis, verified primary literature and explicitly labelled inference. This ordering was adopted to prevent downstream prose or reconstructed scripts from silently overriding the acquisition record. Every numerical quantity intended for final publication must be traceable from a source file through an executable derivation to an output, figure or table and the corresponding manuscript claim.

The experimental and numerical branches were deliberately separated during subset development. CFD information was excluded from frame eligibility, stationarity assessment, experimental subset construction, selector ranking and publication-subset freeze. Numerical results will be opened only after the experimental population, processing configuration, subset and measurement uncertainty have been frozen. In the final paper, **numerical verification** denotes assessment of numerical discretization and solution quality; **experimental validation** denotes comparison of CFD predictions with measurements; and **measurement uncertainty** denotes the metrological quality of the PIV result. These terms are not used interchangeably.

The canonical acquisition object is `vid_2025-08-29_19-28-15.mp4`, identified in Google Drive by file ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U` and a provider-reported size of 714,939,306 bytes. The canonical M0 audit is designed to bind the exact provider object to local bytes, compute a complete-file SHA-256 digest, persist `ffprobe` metadata, decode sequentially to end-of-file, count decoder errors and explicitly test the historical source-frame range 4250–4500. At the current evidence gate this execution remains `[RESULT PENDING — M0]`; the available connector cannot transfer the complete source object. Consequently, canonical video dimensions, declared frame rate, declared frame count and complete decode integrity are not reported as verified acquisition properties in this draft.

## 6.2 Hydraulic and optical test section

The imaging system is documented as a Chronos 1.4 high-speed camera. Manufacturer documentation establishes a full-frame capability of 1280 × 1024 px at approximately 1069 frames s⁻¹; this specification is reported here only as a camera capability, not as evidence of the encoded format of the canonical acquisition. The latter remains dependent on canonical `ffprobe` output. A project analysis script also contains a 1630 × 1345 array size, but direct inspection shows that this size is introduced through bilinear `imresize` of a PIV field. It is therefore treated as a post-processing analysis-grid dimension in that workflow rather than as native camera resolution.

The current analysis scripts and thesis-oriented material consistently identify a cylindrical basin diameter of 183.184 mm, but final prototype-to-CAD revision identity has not yet been frozen. The final test-section description will therefore be inserted only after the physical prototype, CAD revision and run-specific operating condition are tied to the canonical acquisition. In particular, the flow rate is not restated from earlier thesis material at this gate because a run-specific operating-condition record has not yet been re-established.

`[BLOCKER — PROTOTYPE/CAD IDENTITY]`  
`[BLOCKER — OPERATING CONDITION]`  
`[BLOCKER — CANONICAL VIDEO METADATA]`

## 6.3 Historical PIV export provenance and physical conversion

The recovered historical PIVlab population comprises 250 consecutive image-pair exports associated with source labels spanning 4250–4500. Export 1 identifies images 4250 and 4251, whereas export 250 identifies images 4499 and 4500; thus the 250 PIV pairs correspond to 251 source images. The complete Drive folder exposes the expected filename namespace `PIVlab_0001.txt` through `PIVlab_0250.txt`. A complete cryptographic freeze of all 250 files remains pending, but 13 exports distributed across the beginning, interior and end of the population have been retrieved as complete raw bytes and independently hashed.

Across these 13 complete exports, the PIVlab headers store an invariant spatial conversion of 0.00019061 m px⁻¹ and an invariant velocity conversion of 0.20386 (m s⁻¹)/(px frame⁻¹). Their ratio implies an inter-frame interval

\[
\Delta t = \frac{0.00019061\ \mathrm{m\,px^{-1}}}{0.20386\ \mathrm{(m\,s^{-1})/(px\,frame^{-1})}}
= 9.350044148\times10^{-4}\ \mathrm{s},
\]

or approximately 0.935004 ms. The corresponding reciprocal is approximately 1069.5137 s⁻¹. These derived quantities describe the timing encoded by the stored PIV conversion factors; they are not used as a substitute for the canonical container-declared frame rate, which remains `[RESULT PENDING — M0]`. The final spatial calibration will also require independent reconstruction from the calibration reference before the stored conversion is promoted to the final calibration constant.

## 6.4 PIV measurement domain and vector classes

The raw PIVlab exports contain Cartesian coordinates, velocity components and a `Vector type` classification. In the 13 byte-audited exports, each file contains 3,850 vector-grid rows arranged on 70 unique x coordinates and 55 unique y coordinates. Exactly 2,658 locations are classified as type 0 and have non-finite velocity components, while 1,192 locations contain finite velocity vectors. The type-0 mask is identical in the audited exports and is the exact complement of the finite-vector support. The coordinate lattice is likewise invariant across this sample, with a common coordinate-grid SHA-256.

Within the 1,192 active locations, PIVlab type 1 and type 2 vectors are retained as separate data classes. Type 1 is treated as the direct PIVlab vector class and type 2 as the interpolated class for the purpose of forensic QA; neither class is silently collapsed into a single concept of measurement validity. The fraction of type-1 vectors among active locations varies from approximately 49.92% to 62.08% across the 13 audited fields even though the coordinate grid and active-domain mask remain fixed. This observation motivates two publication-level diagnostics after the full 250-file freeze: the temporal evolution of direct-vector fraction and the spatial direct-observation probability, \(P(\mathrm{type\ 1}\mid x,y)\). A direct-only versus all-active-vector sensitivity analysis is also required before derived hydrodynamic quantities are finalized.

This classification must not be equated with the historical `VDP >95%` statement contained in an earlier HardwareX-style manuscript. That document defines VDP as a Valid Data Percentage associated with cross-correlation success, while the current forensic quantity is specifically the fraction of PIVlab type-1 vectors among non-masked active locations. Until the historical VDP denominator, vector classes and calculation are reconstructed, the relationship between the two metrics is `[BLOCKER — DEFINITION AND REPRODUCTION REQUIRED]`.

## 6.5 Exported grid geometry and unresolved PIV processing settings

The median spacing obtained from the complete unique-coordinate lattices of the 13 audited exports is 0.00343104452 m. Dividing by the stored spatial conversion gives a nominal exported node pitch of 18.00033849 px. This value is a property of the archived output coordinates and does not, by itself, identify the interrogation-window size or overlap used by PIVlab.

The historical processing configuration is currently contradictory. A reconstruction script specifies a first interrogation pass of 32 px and a second pass of 18 px; the final thesis describes 36 × 36 px followed by 18 × 18 px with 50% overlap; and a separate analysis script contains a comment indicating 64 px to 18 px. Moreover, a simple 18 px final interrogation window with 50% overlap would nominally generate a 9 px vector step, whereas the archived output lattice is approximately 18 px. No authoritative saved PIVlab session has yet been recovered to explain whether later decimation, resampling or a different processing configuration produced the stored coordinates.

Accordingly, this manuscript does not select among 32, 36 or 64 px, and it does not infer zero overlap from the archived pitch. The final interrogation and vector-validation description remains `[BLOCKER — PIV SETTINGS]`. The exact historical outlier-filtering thresholds are likewise not promoted from reconstruction scripts or prose until the saved processing state or an output-reproducing reconstruction is obtained.

## 6.6 Retrospective temporal subset-selection study

A retrospective real-data tournament was executed on the 250 recovered PIVlab fields without access to CFD information. The active spatial domain contained 1,192 cells. Eleven selection algorithms were evaluated at subset sizes \(N=25, 50, 100, 150\), using five spatial folds and three random seeds. This produced 60 scenarios and 660 algorithm evaluations with zero algorithm errors; the associated real-data software checks passed 9/9 tests. The mean direct-vector fraction in the downstream 250-field tournament population was 0.5542080537.

The decision framework was intentionally allowed to return no selector. Independent decision lenses produced three votes for the uniform baseline, two for temporal-quality stratified sampling and one for the spatial lower-tail method. The resulting consensus fraction of 0.60 was below the predeclared requirement of 0.80, yielding `UNRESOLVED_DECISION_RULE_DISAGREEMENT` and `publication_selector = null`. This outcome is retained as a methodological result rather than overridden by a secondary weighted score.

The retrospective study tests the behavior of the selection framework on recovered downstream PIV fields; it does not establish canonical-video stationarity or authorize the final publication subset. The next experimental stage is therefore `[RESULT PENDING — M1 STATIONARITY]`, followed by sample-size convergence and subset robustness on the admissible canonical interval.

## 6.7 Sample-size convergence

`[RESULT PENDING — SAMPLE-SIZE CONVERGENCE]`

The final analysis will evaluate convergence of spatial velocity statistics and selected PIV-QA metrics under repeated subsampling. Acceptance tolerances and the final publication sample size will be declared before CFD is opened.

## 6.8 Measurement uncertainty

`[RESULT PENDING — UNCERTAINTY REPRODUCTION]`

The final uncertainty analysis will propagate the retained calibration, timing and displacement-estimation contributions and will state the coverage factor explicitly. It will also distinguish uncertainty associated with directly measured vectors from the additional epistemic limitation introduced by rejected/interpolated data and by spatial registration. Historical thesis values are retained in the evidence ledger only and are not used as final constants at this stage.

## 6.9 CFD model and numerical verification

`[RESULT PENDING — CFD GCI]`

The CFD branch remains locked until the experimental subset and uncertainty treatment are frozen. When opened, numerical verification will be reported separately from validation, following an explicit mesh hierarchy and Richardson/GCI procedure consistent with established CFD verification practice. The turbulence and multiphase/free-surface formulations will be reported from the authoritative case files rather than from thesis prose alone.

## 6.10 Common-coordinate PIV–CFD validation

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

The final comparison will transform PIV and CFD fields to a common physical coordinate system and mask, document interpolation and registration, and quantify sensitivity to the registration transform. Local discrepancy maps will be accompanied by RMSE and MAE and, only if retained after methodological review, an explicitly defined normalized/relative error. Agreement thresholds will not be interpreted independently of the reproduced PIV uncertainty field.
