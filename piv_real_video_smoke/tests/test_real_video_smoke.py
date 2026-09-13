from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "outputs"
VIDEO = Path(os.environ.get("PIV_REAL_VIDEO_PATH", "/mnt/data/vid_2025-08-29_19-36-07.mp4"))


class TestRealVideoSmoke(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not VIDEO.exists():
            raise unittest.SkipTest(
                "Real experimental video is not mounted. Set PIV_REAL_VIDEO_PATH to run the real-data suite."
            )
        cls.summary = json.loads((OUT / "video_smoke_summary.json").read_text())
        cls.metrics = pd.read_csv(OUT / "video_frame_metrics.csv")

    def test_01_real_file_exists_and_nontrivial_size(self):
        self.assertTrue(VIDEO.exists())
        self.assertEqual(VIDEO.stat().st_size, 91_113_099)

    def test_02_sha256_matches_manifest(self):
        h = hashlib.sha256()
        with VIDEO.open("rb") as f:
            for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
                h.update(chunk)
        self.assertEqual(
            h.hexdigest(),
            "422439b944c36423db3c37e9540874280b7ced4dc5be8533b320a4b4d7810331"
        )
        self.assertEqual(h.hexdigest(), self.summary["video"]["sha256"])

    def test_03_dimensions_are_1280_by_1024(self):
        opencv = self.summary["video"]["opencv"]
        self.assertEqual(opencv["width"], 1280)
        self.assertEqual(opencv["height"], 1024)

    def test_04_video_is_60_fps(self):
        self.assertAlmostEqual(self.summary["video"]["opencv"]["fps"], 60.0, places=6)

    def test_05_all_declared_frames_decode(self):
        opencv = self.summary["video"]["opencv"]
        self.assertEqual(opencv["declared_frame_count"], 1042)
        self.assertEqual(opencv["decoded_frame_count"], 1042)
        self.assertEqual(len(self.metrics), 1042)

    def test_06_no_shape_change(self):
        self.assertEqual(self.summary["video"]["opencv"]["shape_mismatch_count"], 0)

    def test_07_metrics_are_finite_after_first_pair(self):
        required = [
            "mean_intensity", "std_intensity", "dynamic_range_p99_p01",
            "saturated_fraction_ge250", "dark_fraction_le5",
            "laplacian_variance_small"
        ]
        self.assertFalse(self.metrics[required].isna().any().any())
        temporal = [
            "mean_abs_interframe_diff_small",
            "phase_shift_mag_original_px",
            "phase_response",
        ]
        self.assertFalse(self.metrics.loc[1:, temporal].isna().any().any())

    def test_08_not_canonical_legacy_piv_video(self):
        prov = self.summary["provenance_check"]
        self.assertFalse(prov["source_is_canonical_legacy_piv_video"])
        self.assertEqual(
            prov["classification"],
            "REAL_EXPERIMENTAL_NONCANONICAL_SMOKE_SOURCE"
        )

    def test_09_canonical_legacy_rate_is_incompatible_with_this_file(self):
        prov = self.summary["provenance_check"]
        self.assertGreater(prov["legacy_implied_sampling_hz"], 1000)
        self.assertAlmostEqual(prov["video_sampling_hz"], 60.0, places=6)
        self.assertGreater(
            prov["legacy_implied_sampling_hz"] / prov["video_sampling_hz"],
            17.0
        )

    def test_10_zero_saturation_is_observed(self):
        q = self.summary["qa_metrics"]
        self.assertEqual(q["saturated_fraction_max"], 0.0)

    def test_11_dark_fraction_is_nonzero_and_bounded(self):
        q = self.summary["qa_metrics"]
        self.assertGreater(q["dark_fraction_median"], 0.0)
        self.assertLess(q["dark_fraction_max"], 0.10)

    def test_12_real_video_has_strong_temporal_illumination_modulation(self):
        x = self.metrics["mean_intensity"].to_numpy(float)
        rel_range = (np.max(x) - np.min(x)) / np.median(x)
        self.assertGreater(rel_range, 0.5)

    def test_13_output_figures_exist(self):
        expected = [
            "mean_intensity_vs_time.png",
            "contrast_vs_time.png",
            "interframe_difference_vs_time.png",
            "phase_shift_vs_time.png",
            "phase_response_vs_time.png",
            "saturation_vs_time.png",
            "transition_score_vs_time.png",
            "real_video_contact_sheet.png",
        ]
        for name in expected:
            self.assertTrue((OUT / name).exists(), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
