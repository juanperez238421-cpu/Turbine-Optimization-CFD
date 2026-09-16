# ASTRA v2 real-data regression result

The current regression dataset contains 11 original historical PIVlab ASCII fields and 1192 active grid cells. Direct-vector fraction spans 0.499161–0.620805 (mean 0.545683).

To prevent retrospective information leakage, PIV velocity statistics are excluded from selector inputs. The PIVlab fields are used only as a spatial direct-validity oracle for held-out evaluation.

Corrected held-out spatial cross-validation used N = 3, 5, 7; five spatial folds; and five seeds, producing 75 scenarios per method. Different decision lenses still disagree: the uniform baseline receives three rule votes while kernel herding receives two. The leading consensus fraction is 0.60, below the configured 0.80 requirement. ASTRA therefore returns `UNRESOLVED_DECISION_RULE_DISAGREEMENT` rather than forcing a winner.

Selected strict-no-oracle diagnostics:
- kernel herding: Pareto-front frequency 0.9733; median rank 3; scenario-win frequency 0.2133; unknown-weight win probability about 0.502.
- uniform baseline: Pareto-front frequency 0.8667; median rank 2; scenario-win frequency 0.2667; unknown-weight win probability about 0.209.
- spatial saturated coverage: Pareto-front frequency 0.9067; median rank 5.
- spatial lower-tail coverage: Pareto-front frequency 0.8667; median rank 6.

Direct-only systematic full-span convergence versus the full 11-field direct-only median reference:
- N=3: measured-cell fraction 0.8070; vector RMSE 0.06903 m/s.
- N=5: 0.8708; 0.05723 m/s.
- N=7: 0.9102; 0.04316 m/s.
- N=9: 0.9144; 0.03013 m/s.
- N=11: 0.9362; 0 by definition because this is the reference ensemble.

Software validation in the local real-data environment: Python compilation PASS and 9/9 real-data tests PASS.

**Scope warning:** this is a sparse retrospective regression/sanity dataset, not the canonical full high-speed selector study. It cannot authorize a publication subset. No CFD data were used.
