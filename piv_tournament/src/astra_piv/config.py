from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import json

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class ProvenanceConfig:
    canonical_video_basename: str = "vid_2025-08-29_19-28-15.mp4"
    legacy_xy_m_per_px: float = 0.00019061
    legacy_uv_mps_per_px_per_frame: float = 0.20386
    legacy_pair_first_a: int = 4250
    legacy_pair_last_b: int = 4500
    require_canonical_for_publication: bool = True

    @property
    def legacy_dt_s(self) -> float:
        return self.legacy_xy_m_per_px / self.legacy_uv_mps_per_px_per_frame

    @property
    def legacy_sampling_hz(self) -> float:
        return 1.0 / self.legacy_dt_s


@dataclass
class VideoScanConfig:
    downscale: float = 0.25
    roi: list[int] | None = None  # x0, y0, x1, y1 in original pixels
    publication_mode_requires_explicit_roi: bool = True
    clahe_clip_limit: float = 2.0
    clahe_grid_size: int = 8
    top_hat_kernel_px_small: int = 9
    blob_area_min_small: int = 1
    blob_area_max_small: int = 80
    dark_percentile: float = 5.0
    bright_percentile: float = 99.5


@dataclass
class StationarityConfig:
    methods: list[str] = field(default_factory=lambda: ["pelt_rbf", "robust_plateau"])
    min_segment_pairs: int = 500
    pelt_penalty_scale: float = 1.0
    rolling_window_pairs: int = 150
    plateau_max_robust_slope: float = 0.15
    plateau_max_robust_cv: float = 0.35
    consensus_mode: str = "intersection_or_longest"


@dataclass
class CoarsePIVConfig:
    enabled: bool = True
    window_px: int = 36
    grid_rows: int = 8
    grid_cols: int = 8
    candidate_stride: int = 1
    max_pairs: int | None = None
    preprocess_clahe: bool = True
    highpass_kernel_px: int = 15
    peak_exclusion_radius_px: int = 2
    use_hanning: bool = True
    quality_normalization: str = "empirical_q10_q90"
    quality_low_quantile: float = 10.0
    quality_high_quantile: float = 90.0


@dataclass
class TournamentConfig:
    sample_sizes: list[int] = field(default_factory=lambda: [100, 150, 250])
    methods: list[str] = field(default_factory=lambda: [
        "legacy_control",
        "uniform",
        "stratified_random",
        "quality_top",
        "pareto_temporal",
        "cluster_medoids",
        "farthest_point",
        "facility_location",
        "spatial_coverage_log",
        "qcrc_maximin",
        "best_contiguous_window",
    ])
    random_seed: int = 20260912
    minimum_temporal_gap_pairs: int = 1
    candidate_pool_limit_for_pairwise_methods: int = 2000
    bootstrap_repeats: int = 20
    bootstrap_fraction: float = 0.8
    pareto_tie_tolerance: float = 1e-9
    winner_requires_stability_fraction: float = 0.60
    quality_gate_mad_multiplier: float = 4.0


@dataclass
class OutputConfig:
    output_dir: str = "outputs"
    write_parquet: bool = False
    save_selected_frames: bool = False
    selected_frame_format: str = "png"


@dataclass
class AstraConfig:
    provenance: ProvenanceConfig = field(default_factory=ProvenanceConfig)
    video_scan: VideoScanConfig = field(default_factory=VideoScanConfig)
    stationarity: StationarityConfig = field(default_factory=StationarityConfig)
    coarse_piv: CoarsePIVConfig = field(default_factory=CoarsePIVConfig)
    tournament: TournamentConfig = field(default_factory=TournamentConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    strict_publication_mode: bool = True
    cfd_lockbox: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _merge_dataclass(instance, patch: dict[str, Any]):
    for key, value in patch.items():
        if not hasattr(instance, key):
            raise KeyError(f"Unknown configuration key: {type(instance).__name__}.{key}")
        current = getattr(instance, key)
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            _merge_dataclass(current, value)
        else:
            setattr(instance, key, value)
    return instance


def load_config(path: str | Path | None = None) -> AstraConfig:
    cfg = AstraConfig()
    if path is None:
        return cfg
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to read YAML configuration files.")
        patch = yaml.safe_load(text) or {}
    else:
        patch = json.loads(text)
    if not isinstance(patch, dict):
        raise TypeError("Configuration root must be a mapping.")
    return _merge_dataclass(cfg, patch)


def save_config(cfg: AstraConfig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = cfg.to_dict()
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to write YAML configuration files.")
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
