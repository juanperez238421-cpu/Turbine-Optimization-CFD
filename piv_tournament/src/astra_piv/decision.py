from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd


METRIC_DIRECTIONS = {
    "coverage_log_utility_per_cell": "max",
    "coverage_q10": "max",
    "coverage_gini": "min",
    "quality_p10": "max",
    "quality_median": "max",
    "representativeness_wasserstein_mean": "min",
    "temporal_span_ratio": "max",
    "adjacent_pair_fraction": "min",
    "oracle_holdout_log_coverage": "max",
    "oracle_holdout_q10": "max",
    "oracle_holdout_once_fraction": "max",
}


def _rank_goodness(x: np.ndarray, direction: str) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    finite = np.isfinite(x)
    out = np.full(len(x), np.nan)
    if np.sum(finite) < 2:
        out[finite] = 0.5
        return out
    vals = x[finite]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(len(vals), float)
    ranks[order] = np.arange(len(vals))
    p = ranks / max(len(vals)-1, 1)
    if direction == "min":
        p = 1-p
    out[finite] = p
    return out


def monte_carlo_weight_space(table: pd.DataFrame, metrics: list[str], *, draws: int = 20000, seed: int = 20260912) -> pd.DataFrame:
    """Diagnostic only: probability of being best under unknown nonnegative metric weights."""
    metrics = [m for m in metrics if m in table.columns and m in METRIC_DIRECTIONS]
    if not metrics:
        raise ValueError("No usable metrics")
    G = np.column_stack([_rank_goodness(table[m].to_numpy(float), METRIC_DIRECTIONS[m]) for m in metrics])
    G = np.nan_to_num(G, nan=0.5)
    rng = np.random.default_rng(seed)
    weights = rng.dirichlet(np.ones(len(metrics)), size=draws)
    utility = G @ weights.T
    winners = np.argmax(utility, axis=0)
    counts = np.bincount(winners, minlength=len(table))
    out = table[["method"]].copy()
    out["weight_space_win_probability"] = counts / draws
    out["weight_space_mean_utility"] = np.mean(utility, axis=1)
    out["metrics_count"] = len(metrics)
    return out.sort_values("weight_space_win_probability", ascending=False).reset_index(drop=True)


def aggregate_scenarios(scenario_table: pd.DataFrame, *, winner_col: str = "scenario_winner") -> pd.DataFrame:
    required = {"scenario_id", "method", "rank", "pareto_front", "max_regret"}
    missing = required - set(scenario_table.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    rows = []
    n_scen = scenario_table["scenario_id"].nunique()
    for method, g in scenario_table.groupby("method"):
        rows.append({
            "method": method,
            "scenarios": int(g["scenario_id"].nunique()),
            "pareto_front_frequency": float(np.mean(g["pareto_front"].astype(float))),
            "rank_median": float(np.median(g["rank"])),
            "rank_q90": float(np.quantile(g["rank"], 0.90)),
            "max_regret_median": float(np.median(g["max_regret"])),
            "max_regret_q90": float(np.quantile(g["max_regret"], 0.90)),
            "scenario_win_frequency": float(np.mean(g[winner_col].astype(bool))) if winner_col in g else np.nan,
        })
    out = pd.DataFrame(rows)
    out["scenario_completeness"] = out["scenarios"] / max(n_scen, 1)
    return out.sort_values(["pareto_front_frequency", "rank_median", "max_regret_q90"], ascending=[False, True, True]).reset_index(drop=True)


def consensus_decision(aggregate: pd.DataFrame, weight_space: pd.DataFrame | None = None, *, min_scenario_completeness: float = 0.90, min_pareto_frequency: float = 0.60, min_rule_consensus_fraction: float = 0.80) -> dict:
    """Require strong agreement among independent decision lenses; returning no winner is valid."""
    tab = aggregate.copy()
    if weight_space is not None:
        tab = tab.merge(weight_space[["method", "weight_space_win_probability"]], on="method", how="left")
    else:
        tab["weight_space_win_probability"] = np.nan
    votes: list[str] = []

    def vote_max(col: str):
        if col in tab and np.any(np.isfinite(tab[col].to_numpy(float))):
            x = tab[col].to_numpy(float); best = np.nanmax(x)
            votes.extend(tab.loc[np.isclose(x, best, rtol=0, atol=1e-12), "method"].astype(str).tolist())

    def vote_min(col: str):
        if col in tab and np.any(np.isfinite(tab[col].to_numpy(float))):
            x = tab[col].to_numpy(float); best = np.nanmin(x)
            votes.extend(tab.loc[np.isclose(x, best, rtol=0, atol=1e-12), "method"].astype(str).tolist())

    vote_max("pareto_front_frequency")
    vote_min("rank_median")
    vote_min("max_regret_q90")
    vote_max("scenario_win_frequency")
    vote_max("weight_space_win_probability")
    if not votes:
        return {"status":"UNRESOLVED_NO_DECISION_INFORMATION","publication_selector":None,"numerical_candidate":None,"votes":{}}

    vc = pd.Series(votes).value_counts()
    candidate = str(vc.index[0]); candidate_votes = int(vc.iloc[0])
    n_rules = 5 if weight_space is not None else 4
    consensus_fraction = candidate_votes / n_rules
    row = tab[tab["method"] == candidate].iloc[0]
    passes = float(row["scenario_completeness"]) >= min_scenario_completeness and float(row["pareto_front_frequency"]) >= min_pareto_frequency and consensus_fraction >= min_rule_consensus_fraction
    if not passes:
        return {
            "status":"UNRESOLVED_DECISION_RULE_DISAGREEMENT","publication_selector":None,"numerical_candidate":None,
            "leading_method":candidate,"rule_consensus_fraction":consensus_fraction,"votes":vc.to_dict(),
            "reason":"Independent decision lenses do not agree strongly enough to name a robust selector.",
            "thresholds":{"min_scenario_completeness":min_scenario_completeness,"min_pareto_frequency":min_pareto_frequency,"min_rule_consensus_fraction":min_rule_consensus_fraction},
        }
    return {
        "status":"ROBUST_NUMERICAL_SELECTOR_CANDIDATE_REQUIRES_SCIENTIFIC_GATE","publication_selector":None,"numerical_candidate":candidate,
        "rule_consensus_fraction":consensus_fraction,"votes":vc.to_dict(),"candidate_metrics":row.to_dict(),
        "reason":"Independent decision lenses reach the configured consensus threshold.",
        "thresholds":{"min_scenario_completeness":min_scenario_completeness,"min_pareto_frequency":min_pareto_frequency,"min_rule_consensus_fraction":min_rule_consensus_fraction},
    }


def write_decision(decision: dict, path: str | Path) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(decision, indent=2, default=float), encoding="utf-8")
