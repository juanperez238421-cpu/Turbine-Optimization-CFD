from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

_HEADER_RE = re.compile(
    r"FRAME:\s*(?P<frame>\d+),\s*filenames:\s*A:\[(?P<a>\d+)\].*?"
    r"&\s*B:\[(?P<b>\d+)\].*?conversion factor xy \(px -> m\):\s*(?P<xy>[0-9.eE+-]+),\s*"
    r"conversion factor uv \(px/frame -> m/s\):\s*(?P<uv>[0-9.eE+-]+)"
)


@dataclass
class OracleData:
    pool: pd.DataFrame
    direct_reliability: np.ndarray
    coordinates_m: np.ndarray
    active_mask_reference: np.ndarray
    files: list[str]


def _load_one(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        line1 = f.readline().strip(); line2 = f.readline().strip()
    if not line1.startswith("PIVlab, ASCII chart output"):
        raise ValueError(f"{path}: not a PIVlab ASCII chart export")
    m = _HEADER_RE.search(line2)
    if not m:
        raise ValueError(f"{path}: metadata header could not be parsed")
    df = pd.read_csv(path, skiprows=2)
    required = ["x [m]", "y [m]", "u [m/s]", "v [m/s]", "Vector type [-]"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    meta = {
        "export_frame": int(m.group("frame")), "frame_a": int(m.group("a")), "frame_b": int(m.group("b")),
        "xy_m_per_px": float(m.group("xy")), "uv_mps_per_px_per_frame": float(m.group("uv")),
    }
    return meta, df


def load_pivlab_oracle(paths: list[str | Path]) -> OracleData:
    paths = [Path(p) for p in paths]
    if not paths:
        raise ValueError("No PIVlab files supplied")
    rows, direct_rows, files = [], [], []
    coords_ref = None; active_ref = None
    for path in sorted(paths):
        meta, df = _load_one(path)
        coords = df[["x [m]", "y [m]"]].to_numpy(float)
        vt = df["Vector type [-]"].astype(int).to_numpy(); active = vt != 0
        if coords_ref is None:
            coords_ref = coords; active_ref = active
        else:
            if not np.allclose(coords, coords_ref, rtol=0, atol=1e-12): raise ValueError(f"{path.name}: coordinate grid mismatch")
            if not np.array_equal(active, active_ref): raise ValueError(f"{path.name}: active mask mismatch")
        u = df["u [m/s]"].to_numpy(float); v = df["v [m/s]"].to_numpy(float); speed = np.sqrt(u*u + v*v)
        direct_rows.append((vt == 1)[active_ref].astype(float))
        rows.append({
            "pair_index": meta["frame_a"], "frame_a": meta["frame_a"], "frame_b": meta["frame_b"],
            "export_frame": meta["export_frame"], "xy_m_per_px": meta["xy_m_per_px"],
            "uv_mps_per_px_per_frame": meta["uv_mps_per_px_per_frame"],
            "direct_fraction": float(np.mean(vt[active_ref] == 1)), "type2_fraction": float(np.mean(vt[active_ref] == 2)),
            "median_speed_direct_mps": float(np.nanmedian(speed[vt == 1])),
            "median_speed_active_mps": float(np.nanmedian(speed[active_ref])),
            "p95_speed_active_mps": float(np.nanpercentile(speed[active_ref], 95)),
        })
        files.append(str(path))
    order = np.argsort([r["pair_index"] for r in rows])
    return OracleData(
        pool=pd.DataFrame(rows).iloc[order].reset_index(drop=True),
        direct_reliability=np.vstack(direct_rows)[order],
        coordinates_m=coords_ref[active_ref], active_mask_reference=active_ref, files=files,
    )


def coverage_metrics(Rsel: np.ndarray) -> dict:
    if Rsel.ndim != 2 or Rsel.shape[0] == 0: raise ValueError("Rsel must be [selected_pairs, active_cells]")
    c = np.sum(Rsel, axis=0)
    return {
        "coverage_mean": float(np.mean(c)), "coverage_min": float(np.min(c)),
        "coverage_q05": float(np.quantile(c, 0.05)), "coverage_q10": float(np.quantile(c, 0.10)),
        "coverage_median": float(np.median(c)),
        "fraction_cells_observed_at_least_once": float(np.mean(c >= 1)),
        "fraction_cells_observed_at_least_twice": float(np.mean(c >= 2)),
        "log_coverage_utility": float(np.mean(np.log1p(c))),
    }


def exact_best_subset(R: np.ndarray, n: int, objective: str = "log") -> tuple[tuple[int, ...], float]:
    if len(R) > 24: raise ValueError("Exact enumeration is intentionally restricted to <=24 candidates")
    best_combo, best_value = None, -np.inf
    for combo in itertools.combinations(range(len(R)), n):
        c = np.sum(R[list(combo)], axis=0)
        if objective == "log": value = float(np.mean(np.log1p(c)))
        elif objective == "q10": value = float(np.quantile(c, 0.10))
        elif objective == "once": value = float(np.mean(c >= 1))
        else: raise ValueError(objective)
        if value > best_value: best_value = value; best_combo = combo
    return best_combo, best_value


def spatial_cv_folds(n_cells: int, k: int = 5) -> list[tuple[np.ndarray, np.ndarray]]:
    idx = np.arange(n_cells); folds = []
    for fold in range(k):
        test = idx[idx % k == fold]; train = idx[idx % k != fold]; folds.append((train, test))
    return folds


def save_oracle_inventory(data: OracleData, outdir: str | Path) -> None:
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    data.pool.to_csv(outdir / "oracle_pool.csv", index=False)
    np.save(outdir / "oracle_direct_reliability.npy", data.direct_reliability)
    pd.DataFrame(data.coordinates_m, columns=["x_m", "y_m"]).to_csv(outdir / "oracle_active_coordinates.csv", index=False)
    summary = {
        "n_fields": len(data.pool), "n_active_cells": int(data.direct_reliability.shape[1]),
        "pair_indices": data.pool["pair_index"].astype(int).tolist(),
        "direct_fraction_min": float(data.pool["direct_fraction"].min()),
        "direct_fraction_max": float(data.pool["direct_fraction"].max()),
        "direct_fraction_mean": float(data.pool["direct_fraction"].mean()),
        "files": data.files,
        "warning": "Retrospective oracle evidence. Direct-vector validity must not leak into prospective selection unless explicitly declared.",
    }
    (outdir / "oracle_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
