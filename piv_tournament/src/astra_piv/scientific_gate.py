from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class EvidenceState:
    canonical_video_confirmed: bool = False
    canonical_video_sha256_recorded: bool = False
    full_raw_video_scanned: bool = False
    stationary_interval_resolved: bool = False
    explicit_roi_resolved: bool = False
    calibration_resolved: bool = False
    delta_t_resolved: bool = False
    pivlab_settings_resolved: bool = False
    piv_native_quality_available: bool = False
    spatial_reliability_available: bool = False
    sample_size_convergence_completed: bool = False
    temporal_dependence_assessed: bool = False
    temporal_jackknife_completed: bool = False
    spatial_holdout_validation_completed: bool = False
    ablation_matrix_completed: bool = False
    winner_stability_completed: bool = False
    cfd_locked_during_selection: bool = True


PUBLICATION_REQUIREMENTS = (
    "canonical_video_confirmed",
    "canonical_video_sha256_recorded",
    "full_raw_video_scanned",
    "stationary_interval_resolved",
    "explicit_roi_resolved",
    "calibration_resolved",
    "delta_t_resolved",
    "pivlab_settings_resolved",
    "piv_native_quality_available",
    "spatial_reliability_available",
    "sample_size_convergence_completed",
    "temporal_dependence_assessed",
    "temporal_jackknife_completed",
    "spatial_holdout_validation_completed",
    "ablation_matrix_completed",
    "winner_stability_completed",
    "cfd_locked_during_selection",
)


def publication_gate(state: EvidenceState, numerical_candidate: str | None = None) -> dict:
    data = asdict(state)
    blockers = [name for name in PUBLICATION_REQUIREMENTS if not bool(data[name])]
    if numerical_candidate is None:
        status = "NO_NUMERICAL_SELECTOR_CANDIDATE"
    elif blockers:
        status = "NUMERICAL_CANDIDATE_NOT_PUBLICATION_ELIGIBLE"
    else:
        status = "PUBLICATION_SELECTOR_ELIGIBLE_FOR_FREEZE"
    return {
        "status": status,
        "numerical_candidate": numerical_candidate,
        "publication_selector": numerical_candidate if not blockers and numerical_candidate is not None else None,
        "blockers": blockers,
        "requirements": data,
        "rule": "A selector cannot be frozen for the manuscript until every evidence requirement is satisfied. CFD must remain locked during selection.",
    }


def write_gate_report(report: dict, path: str | Path) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
