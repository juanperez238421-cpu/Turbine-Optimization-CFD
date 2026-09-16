from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from astra_piv.m0 import bind_canonical_file, audit_legacy_frame_range, run_m0_audit, md5_file
from astra_piv.provenance import sha256_file


class M0CoreTests(unittest.TestCase):
    def _fixture(self, root: Path, n: int = 20) -> Path:
        path = root / "canonical.mkv"
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"testsrc=size=64x48:rate=20:duration={n/20}",
            "-c:v", "ffv1", str(path),
        ]
        subprocess.run(cmd, check=True)
        return path

    def test_binding_requires_provider_checksum(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._fixture(Path(td))
            meta = {"id": "ID", "name": p.name, "size": str(p.stat().st_size)}
            b = bind_canonical_file(p, meta, drive_file_id="ID", canonical_basename=p.name, canonical_size_bytes=p.stat().st_size)
            self.assertFalse(b.binding_pass)
            self.assertIsNone(b.md5_matches)

    def test_wrong_id_or_checksum_cannot_pass(self):
        with tempfile.TemporaryDirectory() as td:
            p = self._fixture(Path(td))
            base = {"id": "ID", "name": p.name, "size": str(p.stat().st_size), "md5Checksum": md5_file(p)}
            self.assertTrue(bind_canonical_file(p, base, drive_file_id="ID", canonical_basename=p.name, canonical_size_bytes=p.stat().st_size).binding_pass)
            wrong_id = dict(base, id="OTHER")
            self.assertFalse(bind_canonical_file(p, wrong_id, drive_file_id="ID", canonical_basename=p.name, canonical_size_bytes=p.stat().st_size).binding_pass)
            wrong_md5 = dict(base, md5Checksum="0" * 32)
            self.assertFalse(bind_canonical_file(p, wrong_md5, drive_file_id="ID", canonical_basename=p.name, canonical_size_bytes=p.stat().st_size).binding_pass)

    def test_range_validation_and_complete_m0_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = self._fixture(root, 20)
            digest = sha256_file(p)
            rng = audit_legacy_frame_range(p, digest, 5, 10)
            self.assertTrue(rng["complete"])
            meta = {"id": "ID", "name": p.name, "size": str(p.stat().st_size), "md5Checksum": md5_file(p)}
            out = root / "out"
            result = run_m0_audit(
                p, meta, out,
                drive_file_id="ID", canonical_basename=p.name,
                canonical_size_bytes=p.stat().st_size,
                legacy_start=5, legacy_end=10, repo_root=root,
            )
            self.assertEqual(result["status"], "PASS")
            for name in ["M0_STATUS.json", "M0_STATUS.csv", "M0_REPORT.md", "execution_manifest.json"]:
                self.assertTrue((out / name).exists())

    def test_out_of_range_cannot_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = self._fixture(root, 12)
            meta = {"id": "ID", "name": p.name, "size": str(p.stat().st_size), "md5Checksum": md5_file(p)}
            result = run_m0_audit(
                p, meta, root / "out",
                drive_file_id="ID", canonical_basename=p.name,
                canonical_size_bytes=p.stat().st_size,
                legacy_start=20, legacy_end=25, repo_root=root,
            )
            self.assertEqual(result["status"], "FAIL")
            self.assertFalse(result["checks"]["legacy_range_decode_verified"])


if __name__ == "__main__":
    unittest.main()
