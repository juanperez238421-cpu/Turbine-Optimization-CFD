# MEAS-D-25-17345 — CODEX STAGE 3 START PROMPT

Work in:

`D:\Academía\Maestría\MEAS_D_25_17345_TRANSFER_REVISION`

Do not restart prior stages. Use newest local files.

## 0. Gate first

Run:

`python .\scripts\validate_stage3_prerequisites.py`

If non-zero, STOP and report:

`STAGE 3 BLOCKED — RETURN TO STAGE 2`

Continue only if the final Stage-2C evidence freeze and QA both PASS.

## 1. Objective

Redesign the review methodology and scientific contribution from the frozen evidence.

Central Stage-3 story:

**Evidence-based selection, reporting quality, uncertainty practice, and CFD-validation utility of non-intrusive optical flow diagnostics in hydraulic turbomachinery and directly turbine-relevant hydraulic flows.**

Do not equate method frequency with method superiority.

## 2. Required outputs

Create:

- `03_METHODS/REVIEW_DESIGN_DECISION.md`
- `03_METHODS/INCLUSION_EXCLUSION_RULES.md`
- `03_METHODS/CANONICAL_TAXONOMY_FINAL.md`
- `03_METHODS/METHOD_SELECTION_FRAMEWORK.csv`
- `03_METHODS/UNCERTAINTY_REPORTING_MATRIX.csv`
- `03_METHODS/CFD_VALIDATION_RELEVANCE_MATRIX.csv`
- `03_METHODS/MINIMUM_REPORTING_CHECKLIST.md`
- `03_METHODS/CONTRIBUTION_VS_PRIOR_REVIEWS.md`
- `03_METHODS/RESULTS_ARCHITECTURE.md`
- `03_METHODS/DISCUSSION_ARCHITECTURE.md`
- `03_METHODS/STAGE3_REPORT.md`

Do NOT write the complete manuscript in Stage 3.

## 3. Review-design decision

Determine which label is defensible from the reconstructed and updated evidence:

- systematic review with bibliometric component;
- systematic mapping review;
- structured evidence synthesis with bibliometric component.

Document what can and cannot be claimed, particularly because the original R1 database exports and exclusion ledger were not recovered.

## 4. Scope strata

Use:

- `DIRECT_TURBINE`
- `COMPONENT_OR_PHENOMENON`
- `EXCLUDED`

Do not merge component/phenomenon evidence into direct turbine studies.

## 5. Method family and measurement role

Keep canonical method family separate from measurement role.

Roles:

- `PRIMARY_MEASUREMENT`
- `SUPPORTING_MEASUREMENT`
- `CFD_VALIDATION_DATA`
- `QUALITATIVE_VISUALIZATION`
- `MIXED`

LDV/LDA remain one `LASER_DOPPLER` family.
`SIV` must never be auto-expanded to stereo-PIV.

## 6. Method-selection framework

Build evidence-traceable fields for:
measurement principle, dimensionality, output, flow feature, optical access, seeding/tracer, temporal/spatial resolution, refraction sensitivity, cavitation/bubble sensitivity, near-wall limitations, uncertainty-reporting prevalence, CFD-validation utility, common failure modes, and evidence study IDs.

Generic textbook material must be explicitly labelled as external technical context.

## 7. Uncertainty synthesis

Build `UNCERTAINTY_REPORTING_MATRIX.csv` with:

`study_id, corpus_origin, method_family, measurement_role, uncertainty_reported, uncertainty_type, uncertainty_value_or_range, calibration_reported, spatial_resolution_reported, temporal_resolution_reported, refraction_correction_reported, repeatability_or_convergence_reported, source_page_or_section, reporting_quality_flag, notes`

Derive exact numerator/denominator rates from the frozen ledger.

## 8. CFD-validation synthesis

Build `CFD_VALIDATION_RELEVANCE_MATRIX.csv` with:

`study_id, corpus_origin, system, method_family, measurement_role, measured_quantity, CFD_used, CFD_model_if_reported, comparison_dimension, spatial_registration_reported, temporal_alignment_reported, comparison_metric, uncertainty_used_in_validation, qualitative_or_quantitative, validation_strength_description, source_page_or_section, limitations`

Strict terminology:

- measurement uncertainty != validation;
- experimental validation != numerical verification;
- grid/GCI != experimental validation.

## 9. Minimum reporting checklist

Classify items as:

- `REQUIRED_FOR_REPRODUCIBILITY`
- `RECOMMENDED`
- `CONTEXT_DEPENDENT`

Use only evidence-supported items.

## 10. Novelty / competitors

Verify the closest 2023–2026 reviews before claiming novelty.
Do not claim “first review” unless demonstrably true.

## 11. Architecture only

Design the new Results and Discussion architecture, but do not fully rewrite the manuscript.

## 12. Stage-3 gate

PASS only if every framework/table regenerates from the frozen ledger and every quantitative statement is traceable.

Report:

A. COMPLETED
B. BLOCKERS
C. NEW SCIENTIFIC CONTRIBUTION
D. REQUIRED STAGE-4 INPUTS
E. GATE
F. REJECT RISK

Then STOP. Do not begin Stage 4 automatically.