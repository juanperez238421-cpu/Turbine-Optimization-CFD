from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import os
import re
import subprocess
from typing import Any, Iterable

from .provenance import audit_video_decode, ffprobe_video, sha256_file


@dataclass(frozen=True)
class CanonicalBinding:
    drive_file_id: str
    canonical_basename: str
    canonical_size_bytes: int
    provider_id: str | None
    provider_name: str | None
    provider_size_bytes: int | None
    provider_md5: str | None
    local_md5: str
    local_sha256: str
    id_matches: bool
    name_matches: bool
    size_matches: bool
    md5_matches: bool | None
    binding_pass: bool


def md5_file(path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.md5()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_int(value: Any) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def bind_canonical_file(
    path: str | Path,
    provider_metadata: dict[str, Any],
    *,
    drive_file_id: str,
    canonical_basename: str,
    canonical_size_bytes: int,
) -> CanonicalBinding:
    """Bind mounted bytes to the exact Drive object using provider metadata."""
    path = Path(path)
    provider_id = provider_metadata.get("id")
    provider_name = provider_metadata.get("name")
    provider_size = _parse_int(provider_metadata.get("size"))
    provider_md5 = provider_metadata.get("md5Checksum")
    local_md5 = md5_file(path)
    local_sha256 = sha256_file(path)

    id_matches = provider_id == drive_file_id
    name_matches = provider_name == canonical_basename and path.name == canonical_basename
    size_matches = path.stat().st_size == canonical_size_bytes and provider_size == canonical_size_bytes
    md5_matches = None if not provider_md5 else local_md5.lower() == str(provider_md5).lower()
    binding_pass = bool(id_matches and name_matches and size_matches and md5_matches is True)
    return CanonicalBinding(
        drive_file_id=drive_file_id,
        canonical_basename=canonical_basename,
        canonical_size_bytes=canonical_size_bytes,
        provider_id=provider_id,
        provider_name=provider_name,
        provider_size_bytes=provider_size,
        provider_md5=provider_md5,
        local_md5=local_md5,
        local_sha256=local_sha256,
        id_matches=id_matches,
        name_matches=name_matches,
        size_matches=size_matches,
        md5_matches=md5_matches,
        binding_pass=binding_pass,
    )


def _ffmpeg_selected_decode(path: str | Path, start_index: int, end_index: int, expected_sha256: str) -> dict[str, Any]:
    if start_index < 0 or end_index < start_index:
        raise ValueError("Invalid frame range")
    expected_count = end_index - start_index + 1
    select_expr = f"select=between(n\\,{start_index}\\,{end_index})"
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror",
        "-err_detect", "explode", "-i", str(path), "-map", "0:v:0",
        "-an", "-sn", "-dn", "-vf", select_expr, "-fps_mode", "passthrough",
        "-f", "null", "-", "-progress", "pipe:1", "-nostats",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    counts = re.findall(r"^frame=\s*(\d+)\s*$", proc.stdout, re.MULTILINE)
    decoded = int(counts[-1]) if counts else 0
    ended = "progress=end" in proc.stdout.splitlines()
    errors = [line for line in proc.stderr.splitlines() if line.strip()]
    digest_after = sha256_file(path)
    unchanged = digest_after == expected_sha256
    complete = bool(proc.returncode == 0 and ended and decoded == expected_count and not errors and unchanged)
    return {
        "decoder": "ffmpeg",
        "decoder_index_base": 0,
        "requested_start_index": start_index,
        "requested_end_index": end_index,
        "expected_selected_frame_count": expected_count,
        "decoded_selected_frame_count": decoded,
        "returncode": proc.returncode,
        "end_marker_seen": ended,
        "decoder_error_count": len(errors),
        "error_log": "\n".join(errors)[:8000],
        "source_sha256_after": digest_after,
        "source_unchanged": unchanged,
        "complete": complete,
        "status": "RANGE_DECODE_VERIFIED" if complete else "BLOCKED_RANGE_DECODE_NOT_VERIFIED",
    }


def audit_legacy_frame_range(
    path: str | Path,
    expected_sha256: str,
    start_label: int = 4250,
    end_label: int = 4500,
) -> dict[str, Any]:
    """Decode historical labels under both zero- and one-based mappings."""
    zero_based = _ffmpeg_selected_decode(path, start_label, end_label, expected_sha256)
    one_based = _ffmpeg_selected_decode(path, start_label - 1, end_label - 1, expected_sha256)
    complete = bool(zero_based["complete"] and one_based["complete"])
    return {
        "pivlab_source_labels": [start_label, end_label],
        "expected_label_count": end_label - start_label + 1,
        "zero_based_decoder_mapping": zero_based,
        "one_based_decoder_mapping": one_based,
        "complete": complete,
        "status": "PIVLAB_4250_4500_RANGE_VERIFIED_BOTH_INDEX_CONVENTIONS" if complete else "BLOCKED_PIVLAB_RANGE_NOT_FULLY_VERIFIED",
    }


def _git_head(repo_root: Path) -> str | None:
    proc = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _hash_existing(paths: Iterable[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        if path.exists() and path.is_file():
            result[str(path)] = sha256_file(path)
    return result


def _ffprobe_summary(probe: dict[str, Any]) -> dict[str, Any]:
    stream = probe.get("streams", [{}])[0]
    fmt = probe.get("format", {})

    def parse_fraction(text: Any) -> float | None:
        if text in (None, "", "0/0"):
            return None
        try:
            text = str(text)
            if "/" in text:
                a, b = text.split("/", 1)
                return float(a) / float(b)
            return float(text)
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    declared = _parse_int(stream.get("nb_frames"))
    return {
        "codec": stream.get("codec_name"),
        "pixel_format": stream.get("pix_fmt"),
        "width": _parse_int(stream.get("width")),
        "height": _parse_int(stream.get("height")),
        "avg_frame_rate_raw": stream.get("avg_frame_rate"),
        "r_frame_rate_raw": stream.get("r_frame_rate"),
        "declared_fps": parse_fraction(stream.get("avg_frame_rate")) or parse_fraction(stream.get("r_frame_rate")),
        "declared_frame_count": declared,
        "duration_s": stream.get("duration") or fmt.get("duration"),
        "format_name": fmt.get("format_name"),
        "container_size": _parse_int(fmt.get("size")),
    }


def run_m0_audit(
    video_path: str | Path,
    provider_metadata: dict[str, Any],
    output_dir: str | Path,
    *,
    drive_file_id: str,
    canonical_basename: str,
    canonical_size_bytes: int,
    legacy_start: int = 4250,
    legacy_end: int = 4500,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    binding = bind_canonical_file(
        video_path, provider_metadata,
        drive_file_id=drive_file_id,
        canonical_basename=canonical_basename,
        canonical_size_bytes=canonical_size_bytes,
    )
    probe = ffprobe_video(video_path)
    probe_summary = _ffprobe_summary(probe)
    full_decode = audit_video_decode(video_path, binding.local_sha256)
    full_errors = [line for line in str(full_decode.get("error_log", "")).splitlines() if line.strip()]
    full_decode["decoder_error_count"] = len(full_errors)
    full_count = int(full_decode.get("decoded_frame_count", 0) or 0)
    full_decode["decoder_index_base"] = 0
    full_decode["first_decoded_frame_index"] = 0 if full_count > 0 else None
    full_decode["last_decoded_frame_index"] = full_count - 1 if full_count > 0 else None

    legacy_range = audit_legacy_frame_range(video_path, binding.local_sha256, legacy_start, legacy_end)
    declared_count = probe_summary.get("declared_frame_count")
    declared_count_consistent = None if declared_count is None else declared_count == full_count
    container_size_consistent = probe_summary.get("container_size") in (None, canonical_size_bytes)
    complete_eof = bool(full_decode.get("complete") and full_decode.get("end_marker_seen"))

    m0_pass = bool(
        binding.binding_pass
        and probe_summary.get("width")
        and probe_summary.get("height")
        and probe_summary.get("declared_fps")
        and complete_eof
        and full_decode.get("decoder_error_count") == 0
        and full_count > legacy_end
        and legacy_range.get("complete")
        and declared_count_consistent is not False
        and container_size_consistent
    )

    repo = Path(repo_root) if repo_root else Path.cwd()
    critical = [
        repo / "piv_tournament" / "src" / "astra_piv" / "m0.py",
        repo / "piv_tournament" / "src" / "astra_piv" / "provenance.py",
        repo / "piv_tournament" / "scripts" / "run_m0_canonical.py",
        repo / "piv_tournament" / "scripts" / "astra_colab_m0.py",
    ]
    result = {
        "schema": "ASTRA_M0_STATUS_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if m0_pass else "FAIL",
        "scientific_scope": "Canonical source identity/container/decode integrity only; no stationarity, PIV selection, CFD, or validation.",
        "canonical_binding": asdict(binding),
        "ffprobe": probe_summary,
        "full_sequential_decode": full_decode,
        "legacy_frame_range_decode": legacy_range,
        "checks": {
            "provider_binding": binding.binding_pass,
            "container_metadata_present": bool(probe_summary.get("width") and probe_summary.get("height") and probe_summary.get("declared_fps")),
            "declared_frame_count_available": declared_count is not None,
            "declared_frame_count_consistent": declared_count_consistent,
            "container_size_consistent": container_size_consistent,
            "full_eof_decode": complete_eof,
            "decoder_error_count_zero": full_decode.get("decoder_error_count") == 0,
            "legacy_range_exists_within_full_decode": full_count > legacy_end,
            "legacy_range_decode_verified": legacy_range.get("complete") is True,
        },
        "reproducibility": {
            "git_head": _git_head(repo),
            "critical_script_sha256": _hash_existing(critical),
            "python_version": os.sys.version,
        },
    }

    (output_dir / "ffprobe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
    (output_dir / "M0_STATUS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    rows = [
        ("canonical_drive_id", binding.provider_id, binding.id_matches),
        ("canonical_basename", binding.provider_name, binding.name_matches),
        ("complete_file_size_bytes", binding.provider_size_bytes, binding.size_matches),
        ("complete_file_sha256", binding.local_sha256, True),
        ("width", probe_summary.get("width"), probe_summary.get("width") is not None),
        ("height", probe_summary.get("height"), probe_summary.get("height") is not None),
        ("declared_fps", probe_summary.get("declared_fps"), probe_summary.get("declared_fps") is not None),
        ("declared_frame_count", declared_count, declared_count is not None),
        ("successfully_decoded_frame_count", full_count, complete_eof),
        ("decoder_error_count", full_decode.get("decoder_error_count"), full_decode.get("decoder_error_count") == 0),
        ("first_decoded_frame_index_zero_based", full_decode.get("first_decoded_frame_index"), complete_eof),
        ("last_decoded_frame_index_zero_based", full_decode.get("last_decoded_frame_index"), complete_eof),
        ("frames_4250_4500_verified", legacy_range.get("status"), legacy_range.get("complete") is True),
        ("m0_pass", result["status"], m0_pass),
    ]
    with (output_dir / "M0_STATUS.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["requirement", "value", "pass"])
        writer.writerows(rows)

    report = [
        "# ASTRA M0 canonical source audit", "", f"**Verdict:** {result['status']}",
        f"**Drive file ID:** `{binding.provider_id}`", f"**Canonical basename:** `{binding.provider_name}`",
        f"**Complete size:** {binding.provider_size_bytes} bytes", f"**SHA-256:** `{binding.local_sha256}`",
        f"**Dimensions:** {probe_summary.get('width')} × {probe_summary.get('height')} px",
        f"**Declared FPS:** {probe_summary.get('declared_fps')}",
        f"**Declared frame count:** {declared_count if declared_count is not None else 'not declared by container'}",
        f"**Sequentially decoded frames:** {full_count}", f"**Decoder errors:** {full_decode.get('decoder_error_count')}",
        f"**First/last decoded indices (FFmpeg zero-based):** {full_decode.get('first_decoded_frame_index')} / {full_decode.get('last_decoded_frame_index')}",
        f"**PIVlab labels 4250–4500:** {legacy_range.get('status')}", "",
        "M0 covers byte identity, container metadata, complete sequential decoding, and explicit historical-range decoding only. It does not authorize M1 unless the verdict is PASS.",
    ]
    (output_dir / "M0_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    manifest = {
        "git_head": result["reproducibility"]["git_head"],
        "critical_script_sha256": result["reproducibility"]["critical_script_sha256"],
        "outputs": {},
    }
    for name in ["ffprobe.json", "M0_STATUS.json", "M0_STATUS.csv", "M0_REPORT.md"]:
        manifest["outputs"][name] = sha256_file(output_dir / name)
    (output_dir / "execution_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return result
