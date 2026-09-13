from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
from typing import Any

from .config import ProvenanceConfig


@dataclass
class VideoProvenance:
    path: str
    basename: str
    sha256: str
    size_bytes: int
    width: int | None
    height: int | None
    fps: float | None
    frame_count: int | None
    duration_s: float | None
    codec: str | None
    is_canonical_basename: bool
    canonical_sampling_relative_error: float | None
    publication_ready_source: bool
    notes: list[str]
    expected_sha256: str | None = None
    sha256_matches_reference: bool = False
    canonical_reference: str | None = None
    size_matches_reference: bool | None = None
    acquisition_dt_s: float | None = None
    acquisition_timing_resolved: bool = False
    acquisition_dt_reference: str | None = None


def sha256_file(path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_fraction(text: str | None) -> float | None:
    if not text:
        return None
    try:
        if "/" in text:
            a, b = text.split("/", 1)
            return float(a) / float(b)
        return float(text)
    except Exception:
        return None


def ffprobe_video(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames,duration,pix_fmt:format=duration,size,format_name",
        "-of", "json", str(path),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(p.stdout)


def inspect_video_provenance(path: str | Path, cfg: ProvenanceConfig) -> VideoProvenance:
    path = Path(path)
    probe = ffprobe_video(path)
    stream = probe.get("streams", [{}])[0]
    fmt = probe.get("format", {})
    fps = _parse_fraction(stream.get("avg_frame_rate")) or _parse_fraction(stream.get("r_frame_rate"))
    width = int(stream["width"]) if stream.get("width") is not None else None
    height = int(stream["height"]) if stream.get("height") is not None else None
    frame_text = str(stream.get("nb_frames", ""))
    nframes = int(frame_text) if frame_text.isdigit() and int(frame_text) > 0 else None
    duration = None
    if stream.get("duration") is not None:
        duration = float(stream["duration"])
    elif fmt.get("duration") is not None:
        duration = float(fmt["duration"])

    notes: list[str] = []
    is_name = path.name == cfg.canonical_video_basename
    if not is_name:
        notes.append(
            f"Basename does not match canonical PIVlab provenance ({cfg.canonical_video_basename})."
        )

    rel = None
    if fps and cfg.legacy_sampling_hz:
        rel = abs(fps - cfg.legacy_sampling_hz) / cfg.legacy_sampling_hz
        if rel > 0.01:
            notes.append(
                f"Video fps {fps:.6g} differs from legacy PIVlab-implied {cfg.legacy_sampling_hz:.6g} Hz."
            )

    digest = sha256_file(path)
    expected = cfg.canonical_sha256
    if expected is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError("canonical_sha256 must be an independently recorded 64-character SHA-256 digest")
    matches = bool(expected is not None and digest == expected.lower())
    reference = (cfg.canonical_reference or "").strip()
    size_matches = None if cfg.canonical_size_bytes is None else path.stat().st_size == cfg.canonical_size_bytes
    if expected is None:
        notes.append("BLOCKER: independently recorded canonical SHA-256 is absent; basename/fps cannot prove identity.")
    elif not matches:
        notes.append("BLOCKER: SHA-256 differs from the canonical reference.")
    if not reference:
        notes.append("BLOCKER: canonical reference evidence citation is absent.")
    if size_matches is False:
        notes.append("BLOCKER: byte size differs from the canonical reference.")
    timing_resolved = bool(
        cfg.acquisition_dt_s is not None and math.isfinite(cfg.acquisition_dt_s)
        and cfg.acquisition_dt_s > 0 and (cfg.acquisition_dt_reference or "").strip()
    )
    if not timing_resolved:
        notes.append("BLOCKER: acquisition delta-t evidence unresolved; container playback fps is not an acquisition clock.")
    ready = bool(is_name and matches and reference and size_matches is not False)
    if ready:
        notes.append("Canonical bytes match the independently supplied reference digest. Timing is assessed separately.")

    return VideoProvenance(
        path=str(path),
        basename=path.name,
        sha256=digest,
        size_bytes=path.stat().st_size,
        width=width,
        height=height,
        fps=fps,
        frame_count=nframes,
        duration_s=duration,
        codec=stream.get("codec_name"),
        is_canonical_basename=is_name,
        canonical_sampling_relative_error=rel,
        publication_ready_source=ready,
        notes=notes,
        expected_sha256=expected.lower() if expected else None,
        sha256_matches_reference=matches,
        canonical_reference=reference or None,
        size_matches_reference=size_matches,
        acquisition_dt_s=cfg.acquisition_dt_s,
        acquisition_timing_resolved=timing_resolved,
        acquisition_dt_reference=cfg.acquisition_dt_reference,
    )


def audit_video_decode(path: str | Path, expected_sha256: str) -> dict[str, Any]:
    """Independent, strict full decode. Does not compute PIV features or prove stationarity.

    Passthrough frame timing prevents FFmpeg from duplicating/dropping output frames
    to fit a nominal frame rate. Error-level messages make this audit fail closed.
    """
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror",
           "-err_detect", "explode", "-i", str(path), "-map", "0:v:0",
           "-an", "-sn", "-dn", "-fps_mode", "passthrough", "-f", "null", "-",
           "-progress", "pipe:1", "-nostats"]
    process = subprocess.run(cmd, capture_output=True, text=True, check=False)
    counts = re.findall(r"^frame=\s*(\d+)\s*$", process.stdout, re.MULTILINE)
    count = int(counts[-1]) if counts else 0
    ended = "progress=end" in process.stdout.splitlines()
    digest_after = sha256_file(path)
    unchanged = digest_after == expected_sha256
    errors = process.stderr.strip()
    complete = bool(process.returncode == 0 and ended and count > 1 and not errors and unchanged)
    return {"decoder": "ffmpeg", "command": cmd, "returncode": process.returncode,
            "decoded_frame_count": count, "end_marker_seen": ended,
            "source_sha256": digest_after, "source_unchanged": unchanged,
            "error_log": errors[:8000], "complete": complete,
            "status": "FULL_DECODE_VERIFIED" if complete else "BLOCKED_DECODE_NOT_VERIFIED",
            "scope": "Container decode and byte integrity only; no PIV or acquisition-timing validation."}


def assert_complete_scan(scan: dict, decode: dict) -> None:
    """Publication feature coverage requires agreement with an independent full decode."""
    count = decode.get("decoded_frame_count", 0)
    if not (decode.get("complete") is True and scan.get("scan_complete") is True
            and scan.get("decoded_frame_count") == count
            and scan.get("pair_count") == count - 1
            and scan.get("shape_mismatch_count") == 0
            and scan.get("source_unchanged") is True
            and scan.get("source_sha256_after_scan") == decode.get("source_sha256")):
        raise RuntimeError("Publication mode blocked: full feature scan and independent decode do not agree.")


def source_evidence_flags(prov: VideoProvenance, scan: dict, decode: dict) -> dict[str, bool]:
    try:
        assert_complete_scan(scan, decode)
        complete = decode.get("source_sha256") == prov.sha256
    except RuntimeError:
        complete = False
    return {"canonical_video_confirmed": prov.publication_ready_source,
            "canonical_video_sha256_recorded": bool(prov.sha256_matches_reference and prov.canonical_reference),
            "full_raw_video_scanned": complete,
            "delta_t_resolved": prov.acquisition_timing_resolved}


def write_provenance_manifest(prov: VideoProvenance, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(prov), indent=2), encoding="utf-8")


def assert_publication_source(prov: VideoProvenance, cfg: ProvenanceConfig) -> None:
    if cfg.require_canonical_for_publication and not prov.publication_ready_source:
        raise RuntimeError(
            "Publication mode blocked: the supplied video is not proven to be the canonical high-speed PIV source. "
            + " ".join(prov.notes)
        )
