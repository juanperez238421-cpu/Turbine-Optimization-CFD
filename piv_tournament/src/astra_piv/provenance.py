from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
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
    nframes = int(stream["nb_frames"]) if stream.get("nb_frames") else None
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

    ready = bool(is_name and fps is not None and rel is not None and rel <= 0.01)
    if ready:
        notes.append("Canonical source identity and sampling rate are consistent with legacy PIVlab export metadata.")

    return VideoProvenance(
        path=str(path),
        basename=path.name,
        sha256=sha256_file(path),
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
    )


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
