#!/usr/bin/env python3
"""Authenticated Colab freeze of the complete historical 250 PIVlab exports.

This is retrospective downstream PIV evidence only. It downloads the exact
Drive objects in the known PIVlab export folder, verifies provider size/MD5,
then delegates parsing, SHA-256, grid, vector-type and continuity checks to the
existing freeze_pivlab_ascii.py script.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]
if str(PACKAGE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from astra_piv.drive_freeze import validate_ascii_provider_listing

ASCII_FOLDER_ID = "1UF77fkaEm2NZ2CJCbfADYeAHaoj3PnZO"


def md5_file(path: Path, chunk: int = 4 * 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def list_folder(service) -> list[dict]:
    files: list[dict] = []
    token = None
    while True:
        response = service.files().list(
            q=f"'{ASCII_FOLDER_ID}' in parents and trashed=false",
            fields="nextPageToken,files(id,name,size,md5Checksum,mimeType,modifiedTime,parents)",
            pageSize=1000,
            pageToken=token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        files.extend(response.get("files", []))
        token = response.get("nextPageToken")
        if not token:
            return files


def download_file(service, item: dict, destination: Path) -> None:
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore

    request = service.files().get_media(fileId=item["id"], supportsAllDrives=True)
    with destination.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _status, done = downloader.next_chunk(num_retries=5)


def main() -> int:
    try:
        from google.colab import auth, drive  # type: ignore
    except ImportError as exc:
        raise SystemExit("This runner is intended for Google Colab.") from exc

    drive.mount("/content/drive", force_remount=False)
    auth.authenticate_user()
    from googleapiclient.discovery import build  # type: ignore

    service = build("drive", "v3", cache_discovery=False)
    raw_listing = list_folder(service)
    validation = validate_ascii_provider_listing(raw_listing)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path("/content/drive/MyDrive/ASTRA_ASCII_250_EVIDENCE") / stamp
    out.mkdir(parents=True, exist_ok=False)
    (out / "drive_ascii_provider_manifest.json").write_text(
        json.dumps({"folder_id": ASCII_FOLDER_ID, **validation}, indent=2),
        encoding="utf-8",
    )
    if not validation["pass"]:
        (out / "ASCII_DOWNLOAD_STATUS.json").write_text(
            json.dumps({"status": "FAIL_PROVIDER_NAMESPACE", **validation}, indent=2),
            encoding="utf-8",
        )
        print(json.dumps({k: v for k, v in validation.items() if k != "ordered_files"}, indent=2))
        return 2

    cache = Path("/content/astra_pivlab_250") / stamp
    cache.mkdir(parents=True, exist_ok=False)
    transfer_errors: list[str] = []

    for n, item in enumerate(validation["ordered_files"], start=1):
        dest = cache / item["name"]
        try:
            download_file(service, item, dest)
            provider_size = int(item["size"])
            provider_md5 = str(item["md5Checksum"]).lower()
            if dest.stat().st_size != provider_size:
                raise RuntimeError(f"size {dest.stat().st_size} != provider {provider_size}")
            local_md5 = md5_file(dest).lower()
            if local_md5 != provider_md5:
                raise RuntimeError(f"MD5 {local_md5} != provider {provider_md5}")
        except Exception as exc:
            transfer_errors.append(f"{item.get('name')}: {type(exc).__name__}: {exc}")
            break
        if n == 1 or n % 25 == 0 or n == 250:
            print(f"Verified Drive download {n}/250: {item['name']}")

    download_status = {
        "status": "PASS" if not transfer_errors and len(list(cache.glob("PIVlab_*.txt"))) == 250 else "FAIL",
        "folder_id": ASCII_FOLDER_ID,
        "expected_files": 250,
        "downloaded_files": len(list(cache.glob("PIVlab_*.txt"))),
        "provider_binding": "exact Drive file IDs + provider byte sizes + provider MD5 matched to downloaded bytes",
        "errors": transfer_errors,
    }
    (out / "ASCII_DOWNLOAD_STATUS.json").write_text(json.dumps(download_status, indent=2), encoding="utf-8")
    if download_status["status"] != "PASS":
        print(json.dumps(download_status, indent=2))
        return 2

    runner = PACKAGE_ROOT / "scripts" / "freeze_pivlab_ascii.py"
    freeze_out = out / "ASCII_250_FREEZE"
    proc = subprocess.run(
        [sys.executable, str(runner), "--ascii-dir", str(cache), "--out", str(freeze_out)],
        check=False,
    )
    print("250-ASCII freeze exit code:", proc.returncode)
    if proc.returncode == 0:
        shutil.rmtree(cache, ignore_errors=True)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
