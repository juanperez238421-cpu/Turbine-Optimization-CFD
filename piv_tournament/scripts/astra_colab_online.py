#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


def maybe_mount_drive(mountpoint: str = "/content/drive") -> Path:
    mount = Path(mountpoint)
    if mount.exists() and any(mount.iterdir()): return mount
    try:
        from google.colab import drive  # type: ignore
    except Exception as exc:
        raise RuntimeError("Google Colab drive mount is unavailable; pass --archive-path explicitly.") from exc
    drive.mount(mountpoint); return mount


def locate_archive(root: Path, basename: str) -> Path:
    print(f"[ASTRA] Searching mounted Drive for {basename!r} ...")
    matches=list(root.rglob(basename))
    if not matches: raise FileNotFoundError(f"{basename!r} was not found below {root}. Add a shortcut to My Drive or pass --archive-path.")
    matches=sorted(matches,key=lambda p:(len(p.parts),str(p))); print("[ASTRA] Archive:",matches[0]); return matches[0]


def free_gb(path: Path)->float: return shutil.disk_usage(path).free/1024**3

def parse_roi(values):
    if values is None: return None
    if len(values)!=4: raise ValueError("ROI requires X0 Y0 X1 Y1")
    return list(map(int,values))


def main():
    p=argparse.ArgumentParser(description="ASTRA online runner for the real 02_Articulos.rar dataset")
    p.add_argument("--mode",choices=["inventory","smoke","publication"],default="inventory")
    p.add_argument("--archive-path"); p.add_argument("--archive-name",default="02_Articulos.rar"); p.add_argument("--mountpoint",default="/content/drive"); p.add_argument("--workdir",default="/content/astra_piv_work"); p.add_argument("--extract-canonical",action="store_true"); p.add_argument("--roi",nargs=4,type=int); p.add_argument("--max-frames",type=int); p.add_argument("--copy-results-to-drive")
    args=p.parse_args()
    from astra_piv.archive import ensure_archive_tools_colab,index_archive,publication_targets,extract_members
    from astra_piv.config import load_config
    from astra_piv.pipeline import run_full_video_pipeline
    from astra_piv.pivlab_ascii import audit_pivlab_files
    work=Path(args.workdir); work.mkdir(parents=True,exist_ok=True); inventory_dir=work/"inventory"; extracted_dir=work/"extracted"; outputs_dir=work/"outputs"
    for d in [inventory_dir,extracted_dir,outputs_dir]: d.mkdir(exist_ok=True)
    archive=Path(args.archive_path) if args.archive_path else locate_archive(maybe_mount_drive(args.mountpoint),args.archive_name)
    print(f"[ASTRA] Archive size: {archive.stat().st_size/1024**3:.3f} GiB"); print(f"[ASTRA] Local free disk: {free_gb(work):.2f} GiB"); ensure_archive_tools_colab()
    print("[ASTRA] Building in-place archive inventory; raw archive is not modified.")
    members=index_archive(archive,inventory_dir/"archive_inventory.json"); groups=publication_targets(members); targets_json={k:[m.path for m in v] for k,v in groups.items()}; (inventory_dir/"archive_publication_targets.json").write_text(json.dumps(targets_json,indent=2),encoding="utf-8"); print(json.dumps({k:len(v) for k,v in groups.items()},indent=2))
    canonical=groups["canonical_video"]
    if not canonical: print("[ASTRA][BLOCKER] Canonical video basename not found in archive inventory.")
    elif len(canonical)>1:
        print("[ASTRA][BLOCKER] Multiple canonical video candidates found:"); [print("  ",x.path) for x in canonical]
    else: print("[ASTRA] Canonical video member:",canonical[0].path,"size=",canonical[0].size)
    if args.mode=="inventory" and not args.extract_canonical: print("[ASTRA] Inventory complete. Review archive_publication_targets.json before extraction."); return
    selected=[]
    if args.extract_canonical: selected.extend(canonical[:1])
    selected.extend(groups["pivlab_ascii"]); selected.extend(groups["pivlab_settings"])
    if not selected: raise RuntimeError("No requested publication targets found for extraction.")
    print(f"[ASTRA] Selectively extracting {len(selected)} archive members ..."); extracted=extract_members(archive,selected,extracted_dir,overwrite=False); (inventory_dir/"extracted_members.json").write_text(json.dumps([str(p) for p in extracted],indent=2),encoding="utf-8")
    piv_files=sorted(extracted_dir.rglob("PIVlab_*.txt"))
    if piv_files: print(f"[ASTRA] Auditing {len(piv_files)} PIVlab ASCII files."); audit_pivlab_files(piv_files,outputs_dir/"legacy_pivlab_audit")
    if args.mode=="inventory": print("[ASTRA] Target extraction complete."); return
    video_candidates=list(extracted_dir.rglob("vid_2025-08-29_19-28-15.mp4"))
    if len(video_candidates)!=1: raise RuntimeError(f"Expected exactly one canonical extracted video, found {len(video_candidates)}")
    video=video_candidates[0]; repo_root=Path(__file__).resolve().parents[1]; cfg=load_config(repo_root/"configs"/"publication_q1.yaml"); cfg.video_scan.roi=parse_roi(args.roi)
    if args.mode=="smoke":
        print("[ASTRA] Running real canonical-video smoke mode. Full-frame ROI is diagnostic only."); result=run_full_video_pipeline(video,cfg,outputs_dir/"canonical_smoke",allow_noncanonical_smoke=True,max_frames=args.max_frames)
    else:
        if cfg.video_scan.roi is None: raise RuntimeError("Publication mode requires --roi X0 Y0 X1 Y1 from audited raw-image geometry. Do not let ASTRA guess the final ROI from CFD agreement.")
        print("[ASTRA] Running strict publication-mode tournament on canonical video."); result=run_full_video_pipeline(video,cfg,outputs_dir/"publication_tournament",allow_noncanonical_smoke=False,max_frames=args.max_frames)
    print(json.dumps(result["tournament"],indent=2))
    if args.copy_results_to_drive:
        dest=Path(args.copy_results_to_drive); dest.mkdir(parents=True,exist_ok=True); target=dest/("astra_run_"+result["provenance"]["sha256"][:12]);
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(outputs_dir,target); print("[ASTRA] Copied outputs to",target)


if __name__=="__main__": main()
