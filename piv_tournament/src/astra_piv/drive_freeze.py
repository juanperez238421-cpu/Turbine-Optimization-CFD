from __future__ import annotations

import re
from typing import Any

EXPECTED_ASCII_COUNT = 250
ASCII_NAME_RE = re.compile(r"^PIVlab_(\d{4})\.txt$")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def validate_ascii_provider_listing(files: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate the Drive folder namespace before downloading any PIVlab export.

    Only PIVlab_0001.txt through PIVlab_0250.txt are admitted. Provider size and
    MD5 are required so downloaded bytes can be independently re-bound to the
    Drive objects before SHA-256 freezing.
    """
    by_index: dict[int, list[dict[str, Any]]] = {}
    ignored: list[str] = []

    for item in files:
        name = str(item.get("name", ""))
        match = ASCII_NAME_RE.fullmatch(name)
        if not match:
            ignored.append(name)
            continue
        idx = int(match.group(1))
        by_index.setdefault(idx, []).append(item)

    expected = set(range(1, EXPECTED_ASCII_COUNT + 1))
    observed = set(by_index)
    missing = sorted(expected - observed)
    out_of_range = sorted(observed - expected)
    duplicated = sorted(idx for idx, items in by_index.items() if len(items) != 1)

    provider_metadata_errors: list[str] = []
    ordered_files: list[dict[str, Any]] = []
    for idx in range(1, EXPECTED_ASCII_COUNT + 1):
        items = by_index.get(idx, [])
        if len(items) != 1:
            continue
        item = items[0]
        name = str(item.get("name", ""))
        expected_name = f"PIVlab_{idx:04d}.txt"
        if name != expected_name:
            provider_metadata_errors.append(f"{name}: exact filename mismatch; expected {expected_name}")
        try:
            size = int(item.get("size", -1))
        except (TypeError, ValueError):
            size = -1
        if size <= 0:
            provider_metadata_errors.append(f"{name}: provider size missing/non-positive")
        md5 = str(item.get("md5Checksum", ""))
        if not MD5_RE.fullmatch(md5):
            provider_metadata_errors.append(f"{name}: provider md5Checksum missing/malformed")
        if not item.get("id"):
            provider_metadata_errors.append(f"{name}: provider file id missing")
        ordered_files.append(item)

    ok = not missing and not duplicated and not out_of_range and not provider_metadata_errors and len(ordered_files) == EXPECTED_ASCII_COUNT
    return {
        "pass": ok,
        "expected_count": EXPECTED_ASCII_COUNT,
        "admitted_unique_count": len(ordered_files),
        "missing_indices": missing,
        "duplicated_indices": duplicated,
        "out_of_range_indices": out_of_range,
        "provider_metadata_errors": provider_metadata_errors,
        "ignored_nonmatching_names": sorted(name for name in ignored if name),
        "ordered_files": ordered_files,
    }
