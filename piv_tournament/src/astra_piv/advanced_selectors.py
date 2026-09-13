from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import rankdata
from sklearn.preprocessing import RobustScaler


@dataclass
class AdvancedSelectionResult:
    method: str
    n_requested: int
    pair_indices: np.ndarray
    notes: list[str]


_STATE_EXCLUDE = {
    "pair_index", "frame_a", "frame_b", "time_a_s", "time_b_s",
    "export_frame", "direct_fraction", "type2_fraction",
    "median_speed_direct_mps", "median_speed_active_mps", "p95_speed_active_mps",
}


def _robust_state_matrix(df: pd.DataFrame, columns: list[str] | None = None) -> tuple[np.ndarray, list[str]]:
    if columns is None:
        preferred = [
            "phase_dx_original_px", "phase_dy_original_px",
            "phase_shift_magnitude_original_px", "normalized_interframe_mad",
            "pair_particle_like_blob_density_proxy_mean",
            "pair_optical_dark_region_fraction_proxy_mean",
            "pair_optical_dark_region_cx_proxy_mean",
            "pair_optical_dark_region_cy_proxy_mean",
            "coarse_disp_median_px", "coarse_disp_p90_px",
        ]
        columns = []
        for c in preferred:
            if c in df.columns:
                x = pd.to_numeric(df[c], errors="coerce").to_numpy(float)
                if np.sum(np.isfinite(x)) >= max(3, int(0.5 * len(df))) and np.nanstd(x) > 1e-12:
                    columns.append(c)
        if not columns:
            for c in df.select_dtypes(include=[np.number]).columns:
                if c in _STATE_EXCLUDE:
                    continue
                x = pd.to_numeric(df[c], errors="coerce").to_numpy(float)
                if np.sum(np.isfinite(x)) >= max(3, int(0.5 * len(df))) and np.nanstd(x) > 1e-12:
                    columns.append(c)
                if len(columns) >= 8:
                    break
    if not columns:
        X = np.arange(len(df), dtype=float)[:, None]
        return RobustScaler().fit_transform(X), ["row_index_fallback"]

    # copy=True is required under pandas 3 copy-on-write, which may expose read-only NumPy views.
    X = df[columns].to_numpy(dtype=float, copy=True)
    for j in range(X.shape[1]):
        x = X[:, j]
        med = np.nanmedian(x)
        if not np.isfinite(med):
            med = 0.0
        x[~np.isfinite(x)] = med
        X[:, j] = x
    X = RobustScaler(quantile_range=(10, 90)).fit_transform(X)
    return X, columns


def _rank01(x: np.ndarray, maximize: bool = True) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    finite = np.isfinite(x)
    out = np.full(len(x), 0.5, dtype=float)
    if np.sum(finite) < 2:
        return out
    vals = x[finite]
    ranks = rankdata(vals, method="average")
    p = (ranks - 1.0) / max(len(vals) - 1, 1)
    if not maximize:
        p = 1.0 - p
    out[finite] = p
    return out


def _quality_proxy(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Selection-side quality proxy. It intentionally excludes PIVlab direct_fraction."""
    maximize = [
        "coarse_pce_p10", "coarse_ppr_p10",
        "coarse_pce_median", "coarse_ppr_median",
        "phase_response", "normalized_frame_correlation",
    ]
    minimize = [
        "pair_saturated_fraction_ge250_max",
        "pair_large_bright_component_area_fraction_proxy_max",
    ]
    parts, used = [], []
    for c in maximize:
        if c in df.columns and np.nanstd(df[c].to_numpy(float)) > 1e-12:
            parts.append(_rank01(df[c].to_numpy(float), True)); used.append("+" + c)
    for c in minimize:
        if c in df.columns and np.nanstd(df[c].to_numpy(float)) > 1e-12:
            parts.append(_rank01(df[c].to_numpy(float), False)); used.append("-" + c)
    if not parts:
        return np.full(len(df), 0.5), []
    return np.median(np.column_stack(parts), axis=1), used


def _safe_n(df: pd.DataFrame, n: int) -> int:
    if n < 1:
        raise ValueError("n must be >=1")
    return min(int(n), len(df))


def _ids(df: pd.DataFrame, positions: Iterable[int]) -> np.ndarray:
    pos = np.asarray(list(positions), dtype=int)
    return df.iloc[np.sort(pos)]["pair_index"].to_numpy(int)


def select_uniform_baseline(df: pd.DataFrame, n: int) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    pos = np.unique(np.round(np.linspace(0, len(df)-1, n)).astype(int))
    if len(pos) < n:
        remaining = [i for i in range(len(df)) if i not in set(pos)]
        pos = np.r_[pos, remaining[:n-len(pos)]]
    return AdvancedSelectionResult("uniform_baseline", n, _ids(df, pos), ["systematic full-span baseline"])


def select_stratified_random_baseline(df: pd.DataFrame, n: int, seed: int = 20260912) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    rng = np.random.default_rng(seed)
    edges = np.linspace(0, len(df), n + 1).astype(int)
    chosen = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b <= a:
            continue
        chosen.append(int(rng.integers(a, b)))
    return AdvancedSelectionResult("stratified_random_baseline", n, _ids(df, chosen), [f"one random candidate per temporal stratum; seed={seed}"])


def select_random_iid(df: pd.DataFrame, n: int, seed: int = 20260912) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    rng = np.random.default_rng(seed)
    pos = rng.choice(len(df), size=n, replace=False)
    return AdvancedSelectionResult("random_iid", n, _ids(df, pos), [f"seed={seed}"])


def select_temporal_quality_stratified(df: pd.DataFrame, n: int) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    q, used = _quality_proxy(df)
    edges = np.linspace(0, len(df), n + 1).astype(int)
    chosen = []
    for a, b in zip(edges[:-1], edges[1:]):
        if b <= a:
            continue
        local = np.arange(a, b)
        chosen.append(int(local[np.argmax(q[local])]))
    return AdvancedSelectionResult("temporal_quality_stratified", n, _ids(df, chosen), ["best quality candidate inside each temporal stratum", *used])


def select_kennard_stone(df: pd.DataFrame, n: int) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    X, cols = _robust_state_matrix(df)
    if n >= len(df):
        return AdvancedSelectionResult("kennard_stone", n, df["pair_index"].to_numpy(int), cols)
    D = cdist(X, X)
    i, j = np.unravel_index(np.argmax(D), D.shape)
    selected = [int(i)]
    if n > 1 and j != i:
        selected.append(int(j))
    while len(selected) < n:
        dmin = np.min(D[:, selected], axis=1)
        dmin[selected] = -np.inf
        selected.append(int(np.argmax(dmin)))
    return AdvancedSelectionResult("kennard_stone", n, _ids(df, selected), ["maximin state-space design", *cols])


def select_kernel_herding(df: pd.DataFrame, n: int) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    X, cols = _robust_state_matrix(df)
    D = cdist(X, X)
    positive = D[D > 0]
    sigma = float(np.median(positive)) if len(positive) else 1.0
    K = np.exp(-0.5 * (D / max(sigma, 1e-12)) ** 2)
    target = K.mean(axis=0)
    selected = []
    sum_kernel = np.zeros(len(df), dtype=float)
    available = np.ones(len(df), dtype=bool)
    for t in range(1, n + 1):
        redundancy = sum_kernel / max(t - 1, 1)
        score = target - redundancy
        score[~available] = -np.inf
        j = int(np.argmax(score))
        selected.append(j)
        sum_kernel += K[j]
        available[j] = False
    return AdvancedSelectionResult("kernel_herding", n, _ids(df, selected), ["RBF kernel mean matching", *cols])


def select_d_optimal(df: pd.DataFrame, n: int, ridge: float = 1e-6) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    X, cols = _robust_state_matrix(df)
    X = np.column_stack([np.ones(len(X)), X])
    p = X.shape[1]
    Ainv = np.eye(p) / max(ridge, 1e-12)
    selected = []
    available = np.ones(len(df), dtype=bool)
    for _ in range(n):
        gains = np.einsum("ij,jk,ik->i", X, Ainv, X)
        gains[~available] = -np.inf
        j = int(np.argmax(gains))
        x = X[j:j+1].T
        denom = float(1.0 + (x.T @ Ainv @ x)[0, 0])
        Ainv = Ainv - (Ainv @ x @ x.T @ Ainv) / max(denom, 1e-12)
        selected.append(j)
        available[j] = False
    return AdvancedSelectionResult("d_optimal", n, _ids(df, selected), ["greedy log-det information design", *cols])


def select_mmr_maximin(df: pd.DataFrame, n: int, min_gap_pairs: int = 1) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    X, cols = _robust_state_matrix(df)
    q, used = _quality_proxy(df)
    pair_ids = df["pair_index"].to_numpy(int)
    center = np.median(X, axis=0)
    selected = []
    available = np.ones(len(df), dtype=bool)
    for _ in range(n):
        if not selected:
            state_novelty = np.linalg.norm(X - center[None, :], axis=1)
            temporal_novelty = np.abs(pair_ids - np.median(pair_ids))
        else:
            state_novelty = np.min(cdist(X, X[selected]), axis=1)
            temporal_novelty = np.array([min(abs(pid - pair_ids[s]) for s in selected) for pid in pair_ids], dtype=float)
        compromise = np.minimum.reduce([_rank01(q, True), _rank01(state_novelty, True), _rank01(temporal_novelty, True)])
        compromise[~available] = -np.inf
        if selected and min_gap_pairs > 1:
            bad = np.array([any(abs(pid - pair_ids[s]) < min_gap_pairs for s in selected) for pid in pair_ids])
            if np.any(available & ~bad):
                compromise[bad] = -np.inf
        j = int(np.argmax(compromise))
        selected.append(j)
        available[j] = False
    return AdvancedSelectionResult("mmr_maximin", n, _ids(df, selected), ["maximin quality/state novelty/temporal novelty", *used, *cols])


def _validate_reliability(df: pd.DataFrame, reliability: np.ndarray) -> np.ndarray:
    R = np.asarray(reliability, dtype=float)
    if R.ndim != 2 or R.shape[0] != len(df):
        raise ValueError("reliability must have shape [n_pairs, n_spatial_cells]")
    return np.clip(np.nan_to_num(R, nan=0.0, posinf=1.0, neginf=0.0), 0.0, 1.0)


def select_spatial_saturated_coverage(df: pd.DataFrame, n: int, reliability: np.ndarray, target_fraction_of_n: float = 0.25) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    R = _validate_reliability(df, reliability)
    target = max(1.0, float(n) * float(target_fraction_of_n))
    coverage = np.zeros(R.shape[1], dtype=float)
    selected = []
    available = np.ones(len(df), dtype=bool)
    for _ in range(n):
        current = np.minimum(coverage, target).sum()
        gains = np.minimum(coverage[None, :] + R, target).sum(axis=1) - current
        gains[~available] = -np.inf
        j = int(np.argmax(gains))
        selected.append(j)
        coverage += R[j]
        available[j] = False
    return AdvancedSelectionResult("spatial_saturated_coverage", n, _ids(df, selected), [f"saturated spatial coverage target={target:.3g} equivalent observations/cell"])


def select_spatial_lower_tail(df: pd.DataFrame, n: int, reliability: np.ndarray, lower_tail_fraction: float = 0.10) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    R = _validate_reliability(df, reliability)
    coverage = np.zeros(R.shape[1], dtype=float)
    selected = []
    available = np.ones(len(df), dtype=bool)
    k = max(1, int(np.ceil(R.shape[1] * lower_tail_fraction)))
    for _ in range(n):
        cand_cov = coverage[None, :] + R
        part = np.partition(cand_cov, kth=k-1, axis=1)[:, :k]
        tail_mean = part.mean(axis=1)
        logcov = np.log1p(cand_cov).mean(axis=1)
        score = np.minimum(_rank01(tail_mean, True), _rank01(logcov, True))
        score[~available] = -np.inf
        j = int(np.argmax(score))
        selected.append(j)
        coverage += R[j]
        available[j] = False
    return AdvancedSelectionResult("spatial_lower_tail", n, _ids(df, selected), [f"maximin lower-tail ({100*lower_tail_fraction:.1f}%) + log coverage"])


def select_quality_facility_maximin(df: pd.DataFrame, n: int, min_gap_pairs: int = 1) -> AdvancedSelectionResult:
    n = _safe_n(df, n)
    X, cols = _robust_state_matrix(df)
    q, used = _quality_proxy(df)
    D = cdist(X, X)
    positive = D[D > 0]
    sigma = float(np.median(positive)) if len(positive) else 1.0
    S = np.exp(-(D / max(sigma, 1e-12)) ** 2)
    best = np.zeros(len(df), dtype=float)
    pair_ids = df["pair_index"].to_numpy(int)
    selected = []
    available = np.ones(len(df), dtype=bool)
    for _ in range(n):
        facility_gain = np.sum(np.maximum(best[:, None], S) - best[:, None], axis=0)
        if selected:
            temporal = np.array([min(abs(pid - pair_ids[s]) for s in selected) for pid in pair_ids], float)
        else:
            temporal = np.abs(pair_ids - np.median(pair_ids))
        score = np.minimum.reduce([_rank01(q, True), _rank01(facility_gain, True), _rank01(temporal, True)])
        score[~available] = -np.inf
        if selected and min_gap_pairs > 1:
            bad = np.array([any(abs(pid - pair_ids[s]) < min_gap_pairs for s in selected) for pid in pair_ids])
            if np.any(available & ~bad):
                score[bad] = -np.inf
        j = int(np.argmax(score))
        selected.append(j)
        best = np.maximum(best, S[:, j])
        available[j] = False
    return AdvancedSelectionResult("quality_facility_maximin", n, _ids(df, selected), ["weight-free rank maximin: quality/facility/temporal", *used, *cols])


ADVANCED_METHODS = (
    "uniform_baseline", "stratified_random_baseline", "random_iid", "temporal_quality_stratified",
    "kennard_stone", "kernel_herding", "d_optimal", "mmr_maximin", "spatial_saturated_coverage",
    "spatial_lower_tail", "quality_facility_maximin",
)


def run_advanced_selector(method: str, df: pd.DataFrame, n: int, *, seed: int = 20260912, reliability: np.ndarray | None = None, min_gap_pairs: int = 1, target_fraction_of_n: float = 0.25, lower_tail_fraction: float = 0.10) -> AdvancedSelectionResult:
    if method == "uniform_baseline": return select_uniform_baseline(df, n)
    if method == "stratified_random_baseline": return select_stratified_random_baseline(df, n, seed)
    if method == "random_iid": return select_random_iid(df, n, seed)
    if method == "temporal_quality_stratified": return select_temporal_quality_stratified(df, n)
    if method == "kennard_stone": return select_kennard_stone(df, n)
    if method == "kernel_herding": return select_kernel_herding(df, n)
    if method == "d_optimal": return select_d_optimal(df, n)
    if method == "mmr_maximin": return select_mmr_maximin(df, n, min_gap_pairs)
    if method == "spatial_saturated_coverage":
        if reliability is None: raise ValueError("spatial_saturated_coverage requires reliability")
        return select_spatial_saturated_coverage(df, n, reliability, target_fraction_of_n)
    if method == "spatial_lower_tail":
        if reliability is None: raise ValueError("spatial_lower_tail requires reliability")
        return select_spatial_lower_tail(df, n, reliability, lower_tail_fraction)
    if method == "quality_facility_maximin": return select_quality_facility_maximin(df, n, min_gap_pairs)
    raise ValueError(f"Unknown advanced selector: {method}")
