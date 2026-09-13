from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2


def local_maxima_indices(x: np.ndarray, k: int = 3):
    idx = []
    for i in range(k, len(x)-k):
        if x[i] == np.max(x[i-k:i+k+1]):
            idx.append(i)
    return np.asarray(idx, dtype=int)


def spectral_analysis(metrics_csv: Path, video: Path, outdir: Path):
    df = pd.read_csv(metrics_csv)
    fs = 1.0 / np.median(np.diff(df["time_s"].to_numpy(float)))
    x = df["mean_intensity"].to_numpy(float)
    x0 = x - np.mean(x)

    n = len(x0)
    window = np.hanning(n)
    spec = np.fft.rfft(x0 * window)
    freqs = np.fft.rfftfreq(n, d=1/fs)
    power = np.abs(spec)**2
    power[0] = 0

    order = np.argsort(power)[::-1]
    peaks = []
    used = []
    for j in order:
        f = float(freqs[j])
        if f <= 0:
            continue
        if any(abs(f-u) < fs/n*2 for u in used):
            continue
        peaks.append({"frequency_hz": f, "relative_power": float(power[j]/power[order[0]])})
        used.append(f)
        if len(peaks) >= 10:
            break

    dominant = peaks[0]["frequency_hz"]
    period_s = 1.0 / dominant

    bright_idx = np.argsort(x)[-6:][::-1]
    dark_idx = np.argsort(x)[:6]

    summary = {
        "sampling_hz": float(fs),
        "n_frames": int(n),
        "duration_from_metrics_s": float(df["time_s"].iloc[-1]),
        "intensity": {
            "min": float(np.min(x)),
            "max": float(np.max(x)),
            "median": float(np.median(x)),
            "relative_peak_to_peak_over_median": float((np.max(x)-np.min(x))/np.median(x)),
            "coefficient_of_variation": float(np.std(x, ddof=1)/np.mean(x)),
        },
        "dominant_modulation": {
            "frequency_hz": float(dominant),
            "period_s": float(period_s),
            "frames_per_period": float(fs/dominant),
        },
        "top_spectral_peaks": peaks,
        "brightest_frames_zero_based": [int(i) for i in bright_idx],
        "darkest_frames_zero_based": [int(i) for i in dark_idx],
    }
    (outdir / "illumination_spectrum_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    fig = plt.figure(figsize=(8,4.6))
    ax = fig.add_subplot(111)
    ax.plot(freqs[1:], power[1:]/np.max(power[1:]))
    ax.set_xlim(0, min(30, fs/2))
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Normalized power")
    ax.set_title("Mean-intensity temporal spectrum")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(outdir / "illumination_spectrum.png", dpi=180)
    plt.close(fig)

    cap = cv2.VideoCapture(str(video))
    selected = [("bright", int(i)) for i in bright_idx[:3]] + [("dark", int(i)) for i in dark_idx[:3]]
    fig = plt.figure(figsize=(12,7.5))
    for k, (label, idx) in enumerate(selected, start=1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ax = fig.add_subplot(2,3,k)
        ax.imshow(rgb)
        ax.set_title(f"{label}: frame {idx}, mean={x[idx]:.2f}")
        ax.axis("off")
    cap.release()
    fig.tight_layout()
    fig.savefig(outdir / "bright_dark_extrema_contact_sheet.png", dpi=170)
    plt.close(fig)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--metrics", type=Path, required=True)
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    a = p.parse_args()
    spectral_analysis(a.metrics, a.video, a.outdir)
