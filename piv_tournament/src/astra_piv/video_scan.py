from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
from typing import Iterator

import cv2
import numpy as np
import pandas as pd

from .config import VideoScanConfig
from .provenance import sha256_file


EPS = 1e-12


def robust_location_scale(img: np.ndarray) -> tuple[float, float]:
    x = img.astype(np.float32)
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    scale = max(1.4826 * mad, 1.0)
    return med, scale


def robust_normalize(img: np.ndarray) -> np.ndarray:
    med, scale = robust_location_scale(img)
    z = (img.astype(np.float32) - med) / scale
    return np.clip(z, -6.0, 6.0)


def crop_roi(gray: np.ndarray, roi: list[int] | None) -> np.ndarray:
    if roi is None:
        return gray
    x0, y0, x1, y1 = map(int, roi)
    if not (0 <= x0 < x1 <= gray.shape[1] and 0 <= y0 < y1 <= gray.shape[0]):
        raise ValueError(f"ROI {roi} is outside frame shape {gray.shape[::-1]}")
    return gray[y0:y1, x0:x1]


def _component_blob_metrics(binary_u8: np.ndarray, min_area: int, max_area: int) -> tuple[int, float, float]:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary_u8, connectivity=8)
    if n <= 1:
        return 0, 0.0, 0.0
    areas = stats[1:, cv2.CC_STAT_AREA].astype(float)
    good = (areas >= min_area) & (areas <= max_area)
    large = areas > max_area
    return int(np.sum(good)), float(np.sum(areas[good])), float(np.sum(areas[large]))


def _dark_region_proxy(norm: np.ndarray) -> tuple[float, float, float]:
    """Return dark-area fraction and centroid in normalized coordinates.

    This is an optical proxy only; it must not be called the physical vortex core without
    independent geometric validation.
    """
    h, w = norm.shape
    threshold = np.percentile(norm, 10.0)
    mask = (norm <= threshold).astype(np.uint8)
    k = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return 0.0, np.nan, np.nan
    areas = stats[1:, cv2.CC_STAT_AREA]
    j = int(np.argmax(areas)) + 1
    area = float(stats[j, cv2.CC_STAT_AREA])
    cx, cy = centroids[j]
    return area / float(h * w), float(cx / max(w - 1, 1)), float(cy / max(h - 1, 1))


def compute_frame_metrics(gray_original: np.ndarray, cfg: VideoScanConfig) -> dict[str, float]:
    roi = crop_roi(gray_original, cfg.roi)
    small = cv2.resize(roi, None, fx=cfg.downscale, fy=cfg.downscale, interpolation=cv2.INTER_AREA)
    norm = robust_normalize(small)
    p01, p05, p50, p95, p99 = np.percentile(roi, [1, 5, 50, 95, 99])
    sat = float(np.mean(roi >= 250))
    dark = float(np.mean(roi <= 5))
    lap_var = float(np.var(cv2.Laplacian(norm, cv2.CV_32F)))
    gx = cv2.Sobel(norm, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(norm, cv2.CV_32F, 0, 1, ksize=3)
    tenengrad = float(np.mean(gx * gx + gy * gy))
    norm_8 = cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    kernel_size = max(3, int(cfg.top_hat_kernel_px_small) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    top_hat = cv2.morphologyEx(norm_8, cv2.MORPH_TOPHAT, kernel)
    th_med = float(np.median(top_hat))
    th_mad = float(np.median(np.abs(top_hat.astype(np.float32) - th_med)))
    threshold = th_med + 3.0 * max(1.4826 * th_mad, 1.0)
    particle_binary = (top_hat >= threshold).astype(np.uint8)
    blob_count, blob_area, large_bright_area = _component_blob_metrics(particle_binary, cfg.blob_area_min_small, cfg.blob_area_max_small)
    small_area = float(small.size)
    dark_area, dark_cx, dark_cy = _dark_region_proxy(norm)
    return {
        "mean_intensity": float(np.mean(roi)), "std_intensity": float(np.std(roi)),
        "p01_intensity": float(p01), "p05_intensity": float(p05), "p50_intensity": float(p50),
        "p95_intensity": float(p95), "p99_intensity": float(p99),
        "robust_dynamic_range_p95_p05": float(p95 - p05),
        "saturated_fraction_ge250": sat, "dark_fraction_le5": dark,
        "normalized_laplacian_variance": lap_var, "normalized_tenengrad": tenengrad,
        "particle_like_blob_count_proxy": float(blob_count),
        "particle_like_blob_density_proxy": float(blob_count / max(small_area, 1.0)),
        "particle_like_area_fraction_proxy": float(blob_area / max(small_area, 1.0)),
        "large_bright_component_area_fraction_proxy": float(large_bright_area / max(small_area, 1.0)),
        "optical_dark_region_fraction_proxy": dark_area,
        "optical_dark_region_cx_proxy": dark_cx, "optical_dark_region_cy_proxy": dark_cy,
    }


def _phase_pair_metrics(prev_gray: np.ndarray, curr_gray: np.ndarray, cfg: VideoScanConfig) -> dict[str, float]:
    a = crop_roi(prev_gray, cfg.roi); b = crop_roi(curr_gray, cfg.roi)
    a = cv2.resize(a, None, fx=cfg.downscale, fy=cfg.downscale, interpolation=cv2.INTER_AREA)
    b = cv2.resize(b, None, fx=cfg.downscale, fy=cfg.downscale, interpolation=cv2.INTER_AREA)
    az = robust_normalize(a).astype(np.float32); bz = robust_normalize(b).astype(np.float32)
    diff = bz - az
    madiff = float(np.mean(np.abs(diff))); rmse = float(np.sqrt(np.mean(diff * diff)))
    corr = float(np.corrcoef(az.ravel(), bz.ravel())[0, 1]) if az.size > 2 else np.nan
    hann = cv2.createHanningWindow((az.shape[1], az.shape[0]), cv2.CV_32F)
    shift, response = cv2.phaseCorrelate(az, bz, hann)
    dx = float(shift[0] / cfg.downscale); dy = float(shift[1] / cfg.downscale)
    return {"normalized_interframe_mad": madiff, "normalized_interframe_rmse": rmse,
            "normalized_frame_correlation": corr, "phase_dx_original_px": dx,
            "phase_dy_original_px": dy, "phase_shift_magnitude_original_px": float(math.hypot(dx, dy)),
            "phase_response": float(response)}


def scan_video(video_path: str | Path, cfg: VideoScanConfig, output_dir: str | Path | None = None, max_frames: int | None = None, verified_frame_count: int | None = None, expected_source_sha256: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Decode real video and compute frame/pair metrics after illumination normalization."""
    if max_frames is not None and (isinstance(max_frames, bool) or not isinstance(max_frames, int) or max_frames < 1):
        raise ValueError("max_frames must be a positive integer or None")
    if not (np.isfinite(cfg.downscale) and 0 < cfg.downscale <= 1):
        raise ValueError("downscale must be finite and in (0, 1]")
    video_path = Path(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened(): raise RuntimeError(f"Cannot open video: {video_path}")
    width = int(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))); height = int(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = float(cap.get(cv2.CAP_PROP_FPS)); declared = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    frame_rows=[]; pair_rows=[]; prev_gray=None; decoded=0; first_shape=None; shape_mismatch=0
    termination = "READ_STOP"
    try:
        while True:
            if max_frames is not None and decoded >= max_frames:
                termination = "FRAME_LIMIT"
                break
            ok, frame = cap.read()
            if not ok: break
            if first_shape is None: first_shape = tuple(frame.shape)
            elif tuple(frame.shape) != first_shape:
                shape_mismatch += 1
                termination = "SHAPE_CHANGE"
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            fr={"frame_index":decoded,"time_s":decoded/fps if fps>0 else np.nan,**compute_frame_metrics(gray,cfg)}
            frame_rows.append(fr)
            if prev_gray is not None:
                pr={"pair_index":decoded-1,"frame_a":decoded-1,"frame_b":decoded,
                    "time_a_s":(decoded-1)/fps if fps>0 else np.nan,"time_b_s":decoded/fps if fps>0 else np.nan,
                    **_phase_pair_metrics(prev_gray,gray,cfg)}
                prev_fr=frame_rows[-2]
                for col in ["saturated_fraction_ge250","dark_fraction_le5","normalized_laplacian_variance","normalized_tenengrad","particle_like_blob_density_proxy","particle_like_area_fraction_proxy","large_bright_component_area_fraction_proxy","optical_dark_region_fraction_proxy"]:
                    a_val,b_val=float(prev_fr[col]),float(fr[col]); pr[f"pair_{col}_mean"]=0.5*(a_val+b_val); pr[f"pair_{col}_max"]=max(a_val,b_val)
                for col in ["optical_dark_region_cx_proxy","optical_dark_region_cy_proxy"]:
                    a_val,b_val=float(prev_fr[col]),float(fr[col]); finite=[v for v in (a_val,b_val) if np.isfinite(v)]
                    pr[f"pair_{col}_mean"]=float(np.mean(finite)) if finite else np.nan
                    pr[f"pair_{col}_jump"]=float(abs(b_val-a_val)) if len(finite)==2 else np.nan
                pair_rows.append(pr)
            prev_gray=gray; decoded+=1
    finally:
        cap.release()
    frames=pd.DataFrame(frame_rows); pairs=pd.DataFrame(pair_rows)
    expected = verified_frame_count if verified_frame_count is not None else declared
    declaration_agrees = declared <= 0 or decoded == declared
    complete = bool(termination == "READ_STOP" and expected > 1 and decoded == expected
                    and declaration_agrees and shape_mismatch == 0 and len(pairs) == decoded - 1)
    digest_after = sha256_file(video_path) if expected_source_sha256 is not None else None
    unchanged = digest_after == expected_source_sha256 if expected_source_sha256 is not None else None
    if unchanged is False:
        complete = False
        termination = "SOURCE_CHANGED"
    if termination == "READ_STOP":
        termination = "COMPLETE_COUNT_MATCH" if complete else "UNVERIFIED_OR_EARLY_READ_STOP"
    meta={"video_path":str(video_path),"width":width,"height":height,"fps":fps,"declared_frame_count":declared,
          "decoded_frame_count":decoded,"pair_count":len(pairs),"first_frame_shape_bgr":list(first_shape) if first_shape is not None else None,
          "shape_mismatch_count":shape_mismatch,"roi":cfg.roi,"downscale":cfg.downscale,
          "requested_max_frames":max_frames,"termination_reason":termination,"scan_complete":complete,
          "verified_frame_count":verified_frame_count,
          "source_sha256_after_scan":digest_after,"source_unchanged":unchanged,
          "frame_index_origin":0,"pair_definition":"pair i = (frame i, frame i+1)",
          "time_columns_basis":"frame index / average container playback fps; not verified acquisition time"}
    if output_dir is not None:
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
        frames.to_csv(out/"frame_features.csv",index=False); pairs.to_csv(out/"pair_features_image.csv",index=False)
        (out/"video_scan_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return frames,pairs,meta
