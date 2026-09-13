#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from astra_piv.coarse_piv import scan_coarse_piv, _empirical_quantile_scale
from astra_piv.config import load_config
from astra_piv.provenance import (inspect_video_provenance, assert_publication_source, write_provenance_manifest,
                                 audit_video_decode, assert_complete_scan, source_evidence_flags)
from astra_piv.stationarity import detect_stationary_pool
from astra_piv.video_scan import scan_video
from astra_piv.production_superstudy import run_nested_spatial_cv_portfolio, finalize_superstudy_decision
from astra_piv.scientific_gate import EvidenceState


def merge_scenario(base: dict, patch: dict) -> dict:
    out = dict(base)
    out.update({k: v for k, v in patch.items() if k != "id"})
    out["id"] = patch["id"]
    return out


def main():
    p = argparse.ArgumentParser(description="ASTRA Q1/Q2 selector superstudy with held-out spatial validation")
    p.add_argument("--video", required=True)
    p.add_argument("--config", default="configs/publication_q1.yaml")
    p.add_argument("--ablation-design", default="configs/ablation_oat_q1.yaml")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--roi", nargs=4, type=int, required=True)
    p.add_argument("--sample-sizes", nargs="+", type=int, default=[25,50,75,100,150,200,250])
    p.add_argument("--folds", type=int, default=5)
    p.add_argument("--seeds", nargs="+", type=int, default=[20260912,20260913,20260914,20260915,20260916])
    p.add_argument("--max-frames", type=int)
    p.add_argument("--calibration-resolved", action="store_true")
    p.add_argument("--pivlab-settings-resolved", action="store_true")
    p.add_argument("--temporal-dependence-assessed", action="store_true")
    p.add_argument("--temporal-jackknife-completed", action="store_true")
    p.add_argument("--sample-size-convergence-completed", action="store_true")
    args = p.parse_args()

    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    cfg = load_config(args.config); cfg.video_scan.roi = list(args.roi)
    if not cfg.cfd_lockbox:
        raise RuntimeError("ASTRA experimental analysis requires cfd_lockbox=true.")
    prov = inspect_video_provenance(args.video, cfg.provenance)
    write_provenance_manifest(prov, out/"provenance.json")
    assert_publication_source(prov, cfg.provenance)

    # CFD is deliberately absent from this executable.
    decode = audit_video_decode(args.video, prov.sha256)
    (out/"decode_audit.json").write_text(json.dumps(decode, indent=2), encoding="utf-8")
    if not decode["complete"] or (prov.frame_count is not None and prov.frame_count != decode["decoded_frame_count"]):
        raise RuntimeError("Publication mode blocked: independent full decode failed or contradicts frame metadata.")
    frames, pairs, video_meta = scan_video(args.video, cfg.video_scan, output_dir=out/"01_video_scan",
                                         max_frames=args.max_frames, verified_frame_count=decode["decoded_frame_count"],
                                         expected_source_sha256=prov.sha256)
    assert_complete_scan(video_meta, decode)
    pool, segments, stat_meta = detect_stationary_pool(pairs, cfg.stationarity, output_dir=out/"02_stationarity")
    if not stat_meta.get("consensus", {}).get("stable", False):
        raise RuntimeError("ASTRA blocked: no defensible stationary population.")

    design = yaml.safe_load(Path(args.ablation_design).read_text(encoding="utf-8"))
    base = design["base"]; scenarios = [merge_scenario(base, x) for x in design["scenarios"]]
    candidate_ids = pool["pair_index"].astype(int).to_numpy()

    # Expensive FFT scan is cached once per interrogation-window sensitivity value.
    window_cache = {}
    for window in sorted({int(s["window_px"]) for s in scenarios}):
        cfgw = copy.deepcopy(cfg); cfgw.coarse_piv.window_px = window
        wdir = out/"03_coarse_piv"/f"window_{window}px"
        coarse_df, _, coarse_meta = scan_coarse_piv(args.video, candidate_ids, cfgw.coarse_piv, cfgw.video_scan.roi, output_dir=wdir)
        pce = np.load(wdir/"coarse_piv_pce_matrix.npy"); ppr = np.load(wdir/"coarse_piv_ppr_matrix.npy"); order = np.load(wdir/"coarse_piv_pair_indices.npy")
        merged = pool.merge(coarse_df, on="pair_index", how="inner", validate="one_to_one")
        pos = {int(pid): i for i, pid in enumerate(order)}
        idx = np.array([pos[int(pid)] for pid in merged["pair_index"]], dtype=int)
        window_cache[window] = (merged.reset_index(drop=True), pce[idx], ppr[idx], coarse_meta)

    all_ranked = []; scenario_meta = []
    for s in scenarios:
        pool_s, pce, ppr, coarse_meta = window_cache[int(s["window_px"])]
        q_pce = np.clip(_empirical_quantile_scale(pce, s["q_low"], s["q_high"]), 0, 1)
        q_ppr = np.clip(_empirical_quantile_scale(ppr, s["q_low"], s["q_high"]), 0, 1)
        if s["reliability_mode"] == "geomean": R = np.sqrt(q_pce*q_ppr)
        elif s["reliability_mode"] == "pce_only": R = q_pce
        elif s["reliability_mode"] == "ppr_only": R = q_ppr
        else: raise ValueError(s["reliability_mode"])

        ranked, meta = run_nested_spatial_cv_portfolio(
            pool_s, R, cfg,
            sample_sizes=args.sample_sizes, folds=args.folds, seeds=args.seeds,
            quality_gate_mad=float(s["quality_gate_mad"]),
            spatial_target_fraction_of_n=float(s["spatial_target_fraction_of_n"]),
            spatial_lower_tail_fraction=float(s["lower_tail_fraction"]),
            ablation_id=s["id"], include_base_methods=True,
        )
        all_ranked.append(ranked); scenario_meta.append({"scenario":s,"meta":meta,"coarse_piv":coarse_meta})

    ranked_all = pd.concat(all_ranked, ignore_index=True)
    superdir = out/"04_superstudy"; superdir.mkdir(parents=True, exist_ok=True)
    ranked_all.to_csv(superdir/"all_ablation_ranked_scenarios.csv", index=False)

    evidence = EvidenceState(
        **source_evidence_flags(prov, video_meta, decode),
        stationary_interval_resolved=bool(stat_meta.get("consensus",{}).get("stable",False)),
        explicit_roi_resolved=True,
        calibration_resolved=bool(args.calibration_resolved),
        pivlab_settings_resolved=bool(args.pivlab_settings_resolved),
        piv_native_quality_available=True,
        spatial_reliability_available=True,
        sample_size_convergence_completed=bool(args.sample_size_convergence_completed),
        temporal_dependence_assessed=bool(args.temporal_dependence_assessed),
        temporal_jackknife_completed=bool(args.temporal_jackknife_completed),
        spatial_holdout_validation_completed=True,
        ablation_matrix_completed=True,
        winner_stability_completed=True,
        cfd_locked_during_selection=True,
    )
    decision = finalize_superstudy_decision(ranked_all, evidence_state=evidence, output_dir=superdir)
    (superdir/"ablation_scenarios.json").write_text(json.dumps(scenario_meta, indent=2, default=str), encoding="utf-8")
    context = {"provenance": prov.__dict__, "video_scan": video_meta, "decode_audit": decode, "stationarity": stat_meta, "cfd_used": False}
    (superdir/"SUPERSTUDY_CONTEXT.json").write_text(json.dumps(context, indent=2, default=str), encoding="utf-8")
    print(json.dumps(decision["numerical_decision"], indent=2))
    print(json.dumps(decision["scientific_publication_gate"], indent=2))


if __name__ == "__main__":
    main()
