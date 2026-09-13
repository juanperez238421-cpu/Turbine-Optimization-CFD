# Real experimental video smoke test

This code was executed against the real experimental file:

`vid_2025-08-29_19-36-07.mp4`

The goal is **not** to treat this file as the canonical PIV dataset. The original PIVlab
ASCII exports identify the canonical legacy source as:

`vid_2025-08-29_19-28-15.mp4`

The current Google Drive connector can stream the 91 MB `19-36-07` file, while the
~715 MB canonical `19-28-15` file exceeds the connector's 256 MiB transfer limit.

The test therefore validates the actual raw-video decoding and QA pipeline on real
experimental imagery and, critically, verifies that the software refuses to silently
confuse this 60 Hz video with the ~1069 Hz legacy PIV acquisition.

## What is measured

For every decoded frame:

- grayscale mean and standard deviation;
- robust 1st/99th percentile dynamic range;
- saturated and dark pixel fractions;
- Laplacian-variance sharpness proxy;
- Tenengrad gradient-energy proxy;
- inter-frame absolute/RMS difference;
- phase-correlation displacement proxy and response.

A second pass computes the temporal spectrum of the mean frame intensity to identify
illumination modulation. The current real video shows a dominant modulation near 6.795 Hz.
This is a real-data QA finding for this 60 Hz file; it is **not** transferred as a threshold
or correction to the canonical high-speed PIV dataset.

An exploratory transition score is generated for QA only. It is **not** yet the final
stationarity classifier.

## Scientific safeguards

- The full file is SHA-256 hashed.
- Every declared frame must decode.
- Frame geometry must remain constant.
- Canonical acquisition provenance is checked explicitly.
- No CFD data are used.
- No threshold from this noncanonical 60 Hz video is allowed to become a publication
  threshold for the canonical high-speed PIV acquisition.
- A noncanonical experimental video is never silently substituted for the legacy PIV source.

## Verified real-data run

Real source used for the smoke test:

- File: `vid_2025-08-29_19-36-07.mp4`
- SHA-256: `422439b944c36423db3c37e9540874280b7ced4dc5be8533b320a4b4d7810331`
- File size: 91,113,099 bytes
- Resolution: 1280 × 1024 px
- Frame rate: 60 Hz
- Declared frames: 1042
- Decoded frames: 1042
- Duration represented by frame timestamps: 17.35 s
- Automated tests: 13/13 PASS

## Run

```bash
python src/piv_real_video_smoke.py /path/to/vid_2025-08-29_19-36-07.mp4 --outdir outputs
python src/piv_real_video_flicker_audit.py \
  --metrics outputs/video_frame_metrics.csv \
  --video /path/to/vid_2025-08-29_19-36-07.mp4 \
  --outdir outputs
PIV_REAL_VIDEO_PATH=/path/to/vid_2025-08-29_19-36-07.mp4 \
  python -m unittest discover -s tests -v
```

## Scope boundary

This is a **real-video execution test**, not yet the canonical PIV tournament validation.
The canonical `vid_2025-08-29_19-28-15.mp4` must be analyzed locally or through a transfer
path that preserves the complete ~715 MB source before any publication-level stationarity,
frame/pair-selection, particle-density, correlation-quality, or uncertainty thresholds are frozen.
