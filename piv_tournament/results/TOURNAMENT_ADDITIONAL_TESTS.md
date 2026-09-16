# Additional retrospective tournament tests — evidence update 2026-09-15

## Execution decision

No new selector ranking was manufactured. The no-CFD firewall and `publication_selector = null` remain unchanged.

## New real-data evidence relevant to selector robustness

A stratified set of 13 **complete raw PIVlab ASCII exports** was downloaded, full-byte SHA-256 hashed, and parsed. Across all 13:

- the coordinate lattice is invariant at 70 × 55 nodes;
- the static masked/type-0 domain is invariant at 2,658 nodes;
- the finite active domain is invariant at **1,192 cells**;
- pair provenance and calibration metadata remain consistent;
- type-1/direct fraction among active vectors varies from **49.92% to 62.08%**.

This gives direct raw-file support for the 1,192-cell spatial domain used in the historical tournament and shows that direct-versus-interpolated composition is not constant in the sampled fields.

## Scientific implication

The highest-value additional retrospective test remains **direct-only versus all-vector sensitivity**. It is now motivated by observed raw vector-type variation rather than only by code architecture.

However, executing that test on 13 fields would be underpowered and would change the population relative to the established 250-field tournament. It was therefore **not** used to generate a new selector ranking.

The complete 250-file cryptographic freeze must be executed first. After that freeze, reuse the branch's existing robustness machinery for:

- N=200 and N=250 reference cases;
- contiguous-block deletion and repeated block deletion;
- selector rank/vote stability;
- direct-only versus all-vector sensitivity;
- Pareto frequency, minimax regret, scenario ranks, and unknown-weight robustness.

All such outputs remain labelled **RETROSPECTIVE REAL-DATA VALIDATION** and cannot authorize the publication selector before canonical M0/M1.

## Current result

**NO_NEW_SELECTOR_RESULT_EXECUTED**

This is deliberate: new raw evidence was used to strengthen the eligibility/robustness basis, not to force a winner.
