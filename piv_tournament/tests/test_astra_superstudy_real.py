from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/"src"))

from astra_piv.advanced_selectors import ADVANCED_METHODS, run_advanced_selector
from astra_piv.oracle_validation import load_pivlab_oracle, spatial_cv_folds
from astra_piv.superstudy import run_real_oracle_crossvalidation
from astra_piv.convergence import chronological_convergence
from astra_piv.scientific_gate import EvidenceState, publication_gate
from astra_piv.decision import aggregate_scenarios, monte_carlo_weight_space, consensus_decision

REAL_DIR=Path(os.environ.get("ASTRA_REAL_PIVLAB_DIR","/mnt/data"))
REAL_FILES=sorted(REAL_DIR.glob("PIVlab_*.txt"))


class TestAstraSuperStudyRealData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(REAL_FILES)<3: raise unittest.SkipTest("Real PIVlab ASCII fields are not available")
        cls.data=load_pivlab_oracle(REAL_FILES)

    def test_01_real_fields_share_active_grid(self):
        self.assertGreaterEqual(len(self.data.pool),3)
        self.assertEqual(self.data.direct_reliability.shape[0],len(self.data.pool))
        self.assertGreater(self.data.direct_reliability.shape[1],1000)

    def test_02_known_local_regression_has_11_fields(self):
        if REAL_DIR==Path("/mnt/data"):
            self.assertEqual(len(self.data.pool),11)
            self.assertEqual(self.data.direct_reliability.shape[1],1192)

    def test_03_direct_fraction_does_not_leak_into_representative_selector(self):
        base=self.data.pool.copy(); perturbed=base.copy(); perturbed["direct_fraction"]=np.linspace(0,1,len(perturbed))
        a=run_advanced_selector("kernel_herding",base,min(5,len(base)),reliability=self.data.direct_reliability)
        b=run_advanced_selector("kernel_herding",perturbed,min(5,len(base)),reliability=self.data.direct_reliability)
        self.assertTrue(np.array_equal(a.pair_indices,b.pair_indices))

    def test_04_spatial_cv_is_disjoint_and_complete(self):
        n=self.data.direct_reliability.shape[1]; seen=np.zeros(n,int)
        for train,test in spatial_cv_folds(n,5):
            self.assertEqual(len(np.intersect1d(train,test)),0)
            self.assertEqual(len(np.union1d(train,test)),n); seen[test]+=1
        self.assertTrue(np.all(seen==1))

    def test_05_all_advanced_selectors_return_real_unique_pairs(self):
        n=min(5,len(self.data.pool)); existing=set(self.data.pool["pair_index"].astype(int))
        for method in ADVANCED_METHODS:
            result=run_advanced_selector(method,self.data.pool,n,reliability=self.data.direct_reliability,seed=20260912)
            ids=list(map(int,result.pair_indices)); self.assertEqual(len(ids),n,method); self.assertEqual(len(set(ids)),n,method); self.assertTrue(set(ids).issubset(existing),method)

    def test_06_real_held_out_tournament_runs(self):
        ranked=run_real_oracle_crossvalidation(self.data.pool,self.data.direct_reliability,sample_sizes=[min(3,len(self.data.pool))],folds=3,seeds=[20260912,20260913])
        self.assertGreater(len(ranked),0); self.assertIn("pareto_front",ranked.columns); self.assertIn("rank",ranked.columns)

    def test_07_decision_can_return_no_winner(self):
        ranked=run_real_oracle_crossvalidation(self.data.pool,self.data.direct_reliability,sample_sizes=[min(3,len(self.data.pool)),min(5,len(self.data.pool))],folds=3,seeds=[20260912,20260913])
        agg=aggregate_scenarios(ranked); metrics=["oracle_holdout_log_coverage","oracle_holdout_q10","oracle_holdout_once_fraction","representativeness_wasserstein_mean","temporal_span_ratio","adjacent_pair_fraction"]
        med=ranked.groupby("method",as_index=False)[metrics].median(numeric_only=True); ws=monte_carlo_weight_space(med,metrics,draws=1000,seed=1); decision=consensus_decision(agg,ws)
        self.assertIn(decision["status"],{"UNRESOLVED_DECISION_RULE_DISAGREEMENT","ROBUST_NUMERICAL_SELECTOR_CANDIDATE_REQUIRES_SCIENTIFIC_GATE"})

    def test_08_publication_gate_blocks_sparse_retrospective_data(self):
        state=EvidenceState(calibration_resolved=True,delta_t_resolved=True,piv_native_quality_available=True,spatial_reliability_available=True,spatial_holdout_validation_completed=True,cfd_locked_during_selection=True)
        report=publication_gate(state,numerical_candidate="uniform_baseline"); self.assertIsNone(report["publication_selector"])

    def test_09_direct_only_convergence_runs(self):
        table,meta=chronological_convergence(REAL_FILES,[min(3,len(REAL_FILES)),len(REAL_FILES)])
        self.assertEqual(len(table),2); self.assertGreater(meta["n_active_cells"],1000); self.assertTrue(np.isfinite(table["cells_with_direct_measurement_fraction"]).all())


if __name__=="__main__": unittest.main(verbosity=2)
