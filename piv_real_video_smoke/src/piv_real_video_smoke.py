from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def robust_z(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    med = np.nanmedian(x)
    mad = np.nanmedian(np.abs(x - med))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale < eps:
        return np.zeros_like(x, dtype=float)
    return (x - med) / scale


def ffprobe_metadata(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,pix_fmt:"
        "format=duration,size,format_name",
        "-of", "json", str(path)
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def fraction_ge(img: np.ndarray, threshold: int) -> float:
    return float(np.mean(img >= threshold))


def fraction_le(img: np.ndarray, threshold: int) -> float:
    return float(np.mean(img <= threshold))


def best_windows(score: np.ndarray, window: int, top_k: int = 5) -> list[dict]:
    if len(score) < window:
        return []
    kernel = np.ones(window, dtype=float) / window
    rolling = np.convolve(score, kernel, mode="valid")
    order = np.argsort(rolling)
    chosen = []
    occupied = np.zeros(len(score), dtype=bool)
    for idx in order:
        start = int(idx)
        stop = start + window
        if occupied[start:stop].any():
            continue
        chosen.append({
            "start_frame_zero_based": start,
            "end_frame_zero_based_inclusive": stop - 1,
            "mean_transition_score": float(rolling[idx]),
        })
        occupied[start:stop] = True
        if len(chosen) >= top_k:
            break
    return chosen


def analyze_video(path: Path, outdir: Path, scale: float = 0.25) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    probe = ffprobe_metadata(path)
    stream = probe["streams"][0]
    fmt = probe["format"]

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")

    cap_width = int(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
    cap_height = int(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    cap_fps = float(cap.get(cv2.CAP_PROP_FPS))
    cap_frame_count = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT)))

    rows = []
    prev_small = None
    decoded = 0
    first_shape = None
    shape_mismatch_count = 0
    read_failures = 0

    hann = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if first_shape is None:
            first_shape = tuple(frame.shape)
        elif tuple(frame.shape) != first_shape:
            shape_mismatch_count += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(
            gray, None, fx=scale, fy=scale,
            interpolation=cv2.INTER_AREA
        )

        if hann is None:
            hann = cv2.createHanningWindow((small.shape[1], small.shape[0]), cv2.CV_32F)

        mean_i = float(np.mean(gray))
        std_i = float(np.std(gray))
        p01 = float(np.percentile(gray, 1))
        p99 = float(np.percentile(gray, 99))
        sat_frac = fraction_ge(gray, 250)
        dark_frac = fraction_le(gray, 5)

        lap = cv2.Laplacian(small, cv2.CV_32F)
        lap_var = float(np.var(lap))

        gx = cv2.Sobel(small, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(small, cv2.CV_32F, 0, 1, ksize=3)
        tenengrad = float(np.mean(gx * gx + gy * gy))

        if prev_small is None:
            madiff = np.nan
            rmse_diff = np.nan
            phase_dx = np.nan
            phase_dy = np.nan
            phase_response = np.nan
        else:
            diff = small.astype(np.float32) - prev_small.astype(np.float32)
            madiff = float(np.mean(np.abs(diff)))
            rmse_diff = float(np.sqrt(np.mean(diff * diff)))

            shift, response = cv2.phaseCorrelate(
                prev_small.astype(np.float32),
                small.astype(np.float32),
                hann
            )
            phase_dx = float(shift[0] / scale)
            phase_dy = float(shift[1] / scale)
            phase_response = float(response)

        rows.append({
            "frame_zero_based": decoded,
            "time_s": decoded / cap_fps if cap_fps > 0 else np.nan,
            "mean_intensity": mean_i,
            "std_intensity": std_i,
            "p01_intensity": p01,
            "p99_intensity": p99,
            "dynamic_range_p99_p01": p99 - p01,
            "saturated_fraction_ge250": sat_frac,
            "dark_fraction_le5": dark_frac,
            "laplacian_variance_small": lap_var,
            "tenengrad_small": tenengrad,
            "mean_abs_interframe_diff_small": madiff,
            "rmse_interframe_diff_small": rmse_diff,
            "phase_dx_original_px": phase_dx,
            "phase_dy_original_px": phase_dy,
            "phase_shift_mag_original_px": (
                math.hypot(phase_dx, phase_dy)
                if np.isfinite(phase_dx) and np.isfinite(phase_dy) else np.nan
            ),
            "phase_response": phase_response,
        })
        prev_small = small
        decoded += 1

    cap.release()

    df = pd.DataFrame(rows)
    if len(df) == 0:
        raise RuntimeError("Video decoded zero frames.")

    # Transition score: exploratory QA proxy only, not a scientific stationarity decision.
    feature_names = [
        "mean_intensity",
        "std_intensity",
        "mean_abs_interframe_diff_small",
        "phase_shift_mag_original_px",
        "phase_response",
    ]
    transition_parts = []
    for name in feature_names:
        x = df[name].to_numpy(dtype=float)
        dx = np.r_[np.nan, np.abs(np.diff(x))]
        z = np.abs(robust_z(dx))
        z[~np.isfinite(z)] = 0.0
        transition_parts.append(np.clip(z, 0, 10))

    transition_score = np.mean(np.vstack(transition_parts), axis=0)
    df["exploratory_transition_score"] = transition_score

    df.to_csv(outdir / "video_frame_metrics.csv", index=False)

    sha = sha256_file(path)

    fps_probe = eval_fraction(stream.get("avg_frame_rate", "0/1"))
    duration_probe = float(stream.get("duration") or fmt.get("duration") or np.nan)
    nb_frames_probe = int(stream["nb_frames"]) if stream.get("nb_frames") else None

    canonical_expected = {
        "expected_source_basename": "vid_2025-08-29_19-28-15.mp4",
        "legacy_xy_m_per_px": 0.00019061,
        "legacy_uv_mps_per_px_per_frame": 0.20386,
        "legacy_implied_dt_s": 0.00019061 / 0.20386,
        "legacy_implied_sampling_hz": 0.20386 / 0.00019061,
    }

    source_is_canonical = path.name == canonical_expected["expected_source_basename"]

    summary = {
        "status": "PASS_REAL_VIDEO_SMOKE",
        "scientific_scope": (
            "Real experimental video decoding and image-quality/temporal-proxy smoke test. "
            "This file is NOT treated as the canonical legacy PIV acquisition unless its "
            "basename and sampling metadata match the PIVlab export provenance."
        ),
        "video": {
            "path": str(path),
            "basename": path.name,
            "sha256": sha,
            "size_bytes": int(path.stat().st_size),
            "ffprobe": probe,
            "opencv": {
                "width": cap_width,
                "height": cap_height,
                "fps": cap_fps,
                "declared_frame_count": cap_frame_count,
                "decoded_frame_count": decoded,
                "first_frame_shape_bgr": list(first_shape),
                "shape_mismatch_count": shape_mismatch_count,
                "read_failures_before_eof": read_failures,
            },
        },
        "provenance_check": {
            **canonical_expected,
            "source_is_canonical_legacy_piv_video": source_is_canonical,
            "video_sampling_hz": cap_fps,
            "video_dimensions_px": [cap_width, cap_height],
            "classification": (
                "CANONICAL" if source_is_canonical
                else "REAL_EXPERIMENTAL_NONCANONICAL_SMOKE_SOURCE"
            ),
        },
        "qa_metrics": {
            "mean_intensity_median": float(df["mean_intensity"].median()),
            "std_intensity_median": float(df["std_intensity"].median()),
            "dynamic_range_median": float(df["dynamic_range_p99_p01"].median()),
            "saturated_fraction_median": float(df["saturated_fraction_ge250"].median()),
            "saturated_fraction_max": float(df["saturated_fraction_ge250"].max()),
            "dark_fraction_median": float(df["dark_fraction_le5"].median()),
            "dark_fraction_max": float(df["dark_fraction_le5"].max()),
            "laplacian_variance_median": float(df["laplacian_variance_small"].median()),
            "phase_shift_mag_median_px": float(df["phase_shift_mag_original_px"].median()),
            "phase_shift_mag_p95_px": float(df["phase_shift_mag_original_px"].quantile(0.95)),
            "phase_response_median": float(df["phase_response"].median()),
            "interframe_mad_median": float(df["mean_abs_interframe_diff_small"].median()),
        },
        "exploratory_low_transition_windows_60_frames": best_windows(
            transition_score, window=min(60, len(df)), top_k=5
        ),
    }

    (outdir / "video_smoke_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    plot_series(df, outdir)
    make_contact_sheet(path, outdir, frame_indices=[
        0,
        int(len(df) * 0.2),
        int(len(df) * 0.4),
        int(len(df) * 0.6),
        int(len(df) * 0.8),
        len(df) - 1,
    ])

    return summary


def eval_fraction(value: str) -> float:
    if "/" in value:
        a, b = value.split("/", 1)
        return float(a) / float(b)
    return float(value)


def plot_series(df: pd.DataFrame, outdir: Path) -> None:
    for col, ylabel, fname in [
        ("mean_intensity", "Mean grayscale intensity", "mean_intensity_vs_time.png"),
        ("std_intensity", "Grayscale standard deviation", "contrast_vs_time.png"),
        ("mean_abs_interframe_diff_small", "Mean absolute inter-frame difference", "interframe_difference_vs_time.png"),
        ("phase_shift_mag_original_px", "Phase-correlation shift magnitude (original px)", "phase_shift_vs_time.png"),
        ("phase_response", "Phase-correlation response", "phase_response_vs_time.png"),
        ("saturated_fraction_ge250", "Fraction of pixels >= 250", "saturation_vs_time.png"),
        ("exploratory_transition_score", "Exploratory transition score", "transition_score_vs_time.png"),
    ]:
        fig = plt.figure(figsize=(8, 4.5))
        ax = fig.add_subplot(111)
        ax.plot(df["time_s"], df[col])
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.set_title(fname.replace("_", " ").replace(".png", "").title())
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        fig.savefig(outdir / fname, dpi=170)
        plt.close(fig)


def make_contact_sheet(path: Path, outdir: Path, frame_indices: list[int]) -> None:
    cap = cv2.VideoCapture(str(path))
    images = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        images.append((idx, frame_rgb))
    cap.release()

    if not images:
        return

    fig = plt.figure(figsize=(12, 8))
    cols = 3
    rows = int(math.ceil(len(images) / cols))
    for k, (idx, image) in enumerate(images, start=1):
        ax = fig.add_subplot(rows, cols, k)
        ax.imshow(image)
        ax.set_title(f"Frame {idx}")
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(outdir / "real_video_contact_sheet.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--scale", type=float, default=0.25)
    args = parser.parse_args()
    summary = analyze_video(args.video, args.outdir, scale=args.scale)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
