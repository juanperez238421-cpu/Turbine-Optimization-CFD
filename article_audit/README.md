# Santiago GVT result-metadata audit system

This directory implements a deterministic, auditable metadata layer for the **results** used in the Santiago gravitational-vortex-turbine review.

The purpose is not to assign a vague "quality score". It separates:

1. **what the result is**;
2. **where it came from**;
3. **whether it is measured, simulated, calculated, or inferred**;
4. **whether the calculation can be reproduced**;
5. **whether the compared states are scientifically comparable**;
6. **whether uncertainty and validation are available**;
7. **what claim scope is allowed**;
8. **which blockers prevent publication use**.

## Core evidence modes

| Code | Meaning | Rule |
|---|---|---|
| M | Measured | Experimental value reported by a primary source or raw measurement |
| S | Simulated | CFD / numerical / response-surface value |
| C | Calculated | Value calculated from traceable source values |
| I | Inferred | Interpretation not directly measured or numerically reproduced |

Evidence mode is **provenance**, not a quality grade.

## Audit readiness states

The audit engine assigns one of these states:

- **BLOCKED** — a hard scientific/provenance blocker is present.
- **CONDITIONAL** — usable only with an explicit limitation or unresolved metadata item.
- **REPRODUCIBLE** — a calculated result is traceable and its arithmetic is reproduced by the audit engine.
- **TRACEABLE** — source identity and locator are sufficient, but the result is not independently recalculated.
- **RELEASE_CANDIDATE** — traceability is complete, no declared blocker/warning is active, and the metadata required by policy are present.

A high metadata-completeness percentage can never override a blocker.

## Classification dimensions

Each result record contains explicit fields for:

- result identity;
- manuscript role/location;
- numerical value and unit;
- evidence mode;
- primary source identity and DOI;
- source file and page/table/figure locator;
- result origin;
- reproducible calculation expression and dependencies;
- geometry state;
- operating state;
- comparison class;
- uncertainty status;
- validation scope;
- allowed claim scope;
- declared flags and notes.

See \`schema/result_metadata.schema.json\` and \`config/classification_policy.json\`.

## Santiago seed registry

\`data/santiago_results_registry.csv\` contains the current traceable quantitative core that was reconstructed during the senior audit:

- Dhakal et al. basin results and the +9.24 W within-study output-power difference;
- the source-reported efficiency difference, explicitly blocked by the hydraulic-input denominator inconsistency;
- the 16/18 positive matched spiral-minus-tangential peak-response cells and two reversals;
- runner-position MAE/RMSE for the four tested positions;
- the untested p = 0.60 numerical/RSM results.

These records deliberately preserve limitations. The tool must never "repair" or silently harmonize a source inconsistency.

## Run

\`\`\`bash
python article_audit/audit_results.py \
  --input article_audit/data/santiago_results_registry.csv \
  --policy article_audit/config/classification_policy.json \
  --out-dir article_audit/build
\`\`\`

Outputs:

- \`audit_results.json\`: complete machine-readable decision record;
- \`audit_results.csv\`: flattened audit state per result;
- \`AUDIT_SUMMARY.md\`: publication-facing QA summary.

## Tests

\`\`\`bash
python -m unittest discover -s article_audit/tests -v
\`\`\`

The tests verify DOI normalization, arithmetic reproduction, positive-cell counting, duplicate-ID detection, and hard-blocker precedence.

## Governance rule

A manuscript number may be used as a primary result only when its **source identity, source locator, result type, comparison boundary, and publication-use status** are explicit. Cross-study pooling is forbidden unless a dedicated harmonization record documents common geometry/operating/metric definitions.
