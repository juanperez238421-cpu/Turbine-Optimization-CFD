from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from .benchmark import benchmark_selections
from .config import TournamentConfig, ProvenanceConfig
from .selectors import run_selector


def temporal_block_jackknife(pool: pd.DataFrame, methods: Iterable[str], n: int, cfg: TournamentConfig, provenance: ProvenanceConfig, reliability: np.ndarray | None = None, blocks: int = 5) -> tuple[pd.DataFrame, dict]:
    """Leave-one-temporal-block-out robustness test using only experimental data."""
    pool = pool.sort_values("pair_index").reset_index(drop=True); methods = list(methods)
    if len(pool) < max(n + blocks, 2*n):
        return pd.DataFrame(), {"status": "UNRESOLVED_POOL_TOO_SMALL_FOR_TEMPORAL_JACKKNIFE", "pool_size": int(len(pool)), "n": int(n), "blocks": int(blocks)}
    full = {}
    for method in methods:
        if method == "legacy_control" and n != 250: continue
        try: full[method] = run_selector(method, pool, n, cfg, provenance, reliability=reliability)
        except Exception: continue
    block_indices = np.array_split(np.arange(len(pool)), blocks); rows=[]; winner_by_block=[]
    for b, held in enumerate(block_indices):
        keep_mask=np.ones(len(pool),dtype=bool); keep_mask[held]=False
        sub=pool.loc[keep_mask].reset_index(drop=True); subR=reliability[keep_mask] if reliability is not None else None
        if len(sub)<n: continue
        block_results=[]
        for method,original in full.items():
            try: rerun=run_selector(method,sub,n,cfg,provenance,reliability=subR)
            except Exception: continue
            block_results.append(rerun); held_ids=set(pool.iloc[held]["pair_index"].astype(int)); original_available=set(map(int,original.pair_indices))-held_ids; rerun_ids=set(map(int,rerun.pair_indices)); inter=original_available&rerun_ids; union=original_available|rerun_ids
            rows.append({"block":b,"heldout_start_pair":int(pool.iloc[held[0]]["pair_index"]),"heldout_end_pair":int(pool.iloc[held[-1]]["pair_index"]),"method":method,"n":int(n),"original_available_after_holdout":len(original_available),"intersection_count":len(inter),"retention_fraction":float(len(inter)/max(len(original_available),1)),"jaccard":float(len(inter)/max(len(union),1))})
        _,meta=benchmark_selections(sub,block_results,reliability=subR); winner_by_block.append({"block":b,"status":meta.get("status"),"winner":meta.get("provisional_winner"),"numerical_leader":meta.get("numerical_leader_before_evidence_gate")})
    df=pd.DataFrame(rows)
    aggregate=df.groupby("method",as_index=False).agg(retention_median=("retention_fraction","median"),retention_min=("retention_fraction","min"),jaccard_median=("jaccard","median"),jaccard_min=("jaccard","min")).sort_values(["retention_median","jaccard_median"],ascending=False) if len(df) else pd.DataFrame()
    valid=[x["winner"] for x in winner_by_block if x.get("winner")]; winner_consensus=None; winner_fraction=0.0
    if valid:
        counts=pd.Series(valid).value_counts(); winner_consensus=str(counts.index[0]); winner_fraction=float(counts.iloc[0]/len(valid))
    meta={"status":"TEMPORAL_BLOCK_JACKKNIFE_COMPLETE" if len(df) else "UNRESOLVED_NO_JACKKNIFE_RESULTS","pool_size":int(len(pool)),"n":int(n),"blocks":int(blocks),"winner_by_block":winner_by_block,"winner_consensus":winner_consensus,"winner_consensus_fraction":winner_fraction,"interpretation":"Retention/Jaccard quantify selector sensitivity to removal of contiguous experimental time blocks; they are not CFD validation metrics.","aggregate":aggregate.to_dict(orient="records")}
    return df,meta
