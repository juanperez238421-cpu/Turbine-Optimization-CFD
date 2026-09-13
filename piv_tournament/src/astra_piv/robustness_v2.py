from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .advanced_selectors import ADVANCED_METHODS, run_advanced_selector
from .convergence import effective_sample_size
from .selectors import run_selector


def temporal_dependence_report(pool: pd.DataFrame, *, candidate_metrics: list[str] | None = None) -> dict:
    """Estimate temporal redundancy from stationary experimental observables only."""
    if candidate_metrics is None:
        candidate_metrics=["coarse_disp_median_px","coarse_disp_p90_px","normalized_interframe_mad","phase_dx_original_px","phase_dy_original_px","phase_shift_magnitude_original_px","phase_response","pair_particle_like_blob_density_proxy_mean"]
    reports={}
    for c in candidate_metrics:
        if c not in pool.columns: continue
        x=pd.to_numeric(pool[c],errors="coerce").to_numpy(float)
        if np.sum(np.isfinite(x))<10 or np.nanstd(x)<=1e-12: continue
        reports[c]=effective_sample_size(x)
    if reports:
        tau_max=max(float(r["integrated_autocorrelation_time"]) for r in reports.values()); ess_min=min(float(r["ess"]) for r in reports.values())
    else:
        tau_max=np.nan; ess_min=np.nan
    return {"metrics":reports,"max_integrated_autocorrelation_time_pairs":tau_max,"minimum_metric_effective_sample_size":ess_min,"diagnostic_decorrelation_gap_pairs":int(np.ceil(tau_max)) if np.isfinite(tau_max) else None,"rule":"The decorrelation gap is diagnostic, not an automatic exclusion rule; interpret it with flow physics and sample-size convergence."}


def _select(method,pool,n,cfg,reliability,seed):
    if method in ADVANCED_METHODS:
        return run_advanced_selector(method,pool,n,seed=seed,reliability=reliability,min_gap_pairs=getattr(cfg.tournament,"minimum_temporal_gap_pairs",1))
    return run_selector(method,pool,n,cfg.tournament,cfg.provenance,reliability=reliability)


def _jaccard(a:set[int],b:set[int])->float:
    u=a|b
    return float(len(a&b)/len(u)) if u else 1.0


def temporal_block_jackknife_v2(pool:pd.DataFrame,methods:Iterable[str],n:int,cfg,*,reliability:np.ndarray|None=None,blocks:int=5,seed:int=20260912)->tuple[pd.DataFrame,dict]:
    """Leave-one-contiguous-time-block-out selector stability; CFD-free."""
    pool=pool.sort_values("pair_index").reset_index(drop=True); methods=list(dict.fromkeys(methods))
    if len(pool)<n+blocks: return pd.DataFrame(),{"status":"UNRESOLVED_POOL_TOO_SMALL_FOR_TEMPORAL_JACKKNIFE","pool_size":len(pool),"n":n,"blocks":blocks}
    full={}
    for method in methods:
        if method=="legacy_control" and n!=250: continue
        try: full[method]=_select(method,pool,n,cfg,reliability,seed)
        except Exception: continue
    rows=[]; block_indices=np.array_split(np.arange(len(pool)),blocks)
    for b,held in enumerate(block_indices):
        keep=np.ones(len(pool),bool); keep[held]=False; sub=pool.loc[keep].reset_index(drop=True); subR=reliability[keep] if reliability is not None else None
        if len(sub)<n: continue
        held_ids=set(pool.iloc[held]["pair_index"].astype(int))
        for method,original in full.items():
            try: rerun=_select(method,sub,n,cfg,subR,seed+b)
            except Exception: continue
            ref=set(map(int,original.pair_indices))-held_ids; new=set(map(int,rerun.pair_indices))
            rows.append({"block":b,"method":method,"heldout_start_pair":int(pool.iloc[held[0]]["pair_index"]),"heldout_end_pair":int(pool.iloc[held[-1]]["pair_index"]),"full_selected_available":len(ref),"rerun_selected":len(new),"intersection":len(ref&new),"retention_fraction":float(len(ref&new)/max(len(ref),1)),"jaccard":_jaccard(ref,new)})
    df=pd.DataFrame(rows)
    agg=(df.groupby("method",as_index=False).agg(retention_median=("retention_fraction","median"),retention_min=("retention_fraction","min"),jaccard_median=("jaccard","median"),jaccard_min=("jaccard","min")).sort_values(["jaccard_median","retention_median"],ascending=False)) if len(df) else pd.DataFrame()
    return df,{"status":"TEMPORAL_BLOCK_JACKKNIFE_COMPLETE" if len(df) else "UNRESOLVED_NO_JACKKNIFE_RESULTS","pool_size":int(len(pool)),"n":int(n),"blocks":int(blocks),"aggregate":agg.to_dict(orient="records"),"interpretation":"Jaccard/retention quantify sensitivity to removal of contiguous experimental time blocks; they are not CFD validation metrics."}


def random_contiguous_deletion_stability(pool:pd.DataFrame,methods:Iterable[str],n:int,cfg,*,reliability:np.ndarray|None=None,delete_fraction:float=0.15,repeats:int=50,seed:int=20260912)->tuple[pd.DataFrame,dict]:
    """Repeated random contiguous deletion stress test for selector-set stability."""
    pool=pool.sort_values("pair_index").reset_index(drop=True); methods=list(dict.fromkeys(methods)); rng=np.random.default_rng(seed); delete_len=max(1,int(round(delete_fraction*len(pool))))
    if len(pool)-delete_len<n: return pd.DataFrame(),{"status":"UNRESOLVED_POOL_TOO_SMALL_FOR_DELETION_STRESS","pool_size":len(pool),"n":n,"delete_len":delete_len}
    full={}
    for method in methods:
        if method=="legacy_control" and n!=250: continue
        try: full[method]=_select(method,pool,n,cfg,reliability,seed)
        except Exception: continue
    rows=[]
    for r in range(repeats):
        start=int(rng.integers(0,len(pool)-delete_len+1)); held=np.arange(start,start+delete_len); keep=np.ones(len(pool),bool); keep[held]=False; sub=pool.loc[keep].reset_index(drop=True); subR=reliability[keep] if reliability is not None else None; held_ids=set(pool.iloc[held]["pair_index"].astype(int))
        for method,original in full.items():
            try: rerun=_select(method,sub,n,cfg,subR,seed+r+1)
            except Exception: continue
            ref=set(map(int,original.pair_indices))-held_ids; new=set(map(int,rerun.pair_indices))
            rows.append({"repeat":r,"method":method,"deleted_start_pair":int(pool.iloc[held[0]]["pair_index"]),"deleted_end_pair":int(pool.iloc[held[-1]]["pair_index"]),"jaccard":_jaccard(ref,new),"retention_fraction":float(len(ref&new)/max(len(ref),1))})
    df=pd.DataFrame(rows)
    agg=(df.groupby("method",as_index=False).agg(jaccard_median=("jaccard","median"),jaccard_q10=("jaccard",lambda x:np.quantile(x,0.10)),retention_median=("retention_fraction","median"),retention_q10=("retention_fraction",lambda x:np.quantile(x,0.10))).sort_values(["jaccard_median","jaccard_q10"],ascending=False)) if len(df) else pd.DataFrame()
    return df,{"status":"CONTIGUOUS_DELETION_STRESS_COMPLETE" if len(df) else "UNRESOLVED_NO_STRESS_RESULTS","delete_fraction":delete_fraction,"repeats":repeats,"aggregate":agg.to_dict(orient="records")}


def write_robustness_outputs(output_dir:str|Path,dependence:dict,jackknife_df:pd.DataFrame,jackknife_meta:dict,stress_df:pd.DataFrame|None=None,stress_meta:dict|None=None)->None:
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); (out/"temporal_dependence.json").write_text(json.dumps(dependence,indent=2),encoding="utf-8"); jackknife_df.to_csv(out/"temporal_block_jackknife.csv",index=False); (out/"temporal_block_jackknife_meta.json").write_text(json.dumps(jackknife_meta,indent=2),encoding="utf-8")
    if stress_df is not None: stress_df.to_csv(out/"contiguous_deletion_stress.csv",index=False)
    if stress_meta is not None: (out/"contiguous_deletion_stress_meta.json").write_text(json.dumps(stress_meta,indent=2),encoding="utf-8")
