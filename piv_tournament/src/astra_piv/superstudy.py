from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance, rankdata

from .advanced_selectors import run_advanced_selector
from .oracle_validation import spatial_cv_folds


def _positions(pool: pd.DataFrame, ids: np.ndarray) -> np.ndarray:
    m = {int(pid): i for i, pid in enumerate(pool["pair_index"].astype(int))}
    return np.array([m[int(pid)] for pid in ids], dtype=int)


def _gini_nonnegative(x: np.ndarray) -> float:
    x=np.asarray(x,float); x=x[np.isfinite(x)]
    if len(x)==0 or np.allclose(x,0): return 0.0
    x=np.sort(np.clip(x,0,None)); n=len(x)
    return float((2*np.sum(np.arange(1,n+1)*x)/(n*np.sum(x)))-(n+1)/n)


def benchmark_result(pool: pd.DataFrame, result, reliability_eval: np.ndarray | None = None) -> dict:
    ids=np.asarray(result.pair_indices,int); pos=_positions(pool,ids); sorted_ids=np.sort(ids); gaps=np.diff(sorted_ids)
    full_span=max(int(pool["pair_index"].max())-int(pool["pair_index"].min()),1)
    exclude={"pair_index","frame_a","frame_b","export_frame","direct_fraction","type2_fraction"}; distances=[]
    for c in pool.select_dtypes(include=[np.number]).columns:
        if c in exclude: continue
        x=pool[c].to_numpy(float)
        if np.sum(np.isfinite(x))<3 or np.nanstd(x)<=1e-12: continue
        full=x[np.isfinite(x)]; chosen=x[pos]; chosen=chosen[np.isfinite(chosen)]
        if len(full)==0 or len(chosen)==0: continue
        scale=np.nanpercentile(full,90)-np.nanpercentile(full,10); scale=max(abs(float(scale)),1e-12)
        distances.append(wasserstein_distance(full,chosen)/scale)
    row={"method":result.method,"n_selected":len(ids),"representativeness_wasserstein_mean":float(np.mean(distances)) if distances else 0.0,"temporal_span_ratio":float((sorted_ids[-1]-sorted_ids[0])/full_span) if len(ids)>1 else 0.0,"adjacent_pair_fraction":float(np.mean(gaps<=1)) if len(gaps) else 1.0,"median_temporal_gap_pairs":float(np.median(gaps)) if len(gaps) else 0.0,"notes":" | ".join(result.notes)}
    if reliability_eval is not None:
        R=reliability_eval[pos]; c=np.sum(R,axis=0)
        row.update({"coverage_log_utility_per_cell":float(np.mean(np.log1p(c))),"coverage_q10":float(np.quantile(c,0.10)),"coverage_gini":_gini_nonnegative(c),"oracle_holdout_log_coverage":float(np.mean(np.log1p(c))),"oracle_holdout_q10":float(np.quantile(c,0.10)),"oracle_holdout_once_fraction":float(np.mean(c>=1))})
    return row


def _goodness_rank(df: pd.DataFrame, metrics: dict[str,str]) -> pd.DataFrame:
    out=df.copy(); G=[]; used=[]
    for c,direction in metrics.items():
        if c not in out.columns: continue
        x=out[c].to_numpy(float); finite=np.isfinite(x)
        if np.sum(finite)<2 or np.nanmax(x[finite])-np.nanmin(x[finite])<=1e-12: continue
        ranks=rankdata(x[finite],method="average"); p=(ranks-1.0)/max(np.sum(finite)-1,1)
        if direction=="min": p=1-p
        col=np.full(len(out),0.5); col[finite]=p; G.append(col); used.append(c)
    if not G:
        out["rank"]=np.arange(1,len(out)+1); out["max_regret"]=np.nan; out["pareto_front"]=False; return out
    G=np.column_stack(G); out["max_regret"]=np.max(1-G,axis=1); out["median_goodness"]=np.median(G,axis=1)
    pf=np.ones(len(out),dtype=bool)
    for i in range(len(out)):
        if np.any(np.all(G>=G[i],axis=1)&np.any(G>G[i],axis=1)): pf[i]=False
    out["pareto_front"]=pf
    order=np.lexsort((-out["median_goodness"].to_numpy(),out["max_regret"].to_numpy(),~pf)); ranks=np.empty(len(out),int); ranks[order]=np.arange(1,len(out)+1); out["rank"]=ranks; out["metrics_used"]=",".join(used)
    return out


def run_real_oracle_crossvalidation(pool: pd.DataFrame,reliability: np.ndarray,*,sample_sizes: list[int]=[3,5,7],folds:int=5,seeds:list[int]=[20260912,20260913,20260914,20260915,20260916],outdir:str|Path|None=None)->pd.DataFrame:
    metrics={"oracle_holdout_log_coverage":"max","oracle_holdout_q10":"max","oracle_holdout_once_fraction":"max","representativeness_wasserstein_mean":"min","temporal_span_ratio":"max","adjacent_pair_fraction":"min"}
    records=[]; cv=spatial_cv_folds(reliability.shape[1],folds)
    methods=["uniform_baseline","stratified_random_baseline","random_iid","temporal_quality_stratified","kennard_stone","kernel_herding","d_optimal","mmr_maximin","spatial_saturated_coverage","spatial_lower_tail","quality_facility_maximin"]
    stochastic={"random_iid","stratified_random_baseline"}
    for n in sample_sizes:
        if n>len(pool): continue
        for fold_id,(train_cells,test_cells) in enumerate(cv):
            Rtrain=reliability[:,train_cells]; Rtest=reliability[:,test_cells]
            for seed in seeds:
                scenario_id=f"N{n}_F{fold_id}_S{seed}"
                for method in methods:
                    effective_seed=seed if method in stochastic else seeds[0]
                    try:
                        result=run_advanced_selector(method,pool,n,seed=effective_seed,reliability=Rtrain,min_gap_pairs=1,target_fraction_of_n=0.25,lower_tail_fraction=0.10)
                        row=benchmark_result(pool,result,reliability_eval=Rtest); row.update({"sample_size":n,"fold":fold_id,"seed":seed,"scenario_id":scenario_id}); records.append(row)
                    except Exception as exc:
                        records.append({"method":method,"sample_size":n,"fold":fold_id,"seed":seed,"scenario_id":scenario_id,"error":repr(exc)})
    raw=pd.DataFrame(records); ranked=[]
    for scenario_id,g in raw.groupby("scenario_id"):
        valid=g[g["error"].isna()] if "error" in g.columns else g
        if len(valid)==0: continue
        r=_goodness_rank(valid,metrics); winner_rank=int(r["rank"].min()); r["scenario_winner"]=r["rank"]==winner_rank; ranked.append(r)
    result=pd.concat(ranked,ignore_index=True) if ranked else raw
    if outdir is not None:
        outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True); raw.to_csv(outdir/"real_oracle_cv_raw.csv",index=False); result.to_csv(outdir/"real_oracle_cv_ranked.csv",index=False)
        meta={"scope":"retrospective real-data algorithm sanity test","selection_cells":"training spatial cells only","evaluation_cells":"held-out spatial cells","cfd_used":False,"publication_warning":"Sparse historical PIVlab fields cannot select the final publication subset."}
        (outdir/"real_oracle_cv_meta.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return result
