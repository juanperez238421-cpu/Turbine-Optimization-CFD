#!/usr/bin/env python3
"""One-command Google Colab execution of canonical M0 only.

The exact Drive object is downloaded by file ID through the authenticated Drive
API. This avoids whole-Drive filesystem scans and binds the local bytes to the
provider ID/name/size/MD5 before the existing M0 audit computes SHA-256.
"""
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


def download_exact_drive_object(service, file_id: str, destination: Path) -> None:
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with destination.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=32 * 1024 * 1024)
        done = False
        while not done:
            status, done = downloader.next_chunk(num_retries=5)
            if status is not None:
                print(f"Canonical download: {100.0 * status.progress():.1f}%")


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

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path("/content/drive/MyDrive/ASTRA_M0_EVIDENCE") / stamp
    out.mkdir(parents=True, exist_ok=False)
    metadata_path = out / "drive_provider_metadata.json"
    metadata_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    cache = Path("/content/astra_m0_cache") / CANONICAL_BASENAME
    expected_md5 = str(meta["md5Checksum"]).lower()
    cache_ok = False
    if cache.exists() and cache.is_file() and cache.stat().st_size == CANONICAL_SIZE:
        cache_ok = md5_file(cache).lower() == expected_md5
    if not cache_ok:
        if cache.exists():
            cache.unlink()
        print("Downloading exact canonical Drive object by file ID; no Drive-tree scan is used.")
        download_exact_drive_object(service, CANONICAL_ID, cache)

    if cache.stat().st_size != CANONICAL_SIZE:
        raise RuntimeError(f"Downloaded size mismatch: {cache.stat().st_size} != {CANONICAL_SIZE}")
    local_md5 = md5_file(cache).lower()
    if local_md5 != expected_md5:
        raise RuntimeError(f"Downloaded MD5 mismatch: {local_md5} != provider {expected_md5}")

    repo_root = Path.cwd()
    runner = repo_root / "piv_tournament" / "scripts" / "run_m0_canonical.py"
    cmd = [
        sys.executable, str(runner),
        "--video", str(cache),
        "--provider-metadata", str(metadata_path),
        "--out", str(out),
        "--repo-root", str(repo_root),
    ]
    print("Exact Drive object cached at:", cache)
    print("Persisting M0 evidence to:", out)
    proc = subprocess.run(cmd, check=False)
    print("M0 runner exit code:", proc.returncode)
    print("No M1/stationarity/selector/CFD code was executed by this runner.")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
