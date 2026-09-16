from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from astra_piv.advanced_selectors import ADVANCED_METHODS, run_advanced_selector
from astra_piv.scientific_gate import EvidenceState, publication_gate


class TestAstraSuperStudyCore(unittest.TestCase):
    def setUp(self):
        n=20
        self.pool=pd.DataFrame({
            "pair_index":np.arange(1000,1000+n),
            "coarse_pce_p10":np.linspace(2,8,n),
            "coarse_ppr_p10":np.linspace(1.05,1.8,n)[::-1],
            "coarse_disp_median_px":np.sin(np.linspace(0,3,n))+2,
            "phase_response":np.linspace(0.7,1.1,n),
        })
        j=12; ii=np.arange(n)[:,None]; jj=np.arange(j)[None,:]
        self.R=np.clip(0.5+0.5*np.sin(0.31*ii+0.47*jj),0,1)

    def test_all_advanced_methods_return_valid_unique_subsets(self):
        for method in ADVANCED_METHODS:
            result=run_advanced_selector(method,self.pool,6,reliability=self.R,seed=7)
            self.assertEqual(len(result.pair_indices),6,method)
            self.assertEqual(len(set(result.pair_indices.tolist())),6,method)

    def test_publication_gate_requires_all_evidence(self):
        incomplete=publication_gate(EvidenceState(),"kernel_herding")
        self.assertIsNone(incomplete["publication_selector"])
        complete=EvidenceState(**{name:True for name in EvidenceState.__dataclass_fields__})
        passed=publication_gate(complete,"kernel_herding")
        self.assertEqual(passed["publication_selector"],"kernel_herding")


if __name__=="__main__": unittest.main(verbosity=2)
