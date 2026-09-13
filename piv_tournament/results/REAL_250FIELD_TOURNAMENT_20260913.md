# ASTRA real-data tournament — 250 historical PIVlab fields

**Date:** 2026-09-13  
**Evidence class:** retrospective experimental PIVlab-export tournament  
**Publication status:** diagnostic evidence only; does **not** authorize a publication selector  
**CFD firewall:** closed; no CFD data were used

## Dataset and execution

The real-data tournament used 250 historical PIVlab fields associated with the legacy consecutive-pair window spanning source frames 4250–4500. The active experimental grid contained 1,192 cells. Across the tournament, 11 selection algorithms were evaluated at subset sizes N = 25, 50, 100, and 150 using five spatial folds and three random seeds (20260912, 20260913, 20260914).

The run produced 660 algorithm evaluations across 60 scenarios with zero algorithm errors. The mean direct-vector fraction across the 250 fields was 0.5542080537. The real-data software test suite passed 9/9 tests.

## Decision outcome

ASTRA returned:

`UNRESOLVED_DECISION_RULE_DISAGREEMENT`

The leading method under the current multi-rule aggregation was `uniform_baseline`, but the evidence did not satisfy the predeclared 0.80 consensus threshold required to name a robust publication selector.

| Decision lens vote | Votes |
|---|---:|
| uniform_baseline | 3 |
| temporal_quality_stratified | 2 |
| spatial_lower_tail | 1 |

The resulting rule-consensus fraction was 0.60. Therefore:

- `publication_selector = null`
- `numerical_candidate = null`
- no selector is frozen for publication
- no method is rejected solely because it did not lead this diagnostic run

This is a scientifically admissible unresolved outcome. The present evidence does not justify forcing a preferred algorithm to appear superior.

## What this result supports

The 250-field retrospective run supports four conclusions at the current evidence level:

1. The tournament software can execute the intended multi-algorithm comparison on the recovered historical PIVlab population without algorithm failures.
2. Different defensible decision lenses disagree materially about the preferred selector.
3. A simple uniform baseline remains competitive enough that added selector complexity is not yet justified by this diagnostic dataset.
4. The publication decision must remain unresolved until the canonical raw-video evidence gate is passed and the complete prospective workflow is rerun.

## What this result does not support

This run does **not** establish:

- integrity of the canonical high-speed video;
- stationarity of the raw-video population;
- representativeness outside the historical 250-pair window;
- measured velocity accuracy from direct-vector coverage alone;
- independence of spatial holdout cells;
- a final publication subset;
- any PIV–CFD agreement claim.

The historical exports are downstream PIV products. They are useful as retrospective experimental evidence, but they cannot replace canonical-source verification, raw-image stationarity, audited calibration, PIV settings, uncertainty reproduction, convergence analysis, or the final CFD validation stage.

## Current hard gate

Canonical source: `vid_2025-08-29_19-28-15.mp4`  
Known Drive metadata size: 714,939,306 bytes  
Canonical SHA-256: not yet measured from accessible complete bytes  
Full sequential decode: not yet executed in the current runtime  
Frames 4250–4500 decode verification: not yet executed from canonical bytes

Accordingly, M0 remains blocked and M1 stationarity cannot yet be opened as canonical evidence.
