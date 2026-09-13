from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance, rankdata

from .selectors import SelectionResult, available_state_features, quality_score


METRIC_DIRECTIONS = {
    "quality_p10": "max",
    "quality_median": "max",
    "representativeness_wasserstein_mean": "min",
    "temporal_span_ratio": "max",
    "adjacent_pair_fraction": "min",
    "coverage_log_utility_per_cell": "max",
    "coverage_q10": "max",
    "coverage_gini": "min",
}

PIV_NATIVE_QUALITY_COLUMNS = {
    "coarse_pce_p10",
    "coarse_ppr_p10",
    "coarse_pce_median",
    "coarse_ppr_median",
    "coarse_disp_median_px",
    "coarse_disp_p90_px",
}


def _gini_nonnegative(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    x = np.clip(x, 0, None)
    if np.allclose(x, 0):
        return 0.0
    x = np.sort(x)
    n = len(x)
    return float((2*np.sum((np.arange(1,n+1))*x)/(n*np.sum(x))) - (n+1)/n)


def _selection_positions(pool: pd.DataFrame, pair_ids: np.ndarray) -> np.ndarray:
    mapping = {int(pid): i for i, pid in enumerate(pool["pair_index"].astype(int))}
    missing = [int(pid) for pid in pair_ids if int(pid) not in mapping]
    if missing:
        raise KeyError(f"Selected pair IDs not in pool: {missing[:20]}")
    return np.array([mapping[int(pid)] for pid in pair_ids], dtype=int)


def evaluate_selection(pool: pd.DataFrame, selection: SelectionResult, reliability: np.ndarray | None = None, state_features: list[str] | None = None) -> dict:
    ids = np.asarray(selection.pair_indices, dtype=int)
    if len(ids) == 0:
        return {"method": selection.method, "n_requested": selection.n_requested, "n_selected": 0, "valid_evaluation": False}
    pos = _selection_positions(pool, ids)
    sub = pool.iloc[pos]
    q, _ = quality_score(pool)
    qsel = q[pos]
    state_features = state_features or available_state_features(pool)
    wd = []
    for c in state_features:
        full = pool[c].to_numpy(float); chosen = sub[c].to_numpy(float)
        full = full[np.isfinite(full)]; chosen = chosen[np.isfinite(chosen)]
        if len(full) and len(chosen):
            scale = np.nanpercentile(full, 90) - np.nanpercentile(full, 10)
            if not np.isfinite(scale) or abs(scale) < 1e-12:
                scale = np.nanstd(full)
            scale = max(float(abs(scale)), 1e-12)
            wd.append(wasserstein_distance(full, chosen) / scale)
    sorted_ids = np.sort(ids)
    gaps = np.diff(sorted_ids)
    full_span = max(int(pool["pair_index"].max()) - int(pool["pair_index"].min()), 1)
    temporal_span = (int(sorted_ids[-1]) - int(sorted_ids[0])) / full_span if len(sorted_ids) > 1 else 0.0
    adjacent_fraction = float(np.mean(gaps <= 1)) if len(gaps) else 1.0
    coverage_log = np.nan; coverage_q10 = np.nan; coverage_gini = np.nan
    if reliability is not None:
        if reliability.shape[0] != len(pool):
            raise ValueError("Reliability rows must align with pool rows")
        R = np.nan_to_num(reliability[pos], nan=0.0, posinf=1.0, neginf=0.0)
        coverage = np.sum(R, axis=0)
        coverage_log = float(np.mean(np.log1p(coverage)))
        coverage_q10 = float(np.quantile(coverage, 0.10))
        coverage_gini = _gini_nonnegative(coverage)
    return {
        "method": selection.method,
        "n_requested": int(selection.n_requested),
        "n_selected": int(len(ids)),
        "valid_evaluation": bool(len(ids) == selection.n_requested or selection.method == "legacy_control"),
        "quality_p10": float(np.quantile(qsel, 0.10)),
        "quality_median": float(np.median(qsel)),
        "representativeness_wasserstein_mean": float(np.mean(wd)) if wd else np.nan,
        "temporal_span_ratio": float(temporal_span),
        "adjacent_pair_fraction": adjacent_fraction,
        "median_temporal_gap_pairs": float(np.median(gaps)) if len(gaps) else 0.0,
        "coverage_log_utility_per_cell": coverage_log,
        "coverage_q10": coverage_q10,
        "coverage_gini": coverage_gini,
        "state_feature_count": len(state_features),
        "notes": " | ".join(selection.notes),
    }


def _pareto_layers(df: pd.DataFrame, metrics: list[str]) -> np.ndarray:
    vals = []
    for c in metrics:
        x = df[c].to_numpy(float)
        if METRIC_DIRECTIONS[c] == "max":
            finite = x[np.isfinite(x)]; worst = np.min(finite) if len(finite) else 0.0; x = np.where(np.isfinite(x), x, worst)
        else:
            finite = x[np.isfinite(x)]; worst = np.max(finite) if len(finite) else 1.0; x = np.where(np.isfinite(x), -x, -worst)
        vals.append(x)
    V = np.column_stack(vals)
    remaining = np.arange(len(df)); layers = np.full(len(df), -1, dtype=int); layer = 0
    while len(remaining):
        front = []
        for i in remaining:
            vi = V[i]; dominates_i = False
            for j in remaining:
                if j == i: continue
                vj = V[j]
                if np.all(vj >= vi) and np.any(vj > vi):
                    dominates_i = True; break
            if not dominates_i: front.append(i)
        front = np.array(front, dtype=int); layers[front] = layer
        remaining = remaining[~np.isin(remaining, front)]; layer += 1
    return layers


def _normalized_goodness(df: pd.DataFrame, c: str) -> np.ndarray:
    x = df[c].to_numpy(float); finite = np.isfinite(x); out = np.zeros(len(x), dtype=float)
    if np.sum(finite) <= 1:
        out[:] = 0.5; return out
    ranks = rankdata(x[finite], method="average"); p = (ranks-1)/max(len(ranks)-1, 1)
    if METRIC_DIRECTIONS[c] == "min": p = 1-p
    out[finite] = p
    return out


def _metric_has_information(df: pd.DataFrame, c: str, tol: float = 1e-12) -> bool:
    if c not in df.columns: return False
    x = df[c].to_numpy(float); finite = x[np.isfinite(x)]
    if len(finite) < 2: return False
    return bool(np.nanmax(finite) - np.nanmin(finite) > tol)


def _evidence_adequacy(pool: pd.DataFrame, reliability: np.ndarray | None) -> dict:
    piv_quality_cols = [c for c in PIV_NATIVE_QUALITY_COLUMNS if c in pool.columns and np.sum(np.isfinite(pool[c].to_numpy(float))) >= 20 and np.nanstd(pool[c].to_numpy(float)) > 1e-12]
    has_spatial = reliability is not None and reliability.ndim == 2 and reliability.shape[0] == len(pool) and reliability.shape[1] > 0 and np.any(np.isfinite(reliability))
    return {"piv_native_quality_columns": piv_quality_cols, "has_piv_native_quality": bool(piv_quality_cols), "has_spatial_reliability": bool(has_spatial), "has_population_state_features": bool(available_state_features(pool))}


def benchmark_selections(pool: pd.DataFrame, selections: Iterable[SelectionResult], reliability: np.ndarray | None = None) -> tuple[pd.DataFrame, dict]:
    selections = list(selections)
    rows = [evaluate_selection(pool, s, reliability=reliability) for s in selections]
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df, {"status": "NO_SELECTIONS"}
    metrics = [c for c in METRIC_DIRECTIONS if _metric_has_information(df, c)]
    adequacy = _evidence_adequacy(pool, reliability)
    if metrics:
        df["pareto_layer"] = _pareto_layers(df, metrics)
        goodness = np.column_stack([_normalized_goodness(df, c) for c in metrics])
        df["max_regret"] = np.max(1.0-goodness, axis=1)
        df["median_goodness"] = np.median(goodness, axis=1)
        front0 = df["pareto_layer"] == 0
        eligible = df[front0 & df["valid_evaluation"]].copy()
        if len(eligible):
            winner_idx = eligible.sort_values(["max_regret", "median_goodness"], ascending=[True, False]).index[0]
            numerical_winner = str(df.loc[winner_idx, "method"])
        else:
            numerical_winner = None
    else:
        df["pareto_layer"] = -1; df["max_regret"] = np.nan; df["median_goodness"] = np.nan; numerical_winner = None
    if not metrics:
        winner = None; status = "UNRESOLVED_INSUFFICIENT_METRICS"
    elif numerical_winner is None:
        winner = None; status = "UNRESOLVED_NO_VALID_PARETO_FRONT"
    elif not adequacy["has_piv_native_quality"]:
        winner = None; status = "DESCRIPTIVE_ONLY_NO_PIV_NATIVE_QUALITY"
    elif not adequacy["has_spatial_reliability"]:
        winner = numerical_winner; status = "PROVISIONAL_WINNER_PARTIAL_EVIDENCE_NO_SPATIAL_RELIABILITY"
    else:
        winner = numerical_winner; status = "PROVISIONAL_WINNER_REQUIRES_ROBUSTNESS"
    meta = {
        "status": status,
        "provisional_winner": winner,
        "numerical_leader_before_evidence_gate": numerical_winner,
        "metrics_used": metrics,
        "directions": {c: METRIC_DIRECTIONS[c] for c in metrics},
        "evidence_adequacy": adequacy,
        "selection_rule": "Pareto front first; minimax normalized regret within front. Constant metrics are excluded. No CFD metrics allowed.",
        "warning": "A publication winner requires PIV-native quality evidence, spatial reliability, and robustness across N/ablations/temporal perturbations.",
    }
    return df.sort_values(["pareto_layer", "max_regret", "method"], na_position="last"), meta
