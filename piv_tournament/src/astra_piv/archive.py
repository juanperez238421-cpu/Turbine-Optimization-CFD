from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import fnmatch
import json
import os
import re
import shutil
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class ArchiveMember:
    path: str
    size: int | None = None
    packed_size: int | None = None
    modified: str | None = None
    attributes: str | None = None

    @property
    def basename(self) -> str:
        return Path(self.path).name


class ArchiveError(RuntimeError):
    pass


def find_first(root: str | Path, basename: str) -> Path:
    root = Path(root)
    matches = list(root.rglob(basename))
    if not matches:
        raise FileNotFoundError(f"Could not find {basename!r} below {root}")
    if len(matches) > 1:
        matches = sorted(matches, key=lambda p: (len(p.parts), str(p)))
    return matches[0]


def ensure_archive_tools_colab() -> None:
    """Ensure at least one RAR-capable tool exists in a Debian-like Colab runtime."""
    if shutil.which("7z") or shutil.which("7zz") or shutil.which("lsar"):
        return
    if os.environ.get("COLAB_RELEASE_TAG") or Path("/content").exists():
        cmd = "apt-get update -qq && apt-get install -y -qq p7zip-full unar"
        subprocess.run(["bash", "-lc", cmd], check=True)
    if not (shutil.which("7z") or shutil.which("7zz") or shutil.which("lsar")):
        raise ArchiveError("No RAR-capable listing tool (7z/7zz/lsar) is available.")


def _sevenzip_exe() -> str:
    exe = shutil.which("7zz") or shutil.which("7z")
    if not exe:
        raise ArchiveError("7z/7zz is required for RAR listing/extraction.")
    return exe


def list_archive(path: str | Path) -> list[ArchiveMember]:
    """List ZIP/RAR contents without extracting the archive.

    ZIP is handled natively. RAR uses `7z l -slt`, which avoids copying the
    multi-gigabyte archive out of a mounted Google Drive folder.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(path, "r") as zf:
            return [
                ArchiveMember(
                    path=i.filename,
                    size=i.file_size,
                    packed_size=i.compress_size,
                    modified=None,
                    attributes=str(i.external_attr),
                )
                for i in zf.infolist()
                if not i.is_dir()
            ]

    ensure_archive_tools_colab()
    exe = shutil.which("7zz") or shutil.which("7z")
    if exe:
        p = subprocess.run(
            [exe, "l", "-slt", str(path)],
            capture_output=True, text=True, check=False, errors="replace"
        )
    else:
        p = None

    if p is None or p.returncode != 0:
        # libarchive's lsar is often more reliable for RAR5 archives than p7zip.
        lsar = shutil.which("lsar")
        if not lsar:
            stderr = p.stderr if p is not None else "7z unavailable"
            raise ArchiveError(f"RAR listing failed and lsar is unavailable: {stderr}")
        q = subprocess.run([lsar, "-j", str(path)], capture_output=True, text=True, check=True, errors="replace")
        data = json.loads(q.stdout)
        entries = data.get("lsarContents", [])
        result = []
        for e in entries:
            if e.get("XADIsDirectory"):
                continue
            name = e.get("XADFileName")
            if not name:
                continue
            result.append(ArchiveMember(
                path=str(name),
                size=int(e["XADFileSize"]) if e.get("XADFileSize") is not None else None,
                packed_size=int(e["XADCompressedSize"]) if e.get("XADCompressedSize") is not None else None,
                modified=str(e.get("XADLastModificationDate")) if e.get("XADLastModificationDate") else None,
                attributes=None,
            ))
        return result

    members: list[ArchiveMember] = []
    current: dict[str, str] = {}

    def flush() -> None:
        nonlocal current
        if current.get("Path") and current.get("Folder", "-") != "+":
            try:
                size = int(current["Size"]) if current.get("Size") else None
            except ValueError:
                size = None
            try:
                packed = int(current["Packed Size"]) if current.get("Packed Size") else None
            except ValueError:
                packed = None
            members.append(ArchiveMember(
                path=current["Path"],
                size=size,
                packed_size=packed,
                modified=current.get("Modified"),
                attributes=current.get("Attributes"),
            ))
        current = {}

    for line in p.stdout.splitlines():
        if not line.strip():
            flush()
            continue
        if " = " in line:
            key, value = line.split(" = ", 1)
            current[key.strip()] = value.strip()
    flush()

    # 7z includes archive metadata as the first Path block in some versions.
    archive_abs = str(path.resolve())
    members = [m for m in members if m.path not in {str(path), archive_abs}]
    return members


def filter_members(
    members: Iterable[ArchiveMember],
    patterns: Iterable[str] | None = None,
    regex: str | None = None,
) -> list[ArchiveMember]:
    patterns = list(patterns or [])
    rx = re.compile(regex, re.IGNORECASE) if regex else None
    result = []
    for m in members:
        ok = True
        if patterns:
            ok = any(fnmatch.fnmatch(m.path, p) or fnmatch.fnmatch(m.basename, p) for p in patterns)
        if rx is not None:
            ok = ok and bool(rx.search(m.path))
        if ok:
            result.append(m)
    return result


def extract_members(
    archive: str | Path,
    members: Iterable[ArchiveMember | str],
    destination: str | Path,
    overwrite: bool = False,
) -> list[Path]:
    """Selectively extract requested members.

    The raw archive is never modified. Existing destination files are preserved unless
    overwrite=True.
    """
    archive = Path(archive)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    names = [m.path if isinstance(m, ArchiveMember) else str(m) for m in members]
    if not names:
        return []

    if archive.suffix.lower() == ".zip":
        import zipfile
        out: list[Path] = []
        with zipfile.ZipFile(archive, "r") as zf:
            for name in names:
                target = destination / name
                if target.exists() and not overwrite:
                    out.append(target)
                    continue
                zf.extract(name, destination)
                out.append(target)
        return out

    ensure_archive_tools_colab()
    exe = shutil.which("7zz") or shutil.which("7z")
    if exe:
        flag = "-aoa" if overwrite else "-aos"
        cmd = [exe, "x", str(archive), f"-o{destination}", flag, "--", *names]
        p = subprocess.run(cmd, check=False)
        if p.returncode == 0:
            return [destination / n for n in names]

    unar = shutil.which("unar")
    if not unar:
        raise ArchiveError("Selective RAR extraction failed with 7z and unar is unavailable.")
    # unar accepts optional member names after the archive path.
    cmd = [unar, "-o", str(destination), "-f" if overwrite else "-s", str(archive), *names]
    subprocess.run(cmd, check=True)
    return [destination / n for n in names]


def index_archive(archive: str | Path, output_json: str | Path) -> list[ArchiveMember]:
    members = list_archive(archive)
    output_json = Path(output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps([asdict(m) for m in members], indent=2), encoding="utf-8"
    )
    return members


def publication_targets(members: Iterable[ArchiveMember]) -> dict[str, list[ArchiveMember]]:
    members = list(members)
    groups = {
        "canonical_video": filter_members(members, patterns=["*vid_2025-08-29_19-28-15.mp4"]),
        "pivlab_ascii": filter_members(members, patterns=["PIVlab_*.txt", "*PIVlab_*.txt"]),
        "pivlab_settings": filter_members(members, regex=r"(?i)(sett\.mat|settings.*\.mat|pivlab.*\.mat)$"),
        "calibration": filter_members(members, regex=r"(?i)(calib|ruler|regla|escala).*(png|jpg|jpeg|tif|tiff|bmp|mat)$"),
        "matlab_code": filter_members(members, patterns=["*.m", "*/*.m"]),
        "python_code": filter_members(members, patterns=["*.py", "*/*.py"]),
        "cfd_numeric": filter_members(members, regex=r"(?i)(cfd|fluent|mesh|gci).*(csv|txt|dat|mat|cas|h5|xlsx)$"),
    }
    return groups
