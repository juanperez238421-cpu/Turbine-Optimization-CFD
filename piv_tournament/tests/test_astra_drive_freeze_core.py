from __future__ import annotations

import unittest

from astra_piv.drive_freeze import validate_ascii_provider_listing


class DriveFreezeCoreTests(unittest.TestCase):
    def _files(self):
        return [
            {
                "id": f"id-{i}",
                "name": f"PIVlab_{i:04d}.txt",
                "size": str(480000 + i),
                "md5Checksum": f"{i:032x}"[-32:],
            }
            for i in range(1, 251)
        ]

    def test_exact_provider_namespace_passes(self):
        result = validate_ascii_provider_listing(self._files())
        self.assertTrue(result["pass"])
        self.assertEqual(result["admitted_unique_count"], 250)
        self.assertEqual(result["missing_indices"], [])
        self.assertEqual(result["duplicated_indices"], [])

    def test_missing_and_duplicate_indices_fail(self):
        files = self._files()
        files = [f for f in files if f["name"] != "PIVlab_0042.txt"]
        files.append(dict(files[0]))
        result = validate_ascii_provider_listing(files)
        self.assertFalse(result["pass"])
        self.assertIn(42, result["missing_indices"])
        self.assertIn(1, result["duplicated_indices"])

    def test_provider_md5_is_required(self):
        files = self._files()
        files[99] = dict(files[99], md5Checksum="")
        result = validate_ascii_provider_listing(files)
        self.assertFalse(result["pass"])
        self.assertTrue(any("PIVlab_0100.txt" in e for e in result["provider_metadata_errors"]))

    def test_nonmatching_files_are_ignored_without_hiding_expected_gaps(self):
        files = self._files()
        files.append({"id": "notes", "name": "README.txt", "size": "10", "md5Checksum": "0" * 32})
        result = validate_ascii_provider_listing(files)
        self.assertTrue(result["pass"])
        self.assertIn("README.txt", result["ignored_nonmatching_names"])


if __name__ == "__main__":
    unittest.main()
