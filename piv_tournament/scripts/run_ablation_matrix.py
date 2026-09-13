#!/usr/bin/env python3
from __future__ import annotations

import argparse, copy, json
from pathlib import Path
import numpy as np
import pandas as pd

from astra_piv.coarse_piv import scan_coarse_piv, _empirical_quantile_scale
from astra_piv.config import load_config
from astra_piv.pipeline import run_tournament_on_pool
from astra_piv.provenance import inspect_video_provenance


def main():
    p=argparse.ArgumentParser(description="Ablation/sensitivity matrix for the ASTRA PIV selector tournament")
    p.add_argument("--video",required=True); p.add_argument("--stationary-pool",required=True); p.add_argument("--config",required=True); p.add_argument("--output-dir",required=True)
    p.add_argument("--windows",nargs="+",type=int,default=[32,36]); p.add_argument("--quantiles",nargs="+",default=["5,95","10,90","20,80"]); p.add_argument("--gate-mad",nargs="+",type=float,default=[3.0,4.0,5.0]); p.add_argument("--reliability-modes",nargs="+",default=["geomean","pce_only","ppr_only"])
    args=p.parse_args(); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); base_cfg=load_config(args.config); pool=pd.read_csv(args.stationary_pool).sort_values("pair_index").reset_index(drop=True); prov=inspect_video_provenance(args.video,base_cfg.provenance)
    records=[]
    for window in args.windows:
        wdir=out/f"window_{window}px"; cfg_w=copy.deepcopy(base_cfg); cfg_w.coarse_piv.window_px=int(window)
        summary,_,_=scan_coarse_piv(args.video,pool["pair_index"].astype(int).to_numpy()[::max(1,cfg_w.coarse_piv.candidate_stride)],cfg_w.coarse_piv,cfg_w.video_scan.roi,output_dir=wdir/"coarse_piv")
        merged=pool.merge(summary,on="pair_index",how="inner",validate="one_to_one").sort_values("pair_index").reset_index(drop=True)
        pce=np.load(wdir/"coarse_piv"/"coarse_piv_pce_matrix.npy"); ppr=np.load(wdir/"coarse_piv"/"coarse_piv_ppr_matrix.npy"); pair_order=np.load(wdir/"coarse_piv"/"coarse_piv_pair_indices.npy"); order={int(pid):i for i,pid in enumerate(pair_order)}; idx=np.array([order[int(pid)] for pid in merged["pair_index"]],dtype=int); pce=pce[idx]; ppr=ppr[idx]
        for qspec in args.quantiles:
            lo,hi=map(float,qspec.split(",")); q_pce=np.clip(_empirical_quantile_scale(pce,lo,hi),0,1); q_ppr=np.clip(_empirical_quantile_scale(ppr,lo,hi),0,1); variants={"geomean":np.sqrt(q_pce*q_ppr),"pce_only":q_pce,"ppr_only":q_ppr}
            for reliability_mode in args.reliability_modes:
                if reliability_mode not in variants: raise ValueError(f"Unknown reliability mode: {reliability_mode}")
                reliability=variants[reliability_mode]
                for mad in args.gate_mad:
                    cfg=copy.deepcopy(cfg_w); cfg.coarse_piv.quality_low_quantile=lo; cfg.coarse_piv.quality_high_quantile=hi; cfg.tournament.quality_gate_mad_multiplier=float(mad); run_dir=wdir/f"q{lo:g}_{hi:g}"/reliability_mode/f"gate_{mad:g}MAD"
                    _,summary_meta,_=run_tournament_on_pool(merged,cfg,run_dir,reliability=reliability,source_video_sha256=prov.sha256)
                    records.append({"window_px":window,"quality_low_quantile":lo,"quality_high_quantile":hi,"reliability_mode":reliability_mode,"gate_mad_multiplier":mad,"status":summary_meta["status"],"provisional_winner":summary_meta.get("provisional_overall_winner"),"winner_fraction_across_N":summary_meta.get("cross_sample_size_winner_fraction")})
    df=pd.DataFrame(records); df.to_csv(out/"ablation_matrix.csv",index=False); winners=df["provisional_winner"].dropna()
    if len(winners): counts=winners.value_counts(); method=str(counts.index[0]); fraction=float(counts.iloc[0]/len(winners))
    else: method=None; fraction=0.0
    result={"runs":len(df),"dominant_method":method,"dominant_method_fraction":fraction,"publication_robustness_status":"ROBUST_CANDIDATE" if method is not None and fraction>=base_cfg.tournament.winner_requires_stability_fraction else "UNRESOLVED_METHOD_SENSITIVE","rule":"A preferred selector family must remain dominant across interrogation-window, reliability-normalization and quality-gate sensitivity."}
    (out/"ablation_summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))

if __name__=="__main__": main()
