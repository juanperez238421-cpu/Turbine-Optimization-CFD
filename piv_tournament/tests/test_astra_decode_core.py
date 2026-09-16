"""SOFTWARE UNIT / INTEGRATION TESTS; generated video is not research evidence."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import cv2
import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from astra_piv.config import AstraConfig, VideoScanConfig, save_config
from astra_piv.pipeline import run_full_video_pipeline, run_source_audit
from astra_piv.provenance import audit_video_decode, assert_complete_scan, sha256_file
from astra_piv.video_scan import scan_video


class FakeCapture:
    def __init__(self, images, declared):
        self.images = iter(images)
        self.declared = declared
        self.released = False
    def isOpened(self):
        return True
    def get(self, key):
        return {cv2.CAP_PROP_FRAME_WIDTH: 64, cv2.CAP_PROP_FRAME_HEIGHT: 64,
                cv2.CAP_PROP_FPS: 10, cv2.CAP_PROP_FRAME_COUNT: self.declared}.get(key, 0)
    def read(self):
        frame = next(self.images, None)
        return frame is not None, frame
    def release(self):
        self.released = True


class TestDecodeCompleteness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.video = Path(cls.temp.name) / "generated_fixture.mkv"
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi",
                        "-i", "testsrc2=size=64x64:rate=10", "-frames:v", "8",
                        "-c:v", "ffv1", str(cls.video)], check=True, capture_output=True)
        cls.digest = sha256_file(cls.video)

    def config(self):
        cfg = AstraConfig()
        cfg.provenance.canonical_video_basename = self.video.name
        cfg.provenance.canonical_sha256 = self.digest
        cfg.provenance.canonical_reference = "SOFTWARE TEST fixture definition"
        cfg.video_scan.roi = [0, 0, 64, 64]
        cfg.video_scan.downscale = 1.0
        return cfg

    def test_full_scan_matches_independent_decoder_and_adjacent_pairs(self):
        decode = audit_video_decode(self.video, self.digest)
        self.assertTrue(decode["complete"])
        self.assertEqual(decode["decoded_frame_count"], 8)
        frames, pairs, meta = scan_video(self.video, self.config().video_scan, verified_frame_count=8,
                                         expected_source_sha256=self.digest)
        self.assertEqual(len(frames), 8)
        self.assertEqual(len(pairs), 7)
        np.testing.assert_array_equal(pairs["frame_b"] - pairs["frame_a"], np.ones(7))
        assert_complete_scan(meta, decode)

    def test_partial_scan_cannot_be_promoted_by_complete_decode(self):
        decode = audit_video_decode(self.video, self.digest)
        for limit in [4, 8]:
            with self.subTest(limit=limit):
                _, _, meta = scan_video(self.video, self.config().video_scan, max_frames=limit)
                self.assertFalse(meta["scan_complete"])
                self.assertEqual(meta["termination_reason"], "FRAME_LIMIT")
                with self.assertRaises(RuntimeError):
                    assert_complete_scan(meta, decode)

    def test_limit_larger_than_video_does_not_mislabel_complete_scan(self):
        _, _, meta = scan_video(self.video, self.config().video_scan, max_frames=20)
        self.assertTrue(meta["scan_complete"])

    def test_premature_read_stop_without_limit_is_not_completion(self):
        frames = np.random.default_rng(2).integers(0, 256, (6, 64, 64, 3), dtype=np.uint8)
        cap = FakeCapture(frames, declared=8)
        with patch("astra_piv.video_scan.cv2.VideoCapture", return_value=cap):
            _, _, meta = scan_video("synthetic", VideoScanConfig(downscale=1))
        self.assertFalse(meta["scan_complete"])
        self.assertEqual(meta["termination_reason"], "UNVERIFIED_OR_EARLY_READ_STOP")
        self.assertTrue(cap.released)

    def test_unknown_frame_count_needs_independent_count(self):
        frames = np.random.default_rng(2).integers(0, 256, (6, 64, 64, 3), dtype=np.uint8)
        for expected, complete in [(None, False), (6, True)]:
            with self.subTest(expected=expected):
                with patch("astra_piv.video_scan.cv2.VideoCapture", return_value=FakeCapture(frames, 0)):
                    _, _, meta = scan_video("synthetic", VideoScanConfig(downscale=1), verified_frame_count=expected)
                self.assertEqual(meta["scan_complete"], complete)

    def test_disagreeing_frame_counts_are_blocked(self):
        _, _, meta = scan_video(self.video, self.config().video_scan, verified_frame_count=9)
        self.assertFalse(meta["scan_complete"])

    def test_source_digest_change_blocks_decode_audit(self):
        audit = audit_video_decode(self.video, "0" * 64)
        self.assertFalse(audit["source_unchanged"])
        self.assertFalse(audit["complete"])

    def test_source_change_during_feature_scan_blocks_evidence(self):
        with patch("astra_piv.video_scan.sha256_file", return_value="0" * 64):
            _, _, meta = scan_video(self.video, self.config().video_scan, expected_source_sha256=self.digest)
        self.assertFalse(meta["scan_complete"])
        self.assertEqual(meta["termination_reason"], "SOURCE_CHANGED")

    def test_error_or_missing_end_marker_blocks_decode_audit(self):
        for code, output, error in [(1, "frame=8\nprogress=end\n", "decode failure"),
                                     (0, "frame=8\n", ""),
                                     (0, "frame=8\nprogress=end\n", "decoder reported corrupt data")]:
            with self.subTest(code=code, output=output, error=error):
                result = subprocess.CompletedProcess([], code, output, error)
                with patch("astra_piv.provenance.subprocess.run", return_value=result):
                    self.assertFalse(audit_video_decode(self.video, self.digest)["complete"])

    def test_shape_change_blocks_scan_and_releases_decoder(self):
        frames = [np.ones((64, 64, 3), np.uint8), np.ones((48, 64, 3), np.uint8)]
        cap = FakeCapture(frames, 2)
        with patch("astra_piv.video_scan.cv2.VideoCapture", return_value=cap):
            _, _, meta = scan_video("synthetic", VideoScanConfig(downscale=1))
        self.assertFalse(meta["scan_complete"])
        self.assertEqual(meta["shape_mismatch_count"], 1)
        self.assertTrue(cap.released)

    def test_metric_exception_releases_decoder(self):
        cap = FakeCapture([np.ones((64, 64, 3), np.uint8)], 1)
        with patch("astra_piv.video_scan.cv2.VideoCapture", return_value=cap), \
             patch("astra_piv.video_scan.compute_frame_metrics", side_effect=ValueError("bad ROI")):
            with self.assertRaises(ValueError):
                scan_video("synthetic", VideoScanConfig())
        self.assertTrue(cap.released)

    def test_source_runner_persists_truthful_partial_evidence(self):
        with tempfile.TemporaryDirectory() as out:
            report = run_source_audit(self.video, self.config(), out, scan_features=True, max_frames=4)
            self.assertTrue(report["decode_audit"]["complete"])
            self.assertFalse(report["source_evidence"]["full_raw_video_scanned"])
            self.assertFalse(report["source_evidence"]["delta_t_resolved"])
            self.assertIsNone(report["publication_selector"])
            self.assertFalse(report["cfd_used"])
            self.assertEqual(json.loads((Path(out)/"source_audit.json").read_text()), report)

    def test_source_audit_rejects_change_during_feature_scan(self):
        with tempfile.TemporaryDirectory() as out, \
             patch("astra_piv.video_scan.sha256_file", return_value="0" * 64):
            report = run_source_audit(self.video, self.config(), out, scan_features=True)
        self.assertEqual(report["status"], "M0_BLOCKED")
        self.assertFalse(report["source_evidence"]["full_raw_video_scanned"])

    def test_strict_base_pipeline_stops_before_stationarity_on_partial_scan(self):
        with tempfile.TemporaryDirectory() as out, \
             patch("astra_piv.pipeline.detect_stationary_pool") as stationarity:
            with self.assertRaisesRegex(RuntimeError, "full feature scan"):
                run_full_video_pipeline(self.video, self.config(), out, max_frames=4)
            stationarity.assert_not_called()

    def test_superstudy_runner_stops_before_stationarity_on_partial_scan(self):
        spec = importlib.util.spec_from_file_location("test_runner", PROJECT/"scripts/run_astra_q1_superstudy.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as out:
            config_file = Path(out)/"fixture.json"
            save_config(self.config(), config_file)
            args = ["run", "--video", str(self.video), "--config", str(config_file),
                    "--output-dir", out, "--roi", "0", "0", "64", "64", "--max-frames", "4"]
            with patch.object(sys, "argv", args), patch.object(module, "detect_stationary_pool") as stationarity:
                with self.assertRaisesRegex(RuntimeError, "full feature scan"):
                    module.main()
                stationarity.assert_not_called()

    def test_experimental_entrypoints_require_cfd_lock(self):
        cfg = self.config(); cfg.cfd_lockbox = False
        for runner in [run_source_audit, run_full_video_pipeline]:
            with self.subTest(runner=runner.__name__), tempfile.TemporaryDirectory() as out:
                with self.assertRaisesRegex(RuntimeError, "cfd_lockbox"):
                    runner("must-not-open", cfg, out)


if __name__ == "__main__":
    unittest.main()
