from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import numpy as np
import pandas as pd

from .benchmark import benchmark_selections
from .coarse_piv import scan_coarse_piv
from .config import AstraConfig, save_config
from .manifest import write_selection_manifest
from .provenance import (inspect_video_provenance, write_provenance_manifest, assert_publication_source,
                         audit_video_decode, assert_complete_scan, source_evidence_flags)
from .selectors import run_selector, SelectionResult
from .stationarity import detect_stationary_pool
from .video_scan import scan_video


def run_source_audit(video_path: str | Path, cfg: AstraConfig, output_dir: str | Path,
                     scan_features: bool = False, max_frames: int | None = None) -> dict:
    """M0 runner: source bytes + independent decode, optionally image-feature coverage.

    This entrypoint never runs selectors or opens CFD. A partial feature scan cannot
    set full_raw_video_scanned, even when the independent decoder reaches the end.
    """
    if not cfg.cfd_lockbox:
        raise RuntimeError("ASTRA experimental analysis requires cfd_lockbox=true.")
    if max_frames is not None and not scan_features:
        raise ValueError("max_frames applies to --scan-features; the independent decode is always complete.")
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    save_config(cfg, out / "config_used.json")
    prov = inspect_video_provenance(video_path, cfg.provenance)
    write_provenance_manifest(prov, out / "provenance.json")
    decode = audit_video_decode(video_path, prov.sha256)
    (out / "decode_audit.json").write_text(json.dumps(decode, indent=2), encoding="utf-8")
    count_agrees = prov.frame_count is None or prov.frame_count == decode["decoded_frame_count"]
    scan = {}
    if scan_features and decode["complete"]:
        _, _, scan = scan_video(video_path, cfg.video_scan, output_dir=out / "01_video_scan",
                               max_frames=max_frames, verified_frame_count=decode["decoded_frame_count"],
                               expected_source_sha256=prov.sha256)
    source_stable = decode["source_unchanged"] and (not scan_features or scan.get("source_unchanged") is True)
    report = {
        "evidence_class": "REAL VIDEO DIAGNOSTIC; canonical identity requires independent reference evidence",
        "status": "M0_SOURCE_AND_DECODE_VERIFIED" if prov.publication_ready_source and decode["complete"] and count_agrees and source_stable else "M0_BLOCKED",
        "provenance": asdict(prov), "decode_audit": decode,
        "metadata_frame_count_agrees": count_agrees, "video_scan": scan,
        "source_evidence": source_evidence_flags(prov, scan, decode),
        "publication_selector": None, "selection_freeze": None, "cfd_used": False,
        "scope": "Decode / provenance diagnostic only. No stationarity, selector ranking or PIV validation claim.",
    }
    (out / "source_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _align_reliability_to_pool(pool: pd.DataFrame, coarse_summary: pd.DataFrame, reliability: np.ndarray) -> tuple[pd.DataFrame,np.ndarray]:
    merged=pool.merge(coarse_summary,on="pair_index",how="inner",validate="one_to_one")
    order={int(pid):i for i,pid in enumerate(coarse_summary["pair_index"].astype(int))}
    idx=np.array([order[int(pid)] for pid in merged["pair_index"].astype(int)],dtype=int)
    return merged.sort_values("pair_index").reset_index(drop=True), reliability[idx]


def run_tournament_on_pool(pool:pd.DataFrame,cfg:AstraConfig,output_dir:str|Path,reliability:np.ndarray|None=None,source_video_sha256:str|None=None)->tuple[pd.DataFrame,dict,list[dict]]:
    """Legacy/base selector tournament. Results are always provisional; this function cannot freeze publication data."""
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); all_leaderboards=[]; winner_records=[]; manifest_records=[]
    for n in cfg.tournament.sample_sizes:
        selections=[]
        for method in cfg.tournament.methods:
            if method=="legacy_control" and n!=250: continue
            try:
                result=run_selector(method,pool,n,cfg.tournament,cfg.provenance,reliability=reliability)
                selections.append(result); manifest_records.append(write_selection_manifest(pool,result,out/"manifests",source_video_sha256))
            except Exception as exc:
                selections.append(SelectionResult(method=method,n_requested=n,pair_indices=np.array([],dtype=int),notes=[f"METHOD_FAILED: {type(exc).__name__}: {exc}"]))
        leaderboard,meta=benchmark_selections(pool,selections,reliability=reliability); leaderboard.insert(0,"sample_size",n)
        leaderboard.to_csv(out/f"leaderboard_N{n}.csv",index=False)
        (out/f"leaderboard_N{n}.json").write_text(json.dumps({"metadata":meta,"rows":leaderboard.to_dict(orient="records")},indent=2),encoding="utf-8")
        all_leaderboards.append(leaderboard); winner_records.append({"sample_size":n,**meta})
    combined=pd.concat(all_leaderboards,ignore_index=True) if all_leaderboards else pd.DataFrame(); combined.to_csv(out/"leaderboard_all_sample_sizes.csv",index=False)
    valid=[r["provisional_winner"] for r in winner_records if r.get("provisional_winner")]
    if valid:
        counts=pd.Series(valid).value_counts(); method=str(counts.index[0]); fraction=float(counts.iloc[0]/len(valid))
        if fraction>=cfg.tournament.winner_requires_stability_fraction:
            overall_status="PROVISIONAL_CROSS_N_LEADER_REQUIRES_SUPERSTUDY"; overall_winner=method
        else:
            overall_status="UNRESOLVED_LEADER_NOT_STABLE_ACROSS_N"; overall_winner=None
    else:
        fraction=0.0; overall_status="UNRESOLVED_NO_LEADER"; overall_winner=None
    summary={
        "status":overall_status,
        "provisional_overall_winner":overall_winner,
        "cross_sample_size_winner_fraction":fraction,
        "per_sample_size":winner_records,
        "publication_freeze_allowed":False,
        "rule":"No CFD information permitted upstream. This base tournament can never freeze publication data; use production_superstudy + scientific_gate.",
    }
    (out/"tournament_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    pd.DataFrame(manifest_records).to_csv(out/"selection_manifest_index.csv",index=False)
    return combined,summary,manifest_records


def run_full_video_pipeline(video_path:str|Path,cfg:AstraConfig,output_dir:str|Path,allow_noncanonical_smoke:bool=False,max_frames:int|None=None)->dict:
    """Base diagnostic pipeline. Publication selection freeze is intentionally disabled in ASTRA v0.2."""
    if not cfg.cfd_lockbox:
        raise RuntimeError("ASTRA experimental analysis requires cfd_lockbox=true.")
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    prov=inspect_video_provenance(video_path,cfg.provenance); write_provenance_manifest(prov,out/"provenance.json")
    if cfg.strict_publication_mode and not allow_noncanonical_smoke:
        assert_publication_source(prov,cfg.provenance)
        if cfg.video_scan.publication_mode_requires_explicit_roi and cfg.video_scan.roi is None:
            raise RuntimeError("Publication mode blocked: explicit raw-image ROI is required; auto/full-frame ROI is smoke-test only.")
    decode = None
    if cfg.strict_publication_mode and not allow_noncanonical_smoke:
        decode = audit_video_decode(video_path, prov.sha256)
        (out/"decode_audit.json").write_text(json.dumps(decode,indent=2),encoding="utf-8")
        if not decode["complete"] or (prov.frame_count is not None and prov.frame_count != decode["decoded_frame_count"]):
            raise RuntimeError("Publication mode blocked: independent full decode failed or contradicts frame metadata.")
    frames,pairs,video_meta=scan_video(video_path,cfg.video_scan,output_dir=out/"01_video_scan",max_frames=max_frames,
                                     verified_frame_count=decode["decoded_frame_count"] if decode else None,
                                     expected_source_sha256=prov.sha256)
    if decode is not None:
        assert_complete_scan(video_meta, decode)
    pool,segments,stat_meta=detect_stationary_pool(pairs,cfg.stationarity,output_dir=out/"02_stationarity")
    if not stat_meta["consensus"]["stable"] and cfg.strict_publication_mode and not allow_noncanonical_smoke:
        raise RuntimeError("Publication mode blocked: no defensible stationary segment was identified.")
    reliability=None; tournament_pool=pool.copy(); coarse_meta=None
    if cfg.coarse_piv.enabled:
        candidate_ids=tournament_pool["pair_index"].astype(int).to_numpy()
        if cfg.coarse_piv.candidate_stride>1: candidate_ids=candidate_ids[::cfg.coarse_piv.candidate_stride]
        coarse_df,reliability_raw,coarse_meta=scan_coarse_piv(video_path,candidate_ids,cfg.coarse_piv,cfg.video_scan.roi,output_dir=out/"03_coarse_piv")
        tournament_pool,reliability=_align_reliability_to_pool(tournament_pool,coarse_df,reliability_raw)
        tournament_pool.to_csv(out/"03_coarse_piv"/"tournament_pool_with_piv.csv",index=False)
    leaderboard,tournament_summary,manifests=run_tournament_on_pool(tournament_pool,cfg,out/"04_tournament",reliability=reliability,source_video_sha256=prov.sha256)
    result={
        "provenance":asdict(prov),"video_scan":video_meta,"decode_audit":decode,"stationarity":stat_meta,"coarse_piv":coarse_meta,
        "tournament":tournament_summary,"selection_freeze":None,
        "selection_freeze_status":"DISABLED_USE_ASTRA_SUPERSTUDY_SCIENTIFIC_GATE",
        "warning":"Base pipeline cannot authorize publication selection. Run scripts/run_astra_q1_superstudy.py and pass the scientific evidence gate.",
    }
    (out/"pipeline_result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
