from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler

from .config import TournamentConfig, ProvenanceConfig


PRIMARY_MAXIMIZE = [
    "coarse_pce_p10",
    "coarse_ppr_p10",
    "coarse_pce_median",
    "coarse_ppr_median",
    "phase_response",
    "normalized_frame_correlation",
]
PRIMARY_MINIMIZE = [
    "pair_saturated_fraction_ge250_max",
    "pair_large_bright_component_area_fraction_proxy_max",
    "pair_optical_dark_region_cx_proxy_jump",
    "pair_optical_dark_region_cy_proxy_jump",
]
STATE_FEATURE_CANDIDATES = [
    "phase_dx_original_px",
    "phase_dy_original_px",
    "phase_shift_magnitude_original_px",
    "normalized_interframe_mad",
    "pair_particle_like_blob_density_proxy_mean",
    "pair_optical_dark_region_fraction_proxy_mean",
    "pair_optical_dark_region_cx_proxy_mean",
    "pair_optical_dark_region_cy_proxy_mean",
    "coarse_disp_median_px",
    "coarse_disp_p90_px",
]


@dataclass
class SelectionResult:
    method: str
    n_requested: int
    pair_indices: np.ndarray
    notes: list[str]


def percentile_score(x: np.ndarray, maximize: bool = True) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    finite = np.isfinite(x)
    out = np.full(len(x), 0.5, dtype=float)
    if np.sum(finite) <= 1:
        return out
    ranks = rankdata(x[finite], method="average")
    p = (ranks - 1.0) / max(len(ranks)-1.0, 1.0)
    if not maximize:
        p = 1.0 - p
    out[finite] = p
    return out


def available_state_features(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in STATE_FEATURE_CANDIDATES:
        if c in df.columns:
            x = df[c].to_numpy(float)
            if np.sum(np.isfinite(x)) >= max(10, int(0.5*len(x))) and np.nanstd(x) > 1e-12:
                cols.append(c)
    if not cols:
        numeric = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c not in {"pair_index", "frame_a", "frame_b", "time_a_s", "time_b_s"}
        ]
        cols = [c for c in numeric if np.nanstd(df[c].to_numpy(float)) > 1e-12][:6]
    return cols


def state_matrix(df: pd.DataFrame, columns: list[str] | None = None) -> tuple[np.ndarray, list[str]]:
    columns = columns or available_state_features(df)
    X = df[columns].to_numpy(float)
    for j in range(X.shape[1]):
        col = X[:, j]
        med = np.nanmedian(col)
        col[~np.isfinite(col)] = med if np.isfinite(med) else 0.0
        X[:, j] = col
    X = RobustScaler(quantile_range=(10, 90)).fit_transform(X)
    return X, columns


def quality_score(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Comparator score based on rank aggregation, not a publication acceptance rule."""
    parts = []
    used = []
    for c in PRIMARY_MAXIMIZE:
        if c in df.columns and np.nanstd(df[c].to_numpy(float)) > 1e-12:
            parts.append(percentile_score(df[c].to_numpy(float), maximize=True))
            used.append(f"+{c}")
    for c in PRIMARY_MINIMIZE:
        if c in df.columns and np.nanstd(df[c].to_numpy(float)) > 1e-12:
            parts.append(percentile_score(df[c].to_numpy(float), maximize=False))
            used.append(f"-{c}")
    if not parts:
        return np.full(len(df), 0.5), []
    return np.median(np.column_stack(parts), axis=1), used


def robust_quality_gate(df: pd.DataFrame, mad_multiplier: float = 4.0) -> tuple[np.ndarray, list[str]]:
    """Reject only extreme empirical outliers in primary QA metrics."""
    keep = np.ones(len(df), dtype=bool)
    rules = []
    for c in PRIMARY_MAXIMIZE:
        if c not in df.columns:
            continue
        x = df[c].to_numpy(float)
        finite = np.isfinite(x)
        if np.sum(finite) < 20:
            continue
        med = np.nanmedian(x)
        mad = 1.4826*np.nanmedian(np.abs(x-med))
        if mad <= 1e-12:
            continue
        threshold = med - mad_multiplier*mad
        keep &= (~finite) | (x >= threshold)
        rules.append(f"{c} >= median-{mad_multiplier:g}MAD ({threshold:.6g})")
    for c in PRIMARY_MINIMIZE:
        if c not in df.columns:
            continue
        x = df[c].to_numpy(float)
        finite = np.isfinite(x)
        if np.sum(finite) < 20:
            continue
        med = np.nanmedian(x)
        mad = 1.4826*np.nanmedian(np.abs(x-med))
        if mad <= 1e-12:
            continue
        threshold = med + mad_multiplier*mad
        keep &= (~finite) | (x <= threshold)
        rules.append(f"{c} <= median+{mad_multiplier:g}MAD ({threshold:.6g})")
    return keep, rules


def _enforce_gap(candidate_positions: Iterable[int], pair_ids: np.ndarray, n: int, min_gap: int) -> np.ndarray:
    selected_pos = []
    selected_ids = []
    for pos in candidate_positions:
        pid = int(pair_ids[pos])
        if all(abs(pid - other) >= min_gap for other in selected_ids):
            selected_pos.append(int(pos))
            selected_ids.append(pid)
            if len(selected_pos) == n:
                break
    return np.asarray(selected_pos, dtype=int)


def select_uniform(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    if n >= len(df):
        return SelectionResult("uniform", n, df["pair_index"].to_numpy(int), ["n >= pool size"])
    pos = np.unique(np.round(np.linspace(0, len(df)-1, n)).astype(int))
    if len(pos) < n:
        extra = [i for i in range(len(df)) if i not in set(pos)]
        pos = np.r_[pos, extra[: n-len(pos)]]
    return SelectionResult("uniform", n, df.iloc[np.sort(pos)]["pair_index"].to_numpy(int), [])


def select_stratified_random(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    rng = np.random.default_rng(cfg.random_seed)
    if n >= len(df):
        ids = df["pair_index"].to_numpy(int)
    else:
        edges = np.linspace(0, len(df), n+1).astype(int)
        pos = []
        for a, b in zip(edges[:-1], edges[1:]):
            if b <= a:
                continue
            pos.append(int(rng.integers(a, b)))
        ids = df.iloc[np.sort(np.asarray(pos, int))]["pair_index"].to_numpy(int)
    return SelectionResult("stratified_random", n, ids, [f"seed={cfg.random_seed}"])


def select_quality_top(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    q, used = quality_score(df)
    order = np.argsort(-q)
    pos = _enforce_gap(order, df["pair_index"].to_numpy(int), n, cfg.minimum_temporal_gap_pairs)
    if len(pos) < n:
        missing = [i for i in order if i not in set(pos)]
        pos = np.r_[pos, missing[: n-len(pos)]]
    return SelectionResult("quality_top", n, df.iloc[pos]["pair_index"].to_numpy(int), ["median percentile-rank comparator", *used])


def _pareto_mask(values: np.ndarray) -> np.ndarray:
    n = len(values)
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        if not mask[i]:
            continue
        dominated = np.all(values >= values[i], axis=1) & np.any(values > values[i], axis=1)
        if np.any(dominated):
            mask[i] = False
    return mask


def select_pareto_temporal(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    criteria = []
    labels = []
    for c in PRIMARY_MAXIMIZE:
        if c in df.columns and np.nanstd(df[c].to_numpy(float)) > 1e-12:
            criteria.append(percentile_score(df[c].to_numpy(float), True)); labels.append("+"+c)
    for c in PRIMARY_MINIMIZE:
        if c in df.columns and np.nanstd(df[c].to_numpy(float)) > 1e-12:
            criteria.append(percentile_score(df[c].to_numpy(float), False)); labels.append("-"+c)
    if not criteria:
        return select_uniform(df, n, cfg)
    C = np.column_stack(criteria)
    remaining = np.arange(len(df))
    layers = []
    while len(remaining) and sum(len(x) for x in layers) < n:
        m = _pareto_mask(C[remaining])
        layer = remaining[m]
        layers.append(layer)
        remaining = remaining[~m]
    selected = []
    pair_ids = df["pair_index"].to_numpy(int)
    for layer in layers:
        candidates = list(map(int, layer))
        while candidates and len(selected) < n:
            if not selected:
                center = 0.5*(pair_ids.min()+pair_ids.max())
                j = max(candidates, key=lambda p: abs(pair_ids[p]-center))
            else:
                j = max(candidates, key=lambda p: min(abs(pair_ids[p]-pair_ids[s]) for s in selected))
            if all(abs(pair_ids[j]-pair_ids[s]) >= cfg.minimum_temporal_gap_pairs for s in selected):
                selected.append(j)
            candidates.remove(j)
        if len(selected) >= n:
            break
    if len(selected) < n:
        rest = [i for i in range(len(df)) if i not in set(selected)]
        selected.extend(rest[: n-len(selected)])
    return SelectionResult("pareto_temporal", n, pair_ids[np.asarray(selected[:n], int)], ["Pareto layers + temporal spread", *labels])


def select_cluster_medoids(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    X, cols = state_matrix(df)
    if n >= len(df):
        return SelectionResult("cluster_medoids", n, df["pair_index"].to_numpy(int), cols)
    km = KMeans(n_clusters=n, random_state=cfg.random_seed, n_init=10)
    labels = km.fit_predict(X)
    chosen = []
    for k in range(n):
        idx = np.flatnonzero(labels == k)
        if len(idx) == 0:
            continue
        d = np.sum((X[idx] - km.cluster_centers_[k])**2, axis=1)
        chosen.append(int(idx[int(np.argmin(d))]))
    if len(chosen) < n:
        rest = [i for i in range(len(df)) if i not in set(chosen)]
        chosen.extend(rest[: n-len(chosen)])
    ids = df.iloc[np.sort(chosen[:n])]["pair_index"].to_numpy(int)
    return SelectionResult("cluster_medoids", n, ids, ["KMeans clusters; actual nearest observation retained", *cols])


def select_farthest_point(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    X, cols = state_matrix(df)
    if n >= len(df):
        return SelectionResult("farthest_point", n, df["pair_index"].to_numpy(int), cols)
    center = np.median(X, axis=0)
    first = int(np.argmin(np.sum((X-center)**2, axis=1)))
    selected = [first]
    min_d2 = np.sum((X-X[first])**2, axis=1)
    min_d2[first] = -np.inf
    for _ in range(1, n):
        j = int(np.argmax(min_d2))
        selected.append(j)
        d2 = np.sum((X-X[j])**2, axis=1)
        min_d2 = np.minimum(min_d2, d2)
        min_d2[selected] = -np.inf
    ids = df.iloc[np.sort(selected)]["pair_index"].to_numpy(int)
    return SelectionResult("farthest_point", n, ids, ["greedy k-center in robust-scaled state space", *cols])


def _candidate_reduce(df: pd.DataFrame, X: np.ndarray, limit: int) -> np.ndarray:
    if len(df) <= limit:
        return np.arange(len(df))
    return np.unique(np.round(np.linspace(0, len(df)-1, limit)).astype(int))


def select_facility_location(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    X, cols = state_matrix(df)
    reduced = _candidate_reduce(df, X, cfg.candidate_pool_limit_for_pairwise_methods)
    XR = X[reduced]
    D = cdist(XR, XR)
    positive = D[D > 0]
    sigma = float(np.median(positive)) if len(positive) else 1.0
    S = np.exp(-(D/max(sigma, 1e-12))**2).astype(np.float32)
    best = np.zeros(len(XR), dtype=np.float32)
    selected_r = []
    available = np.ones(len(XR), dtype=bool)
    for _ in range(min(n, len(XR))):
        gains = np.sum(np.maximum(best[:, None], S) - best[:, None], axis=0)
        gains[~available] = -np.inf
        j = int(np.argmax(gains))
        selected_r.append(j)
        best = np.maximum(best, S[:, j])
        available[j] = False
    chosen = reduced[np.asarray(selected_r, int)]
    if len(chosen) < n:
        rest = [i for i in range(len(df)) if i not in set(chosen)]
        chosen = np.r_[chosen, rest[: n-len(chosen)]]
    ids = df.iloc[np.sort(chosen[:n])]["pair_index"].to_numpy(int)
    return SelectionResult("facility_location", n, ids, [f"candidate_limit={len(reduced)}", *cols])


def _coverage_greedy(reliability: np.ndarray, n: int) -> list[int]:
    R = np.nan_to_num(np.asarray(reliability, dtype=float), nan=0.0, posinf=1.0, neginf=0.0)
    coverage = np.zeros(R.shape[1], dtype=float)
    selected = []
    available = np.ones(R.shape[0], dtype=bool)
    for _ in range(min(n, len(R))):
        gains = np.sum(np.log1p(coverage[None, :] + R) - np.log1p(coverage[None, :]), axis=1)
        gains[~available] = -np.inf
        j = int(np.argmax(gains))
        selected.append(j)
        coverage += R[j]
        available[j] = False
    return selected


def select_spatial_coverage_log(df: pd.DataFrame, n: int, cfg: TournamentConfig, reliability: np.ndarray | None) -> SelectionResult:
    if reliability is None:
        r = select_facility_location(df, n, cfg)
        r.method = "spatial_coverage_log_fallback_facility"
        r.notes.insert(0, "No spatial reliability map supplied")
        return r
    if reliability.shape[0] != len(df):
        raise ValueError("Reliability rows must align with selection pool rows")
    chosen = _coverage_greedy(reliability, n)
    ids = df.iloc[np.sort(chosen)]["pair_index"].to_numpy(int)
    return SelectionResult("spatial_coverage_log", n, ids, ["maximize sum(log1p(cumulative spatial reliability))"])


def _maximin_rank(columns: list[np.ndarray]) -> np.ndarray:
    scores = [percentile_score(np.asarray(c), maximize=True) for c in columns]
    return np.min(np.column_stack(scores), axis=1)


def select_qcrc_maximin(df: pd.DataFrame, n: int, cfg: TournamentConfig, reliability: np.ndarray | None) -> SelectionResult:
    """Quality-Constrained Representative Coverage (QCRC), independent of CFD."""
    keep, gate_rules = robust_quality_gate(df, cfg.quality_gate_mad_multiplier)
    if np.sum(keep) < n:
        keep[:] = True
        gate_rules.append("Gate relaxed because fewer than N candidates survived.")
    base_pos = np.flatnonzero(keep)
    sub = df.iloc[base_pos].reset_index(drop=True)
    X, cols = state_matrix(sub)
    pair_ids = sub["pair_index"].to_numpy(int)
    R = reliability[base_pos] if reliability is not None else None
    ref_idx = np.unique(np.round(np.linspace(0, len(sub)-1, min(1000, len(sub)))).astype(int))
    Xref = X[ref_idx]
    D = cdist(Xref, X)
    posD = D[D > 0]
    sigma = float(np.median(posD)) if len(posD) else 1.0
    Sim = np.exp(-(D/max(sigma, 1e-12))**2).astype(np.float32)
    facility_best = np.zeros(len(Xref), dtype=np.float32)
    spatial_cov = np.zeros(R.shape[1], dtype=float) if R is not None else None
    selected = []
    available = np.ones(len(sub), dtype=bool)
    for step in range(min(n, len(sub))):
        facility_gain = np.sum(np.maximum(facility_best[:, None], Sim) - facility_best[:, None], axis=0)
        if R is not None:
            coverage_gain = np.sum(np.log1p(spatial_cov[None, :] + R) - np.log1p(spatial_cov[None, :]), axis=1)
        else:
            coverage_gain = facility_gain.copy()
        if selected:
            temporal_gain = np.array([min(abs(pid - pair_ids[s]) for s in selected) for pid in pair_ids], dtype=float)
        else:
            mid = 0.5*(pair_ids.min()+pair_ids.max())
            temporal_gain = np.abs(pair_ids-mid)
        compromise = _maximin_rank([coverage_gain, facility_gain, temporal_gain])
        compromise[~available] = -np.inf
        if selected and cfg.minimum_temporal_gap_pairs > 1:
            invalid_gap = np.array([any(abs(pid-pair_ids[s]) < cfg.minimum_temporal_gap_pairs for s in selected) for pid in pair_ids])
            allowed = available & (~invalid_gap)
            if np.any(allowed):
                compromise[invalid_gap] = -np.inf
        j = int(np.argmax(compromise))
        selected.append(j)
        available[j] = False
        facility_best = np.maximum(facility_best, Sim[:, j])
        if R is not None:
            spatial_cov += np.nan_to_num(R[j], nan=0.0)
    chosen_global = base_pos[np.asarray(selected, int)]
    ids = df.iloc[np.sort(chosen_global)]["pair_index"].to_numpy(int)
    return SelectionResult("qcrc_maximin", n, ids, ["robust empirical quality gate", *gate_rules, "maximin coverage/representativeness/temporal spread", *cols])


def select_best_contiguous_window(df: pd.DataFrame, n: int, cfg: TournamentConfig) -> SelectionResult:
    if n >= len(df):
        return SelectionResult("best_contiguous_window", n, df["pair_index"].to_numpy(int), ["n >= pool size"])
    q, used = quality_score(df)
    X, cols = state_matrix(df)
    pool_center = np.mean(X, axis=0)
    qsum = np.r_[0.0, np.cumsum(q)]
    xsum = np.vstack([np.zeros(X.shape[1]), np.cumsum(X, axis=0)])
    starts = np.arange(0, len(df)-n+1)
    quality_mean = (qsum[starts+n]-qsum[starts])/n
    xmean = (xsum[starts+n]-xsum[starts])/n
    repr_distance = np.linalg.norm(xmean-pool_center[None, :], axis=1)
    repr_score = percentile_score(repr_distance, maximize=False)
    q_score = percentile_score(quality_mean, maximize=True)
    compromise = np.minimum(q_score, repr_score)
    best_start = int(starts[int(np.argmax(compromise))])
    ids = df.iloc[best_start:best_start+n]["pair_index"].to_numpy(int)
    return SelectionResult("best_contiguous_window", n, ids, ["maximin rolling quality and population-centroid representativeness", *used, *cols])


def select_legacy_control(df: pd.DataFrame, n: int, provenance: ProvenanceConfig) -> SelectionResult:
    target = np.arange(provenance.legacy_pair_first_a, provenance.legacy_pair_last_b, dtype=int)
    available = set(df["pair_index"].astype(int))
    ids = np.array([i for i in target if i in available], dtype=int)
    notes = ["legacy raw-pair control from PIVlab ASCII provenance: A=4250..4499, B=4251..4500"]
    if n != 250:
        notes.append("Legacy control is intrinsically 250 pairs; returned control is not resized.")
    if len(ids) != 250:
        notes.append(f"BLOCKER: only {len(ids)}/250 legacy pair IDs are present in current pool.")
    return SelectionResult("legacy_control", n, ids, notes)


def run_selector(method: str, df: pd.DataFrame, n: int, cfg: TournamentConfig, provenance: ProvenanceConfig, reliability: np.ndarray | None = None) -> SelectionResult:
    dispatch: dict[str, Callable] = {
        "uniform": lambda: select_uniform(df, n, cfg),
        "stratified_random": lambda: select_stratified_random(df, n, cfg),
        "quality_top": lambda: select_quality_top(df, n, cfg),
        "pareto_temporal": lambda: select_pareto_temporal(df, n, cfg),
        "cluster_medoids": lambda: select_cluster_medoids(df, n, cfg),
        "farthest_point": lambda: select_farthest_point(df, n, cfg),
        "facility_location": lambda: select_facility_location(df, n, cfg),
        "spatial_coverage_log": lambda: select_spatial_coverage_log(df, n, cfg, reliability),
        "qcrc_maximin": lambda: select_qcrc_maximin(df, n, cfg, reliability),
        "best_contiguous_window": lambda: select_best_contiguous_window(df, n, cfg),
        "legacy_control": lambda: select_legacy_control(df, n, provenance),
    }
    if method not in dispatch:
        raise ValueError(f"Unknown selector {method}")
    return dispatch[method]()
