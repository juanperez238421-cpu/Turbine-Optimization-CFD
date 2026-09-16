#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]
if str(PACKAGE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from astra_piv.m0 import run_m0_audit

CANONICAL_ID = "1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U"
CANONICAL_BASENAME = "vid_2025-08-29_19-28-15.mp4"
CANONICAL_SIZE = 714_939_306


def main() -> int:
    ap = argparse.ArgumentParser(description="ASTRA M0-only canonical source audit")
    ap.add_argument("--video", required=True)
    ap.add_argument("--provider-metadata", required=True, help="JSON from Google Drive files.get")
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo-root", default=str(HERE.parents[2]))
    args = ap.parse_args()
    provider = json.loads(Path(args.provider_metadata).read_text(encoding="utf-8"))
    result = run_m0_audit(
        args.video, provider, args.out,
        drive_file_id=CANONICAL_ID,
        canonical_basename=CANONICAL_BASENAME,
        canonical_size_bytes=CANONICAL_SIZE,
        legacy_start=4250,
        legacy_end=4500,
        repo_root=args.repo_root,
    )
    print(json.dumps({
        "status": result["status"],
        "m0_status": str(Path(args.out) / "M0_STATUS.json"),
        "sha256": result["canonical_binding"]["local_sha256"],
        "decoded_frames": result["full_sequential_decode"]["decoded_frame_count"],
    }, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
