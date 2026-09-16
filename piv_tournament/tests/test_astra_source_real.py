"""REAL VIDEO DIAGNOSTIC REGRESSION, requiring private input and saved CLI output.

Not a canonical PIV scientific test. CI skips without the actual recording.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import unittest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from astra_piv.provenance import sha256_file, ffprobe_video

VIDEO = Path(os.environ.get("ASTRA_REAL_VIDEO", "/missing/astra-real-video"))
OUTPUT = Path(os.environ.get("ASTRA_REAL_SOURCE_AUDIT_DIR", "/missing/astra-real-audit"))


@unittest.skipUnless(VIDEO.is_file() and (OUTPUT/"source_audit.json").is_file(),
                     "Private real video and executed source-audit outputs are required")
class TestRealSourceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT/"source_audit.json").read_text())

    def test_output_is_bound_to_actual_recording_bytes(self):
        digest = sha256_file(VIDEO)
        self.assertEqual(digest, self.report["provenance"]["sha256"])
        self.assertEqual(digest, self.report["decode_audit"]["source_sha256"])
        self.assertEqual(digest, self.report["video_scan"]["source_sha256_after_scan"])
        self.assertTrue(self.report["video_scan"]["source_unchanged"])

    def test_full_decode_matches_independent_container_metadata(self):
        stream = ffprobe_video(VIDEO)["streams"][0]
        self.assertEqual(int(stream["nb_frames"]), self.report["decode_audit"]["decoded_frame_count"])
        self.assertTrue(self.report["decode_audit"]["complete"])
        self.assertEqual(self.report["decode_audit"]["error_log"], "")

    def test_partial_feature_rows_are_adjacent_and_explicitly_incomplete(self):
        frames = pd.read_csv(OUTPUT/"01_video_scan/frame_features.csv")
        pairs = pd.read_csv(OUTPUT/"01_video_scan/pair_features_image.csv")
        scan = self.report["video_scan"]
        self.assertEqual(len(frames), scan["requested_max_frames"])
        self.assertEqual(len(pairs), len(frames)-1)
        self.assertEqual(pairs["frame_a"].tolist(), list(range(len(pairs))))
        self.assertEqual(pairs["frame_b"].tolist(), list(range(1,len(frames))))
        self.assertFalse(scan["scan_complete"])
        self.assertFalse(self.report["source_evidence"]["full_raw_video_scanned"])

    def test_noncanonical_diagnostic_cannot_be_a_publication_result(self):
        self.assertFalse(self.report["source_evidence"]["canonical_video_confirmed"])
        self.assertFalse(self.report["source_evidence"]["delta_t_resolved"])
        self.assertIsNone(self.report["publication_selector"])
        self.assertIsNone(self.report["selection_freeze"])
        self.assertFalse(self.report["cfd_used"])


if __name__ == "__main__":
    unittest.main()
