from __future__ import annotations

import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from .oracle_validation import _load_one


def effective_sample_size(x: np.ndarray, max_lag: int | None = None) -> dict:
    x = np.asarray(x, dtype=float); x = x[np.isfinite(x)]; n = len(x)
    if n < 3:
        return {"n":n,"ess":float(n),"integrated_autocorrelation_time":1.0,"acf":[1.0]}
    x = x - np.mean(x); var = np.dot(x, x) / n
    if var <= 1e-18:
        return {"n":n,"ess":float(n),"integrated_autocorrelation_time":1.0,"acf":[1.0]}
    max_lag = min(max_lag or (n//2), n-1); acf = [1.0]
    for lag in range(1, max_lag+1):
        acf.append(float(np.dot(x[:-lag], x[lag:]) / ((n-lag)*var)))
    s = 0.0
    for rho in acf[1:]:
        if rho <= 0: break
        s += rho
    tau = max(1.0, 1.0 + 2.0*s); ess = min(float(n), float(n/tau))
    return {"n":n,"ess":ess,"integrated_autocorrelation_time":tau,"acf":acf}


def load_direct_field_cube(paths: list[str | Path]):
    paths = [Path(p) for p in paths]; records=[]; active_ref=None; coords_ref=None; U=[]; V=[]; TYPES=[]
    for path in sorted(paths):
        meta, df = _load_one(path); coords = df[["x [m]","y [m]"]].to_numpy(float)
        vt = df["Vector type [-]"].astype(int).to_numpy(); active = vt != 0
        if active_ref is None:
            active_ref = active; coords_ref = coords
        else:
            if not np.array_equal(active, active_ref): raise ValueError("Active mask changes across PIVlab fields")
            if not np.allclose(coords, coords_ref, rtol=0, atol=1e-12): raise ValueError("Coordinate grid changes across PIVlab fields")
        u = df["u [m/s]"].to_numpy(float)[active_ref]; v = df["v [m/s]"].to_numpy(float)[active_ref]; t = vt[active_ref]
        u = np.where(t == 1, u, np.nan); v = np.where(t == 1, v, np.nan)
        U.append(u); V.append(v); TYPES.append(t)
        records.append({"pair_index":meta["frame_a"],"export_frame":meta["export_frame"],"direct_fraction":float(np.mean(t==1)),"median_direct_speed":float(np.nanmedian(np.sqrt(u*u+v*v)))})
    order = np.argsort([r["pair_index"] for r in records])
    return pd.DataFrame(records).iloc[order].reset_index(drop=True), np.asarray(U)[order], np.asarray(V)[order], np.asarray(TYPES)[order], coords_ref[active_ref]


def _nanmedian_silent(a, axis=0):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmedian(a, axis=axis)


def direct_only_reference(U: np.ndarray, V: np.ndarray, min_observations: int = 2):
    count = np.sum(np.isfinite(U) & np.isfinite(V), axis=0)
    uref = _nanmedian_silent(U, axis=0); vref = _nanmedian_silent(V, axis=0); valid = count >= min_observations
    return uref, vref, count, valid


def subset_field_metrics(U, V, subset_positions, reference_u, reference_v, reference_valid, min_subset_observations: int = 1) -> dict:
    us = U[subset_positions]; vs = V[subset_positions]; count = np.sum(np.isfinite(us) & np.isfinite(vs), axis=0)
    uhat = _nanmedian_silent(us, axis=0); vhat = _nanmedian_silent(vs, axis=0)
    valid = reference_valid & (count >= min_subset_observations) & np.isfinite(uhat) & np.isfinite(vhat)
    if np.any(valid):
        du = uhat[valid]-reference_u[valid]; dv = vhat[valid]-reference_v[valid]
        vector_rmse = float(np.sqrt(np.mean(du*du + dv*dv))); ref_speed=np.sqrt(reference_u[valid]**2+reference_v[valid]**2)
        nrmse = float(vector_rmse / max(np.nanmedian(ref_speed),1e-12))
    else: vector_rmse=np.nan; nrmse=np.nan
    return {"n_selected":int(len(subset_positions)),"cells_with_direct_measurement_fraction":float(np.mean(count>=min_subset_observations)),"direct_count_q10":float(np.quantile(count,0.10)),"direct_count_median":float(np.median(count)),"vector_rmse_to_full_direct_median_mps":vector_rmse,"nrmse_to_full_direct_median":nrmse}


def chronological_convergence(paths: list[str | Path], sample_sizes: list[int]) -> tuple[pd.DataFrame,dict]:
    pool,U,V,T,coords = load_direct_field_cube(paths); uref,vref,full_count,full_valid = direct_only_reference(U,V,min_observations=2); rows=[]
    for n in sample_sizes:
        if n > len(pool): continue
        pos = np.unique(np.round(np.linspace(0,len(pool)-1,n)).astype(int))
        row={"scheme":"systematic_full_span",**subset_field_metrics(U,V,pos,uref,vref,full_valid)}; row["requested_n"]=n; rows.append(row)
    ess = effective_sample_size(pool["median_direct_speed"].to_numpy(float))
    meta={"n_fields":len(pool),"n_active_cells":int(U.shape[1]),"full_reference_cells_min2_fraction":float(np.mean(full_valid)),"effective_sample_size_median_direct_speed":ess,"warning":"Convergence reference is the full available direct-only PIVlab ensemble, not CFD."}
    return pd.DataFrame(rows),meta


def write_convergence(paths: list[str | Path], sample_sizes: list[int], outdir: str | Path):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True); table,meta=chronological_convergence(paths,sample_sizes)
    table.to_csv(outdir/"direct_only_convergence.csv",index=False); (outdir/"direct_only_convergence_meta.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return table,meta
