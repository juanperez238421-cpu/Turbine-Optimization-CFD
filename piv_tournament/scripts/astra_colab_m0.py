#!/usr/bin/env python3
"""One-command Google Colab / mounted-Drive execution of canonical M0 only."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

CANONICAL_ID = "1AqnbXPiEFmCsUeO3WlwkuxolkxI7af6U"
CANONICAL_BASENAME = "vid_2025-08-29_19-28-15.mp4"
CANONICAL_SIZE = 714_939_306


def md5_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    try:
        from google.colab import auth, drive  # type: ignore
    except ImportError as exc:
        raise SystemExit("This runner is intended for Google Colab. Use run_m0_canonical.py locally.") from exc

    drive.mount("/content/drive", force_remount=False)
    auth.authenticate_user()
    from googleapiclient.discovery import build  # type: ignore

    service = build("drive", "v3", cache_discovery=False)
    meta = service.files().get(
        fileId=CANONICAL_ID,
        fields="id,name,size,md5Checksum,modifiedTime,mimeType,parents",
        supportsAllDrives=True,
    ).execute()
    if meta.get("id") != CANONICAL_ID or meta.get("name") != CANONICAL_BASENAME:
        raise RuntimeError(f"Provider identity mismatch: {meta}")
    if int(meta.get("size", -1)) != CANONICAL_SIZE:
        raise RuntimeError(f"Provider size mismatch: {meta.get('size')} != {CANONICAL_SIZE}")
    if not meta.get("md5Checksum"):
        raise RuntimeError("Google Drive did not expose md5Checksum; fail closed rather than bind by name/size only.")

    roots = [p for p in [Path("/content/drive/MyDrive"), Path("/content/drive/Shareddrives")] if p.exists()]
    candidates: list[Path] = []
    for root in roots:
        for path in root.rglob(CANONICAL_BASENAME):
            try:
                if path.is_file() and path.stat().st_size == CANONICAL_SIZE:
                    candidates.append(path)
            except OSError:
                continue
    if not candidates:
        raise FileNotFoundError("Canonical Drive object is not visible in the mounted Drive filesystem.")

    expected_md5 = str(meta["md5Checksum"]).lower()
    exact = [path for path in candidates if md5_file(path).lower() == expected_md5]
    if len(exact) != 1:
        raise RuntimeError(
            "Canonical path resolution is ambiguous or mismatched. "
            f"size-matched candidates={len(candidates)}, md5-matched candidates={len(exact)}"
        )
    video = exact[0]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path("/content/drive/MyDrive/ASTRA_M0_EVIDENCE") / stamp
    out.mkdir(parents=True, exist_ok=False)
    metadata_path = out / "drive_provider_metadata.json"
    metadata_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    repo_root = Path.cwd()
    runner = repo_root / "piv_tournament" / "scripts" / "run_m0_canonical.py"
    cmd = [
        sys.executable, str(runner),
        "--video", str(video),
        "--provider-metadata", str(metadata_path),
        "--out", str(out),
        "--repo-root", str(repo_root),
    ]
    print("Resolved canonical path:", video)
    print("Persisting M0 evidence to:", out)
    proc = subprocess.run(cmd, check=False)
    print("M0 runner exit code:", proc.returncode)
    print("No M1/stationarity/selector/CFD code was executed by this runner.")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
