from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
from typing import Iterable

import numpy as np
import pandas as pd


HEADER_RE = re.compile(
    r"FRAME:\s*(?P<frame>\d+),\s*filenames:\s*"
    r"A:\[(?P<a>\d+)\].*?&\s*B:\[(?P<b>\d+)\].*?"
    r"conversion factor xy \(px -> m\):\s*(?P<xy>[0-9.eE+-]+),\s*"
    r"conversion factor uv \(px/frame -> m/s\):\s*(?P<uv>[0-9.eE+-]+)"
)


@dataclass(frozen=True)
class PIVlabMeta:
    path: str
    export_frame: int
    source_a: int
    source_b: int
    xy_m_per_px: float
    uv_mps_per_px_per_frame: float

    @property
    def dt_s(self) -> float:
        return self.xy_m_per_px / self.uv_mps_per_px_per_frame


def parse_pivlab_file(path: str | Path) -> tuple[PIVlabMeta, pd.DataFrame]:
    path = Path(path)
    with path.open("r", encoding="utf-8", errors="replace") as f:
        line1 = f.readline().strip()
        line2 = f.readline().strip()
    if not line1.startswith("PIVlab, ASCII chart output"):
        raise ValueError(f"Not a PIVlab ASCII export: {path}")
    m = HEADER_RE.search(line2)
    if not m:
        raise ValueError(f"Could not parse PIVlab metadata line: {line2[:300]}")
    meta = PIVlabMeta(
        path=str(path),
        export_frame=int(m.group("frame")),
        source_a=int(m.group("a")),
        source_b=int(m.group("b")),
        xy_m_per_px=float(m.group("xy")),
        uv_mps_per_px_per_frame=float(m.group("uv")),
    )
    df = pd.read_csv(path, skiprows=2)
    required = ["x [m]", "y [m]", "u [m/s]", "v [m/s]", "Vector type [-]", "magnitude [m/s]"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing {missing}")
    return meta, df


def audit_pivlab_files(paths: Iterable[str | Path], output_dir: str | Path | None = None):
    paths = sorted(Path(p) for p in paths)
    if not paths:
        raise FileNotFoundError("No PIVlab ASCII files supplied")

    metas = []
    dfs = []
    summaries = []
    ref_coords = None
    ref_mask = None

    for path in paths:
        meta, df = parse_pivlab_file(path)
        metas.append(meta)
        dfs.append(df)
        coords = df[["x [m]", "y [m]"]].to_numpy(float)
        vt = df["Vector type [-]"].astype(int).to_numpy()
        mask = vt == 0
        if ref_coords is None:
            ref_coords = coords
            ref_mask = mask
        else:
            if not np.allclose(coords, ref_coords, rtol=0, atol=1e-12):
                raise AssertionError(f"Coordinate grid mismatch: {path.name}")
            if not np.array_equal(mask, ref_mask):
                raise AssertionError(f"Mask mismatch: {path.name}")

        active = vt != 0
        direct = vt == 1
        type2 = vt == 2
        u = df["u [m/s]"].to_numpy(float)
        v = df["v [m/s]"].to_numpy(float)
        speed = np.sqrt(u*u + v*v)
        summaries.append({
            "file": path.name,
            "export_frame": meta.export_frame,
            "source_a": meta.source_a,
            "source_b": meta.source_b,
            "dt_s": meta.dt_s,
            "rows": len(df),
            "masked_count": int(np.sum(~active)),
            "active_count": int(np.sum(active)),
            "direct_count": int(np.sum(direct)),
            "type2_count": int(np.sum(type2)),
            "direct_fraction_active": float(np.sum(direct) / max(np.sum(active), 1)),
            "type2_fraction_active": float(np.sum(type2) / max(np.sum(active), 1)),
            "median_speed_active_mps": float(np.nanmedian(speed[active])),
            "median_speed_direct_mps": float(np.nanmedian(speed[direct])) if np.any(direct) else np.nan,
        })

    summary_df = pd.DataFrame(summaries).sort_values("export_frame").reset_index(drop=True)
    stack = np.stack([df["Vector type [-]"].astype(int).to_numpy() for df in dfs], axis=0)
    active_ref = ~ref_mask
    direct = (stack == 1).astype(float)
    direct[:, ~active_ref] = np.nan
    reliability = direct[:, active_ref]

    spatial = pd.DataFrame(ref_coords, columns=["x_m", "y_m"])
    spatial["active"] = active_ref
    p_direct = np.full(len(spatial), np.nan)
    p_direct[active_ref] = np.nanmean(direct[:, active_ref], axis=0)
    spatial["p_direct"] = p_direct

    x_unique = np.sort(np.unique(ref_coords[:, 0]))
    y_unique = np.sort(np.unique(ref_coords[:, 1]))
    dx = float(np.median(np.diff(x_unique))) if len(x_unique) > 1 else np.nan
    dy = float(np.median(np.diff(y_unique))) if len(y_unique) > 1 else np.nan
    xy = float(np.median([m.xy_m_per_px for m in metas]))

    meta = {
        "n_fields": len(paths),
        "first_source_pair": [int(summary_df.iloc[0]["source_a"]), int(summary_df.iloc[0]["source_b"])],
        "last_source_pair": [int(summary_df.iloc[-1]["source_a"]), int(summary_df.iloc[-1]["source_b"])],
        "xy_m_per_px": xy,
        "uv_mps_per_px_per_frame": float(np.median([m.uv_mps_per_px_per_frame for m in metas])),
        "dt_s": float(np.median([m.dt_s for m in metas])),
        "grid_nx": len(x_unique),
        "grid_ny": len(y_unique),
        "grid_dx_m": dx,
        "grid_dy_m": dy,
        "grid_dx_px": dx / xy if np.isfinite(dx) else np.nan,
        "grid_dy_px": dy / xy if np.isfinite(dy) else np.nan,
        "active_points": int(np.sum(active_ref)),
        "masked_points": int(np.sum(~active_ref)),
        "direct_fraction_mean": float(summary_df["direct_fraction_active"].mean()),
        "direct_fraction_min": float(summary_df["direct_fraction_active"].min()),
        "direct_fraction_max": float(summary_df["direct_fraction_active"].max()),
    }

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        summary_df.to_csv(out / "pivlab_field_audit.csv", index=False)
        spatial.to_csv(out / "pivlab_spatial_direct_probability.csv", index=False)
        np.save(out / "pivlab_direct_reliability.npy", reliability)
        np.save(out / "pivlab_source_pair_a.npy", summary_df["source_a"].to_numpy(int))
        (out / "pivlab_audit_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return summary_df, reliability, spatial, meta
