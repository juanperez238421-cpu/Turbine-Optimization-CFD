from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import pandas as pd

from .selectors import SelectionResult


def selection_hash(pair_indices) -> str:
    canonical = ",".join(map(str, sorted(map(int, pair_indices))))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_selection_manifest(
    pool: pd.DataFrame,
    selection: SelectionResult,
    output_dir: str | Path,
    source_video_sha256: str | None = None,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ids = sorted(map(int, selection.pair_indices))
    subset = pool[pool["pair_index"].astype(int).isin(ids)].copy().sort_values("pair_index")
    subset.insert(0, "selection_method", selection.method)
    subset.insert(1, "n_requested", selection.n_requested)
    manifest_path = out / f"selection_manifest__{selection.method}__N{selection.n_requested}.csv"
    subset.to_csv(manifest_path, index=False)
    info = {
        "method": selection.method,
        "n_requested": selection.n_requested,
        "n_selected": len(ids),
        "pair_indices_sha256": selection_hash(ids),
        "source_video_sha256": source_video_sha256,
        "notes": selection.notes,
        "manifest_csv": str(manifest_path),
    }
    (out / f"selection_manifest__{selection.method}__N{selection.n_requested}.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )
    return info


def freeze_winner(
    winner_info: dict,
    config_dict: dict,
    output_path: str | Path,
) -> dict:
    payload = {
        "selection_freeze_version": 1,
        "winner": winner_info,
        "config": config_dict,
        "CFD_LOCKBOX": "SEALED_UNTIL_SELECTION_FREEZE",
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["freeze_sha256"] = hashlib.sha256(raw).hexdigest()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def assert_cfd_unlock(freeze_path: str | Path, expected_hash: str) -> dict:
    payload = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    if payload.get("freeze_sha256") != expected_hash:
        raise RuntimeError("CFD lockbox blocked: selection freeze hash mismatch.")
    return payload
