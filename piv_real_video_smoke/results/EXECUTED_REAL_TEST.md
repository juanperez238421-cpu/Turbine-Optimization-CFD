# Executed real-video test record

## Source actually processed

- File: `vid_2025-08-29_19-36-07.mp4`
- SHA-256: `422439b944c36423db3c37e9540874280b7ced4dc5be8533b320a4b4d7810331`
- Size: 91,113,099 bytes
- Resolution: 1280 × 1024 px
- Video rate: 60.0 Hz
- Declared frame count: 1042
- Successfully decoded frame count: 1042
- Shape mismatches: 0

## Automated verification

The exact GitHub-branch Python sources were compiled and the real-data unit suite was re-run with `PIV_REAL_VIDEO_PATH` pointing to the source above.

Result: **13/13 PASS**.

Checks include file identity, SHA-256 integrity, dimensions, frame rate, complete decoding, constant frame shape, finite QA metrics, provenance rejection as canonical PIV input, sampling-rate incompatibility with the legacy PIV source, saturation/dark-pixel checks, observed temporal illumination modulation, and output generation.

## Real-data QA findings

- Median mean intensity: 37.6781 gray levels
- Mean-intensity range: 21.5804–50.7760
- Relative peak-to-peak intensity range / median: 0.77487
- Mean-intensity coefficient of variation: 0.27091
- Median 1st–99th percentile dynamic range: 78 gray levels
- Saturated fraction (`gray >= 250`): median 0, maximum 0
- Dark fraction (`gray <= 5`): median 0.01316, maximum 0.08939
- Median phase-correlation shift magnitude: 0.0823 original pixels
- 95th-percentile phase-correlation shift magnitude: 0.1881 original pixels
- Dominant mean-intensity modulation: 6.79463 Hz
- Corresponding period: 0.14718 s (~8.83 frames at 60 Hz)

## Provenance decision

This source is **real experimental video**, but it is **not** the canonical video used by the legacy PIVlab exports. Those exports identify `vid_2025-08-29_19-28-15.mp4` and imply `Δt = 0.935004 ms` / `f ≈ 1069.51 Hz`. Therefore the current 60 Hz source is classified as:

`REAL_EXPERIMENTAL_NONCANONICAL_SMOKE_SOURCE`

No threshold learned from this file is allowed to enter the publication PIV selector without confirmation on the canonical high-speed acquisition.

## Current blocker

The canonical `vid_2025-08-29_19-28-15.mp4` is ~715 MB and currently exceeds the connected Drive transfer limit. The next publication-level test must run the same code, followed by PIV-native pair metrics, on that exact source or on a lossless/local extraction of its frames.
