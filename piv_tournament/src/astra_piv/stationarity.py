from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Iterable

import numpy as np
import pandas as pd

from .config import StationarityConfig


DEFAULT_STATE_FEATURES = [
    "normalized_interframe_mad",
    "phase_shift_magnitude_original_px",
    "phase_response",
    "pair_particle_like_blob_density_proxy_mean",
    "pair_optical_dark_region_fraction_proxy_mean",
    "pair_optical_dark_region_cx_proxy_mean",
    "pair_optical_dark_region_cy_proxy_mean",
]


@dataclass
class Segment:
    start_pair: int
    end_pair: int  # inclusive
    n_pairs: int
    method: str
    stable: bool
    robust_slope_max: float
    robust_cv_max: float
    score: float


def robust_standardize_matrix(df: pd.DataFrame, columns: list[str]) -> np.ndarray:
    arrays = []
    for col in columns:
        x = df[col].to_numpy(dtype=float)
        med = np.nanmedian(x)
        mad = np.nanmedian(np.abs(x-med))
        scale = max(1.4826 * mad, 1e-12)
        z = (x-med)/scale
        # Missing optical proxies are neutral after robust centering.
        z[~np.isfinite(z)] = 0.0
        arrays.append(z)
    return np.column_stack(arrays)


def choose_available_features(df: pd.DataFrame, requested: Iterable[str] | None = None) -> list[str]:
    requested = list(requested or DEFAULT_STATE_FEATURES)
    result = []
    for col in requested:
        if col in df.columns:
            x = df[col].to_numpy(dtype=float)
            if np.sum(np.isfinite(x)) >= max(10, int(0.5 * len(x))):
                result.append(col)
    if not result:
        numeric = [c for c in df.select_dtypes(include=[np.number]).columns if c not in {"pair_index", "frame_a", "frame_b", "time_a_s", "time_b_s"}]
        result = numeric[: min(5, len(numeric))]
    return result


def _segment_diagnostics(X: np.ndarray, start: int, end_exclusive: int, cfg: StationarityConfig, method: str) -> Segment:
    Y = X[start:end_exclusive]
    n = len(Y)
    t = np.linspace(-0.5, 0.5, n) if n > 1 else np.array([0.0])
    slopes = []
    cvs = []
    for j in range(Y.shape[1]):
        y = Y[:, j]
        if n > 2:
            slope = np.polyfit(t, y, 1)[0]
        else:
            slope = 0.0
        slopes.append(abs(float(slope)))
        denom = max(abs(float(np.median(y))), 1.0)
        cvs.append(float(np.std(y, ddof=1) / denom) if n > 1 else 0.0)
    slope_max = max(slopes, default=0.0)
    cv_max = max(cvs, default=0.0)
    stable = bool(
        n >= cfg.min_segment_pairs
        and slope_max <= cfg.plateau_max_robust_slope
        and cv_max <= cfg.plateau_max_robust_cv
    )
    # Lower score is better; length provides a gentle preference for longer segments.
    score = slope_max + cv_max + 1.0 / max(n, 1)
    return Segment(
        start_pair=start,
        end_pair=end_exclusive - 1,
        n_pairs=n,
        method=method,
        stable=stable,
        robust_slope_max=slope_max,
        robust_cv_max=cv_max,
        score=float(score),
    )


def pelt_segments(pair_df: pd.DataFrame, cfg: StationarityConfig, features: list[str]) -> list[Segment]:
    X = robust_standardize_matrix(pair_df, features)
    n, d = X.shape
    if n == 0:
        return []
    try:
        import ruptures as rpt
    except Exception:
        return [_segment_diagnostics(X, 0, n, cfg, "pelt_rbf_fallback_all")]

    # BIC-like scale; no result is accepted solely because PELT partitions it.
    penalty = float(cfg.pelt_penalty_scale * d * np.log(max(n, 2)))
    algo = rpt.Pelt(model="rbf", min_size=max(20, min(cfg.min_segment_pairs // 4, n))).fit(X)
    bkps = algo.predict(pen=penalty)
    segments = []
    start = 0
    for end in bkps:
        segments.append(_segment_diagnostics(X, start, end, cfg, "pelt_rbf"))
        start = end
    return segments


def robust_plateau_segments(pair_df: pd.DataFrame, cfg: StationarityConfig, features: list[str]) -> list[Segment]:
    X = robust_standardize_matrix(pair_df, features)
    n = len(X)
    if n == 0:
        return []
    w = min(cfg.rolling_window_pairs, n)
    if w < 20:
        return [_segment_diagnostics(X, 0, n, cfg, "robust_plateau_all")]

    # Compute diagnostics on overlapping windows, mark acceptable windows, then merge them.
    good = np.zeros(n, dtype=bool)
    step = max(1, w // 10)
    for start in range(0, n-w+1, step):
        seg = _segment_diagnostics(X, start, start+w, cfg, "robust_plateau_window")
        if seg.robust_slope_max <= cfg.plateau_max_robust_slope and seg.robust_cv_max <= cfg.plateau_max_robust_cv:
            good[start:start+w] = True

    segments = []
    i = 0
    while i < n:
        if not good[i]:
            i += 1
            continue
        j = i + 1
        while j < n and good[j]:
            j += 1
        segments.append(_segment_diagnostics(X, i, j, cfg, "robust_plateau"))
        i = j
    if not segments:
        segments = [_segment_diagnostics(X, 0, n, cfg, "robust_plateau_no_plateau")]
    return segments


def _interval_intersection(a: Segment, b: Segment, cfg: StationarityConfig) -> Segment | None:
    s = max(a.start_pair, b.start_pair)
    e = min(a.end_pair, b.end_pair)
    if e < s:
        return None
    n = e - s + 1
    if n < cfg.min_segment_pairs:
        return None
    return Segment(s, e, n, "consensus_intersection", True, max(a.robust_slope_max, b.robust_slope_max), max(a.robust_cv_max, b.robust_cv_max), max(a.score, b.score))


def detect_stationary_pool(
    pair_df: pd.DataFrame,
    cfg: StationarityConfig,
    features: list[str] | None = None,
    output_dir: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    pair_df = pair_df.sort_values("pair_index").reset_index(drop=True).copy()
    features = choose_available_features(pair_df, features)

    by_method: dict[str, list[Segment]] = {}
    for method in cfg.methods:
        if method == "pelt_rbf":
            by_method[method] = pelt_segments(pair_df, cfg, features)
        elif method == "robust_plateau":
            by_method[method] = robust_plateau_segments(pair_df, cfg, features)
        else:
            raise ValueError(f"Unknown stationarity method: {method}")

    candidates = [s for ss in by_method.values() for s in ss if s.stable]
    consensus = None
    if len(by_method) >= 2:
        methods = list(by_method)
        a = sorted([s for s in by_method[methods[0]] if s.stable], key=lambda s: (-s.n_pairs, s.score))
        b = sorted([s for s in by_method[methods[1]] if s.stable], key=lambda s: (-s.n_pairs, s.score))
        for sa in a:
            for sb in b:
                inter = _interval_intersection(sa, sb, cfg)
                if inter and (consensus is None or inter.n_pairs > consensus.n_pairs):
                    consensus = inter

    if consensus is None:
        if candidates:
            consensus = sorted(candidates, key=lambda s: (-s.n_pairs, s.score))[0]
            consensus = Segment(**{**asdict(consensus), "method": "consensus_longest_stable"})
        else:
            # No silent pass: return the complete record but flag it as unresolved.
            consensus = Segment(
                start_pair=int(pair_df["pair_index"].min()),
                end_pair=int(pair_df["pair_index"].max()),
                n_pairs=len(pair_df),
                method="UNRESOLVED_no_stable_segment",
                stable=False,
                robust_slope_max=np.nan,
                robust_cv_max=np.nan,
                score=np.inf,
            )

    mask = (pair_df["pair_index"] >= consensus.start_pair) & (pair_df["pair_index"] <= consensus.end_pair)
    pool = pair_df.loc[mask].copy()
    segment_df = pd.DataFrame([asdict(s) for ss in by_method.values() for s in ss] + [asdict(consensus)])
    meta = {
        "features": features,
        "consensus": asdict(consensus),
        "methods": {k: [asdict(s) for s in v] for k, v in by_method.items()},
        "warning": "Stationarity is an experimental-data segmentation step; it is independent of CFD.",
    }

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        segment_df.to_csv(out / "stationarity_segments.csv", index=False)
        pool.to_csv(out / "stationary_pair_pool.csv", index=False)
        (out / "stationarity_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return pool, segment_df, meta
