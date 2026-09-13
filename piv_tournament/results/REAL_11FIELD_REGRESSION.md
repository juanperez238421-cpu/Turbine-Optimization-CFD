# ASTRA v2 real-data regression result

The current local regression dataset contains 11 original historical PIVlab ASCII fields and 1192 active grid cells. Direct-vector fraction spans 0.499161–0.620805 (mean 0.545683).

A corrected held-out spatial cross-validation study used N = 3, 5, 7; five spatial folds; and five seeds, producing 75 scenarios per method. Different decision lenses disagreed: the uniform baseline received three rule votes, kernel herding two, and Kennard–Stone one due to a tie. The leading consensus fraction was 0.60, below the configured 0.80 threshold. ASTRA therefore returned `UNRESOLVED_DECISION_RULE_DISAGREEMENT` rather than forcing a winner.

Selected diagnostics:
- kernel herding: Pareto-front frequency 0.9733; median rank 5; unknown-weight win probability 0.5605.
- uniform baseline: Pareto-front frequency 0.8667; median rank 2; scenario-win frequency 0.3467; unknown-weight win probability 0.16155.
- spatial saturated coverage: Pareto-front frequency 0.9067; median rank 6.

Direct-only systematic full-span convergence versus the full 11-field direct-only median reference:
- N=3: measured-cell fraction 0.8070; vector RMSE 0.06903 m/s.
- N=5: 0.8708; 0.05723 m/s.
- N=7: 0.9102; 0.04316 m/s.
- N=9: 0.9144; 0.03013 m/s.
- N=11: 0.9362; 0 by definition because this is the reference ensemble.

Software validation: Python compilation PASS; real-data unit tests 9/9 PASS.

**Scope warning:** this is a sparse retrospective regression/sanity dataset, not the canonical full high-speed selector study. It cannot authorize a publication subset. No CFD data were used.
