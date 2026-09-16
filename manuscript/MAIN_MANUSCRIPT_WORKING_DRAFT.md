# Uncertainty-aware spatially resolved PIV–CFD validation of free-surface gravitational vortex hydrodynamics

**Working manuscript — evidence-gated, not submission-ready**  
**Current scientific gate:** M0 canonical-source audit pending; M1 and CFD locked.  
**Scope:** hydrodynamics, measurement credibility, numerical verification and spatial validation. Turbine-efficiency claims are outside the present paper unless new rotor-performance data are introduced.

---

## Highlights — provisional

- An evidence-gated workflow separates PIV measurement uncertainty, experimental subset selection, CFD numerical verification and experimental validation.
- Thirteen byte-audited PIVlab exports share a fixed 70 × 55 lattice and 1,192-cell active domain, while direct-vector coverage varies between fields.
- The archived vector-grid pitch is nominally 18 px, exposing an unresolved contradiction with the documented 18 px interrogation window at 50% overlap.
- A 250-field retrospective selector tournament returned an unresolved decision; no publication selector was forced.
- CFD is explicitly firewalled from experimental stationarity, subset construction and selector ranking until the experimental evidence is frozen.

> Final Highlights must be re-evaluated after M0/M1, uncertainty reproduction, CFD verification and common-coordinate validation.

---

## Abstract

`[NOT FINALIZED — EVIDENCE GATES OPEN]`

The final Abstract will be written only after the canonical experimental subset, measurement uncertainty, CFD numerical verification and common-coordinate PIV–CFD validation have been reproduced. Historical validation percentages, uncertainty values and GCI values are intentionally excluded at this stage.

---

## Keywords

Gravitational water vortex; particle image velocimetry; CFD validation; measurement uncertainty; spatial registration; free-surface flow; grid convergence.

---

# 1. Introduction

Free-surface vortices combine strong azimuthal motion, radial transport, an air–water interface and a spatially concentrated core, so their hydrodynamics cannot be represented adequately by a single bulk performance quantity. Experimental studies of hydraulic free-surface and intake vortices have shown that physically informative descriptors include radial and tangential velocity profiles, vortex-core position and radius, circulation, vorticity and free-surface shape. Particle image velocimetry (PIV) has enabled spatially resolved measurements of these quantities in hydraulic vortex flows, including two-component measurements around air-core vortices and stereoscopic measurements of three-dimensional free-surface-vortex structure [1–3]. These studies also show why the vortex core is a demanding measurement region: the strongest velocity gradients and the air–water interface occur in the same area in which optical access is most vulnerable to reflections, refraction, masking and loss of usable particle images [1]. For gravitational water-vortex systems, a local velocity-field description is therefore required if numerical models are to be assessed in terms of the underlying hydrodynamics rather than only integral or geometric responses.

Computational fluid dynamics (CFD) is widely used to examine gravitational-vortex flow structure because it provides access to velocity, vorticity, phase distribution and other quantities throughout the computational domain. However, numerical verification and experimental validation answer different questions. Grid-convergence or discretization analysis assesses the numerical sensitivity of the computed solution, whereas validation assesses its consistency with physical measurements. This distinction is particularly important for free-surface vortices, for which a numerical model may reproduce a bulk response or surface profile while local velocity errors remain spatially heterogeneous. A recent gravitational-water-vortex study used two-phase CFD to resolve internal flow structure and compared predicted free-surface profiles with experiments, reporting deviations within 20% [4]. Such validation is useful, but it does not provide a spatially resolved experimental test of the local velocity field. The remaining need is therefore not simply for more CFD, but for an experimentally traceable local comparison in which the measurement coordinates, numerical coordinates, masks, interpolation and discrepancy metrics are all explicitly controlled.

PIV is well suited to this purpose because it estimates particle-image displacement over a field of view and can resolve coherent spatial flow structure without inserting a probe into the vortex [5]. Modern PIV processing commonly uses multi-pass interrogation and image deformation to improve spatial resolution and reduce residual displacement errors [6], together with vector-validation procedures that identify local outliers [7]. These processing steps nevertheless create an important metrological distinction between vectors obtained directly from an image-correlation measurement and values that are rejected, masked or subsequently interpolated. That distinction matters in a free-surface vortex because optical quality is not spatially uniform. PIV uncertainty is likewise not a single generic property of the camera or algorithm; it depends on image quality, particle displacement, gradients, calibration, timing, processing and the local information available to the correlation analysis. A-posteriori PIV uncertainty methods and inter-method assessments have therefore emphasized local uncertainty estimation rather than unqualified claims of field accuracy [8,9]. For air-core hydraulic vortices specifically, PIV studies have documented the difficulty of resolving the complete velocity field close to the air–water interface because of optical reflections [1]. These considerations motivate a validation workflow in which vector provenance, spatial support and measurement uncertainty are treated as part of the result rather than as post-processing details.

The present study develops that workflow for a free-surface gravitational vortex. Its objective is to perform an uncertainty-aware, spatially resolved PIV–CFD validation in which experimental credibility is established before the numerical comparison is opened. The methodology is organized around four separable evidence layers: (i) canonical acquisition provenance and an auditable PIV measurement domain; (ii) temporal robustness, sample-size convergence and subset selection based only on experimental information; (iii) measurement-uncertainty quantification for the frozen PIV result; and (iv) independent CFD numerical verification followed by common-coordinate validation. A deliberate firewall prevents CFD results from influencing frame eligibility, stationarity assessment, subset construction or selector ranking. The current forensic reconstruction further distinguishes masked, direct and interpolated PIV vectors and tests whether the spatial support of the measurement remains invariant while direct-observation coverage changes in time. The intended contribution is therefore not a new turbine-efficiency correlation, but a reproducible validation architecture that localizes where agreement and disagreement occur, evaluates whether those differences are resolvable within measurement capability, and preserves unresolved or negative methodological results rather than converting them into a forced validation claim.

---

# 2. Experimental and Numerical Methodology

## 2.1 Evidence architecture and analysis order

The study was organized as an evidence-gated validation workflow. Raw experimental and numerical data were assigned the highest evidential priority, followed by executable analysis outputs, frozen forensic manifests, the final thesis, verified primary literature and explicitly labelled inference. This ordering prevents downstream prose or reconstructed scripts from silently overriding the acquisition record. Every numerical quantity intended for final publication must be traceable from a source file through an executable derivation to an output, figure or table and the corresponding manuscript claim.

The experimental and numerical branches were deliberately separated during subset development. CFD information was excluded from frame eligibility, stationarity assessment, experimental subset construction, selector ranking and publication-subset freeze. Numerical results will be opened only after the experimental population, processing configuration, subset and measurement uncertainty have been frozen. In this paper, **numerical verification** denotes assessment of numerical discretization and solution quality; **experimental validation** denotes comparison of CFD predictions with measurements; and **measurement uncertainty** denotes the metrological quality of the PIV result.

The canonical acquisition object is `vid_2025-08-29_19-28-15.mp4`, identified in Google Drive by file ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U` and a provider-reported size of 714,939,306 bytes. The canonical M0 audit is designed to bind the exact provider object to local bytes, compute a complete-file SHA-256 digest, persist `ffprobe` metadata, decode sequentially to end-of-file, count decoder errors and explicitly test the historical source-frame range 4250–4500. At the current evidence gate this execution remains `[RESULT PENDING — M0]`; the available connector cannot transfer the complete source object. Consequently, canonical video dimensions, declared frame rate, declared frame count and complete decode integrity are not reported as verified acquisition properties here.

## 2.2 Hydraulic and optical test section

The imaging system is documented as a Chronos 1.4 high-speed camera. Manufacturer documentation establishes a full-frame capability of 1280 × 1024 px at approximately 1069 frames s⁻¹; this specification is reported only as a camera capability, not as evidence of the encoded format of the canonical acquisition. The latter remains dependent on canonical `ffprobe` output. A project analysis script also contains a 1630 × 1345 array size, but direct inspection shows that this size is introduced through bilinear `imresize` of a PIV field. It is therefore treated as a post-processing analysis-grid dimension in that workflow rather than as native camera resolution.

The current analysis scripts and thesis-oriented material consistently identify a cylindrical basin diameter of 183.184 mm, but final prototype-to-CAD revision identity has not yet been frozen. The final test-section description will therefore be inserted only after the physical prototype, CAD revision and run-specific operating condition are tied to the canonical acquisition. In particular, the flow rate is not restated from earlier thesis material at this gate because a run-specific operating-condition record has not yet been re-established.

`[BLOCKER — PROTOTYPE/CAD IDENTITY]`  
`[BLOCKER — OPERATING CONDITION]`  
`[BLOCKER — CANONICAL VIDEO METADATA]`

## 2.3 Historical PIV export provenance and physical conversion

The recovered historical PIVlab population comprises 250 consecutive image-pair exports associated with source labels spanning 4250–4500. Export 1 identifies images 4250 and 4251, whereas export 250 identifies images 4499 and 4500; thus the 250 PIV pairs correspond to 251 source images. The complete Drive folder exposes the expected filename namespace `PIVlab_0001.txt` through `PIVlab_0250.txt`. A complete cryptographic freeze of all 250 files remains pending, but 13 exports distributed across the beginning, interior and end of the population have been retrieved as complete raw bytes and independently hashed.

Across these 13 complete exports, the PIVlab headers store an invariant spatial conversion of 0.00019061 m px⁻¹ and an invariant velocity conversion of 0.20386 (m s⁻¹)/(px frame⁻¹). Their ratio implies an inter-frame interval

\[
\Delta t = \frac{0.00019061\ \mathrm{m\,px^{-1}}}{0.20386\ \mathrm{(m\,s^{-1})/(px\,frame^{-1})}}
= 9.350044148\times10^{-4}\ \mathrm{s},
\]

or approximately 0.935004 ms. The corresponding reciprocal is approximately 1069.5137 s⁻¹. These derived quantities describe the timing encoded by the stored PIV conversion factors; they are not used as a substitute for the canonical container-declared frame rate, which remains `[RESULT PENDING — M0]`. The final spatial calibration also requires independent reconstruction from the calibration reference before the stored conversion is promoted to the final calibration constant.

## 2.4 PIV measurement domain and vector classes

The raw PIVlab exports contain Cartesian coordinates, velocity components and a `Vector type` classification. In the 13 byte-audited exports, each file contains 3,850 vector-grid rows arranged on 70 unique x coordinates and 55 unique y coordinates. Exactly 2,658 locations are classified as type 0 and have non-finite velocity components, while 1,192 locations contain finite velocity vectors. The type-0 mask is identical in the audited exports and is the exact complement of the finite-vector support. The coordinate lattice is likewise invariant across this sample, with a common coordinate-grid SHA-256.

Within the 1,192 active locations, PIVlab type 1 and type 2 vectors are retained as separate data classes. Type 1 is treated as the direct PIVlab vector class and type 2 as the interpolated class for forensic QA; neither class is silently collapsed into a single concept of measurement validity. The fraction of type-1 vectors among active locations varies from approximately 49.92% to 62.08% across the 13 audited fields even though the coordinate grid and active-domain mask remain fixed. This observation motivates two publication-level diagnostics after the full 250-file freeze: the temporal evolution of direct-vector fraction and the spatial direct-observation probability, \(P(\mathrm{type\ 1}\mid x,y)\). A direct-only versus all-active-vector sensitivity analysis is also required before derived hydrodynamic quantities are finalized.

This classification must not be equated with the historical `VDP >95%` statement contained in an earlier HardwareX-style manuscript. That document defines VDP as a Valid Data Percentage associated with cross-correlation success, while the current forensic quantity is specifically the fraction of PIVlab type-1 vectors among non-masked active locations. Until the historical VDP denominator, vector classes and calculation are reconstructed, the relationship between the two metrics is `[BLOCKER — DEFINITION AND REPRODUCTION REQUIRED]`.

## 2.5 Exported grid geometry and unresolved PIV processing settings

The median spacing obtained from the complete unique-coordinate lattices of the 13 audited exports is 0.00343104452 m. Dividing by the stored spatial conversion gives a nominal exported node pitch of 18.00033849 px. This value is a property of the archived output coordinates and does not, by itself, identify the interrogation-window size or overlap used by PIVlab.

The historical processing configuration is currently contradictory. A reconstruction script specifies a first interrogation pass of 32 px and a second pass of 18 px; the final thesis describes 36 × 36 px followed by 18 × 18 px with 50% overlap; and a separate analysis script contains a comment indicating 64 px to 18 px. Moreover, a simple 18 px final interrogation window with 50% overlap would nominally generate a 9 px vector step, whereas the archived output lattice is approximately 18 px. No authoritative saved PIVlab session has yet been recovered to explain whether later decimation, resampling or a different processing configuration produced the stored coordinates.

Accordingly, this manuscript does not select among 32, 36 or 64 px, and it does not infer zero overlap from the archived pitch. The final interrogation and vector-validation description remains `[BLOCKER — PIV SETTINGS]`. The exact historical outlier-filtering thresholds are likewise not promoted from reconstruction scripts or prose until the saved processing state or an output-reproducing reconstruction is obtained.

## 2.6 Retrospective temporal subset-selection study

A retrospective real-data tournament was executed on the 250 recovered PIVlab fields without access to CFD information. The active spatial domain contained 1,192 cells. Eleven selection algorithms were evaluated at subset sizes \(N=25, 50, 100, 150\), using five spatial folds and three random seeds. This produced 60 scenarios and 660 algorithm evaluations with zero algorithm errors; the associated real-data software checks passed 9/9 tests. The mean direct-vector fraction in the downstream 250-field tournament population was 0.5542080537.

The decision framework was intentionally allowed to return no selector. Independent decision lenses produced three votes for the uniform baseline, two for temporal-quality stratified sampling and one for the spatial lower-tail method. The resulting consensus fraction of 0.60 was below the predeclared requirement of 0.80, yielding `UNRESOLVED_DECISION_RULE_DISAGREEMENT` and `publication_selector = null`. This outcome is retained as a methodological result rather than overridden by a secondary weighted score.

The retrospective study tests the behavior of the selection framework on recovered downstream PIV fields; it does not establish canonical-video stationarity or authorize the final publication subset. The next experimental stage is therefore `[RESULT PENDING — M1 STATIONARITY]`, followed by sample-size convergence and subset robustness on the admissible canonical interval.

## 2.7 Sample-size convergence

`[RESULT PENDING — SAMPLE-SIZE CONVERGENCE]`

## 2.8 Measurement uncertainty

`[RESULT PENDING — UNCERTAINTY REPRODUCTION]`

Historical thesis uncertainty values are retained in the evidence matrix as reproduction targets but are not used as final constants in the present manuscript draft.

## 2.9 CFD model and numerical verification

`[RESULT PENDING — CFD GCI]`

The CFD branch remains intentionally locked until the experimental subset and uncertainty treatment are frozen. When opened, numerical verification will be reported separately from validation. The final turbulence, multiphase/free-surface, discretization and convergence settings will be reported from authoritative CFD case files rather than reconstructed thesis prose alone. The standard GCI framework will be documented consistently with Celik et al. [10]; any retained SST model description will be tied to the authoritative case and original model reference [11].

## 2.10 Common-coordinate PIV–CFD validation

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

The final comparison will transform PIV and CFD fields to a common physical coordinate system and mask, document interpolation and registration, and quantify sensitivity to the registration transform. Local discrepancy maps will be accompanied by RMSE and MAE and, only if retained after methodological review, an explicitly defined normalized/relative error. Agreement thresholds will not be interpreted independently of the reproduced PIV uncertainty field.

---

# 3. Results

## 3.1 Experimental evidence and provenance

**Observation.** The historical downstream PIVlab population is accessible and partially auditable at byte level, whereas the complete canonical MP4 cannot be transferred through the current connector, preventing canonical byte-level closure in this runtime.

**Quantitative result.** The exact canonical object has Drive ID `1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U` and provider-reported size 714,939,306 bytes. M0 currently returns `BLOCKED_EXTERNAL_CANONICAL_EXECUTION_REQUIRED`. The historical PIVlab namespace contains exports `0001`–`0250`; 13 distributed complete exports have been raw-byte parsed and SHA-256 hashed, and all audited checkpoints follow the pair rule from 4250/4251 to 4499/4500.

**Interpretation.** The downstream fields support scoped forensic characterization but cannot replace canonical-source verification. No canonical stationarity claim, final publication subset or CFD validation is opened from these exports alone. `[RESULT PENDING — M0]`

## 3.2 PIV measurement-domain characterization

**Observation.** The audited fields share a fixed coordinate support and masked region, while the direct/interpolated composition of active vectors varies between fields.

**Quantitative result.** Each audited export contains 3,850 nodes on a 70 × 55 lattice, with 2,658 type-0/masked locations and 1,192 finite active vectors. The coordinate-grid geometry and type-0 mask are invariant across the 13-file byte-audited sample. Direct/type-1 fraction among active vectors ranges from approximately 49.92% to 62.08%. The median exported pitch is 0.00343104452 m, equivalent to 18.00033849 px using the stored scale.

**Interpretation.** A fixed output mask does not imply a fixed amount of directly measured PIV information. Interpolated and direct vectors must therefore be treated separately in sensitivity analyses. The approximately 18 px output pitch also strengthens, but does not resolve, the contradiction with the documented 18 px/50%-overlap processing description. `[BLOCKER — PIV SETTINGS]`

## 3.3 Temporal robustness and subset-selection analysis

**Observation.** Different predeclared decision criteria do not select the same temporal sampling approach.

**Quantitative result.** The retrospective study comprised 250 fields, 1,192 active cells, 11 algorithms, four subset sizes, five spatial folds, three seeds, 60 scenarios and 660 algorithm evaluations with zero algorithm errors; 9/9 real-data software checks passed. Decision-lens votes were 3 for the uniform baseline, 2 for temporal-quality stratified sampling and 1 for the spatial lower-tail method. Consensus was 0.60, below the required 0.80; the outcome was `UNRESOLVED_DECISION_RULE_DISAGREEMENT` with `publication_selector = null`.

**Interpretation.** The recovered evidence does not justify a privileged temporal-selection algorithm. A complex selector has not demonstrated robust superiority, while uniform sampling remains competitive. The publication decision therefore remains intentionally unresolved until canonical stationarity and full-population convergence are demonstrated.

## 3.4 Sample-size convergence

`[RESULT PENDING — SAMPLE-SIZE CONVERGENCE]`

## 3.5 Experimental vortex hydrodynamics

`[RESULT PENDING — EXPERIMENTAL HYDRODYNAMICS]`

## 3.6 Measurement uncertainty

`[RESULT PENDING — UNCERTAINTY REPRODUCTION]`

The historically documented expanded PIV uncertainty and median relative uncertainty are not inserted as final quantitative Results until independently reproduced.

## 3.7 CFD numerical verification

`[RESULT PENDING — CFD GCI]`

The historical fine-grid GCI remains a reproduction target, not a final result.

## 3.8 Common-coordinate PIV–CFD validation

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

Historical 10% and 15% threshold-area fractions are retained only in the traceability/blocker ledgers until the registration, mask, interpolation and error calculation are independently rerun.

## 3.9 Spatial localization of discrepancy and uncertainty

`[RESULT PENDING — COMMON-COORDINATE VALIDATION]`

The final analysis will identify whether elevated discrepancy co-locates with experimental uncertainty, intermittent direct-vector coverage, the air-core boundary, strong gradients or registration-sensitive regions. Causal language will be avoided unless supported by dedicated sensitivity evidence.

---

# 4. Discussion

## 4.1 Experimental credibility before numerical comparison

The present evidence supports a methodological conclusion before it supports a final PIV–CFD accuracy conclusion: provenance, vector support and sampling decisions materially affect the field that will later be used for validation. Treating these steps as part of validation rather than as invisible preprocessing reduces the risk of reporting a numerically precise comparison whose experimental reference is insufficiently characterized.

## 4.2 Direct versus interpolated PIV information

The distinction between direct and interpolated active vectors is potentially consequential in a free-surface vortex because optical conditions vary strongly in space. The current forensic audit shows that the active mask can remain fixed while the direct-vector fraction varies between fields. The final paper will therefore test whether median fields, derived profiles and PIV–CFD metrics change when interpolated vectors are included or excluded. The historical `VDP >95%` statement is not interpreted as equivalent to direct-vector coverage until its exact definition is reconstructed.

## 4.3 Meaning of the unresolved selector result

The null selector decision is retained as evidence rather than treated as a failed optimization. A selection method should not be declared superior merely because one scoring rule ranks it first. The current rule disagreement demonstrates that representativeness is criterion-dependent in the recovered historical population. If this conclusion survives the canonical prospective workflow, methodological simplicity may be preferable where added selector complexity does not generate robust, decision-invariant benefit.

## 4.4 Numerical verification and experimental validation

The CFD branch remains logically separate from the experimental sampling branch. This prevents the experimental subset from being optimized toward the numerical field that it will later be used to assess. Once the experimental reference is frozen, numerical verification will quantify discretization sensitivity and the subsequent common-coordinate comparison will quantify agreement with measurement; neither step will be used retrospectively to redefine the experimental data.

---

# 5. Limitations

The present working manuscript is intentionally incomplete because several high-severity evidence gates remain open. First, the canonical MP4 has not yet been hashed, probed and decoded to end-of-file in an authenticated runtime; therefore canonical acquisition dimensions, declared frame rate/count and direct decode integrity of the historical 4250–4500 range remain unverified. Second, only 13 of the 250 historical PIVlab exports have been frozen at byte level, although the complete expected namespace is visible. Third, the historical PIV interrogation configuration is contradictory: available sources indicate first-pass sizes of 32, 36 or 64 px, and the documented 18 px final window with 50% overlap is inconsistent with the approximately 18 px exported node pitch. The exact vector-filtering configuration is also unresolved.

Fourth, the run-specific operating condition, final calibration reconstruction and prototype-to-CAD identity are not yet fully tied to the canonical acquisition. Fifth, canonical stationarity, sample-size convergence and the final experimental subset remain open, so the present selector result is retrospective only. Sixth, the PIV uncertainty budget has not been independently reproduced from frozen inputs. Seventh, CFD remains intentionally locked; therefore the historical GCI and final numerical-model settings are not yet reproduced. Finally, common-coordinate registration, interpolation sensitivity and the historical relative-error area fractions have not yet been rerun from authoritative PIV and CFD arrays.

These limitations are not filled with thesis values by assumption. Until the corresponding evidence gates close, they remain explicit blockers to submission.

---

# 6. Conclusions

`[NOT FINALIZED — MAJOR EVIDENCE GATES REMAIN OPEN]`

---

# 7. Data and Code Availability

The active reproducibility workflow is maintained in the repository `juanperez238421-cpu/Turbine-Optimization-CFD`, branch `astra-piv-tournament-v1`. The branch contains the M0 audit implementation, historical PIVlab forensic scripts, retrospective selector workflow, evidence manifests and manuscript traceability files. A permanent archival release and immutable identifier will be assigned only after the final experimental, numerical and validation evidence packages are frozen.

---

# 8. CRediT Authorship

`[PENDING AUTHOR CONTRIBUTION CONFIRMATION]`

# 9. Funding

`[PENDING VERIFIED FUNDING STATEMENT]`

# 10. Conflict of Interest

`[PENDING AUTHOR CONFIRMATION]`

---

# References — verified core set for current text

1. Keller, J., Möller, G., & Boes, R. (2014). PIV measurements of air-core intake vortices. *Flow Measurement and Instrumentation*, 40, 74–81. https://doi.org/10.1016/j.flowmeasinst.2014.08.004
2. Sun, H., & Liu, Y. (2015). Theoretical and experimental study on the vortex at hydraulic intakes. *Journal of Hydraulic Research*, 53(6), 787–796. https://doi.org/10.1080/00221686.2015.1076533
3. Duinmeijer, A., Oldenziel, G., & Clemens, F. (2020). Experimental study on the 3D-flow field of a free-surface vortex using stereo PIV. *Journal of Hydraulic Research*, 58(1), 105–119. https://doi.org/10.1080/00221686.2018.1555558
4. Nayab, Cheema, T. A., Rehman, M. M. U., & Saeed, M. O. B. (2026). Flow structure analysis in gravity-driven water vortex: An experimentally validated numerical study. *Flow Measurement and Instrumentation*, 111, 103356. https://doi.org/10.1016/j.flowmeasinst.2026.103356
5. Adrian, R. J. (1991). Particle-Imaging Techniques for Experimental Fluid Mechanics. *Annual Review of Fluid Mechanics*, 23, 261–304. https://doi.org/10.1146/annurev.fl.23.010191.001401
6. Scarano, F. (2002). Iterative image deformation methods in PIV. *Measurement Science and Technology*, 13(1), R1–R19. https://doi.org/10.1088/0957-0233/13/1/201
7. Westerweel, J., & Scarano, F. (2005). Universal outlier detection for PIV data. *Experiments in Fluids*, 39(6), 1096–1100. https://doi.org/10.1007/s00348-005-0016-6
8. Sciacchitano, A., Wieneke, B., & Scarano, F. (2013). PIV uncertainty quantification by image matching. *Measurement Science and Technology*, 24, 045302. https://doi.org/10.1088/0957-0233/24/4/045302
9. Sciacchitano, A., Neal, D. R., Smith, B. L., Warner, S. O., Vlachos, P. P., Wieneke, B., & Scarano, F. (2015). Collaborative framework for PIV uncertainty quantification: comparative assessment of methods. *Measurement Science and Technology*, 26(7), 074004. https://doi.org/10.1088/0957-0233/26/7/074004
10. Celik, I. B., Ghia, U., Roache, P. J., Freitas, C. J., Coleman, H., & Raad, P. E. (2008). Procedure for estimation and reporting of uncertainty due to discretization in CFD applications. *Journal of Fluids Engineering*, 130(7), 078001. https://doi.org/10.1115/1.2960953
11. Menter, F. R. (1994). Two-equation eddy-viscosity turbulence models for engineering applications. *AIAA Journal*, 32(8), 1598–1605. https://doi.org/10.2514/3.12149

---

# Supplementary Material — planned

- S1: canonical M0 provider/source/decode manifest;
- S2: complete 250-ASCII cryptographic manifest;
- S3: PIV settings contradiction/reconciliation record;
- S4: stationarity and admissible-interval tests;
- S5: sample-size convergence and selector robustness;
- S6: PIV uncertainty budget and maps;
- S7: CFD numerical-verification/GCI reproduction;
- S8: common-coordinate registration and sensitivity;
- S9: additional validation metrics and direct-only/interpolated sensitivity;
- S10: software environment, Git commit and script hashes.
