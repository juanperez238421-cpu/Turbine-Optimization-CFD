from __future__ import annotations

from pathlib import Path
import json
import math
from typing import Iterable

import cv2
import numpy as np
import pandas as pd

from .config import CoarsePIVConfig
from .video_scan import crop_roi, robust_normalize

EPS = 1e-12

def _preprocess_tile(tile: np.ndarray, cfg: CoarsePIVConfig) -> np.ndarray:
    x = tile.astype(np.uint8, copy=False)
    if cfg.preprocess_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)); x = clahe.apply(x)
    if cfg.highpass_kernel_px and cfg.highpass_kernel_px >= 3:
        k = int(cfg.highpass_kernel_px) | 1; bg = cv2.GaussianBlur(x, (k, k), 0); hp = cv2.subtract(x, bg)
    else: hp = x
    return robust_normalize(hp).astype(np.float32)

def _parabolic_offset(a: float, b: float, c: float) -> float:
    denom = a - 2.0*b + c
    return 0.0 if abs(denom)<1e-12 else float(0.5*(a-c)/denom)

def correlate_tiles(a: np.ndarray, b: np.ndarray, cfg: CoarsePIVConfig) -> dict[str,float]:
    a=_preprocess_tile(a,cfg); b=_preprocess_tile(b,cfg)
    if cfg.use_hanning:
        w=(np.hanning(a.shape[0])[:,None]*np.hanning(a.shape[1])[None,:]).astype(np.float32); a*=w; b*=w
    corr=np.fft.fftshift(np.fft.ifft2(np.fft.fft2(a)*np.conj(np.fft.fft2(b))).real).astype(np.float64)
    py,px=map(int,np.unravel_index(int(np.argmax(corr)),corr.shape)); peak=float(corr[py,px])
    mask=np.ones(corr.shape,bool); r=int(cfg.peak_exclusion_radius_px); mask[max(0,py-r):min(corr.shape[0],py+r+1),max(0,px-r):min(corr.shape[1],px+r+1)]=False
    second=float(np.max(corr[mask])) if np.any(mask) else np.nan; baseline=float(np.median(corr))
    ppr=(peak-baseline)/max(second-baseline,EPS) if np.isfinite(second) else np.nan
    pce=(peak-baseline)**2/max(float(np.mean((corr-baseline)**2)),EPS)
    subx=_parabolic_offset(corr[py,px-1],corr[py,px],corr[py,px+1]) if 1<=px<corr.shape[1]-1 else 0.0
    suby=_parabolic_offset(corr[py-1,px],corr[py,px],corr[py+1,px]) if 1<=py<corr.shape[0]-1 else 0.0
    dx=float((px+subx)-(corr.shape[1]-1)/2.0); dy=float((py+suby)-(corr.shape[0]-1)/2.0)
    return {"dx_px":dx,"dy_px":dy,"disp_px":float(math.hypot(dx,dy)),"peak":peak,"second_peak":second,"ppr":float(ppr),"pce":float(pce)}

def interrogation_centers(width:int,height:int,window:int,rows:int,cols:int):
    half=window//2
    if width<window or height<window: raise ValueError(f"ROI {width}x{height} is smaller than interrogation window {window}px")
    xs=np.linspace(half,width-half-1,cols); ys=np.linspace(half,height-half-1,rows)
    return [(int(round(x)),int(round(y))) for y in ys for x in xs]

def _window(img,cx,cy,window):
    half=window//2; return img[cy-half:cy-half+window,cx-half:cx-half+window]

def _empirical_quantile_scale(x,low_q,high_q):
    x=np.asarray(x,float); finite=np.isfinite(x); out=np.zeros_like(x,float)
    if not np.any(finite): return out
    lo,hi=np.nanpercentile(x[finite],[low_q,high_q])
    if hi<=lo+EPS: out[finite]=0.5; return out
    out[finite]=np.clip((x[finite]-lo)/(hi-lo),0,1); return out

def scan_coarse_piv(video_path, pair_indices:Iterable[int], cfg:CoarsePIVConfig, roi, output_dir=None):
    video_path=Path(video_path); pair_indices=sorted({int(i) for i in pair_indices if int(i)>=0})
    if cfg.max_pairs is not None: pair_indices=pair_indices[:int(cfg.max_pairs)]
    wanted=set(pair_indices)
    if not wanted: raise ValueError("No candidate pair indices supplied.")
    cap=cv2.VideoCapture(str(video_path))
    if not cap.isOpened(): raise RuntimeError(f"Cannot open {video_path}")
    rows=[]; tile_records=[]; pair_order=[]; prev_gray=None; frame_idx=0; centers=None; roi_shape=None
    while True:
        ok,frame=cap.read()
        if not ok: break
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            pair_idx=frame_idx-1
            if pair_idx in wanted:
                a=crop_roi(prev_gray,roi); b=crop_roi(gray,roi)
                if centers is None:
                    roi_shape=a.shape; centers=interrogation_centers(a.shape[1],a.shape[0],cfg.window_px,cfg.grid_rows,cfg.grid_cols)
                tm=[]
                for tile_id,(cx,cy) in enumerate(centers):
                    m=correlate_tiles(_window(a,cx,cy,cfg.window_px),_window(b,cx,cy,cfg.window_px),cfg); m.update({"tile_id":tile_id,"cx_px":cx,"cy_px":cy}); tm.append(m)
                pce=np.array([m["pce"] for m in tm]); ppr=np.array([m["ppr"] for m in tm]); disp=np.array([m["disp_px"] for m in tm])
                rows.append({"pair_index":pair_idx,"coarse_pce_median":float(np.nanmedian(pce)),"coarse_pce_p10":float(np.nanpercentile(pce,10)),"coarse_ppr_median":float(np.nanmedian(ppr)),"coarse_ppr_p10":float(np.nanpercentile(ppr,10)),"coarse_disp_median_px":float(np.nanmedian(disp)),"coarse_disp_p90_px":float(np.nanpercentile(disp,90)),"coarse_disp_p90_over_window":float(np.nanpercentile(disp,90)/cfg.window_px)})
                tile_records.append(tm); pair_order.append(pair_idx)
        prev_gray=gray; frame_idx+=1
        if frame_idx>max(wanted)+1 and len(pair_order)==len(wanted): break
    cap.release()
    if len(pair_order)!=len(wanted): raise RuntimeError(f"Could not decode requested pair indices: {sorted(wanted.difference(pair_order))[:20]}")
    pce_matrix=np.array([[m["pce"] for m in tm] for tm in tile_records],float); ppr_matrix=np.array([[m["ppr"] for m in tm] for tm in tile_records],float)
    q_pce=_empirical_quantile_scale(pce_matrix,cfg.quality_low_quantile,cfg.quality_high_quantile); q_ppr=_empirical_quantile_scale(ppr_matrix,cfg.quality_low_quantile,cfg.quality_high_quantile)
    reliability=np.sqrt(np.clip(q_pce,0,1)*np.clip(q_ppr,0,1))
    summary_df=pd.DataFrame(rows).sort_values("pair_index").reset_index(drop=True); order_map={p:i for i,p in enumerate(pair_order)}; idx=[order_map[int(p)] for p in summary_df["pair_index"]]; reliability=reliability[idx,:]
    meta={"video_path":str(video_path),"n_pairs":len(summary_df),"window_px":cfg.window_px,"grid_rows":cfg.grid_rows,"grid_cols":cfg.grid_cols,"tile_count":int(cfg.grid_rows*cfg.grid_cols),"roi":roi,"roi_shape":list(roi_shape) if roi_shape is not None else None,"quality_definition":f"sqrt(empirical_q{cfg.quality_low_quantile:g}_q{cfg.quality_high_quantile:g}(PCE) * empirical_q{cfg.quality_low_quantile:g}_q{cfg.quality_high_quantile:g}(PPR))","warning":"Coarse PIV reliability is a selection proxy, not the final measurement field."}
    if output_dir is not None:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); summary_df.to_csv(out/"coarse_piv_pair_summary.csv",index=False); np.save(out/"coarse_piv_reliability.npy",reliability); np.save(out/"coarse_piv_pce_matrix.npy",pce_matrix[idx,:]); np.save(out/"coarse_piv_ppr_matrix.npy",ppr_matrix[idx,:]); np.save(out/"coarse_piv_pair_indices.npy",summary_df["pair_index"].to_numpy(int)); (out/"coarse_piv_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return summary_df,reliability,meta
