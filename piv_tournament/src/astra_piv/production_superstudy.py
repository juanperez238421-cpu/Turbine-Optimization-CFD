from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from .advanced_selectors import ADVANCED_METHODS, run_advanced_selector
from .decision import aggregate_scenarios, monte_carlo_weight_space, consensus_decision
from .scientific_gate import EvidenceState, publication_gate
from .superstudy import benchmark_result


BASE_METHODS = (
    "legacy_control","uniform","stratified_random","quality_top","pareto_temporal",
    "cluster_medoids","farthest_point","facility_location","spatial_coverage_log",
    "qcrc_maximin","best_contiguous_window",
)

METHOD_FAMILY = {
    "legacy_control":"control","uniform":"baseline","stratified_random":"baseline","random_iid":"baseline",
    "uniform_baseline":"baseline","stratified_random_baseline":"baseline","best_contiguous_window":"baseline",
    "quality_top":"quality","temporal_quality_stratified":"quality","pareto_temporal":"hybrid",
    "cluster_medoids":"representative","farthest_point":"representative","kennard_stone":"representative",
    "kernel_herding":"representative","d_optimal":"representative","facility_location":"representative",
    "spatial_coverage_log":"spatial","spatial_saturated_coverage":"spatial","spatial_lower_tail":"spatial",
    "qcrc_maximin":"hybrid","mmr_maximin":"hybrid","quality_facility_maximin":"hybrid",
}

PRIMARY_HOLDOUT_METRICS = {
    "coverage_log_utility_per_cell":"max",
    "coverage_q10":"max",
    "coverage_gini":"min",
    "representativeness_wasserstein_mean":"min",
    "temporal_span_ratio":"max",
    "adjacent_pair_fraction":"min",
}


def quality_eligibility_mask(pool: pd.DataFrame, mad_multiplier: float = 4.0) -> tuple[np.ndarray,dict]:
    """Common PIV-correlation gate applied before methods compete."""
    cols=["coarse_pce_p10","coarse_ppr_p10","coarse_pce_median","coarse_ppr_median"]
    keep=np.ones(len(pool),dtype=bool); rules=[]
    for c in cols:
        if c not in pool.columns: continue
        x=pool[c].to_numpy(float); finite=np.isfinite(x)
        if np.sum(finite)<max(10,int(0.5*len(pool))): continue
        med=np.nanmedian(x); mad=1.4826*np.nanmedian(np.abs(x-med))
        if not np.isfinite(mad) or mad<=1e-12: continue
        threshold=med-mad_multiplier*mad; keep &= (~finite)|(x>=threshold)
        rules.append({"metric":c,"direction":">=","threshold":float(threshold)})
    return keep,{"mad_multiplier":float(mad_multiplier),"rules":rules,"survival_fraction":float(np.mean(keep)),"n_surviving":int(np.sum(keep)),"n_total":int(len(pool))}


def spatial_cell_folds(n_cells:int,k:int=5):
    idx=np.arange(n_cells); out=[]
    for f in range(k):
        test=idx[idx%k==f]; train=idx[idx%k!=f]; out.append((train,test))
    return out


def _run_base_selector(method,pool,n,cfg,reliability):
    from .selectors import run_selector
    return run_selector(method,pool,n,cfg.tournament,cfg.provenance,reliability=reliability)


def _all_methods(include_base=True):
    m=list(BASE_METHODS) if include_base else []
    m.extend(ADVANCED_METHODS)
    return list(dict.fromkeys(m))


def _rank_scenario(df:pd.DataFrame)->pd.DataFrame:
    out=df.copy(); G=[]; used=[]
    for c,direction in PRIMARY_HOLDOUT_METRICS.items():
        if c not in out.columns: continue
        x=out[c].to_numpy(float); finite=np.isfinite(x)
        if np.sum(finite)<2 or np.nanmax(x[finite])-np.nanmin(x[finite])<=1e-12: continue
        p=np.full(len(x),0.5); p[finite]=(rankdata(x[finite],method="average")-1.0)/max(np.sum(finite)-1,1)
        if direction=="min": p[finite]=1.0-p[finite]
        G.append(p); used.append(c)
    if not G:
        out["pareto_front"]=False; out["max_regret"]=np.nan; out["median_goodness"]=np.nan; out["rank"]=np.arange(1,len(out)+1); out["scenario_winner"]=False; out["decision_metrics"]=""; return out
    G=np.column_stack(G); pareto=np.ones(len(out),dtype=bool)
    for i in range(len(out)):
        if np.any(np.all(G>=G[i],axis=1)&np.any(G>G[i],axis=1)): pareto[i]=False
    out["pareto_front"]=pareto; out["max_regret"]=np.max(1.0-G,axis=1); out["median_goodness"]=np.median(G,axis=1)
    order=np.lexsort((-out["median_goodness"].to_numpy(),out["max_regret"].to_numpy(),~pareto)); ranks=np.empty(len(out),int); ranks[order]=np.arange(1,len(out)+1)
    out["rank"]=ranks; out["scenario_winner"]=ranks==1; out["decision_metrics"]=",".join(used); return out


def run_nested_spatial_cv_portfolio(pool:pd.DataFrame,reliability:np.ndarray,cfg:Any,*,sample_sizes:list[int],folds:int=5,seeds:list[int]=[20260912,20260913,20260914,20260915,20260916],methods:list[str]|None=None,quality_gate_mad:float=4.0,spatial_target_fraction_of_n:float=0.25,spatial_lower_tail_fraction:float=0.10,ablation_id:str="base",include_base_methods:bool=True):
    if reliability.ndim!=2 or reliability.shape[0]!=len(pool): raise ValueError("reliability must align with pool rows")
    keep,gate_meta=quality_eligibility_mask(pool,quality_gate_mad); eligible_pool=pool.loc[keep].reset_index(drop=True); eligible_R=reliability[keep]
    methods=methods or _all_methods(include_base_methods); scenarios=[]; spatial_folds=spatial_cell_folds(eligible_R.shape[1],folds); stochastic={"stratified_random","random_iid","stratified_random_baseline"}
    for n in sample_sizes:
        if n>len(eligible_pool): continue
        for fold_id,(train_cells,test_cells) in enumerate(spatial_folds):
            Rtrain=eligible_R[:,train_cells]; Rtest=eligible_R[:,test_cells]
            for seed in seeds:
                scenario_id=f"{ablation_id}|N{n}|F{fold_id}|S{seed}"; rows=[]
                for method in methods:
                    if method=="legacy_control" and n!=250: continue
                    effective_seed=seed if method in stochastic else seeds[0]
                    try:
                        if method in BASE_METHODS: result=_run_base_selector(method,eligible_pool,n,cfg,Rtrain)
                        else: result=run_advanced_selector(method,eligible_pool,n,seed=effective_seed,reliability=Rtrain,min_gap_pairs=getattr(cfg.tournament,"minimum_temporal_gap_pairs",1),target_fraction_of_n=spatial_target_fraction_of_n,lower_tail_fraction=spatial_lower_tail_fraction)
                        row=benchmark_result(eligible_pool,result,Rtest); row.update({"ablation_id":ablation_id,"scenario_id":scenario_id,"sample_size":int(n),"spatial_fold":int(fold_id),"seed":int(seed),"method_family":METHOD_FAMILY.get(method,"other"),"quality_gate_survival_fraction":gate_meta["survival_fraction"]})
                    except Exception as exc:
                        row={"method":method,"method_family":METHOD_FAMILY.get(method,"other"),"ablation_id":ablation_id,"scenario_id":scenario_id,"sample_size":int(n),"spatial_fold":int(fold_id),"seed":int(seed),"error":f"{type(exc).__name__}: {exc}"}
                    rows.append(row)
                sdf=pd.DataFrame(rows); valid=sdf[sdf["error"].isna()].copy() if "error" in sdf.columns else sdf
                if len(valid): scenarios.append(_rank_scenario(valid))
    ranked=pd.concat(scenarios,ignore_index=True) if scenarios else pd.DataFrame()
    meta={"ablation_id":ablation_id,"quality_gate":gate_meta,"n_eligible_pairs":int(len(eligible_pool)),"spatial_folds":int(folds),"seeds":list(map(int,seeds)),"sample_sizes_requested":list(map(int,sample_sizes)),"methods_requested":methods,"decision_metrics":PRIMARY_HOLDOUT_METRICS,"selection_evaluation_separation":"Spatial selectors see only training reliability cells. Ranking uses held-out spatial cells plus temporal/population representativeness. CFD is not used."}
    return ranked,meta


def selection_rank_stability(ranked:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for method,g in ranked.groupby("method"):
        rows.append({"method":method,"rank_median":float(np.median(g["rank"])),"rank_iqr":float(np.quantile(g["rank"],0.75)-np.quantile(g["rank"],0.25)),"winner_frequency":float(np.mean(g["scenario_winner"])),"pareto_front_frequency":float(np.mean(g["pareto_front"])),"scenario_count":int(g["scenario_id"].nunique())})
    return pd.DataFrame(rows).sort_values(["pareto_front_frequency","rank_median"],ascending=[False,True]).reset_index(drop=True)


def finalize_superstudy_decision(ranked:pd.DataFrame,*,evidence_state:EvidenceState,output_dir:str|Path|None=None)->dict:
    agg=aggregate_scenarios(ranked); metric_cols=[c for c in PRIMARY_HOLDOUT_METRICS if c in ranked.columns]
    med=ranked.groupby("method",as_index=False)[metric_cols].median(numeric_only=True); ws=monte_carlo_weight_space(med,metric_cols,draws=20000,seed=20260912)
    numerical=consensus_decision(agg,ws); candidate=numerical.get("numerical_candidate"); gate=publication_gate(evidence_state,candidate)
    result={"numerical_decision":numerical,"scientific_publication_gate":gate,"method_aggregate":agg.to_dict(orient="records"),"weight_space":ws.to_dict(orient="records"),"rule":"Numerical tournament and scientific evidence gate are separate. No selector reaches manuscript freeze unless BOTH pass."}
    if output_dir is not None:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); ranked.to_csv(out/"superstudy_ranked_scenarios.csv",index=False); agg.to_csv(out/"superstudy_method_aggregate.csv",index=False); ws.to_csv(out/"superstudy_weight_space.csv",index=False); selection_rank_stability(ranked).to_csv(out/"superstudy_rank_stability.csv",index=False); (out/"ASTRA_SUPERSTUDY_DECISION.json").write_text(json.dumps(result,indent=2,default=float),encoding="utf-8")
    return result
