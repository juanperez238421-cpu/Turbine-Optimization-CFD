# Additional retrospective tournament tests — 2026-09-15

## Execution decision

No new selector ranking was manufactured in this session. The current Git branch contains the 250-field summary but not the private per-field arrays required to execute new retrospective tests inside GitHub Actions. Re-running a weighted score from summary tables would not be scientifically valid.

## Existing executable robustness code found

The branch already contains `run_temporal_robustness_v2.py` / `robustness_v2.py`, including temporal autocorrelation/ESS diagnostics, leave-one-contiguous-block-out stability and repeated contiguous-block deletion. This code should be reused after the 250 ASCII population is frozen in a mounted-Drive runtime rather than reimplemented.

## Scientifically valid next retrospective additions after the ASCII freeze

Priority tests are: N=200 and N=250 reference cases; contiguous-block deletion; selector rank/vote stability; direct-only versus all-vector sensitivity; Pareto frequency; minimax regret; scenario ranks; and the existing unknown-weight robustness diagnostic. Results must remain labelled **RETROSPECTIVE REAL-DATA VALIDATION** and cannot authorize the publication selector before canonical M0/M1.

## Current result

**NO_NEW_SELECTOR_RESULT_EXECUTED** — deliberate preservation of the no-CFD and no-forced-winner rules.
