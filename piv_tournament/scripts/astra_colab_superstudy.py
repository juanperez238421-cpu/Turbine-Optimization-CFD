#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

import cv2

CANONICAL = "vid_2025-08-29_19-28-15.mp4"


def mount_drive(mountpoint="/content/drive"):
    try:
        from google.colab import drive
    except Exception as exc:
        raise RuntimeError("This helper is intended for Google Colab.") from exc
    drive.mount(mountpoint)
    return Path(mountpoint)


def find_best_video(root: Path, basename: str = CANONICAL) -> Path:
    matches = sorted(root.rglob(basename), key=lambda p: (len(p.parts), str(p)))
    if not matches:
        raise FileNotFoundError(f"{basename} not found below {root}. Add a Drive shortcut to the PIV data or pass --video.")
    if len(matches) > 1:
        print("[ASTRA] Multiple canonical-name files found; SHA/provenance will be recorded:")
        for p in matches: print("  ", p)
    return matches[0]


def find_pivlab_dir(root: Path) -> Path | None:
    parents = {}
    for p in root.rglob("PIVlab_*.txt"):
        parents[p.parent] = parents.get(p.parent, 0) + 1
    return max(parents, key=parents.get) if parents else None


def full_frame_roi(video: Path):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened(): raise RuntimeError(f"Cannot open {video}")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); cap.release()
    return [0,0,w,h]


def main():
    p=argparse.ArgumentParser(description="ASTRA maximum online real-data study in Google Colab")
    p.add_argument("--video"); p.add_argument("--drive-root",default="/content/drive"); p.add_argument("--output-dir",default="/content/astra_superstudy_outputs")
    p.add_argument("--roi",nargs=4,type=int); p.add_argument("--exploratory-full-frame",action="store_true"); p.add_argument("--max-frames",type=int)
    args=p.parse_args()
    root=mount_drive(args.drive_root); video=Path(args.video) if args.video else find_best_video(root); pivlab_dir=find_pivlab_dir(root)
    print("[ASTRA] Canonical candidate:",video); print("[ASTRA] Historical PIVlab directory:",pivlab_dir)
    if args.roi: roi=list(args.roi); exploratory=False
    elif args.exploratory_full_frame: roi=full_frame_roi(video); exploratory=True; print("[ASTRA][WARNING] Full-frame ROI is exploratory only; publication gate will remain blocked.")
    else: raise RuntimeError("Provide --roi X0 Y0 X1 Y1 from audited experimental geometry, or use --exploratory-full-frame for a non-publication test.")
    repo=Path(__file__).resolve().parents[1]; out=Path(args.output_dir)
    cmd=[sys.executable,str(repo/"scripts"/"run_astra_q1_superstudy.py"),"--video",str(video),"--config",str(repo/"configs"/"publication_q1.yaml"),"--ablation-design",str(repo/"configs"/"ablation_oat_q1.yaml"),"--output-dir",str(out),"--roi",*map(str,roi)]
    if args.max_frames is not None: cmd += ["--max-frames",str(args.max_frames)]
    print("[ASTRA] Running:"," ".join(cmd)); subprocess.run(cmd,check=True)
    if pivlab_dir is not None:
        from astra_piv.convergence import write_convergence
        piv_files=sorted(pivlab_dir.glob("PIVlab_*.txt")); sizes=[n for n in [25,50,75,100,150,200,250] if n<=len(piv_files)]
        if sizes: write_convergence(piv_files,sizes,out/"05_historical_pivlab_direct_only_convergence")
        print(f"[ASTRA] Historical direct-only audit saw {len(piv_files)} PIVlab files.")
    meta={"video":str(video),"pivlab_dir":str(pivlab_dir) if pivlab_dir else None,"roi":roi,"exploratory_full_frame":exploratory,"cfd_used":False}
    (out/"ONLINE_RUN_CONTEXT.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("[ASTRA] Completed. CFD remained sealed.")


if __name__=="__main__": main()
