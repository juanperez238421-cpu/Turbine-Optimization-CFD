#!/usr/bin/env python3
"""Render publication-grade CFD figures from real exported data.

Input formats are open post-processing formats readable by VTK/PyVista
(e.g. EnSight Gold .case/.encas, CGNS .cgns, VTK/VTU/VTM/PVTU).

This script intentionally does NOT read proprietary ANSYS CFX .res/.trn files.
Use the companion cfx5export script on a licensed ANSYS workstation first.

Scientific safeguards:
- one camera/plane/scalar range is shared across cases;
- case status is shown in figure metadata, not hidden;
- ambiguous Carolina cases are not renamed as verified designs;
- no interpolation beyond VTK's native slice/contour operations;
- no generative image processing.
"""

from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pyvista as pv


def load_dataset(path: Path) -> pv.DataSet:
    """Read one supported CFD dataset and collapse MultiBlock data if needed."""
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        obj = pv.read(path)
    except Exception:
        reader = pv.get_reader(str(path))
        obj = reader.read()

    if isinstance(obj, pv.MultiBlock):
        nonempty = [b for b in obj if b is not None and getattr(b, "n_points", 0) > 0]
        if not nonempty:
            raise ValueError(f"No non-empty blocks found in {path}")
        if len(nonempty) == 1:
            obj = nonempty[0]
        else:
            blocks = pv.MultiBlock(nonempty)
            obj = blocks.combine(merge_points=False)
    return obj


def resolve_array(ds: pv.DataSet, candidates: Iterable[str]) -> str | None:
    names = list(ds.point_data.keys()) + list(ds.cell_data.keys())
    lower = {n.lower(): n for n in names}
    for c in candidates:
        if c in names:
            return c
        if c.lower() in lower:
            return lower[c.lower()]
    # fallback substring match, but only when unique
    for c in candidates:
        hits = [n for n in names if c.lower() in n.lower()]
        if len(hits) == 1:
            return hits[0]
    return None


def ensure_point_data(ds: pv.DataSet, array_name: str) -> pv.DataSet:
    if array_name in ds.point_data:
        return ds
    if array_name in ds.cell_data:
        return ds.cell_data_to_point_data(pass_cell_data=True)
    return ds


def vector_magnitude(ds: pv.DataSet, vector_name: str, out_name: str = "Velocity Magnitude") -> tuple[pv.DataSet, str]:
    ds = ensure_point_data(ds, vector_name)
    arr = np.asarray(ds.point_data[vector_name])
    if arr.ndim != 2 or arr.shape[1] < 2:
        raise ValueError(f"{vector_name!r} is not a vector field")
    ds = ds.copy()
    ds.point_data[out_name] = np.linalg.norm(arr, axis=1)
    return ds, out_name


def magnitude_from_existing(ds: pv.DataSet, name: str, out_name: str) -> tuple[pv.DataSet, str]:
    ds = ensure_point_data(ds, name)
    arr = np.asarray(ds.point_data[name])
    if arr.ndim == 2:
        ds = ds.copy()
        ds.point_data[out_name] = np.linalg.norm(arr, axis=1)
        return ds, out_name
    return ds, name


def center_of(ds: pv.DataSet) -> np.ndarray:
    return np.asarray(ds.center, dtype=float)


def domain_diagonal(ds: pv.DataSet) -> float:
    b = ds.bounds
    return math.sqrt((b[1]-b[0])**2 + (b[3]-b[2])**2 + (b[5]-b[4])**2)


def scalar_range(ds: pv.DataSet, name: str) -> tuple[float, float]:
    ds = ensure_point_data(ds, name)
    arr = np.asarray(ds.point_data[name], dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise ValueError(f"No finite values for {name}")
    return float(arr.min()), float(arr.max())


def global_range(cases: list[dict], key: str) -> tuple[float, float] | None:
    vals = []
    for c in cases:
        if key not in c["resolved"] or c["resolved"][key] is None:
            continue
        try:
            vals.append(scalar_range(c["dataset"], c["resolved"][key]))
        except Exception:
            pass
    if not vals:
        return None
    return min(v[0] for v in vals), max(v[1] for v in vals)


def get_camera(ds: pv.DataSet, cfg: dict):
    if cfg.get("camera_position"):
        return cfg["camera_position"]
    b = ds.bounds
    c = center_of(ds)
    span = domain_diagonal(ds)
    # deterministic oblique engineering view
    return [
        [c[0] + 1.15*span, c[1] + 0.85*span, c[2] + 0.75*span],
        c.tolist(),
        [0.0, 1.0, 0.0],
    ]


def make_plotter(cfg: dict) -> pv.Plotter:
    p = pv.Plotter(off_screen=True, window_size=tuple(cfg["view"].get("image_size", [2400, 1600])))
    p.set_background(cfg["view"].get("background", "white"))
    return p


def scalar_bar_args(title: str, cfg: dict) -> dict:
    pub = cfg.get("publication", {})
    return {
        "title": title,
        "vertical": True,
        "position_x": 0.86,
        "position_y": 0.20,
        "width": pub.get("scalar_bar_width", 0.10),
        "height": pub.get("scalar_bar_height", 0.55),
        "title_font_size": pub.get("font_size", 22),
        "label_font_size": max(12, int(pub.get("font_size", 22)*0.72)),
        "n_labels": 5,
        "fmt": "%.3g",
        "color": "black",
    }


def screenshot(plotter: pv.Plotter, path: Path, camera):
    plotter.camera_position = camera
    plotter.show(auto_close=False)
    plotter.screenshot(str(path), transparent_background=False, return_img=False)
    plotter.close()


def render_mesh(case: dict, out: Path, cfg: dict):
    ds = case["dataset"]
    p = make_plotter(cfg)
    surf = ds.extract_surface()
    p.add_mesh(
        surf,
        color="#d9d9d9",
        show_edges=bool(cfg["view"].get("show_mesh_edges", True)),
        edge_color="#595959",
        line_width=0.35,
        smooth_shading=False,
    )
    p.add_text(f'{case["label"]}\nstatus: {case["status"]}', position="upper_left", font_size=14, color="black")
    screenshot(p, out / f'{case["id"]}__mesh.png', get_camera(ds, cfg))


def slice_for(ds: pv.DataSet, cfg: dict) -> pv.PolyData:
    origin = cfg["view"].get("slice_origin")
    if origin is None:
        origin = center_of(ds)
    normal = cfg["view"].get("slice_normal", [0.0, 1.0, 0.0])
    return ds.slice(normal=normal, origin=origin)


def render_scalar_slice(case: dict, field_key: str, title: str, clim, out: Path, cfg: dict, cmap="viridis"):
    name = case["resolved"].get(field_key)
    if name is None:
        return
    ds = ensure_point_data(case["dataset"], name)
    sl = slice_for(ds, cfg)
    p = make_plotter(cfg)
    p.add_mesh(sl, scalars=name, cmap=cmap, clim=clim, scalar_bar_args=scalar_bar_args(title, cfg))
    p.add_text(f'{case["label"]}\nstatus: {case["status"]}', position="upper_left", font_size=14, color="black")
    screenshot(p, out / f'{case["id"]}__{field_key}_slice.png', get_camera(ds, cfg))


def render_velocity_streamlines(case: dict, clim, out: Path, cfg: dict):
    vname = case["resolved"].get("velocity")
    mname = case["resolved"].get("velocity_magnitude")
    if vname is None or mname is None:
        return
    ds = ensure_point_data(case["dataset"], vname)
    ds = ensure_point_data(ds, mname)
    sl = slice_for(ds, cfg)
    p = make_plotter(cfg)
    p.add_mesh(sl, scalars=mname, cmap="viridis", clim=clim, opacity=0.95,
               scalar_bar_args=scalar_bar_args("Velocity magnitude [m/s]", cfg))

    seed_cfg = cfg["view"].get("streamline_seed", {})
    center = seed_cfg.get("center")
    if center is None:
        center = center_of(ds)
    radius = float(seed_cfg.get("radius_fraction_of_domain_diagonal", 0.06))*domain_diagonal(ds)
    n_points = int(seed_cfg.get("n_points", 250))
    try:
        stream = ds.streamlines(
            vectors=vname,
            source_center=center,
            source_radius=radius,
            n_points=n_points,
            max_time=float(seed_cfg.get("max_time", 10.0)),
            integration_direction="both",
            initial_step_length=0.02,
        )
        if stream.n_points > 0:
            p.add_mesh(stream.tube(radius=max(domain_diagonal(ds)*0.0012, 1e-6)), color="black", opacity=0.75)
    except Exception as exc:
        p.add_text(f"streamlines unavailable: {type(exc).__name__}", position="lower_left", font_size=10, color="black")
    p.add_text(f'{case["label"]}\nstatus: {case["status"]}', position="upper_left", font_size=14, color="black")
    screenshot(p, out / f'{case["id"]}__velocity_streamlines.png', get_camera(ds, cfg))


def render_free_surface(case: dict, out: Path, cfg: dict):
    name = case["resolved"].get("vof")
    if name is None:
        return
    ds = ensure_point_data(case["dataset"], name)
    iso = float(cfg["view"].get("vof_iso_value", 0.5))
    try:
        surf = ds.contour([iso], scalars=name)
    except Exception:
        return
    if surf.n_points == 0:
        return
    p = make_plotter(cfg)
    p.add_mesh(ds.extract_surface(), color="#efefef", opacity=0.12)
    p.add_mesh(surf, color="#4c78a8", opacity=0.80, smooth_shading=True)
    p.add_text(f'{case["label"]}\nWater volume fraction = {iso:g}\nstatus: {case["status"]}',
               position="upper_left", font_size=14, color="black")
    screenshot(p, out / f'{case["id"]}__free_surface_vof.png', get_camera(ds, cfg))


def inspect_case(case_cfg: dict, cfg: dict) -> dict:
    ds = load_dataset(Path(case_cfg["file"]))
    fields = cfg["fields"]
    resolved = {
        "velocity": resolve_array(ds, fields.get("velocity_vector_candidates", [])),
        "vof": resolve_array(ds, fields.get("water_volume_fraction_candidates", [])),
        "pressure": resolve_array(ds, fields.get("pressure_candidates", [])),
        "vorticity": resolve_array(ds, fields.get("vorticity_candidates", [])),
    }
    if resolved["velocity"]:
        ds, resolved["velocity_magnitude"] = vector_magnitude(ds, resolved["velocity"])
    else:
        resolved["velocity_magnitude"] = resolve_array(ds, ["Velocity Magnitude", "velocity_magnitude"])
    if resolved["vorticity"]:
        ds, resolved["vorticity_magnitude"] = magnitude_from_existing(ds, resolved["vorticity"], "Vorticity Magnitude")
    else:
        resolved["vorticity_magnitude"] = None
    return {**case_cfg, "dataset": ds, "resolved": resolved}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--output", type=Path, default=Path("q1_rendered"))
    args = ap.parse_args()

    cfg = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    pv.global_theme.font.family = "times"
    pv.global_theme.font.color = "black"
    pv.global_theme.show_edges = False

    cases = [inspect_case(c, cfg) for c in cfg["cases"]]

    # Global ranges are computed once across all cases so comparisons are honest.
    ranges = {
        "velocity_magnitude": global_range(cases, "velocity_magnitude"),
        "pressure": global_range(cases, "pressure"),
        "vorticity_magnitude": global_range(cases, "vorticity_magnitude"),
    }

    audit = []
    for c in cases:
        render_mesh(c, args.output, cfg)
        if ranges["velocity_magnitude"]:
            render_velocity_streamlines(c, ranges["velocity_magnitude"], args.output, cfg)
        render_free_surface(c, args.output, cfg)
        if ranges["pressure"]:
            render_scalar_slice(c, "pressure", "Pressure [Pa]", ranges["pressure"], args.output, cfg, cmap="coolwarm")
        if ranges["vorticity_magnitude"]:
            render_scalar_slice(c, "vorticity_magnitude", "Vorticity magnitude [1/s]", ranges["vorticity_magnitude"], args.output, cfg, cmap="magma")
        audit.append({
            "id": c["id"], "label": c["label"], "status": c["status"],
            "input_file": c["file"], "n_points": c["dataset"].n_points,
            "n_cells": c["dataset"].n_cells, "bounds": list(c["dataset"].bounds),
            "resolved_fields": c["resolved"],
        })

    (args.output / "render_audit.json").write_text(
        json.dumps({"global_ranges": ranges, "cases": audit}, indent=2), encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "global_ranges": ranges, "case_count": len(cases)}, indent=2))


if __name__ == "__main__":
    main()
