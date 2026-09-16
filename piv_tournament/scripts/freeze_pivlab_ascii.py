#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]
if str(PACKAGE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from astra_piv.pivlab_ascii import parse_pivlab_file

EXPECTED_COUNT = 250
FIRST_A = 4250


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def grid_hash(df: pd.DataFrame) -> str:
    arr = df[["x [m]", "y [m]"]].to_numpy(np.float64)
    return hashlib.sha256(arr.tobytes(order="C")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Forensic freeze of PIVlab_0001..0250 ASCII exports")
    ap.add_argument("--ascii-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    source = Path(args.ascii_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    by_index: dict[int, list[Path]] = {}
    for path in source.glob("PIVlab_*.txt"):
        match = re.fullmatch(r"PIVlab_(\d{4})\.txt", path.name)
        if match:
            by_index.setdefault(int(match.group(1)), []).append(path)

    rows: list[dict] = []
    missing: list[int] = []
    duplicated: list[int] = []
    ref_grid_hash = None
    ref_xy = None
    ref_uv = None
    anomalies: list[str] = []

    for idx in range(1, EXPECTED_COUNT + 1):
        paths = by_index.get(idx, [])
        if not paths:
            missing.append(idx)
            continue
        if len(paths) != 1:
            duplicated.append(idx)
            continue
        path = paths[0]
        meta, df = parse_pivlab_file(path)
        x = np.sort(df["x [m]"].dropna().unique().astype(float))
        y = np.sort(df["y [m]"].dropna().unique().astype(float))
        dx = float(np.median(np.diff(x))) if len(x) > 1 else np.nan
        dy = float(np.median(np.diff(y))) if len(y) > 1 else np.nan
        vt = df["Vector type [-]"].astype(int).to_numpy()
        finite = np.isfinite(df["u [m/s]"].to_numpy(float)) & np.isfinite(df["v [m/s]"].to_numpy(float))
        gh = grid_hash(df)
        if ref_grid_hash is None:
            ref_grid_hash = gh
            ref_xy = meta.xy_m_per_px
            ref_uv = meta.uv_mps_per_px_per_frame
        expected_a = FIRST_A + idx - 1
        expected_b = expected_a + 1
        pair_ok = meta.source_a == expected_a and meta.source_b == expected_b
        calibration_ok = meta.xy_m_per_px == ref_xy and meta.uv_mps_per_px_per_frame == ref_uv
        grid_ok = gh == ref_grid_hash
        if not pair_ok:
            anomalies.append(f"{path.name}: source pair {meta.source_a}/{meta.source_b} != {expected_a}/{expected_b}")
        if not calibration_ok:
            anomalies.append(f"{path.name}: conversion metadata changed")
        if not grid_ok:
            anomalies.append(f"{path.name}: coordinate grid changed")
        counts = {int(k): int(v) for k, v in pd.Series(vt).value_counts().to_dict().items()}
        rows.append({
            "index": idx,
            "filename": path.name,
            "source_frame_a": meta.source_a,
            "source_frame_b": meta.source_b,
            "xy_m_per_px": meta.xy_m_per_px,
            "uv_mps_per_px_per_frame": meta.uv_mps_per_px_per_frame,
            "dt_s": meta.dt_s,
            "row_count": len(df),
            "grid_nx": len(x),
            "grid_ny": len(y),
            "pitch_x_m": dx,
            "pitch_y_m": dy,
            "pitch_x_px": dx / meta.xy_m_per_px if np.isfinite(dx) else np.nan,
            "pitch_y_px": dy / meta.xy_m_per_px if np.isfinite(dy) else np.nan,
            "vector_type_0_count": counts.get(0, 0),
            "vector_type_1_count": counts.get(1, 0),
            "vector_type_2_count": counts.get(2, 0),
            "vector_type_other_count": sum(v for k, v in counts.items() if k not in {0, 1, 2}),
            "finite_vector_count": int(np.sum(finite)),
            "file_size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "grid_sha256": gh,
            "pair_continuity_ok": pair_ok,
            "calibration_metadata_constant": calibration_ok,
            "grid_constant": grid_ok,
            "duplicate_index": False,
        })

    manifest = pd.DataFrame(rows).sort_values("index") if rows else pd.DataFrame()
    manifest.to_csv(out / "ASCII_250_MANIFEST.csv", index=False)
    complete = not missing and not duplicated and len(rows) == EXPECTED_COUNT and not anomalies
    summary = {
        "status": "PASS" if complete else "FAIL",
        "expected_exports": EXPECTED_COUNT,
        "parsed_unique_exports": len(rows),
        "missing_indices": missing,
        "duplicated_indices": duplicated,
        "anomalies": anomalies,
        "first_expected_pair": [4250, 4251],
        "last_expected_pair": [4499, 4500],
        "all_content_sha256_recorded": len(rows) == EXPECTED_COUNT,
    }
    (out / "ASCII_250_FORENSIC_STATUS.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = [
        "# PIVlab 250-ASCII forensic freeze", "", f"**Verdict:** {summary['status']}",
        f"**Expected indexed exports:** {EXPECTED_COUNT}", f"**Unique parsed exports:** {len(rows)}",
        f"**Missing indices:** {missing if missing else 'none'}", f"**Duplicated indices:** {duplicated if duplicated else 'none'}",
        f"**Content/grid/calibration anomalies:** {len(anomalies)}", "",
        "PASS requires all 250 exact filenames, continuous source pairs 4250/4251 through 4499/4500, constant conversion metadata, a constant coordinate grid, and a SHA-256 for every file.",
    ]
    (out / "ASCII_250_FORENSIC_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
