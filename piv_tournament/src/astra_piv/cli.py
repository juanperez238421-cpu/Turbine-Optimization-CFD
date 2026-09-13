from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .archive import index_archive, publication_targets, extract_members, find_first
from .config import load_config
from .pipeline import run_full_video_pipeline, run_tournament_on_pool, run_source_audit
from .provenance import inspect_video_provenance
from .pivlab_ascii import audit_pivlab_files


def cmd_archive_index(args):
    members = index_archive(args.archive, args.output)
    groups = publication_targets(members)
    summary = {k: [m.path for m in v] for k, v in groups.items()}
    print(json.dumps(summary, indent=2))


def cmd_extract_targets(args):
    from .archive import list_archive
    members = list_archive(args.archive)
    groups = publication_targets(members)
    selected = []
    for group in args.groups:
        selected.extend(groups.get(group, []))
    paths = extract_members(args.archive, selected, args.destination, overwrite=args.overwrite)
    print(json.dumps([str(p) for p in paths], indent=2))


def cmd_full(args):
    cfg = load_config(args.config)
    result = run_full_video_pipeline(
        args.video,
        cfg,
        args.output_dir,
        allow_noncanonical_smoke=args.allow_noncanonical_smoke,
        max_frames=args.max_frames,
    )
    print(json.dumps(result, indent=2))


def cmd_source_audit(args):
    cfg = load_config(args.config)
    result = run_source_audit(args.video, cfg, args.output_dir,
                              scan_features=args.scan_features, max_frames=args.max_frames)
    print(json.dumps(result, indent=2))


def cmd_tournament_csv(args):
    cfg = load_config(args.config)
    df = pd.read_csv(args.pair_csv)
    reliability = np.load(args.reliability) if args.reliability else None
    _, summary, _ = run_tournament_on_pool(
        df, cfg, args.output_dir, reliability=reliability, source_video_sha256=args.source_video_sha256
    )
    print(json.dumps(summary, indent=2))


def cmd_pivlab_audit(args):
    paths = sorted(Path(args.directory).glob(args.pattern))
    _, _, _, meta = audit_pivlab_files(paths, args.output_dir)
    print(json.dumps(meta, indent=2))


def build_parser():
    p = argparse.ArgumentParser(prog="astra-piv")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("source-audit", help="Verify source identity and full decode; never select experimental pairs")
    s.add_argument("video")
    s.add_argument("--config")
    s.add_argument("--output-dir", required=True)
    s.add_argument("--scan-features", action="store_true")
    s.add_argument("--max-frames", type=int, help="Limit optional feature scan only; always reported as partial when reached")
    s.set_defaults(func=cmd_source_audit)

    a = sub.add_parser("archive-index", help="Index a ZIP/RAR without bulk extraction")
    a.add_argument("archive")
    a.add_argument("--output", required=True)
    a.set_defaults(func=cmd_archive_index)

    e = sub.add_parser("extract-targets", help="Selectively extract publication-relevant archive members")
    e.add_argument("archive")
    e.add_argument("--groups", nargs="+", default=["canonical_video", "pivlab_ascii", "pivlab_settings"])
    e.add_argument("--destination", required=True)
    e.add_argument("--overwrite", action="store_true")
    e.set_defaults(func=cmd_extract_targets)

    f = sub.add_parser("full", help="Run real-video stationarity + coarse PIV + selector tournament")
    f.add_argument("video")
    f.add_argument("--config")
    f.add_argument("--output-dir", required=True)
    f.add_argument("--allow-noncanonical-smoke", action="store_true")
    f.add_argument("--max-frames", type=int)
    f.set_defaults(func=cmd_full)

    t = sub.add_parser("tournament-csv", help="Run selector tournament from a precomputed pair-feature CSV")
    t.add_argument("pair_csv")
    t.add_argument("--config")
    t.add_argument("--reliability")
    t.add_argument("--source-video-sha256")
    t.add_argument("--output-dir", required=True)
    t.set_defaults(func=cmd_tournament_csv)

    q = sub.add_parser("pivlab-audit", help="Audit original PIVlab ASCII exports")
    q.add_argument("directory")
    q.add_argument("--pattern", default="PIVlab_*.txt")
    q.add_argument("--output-dir", required=True)
    q.set_defaults(func=cmd_pivlab_audit)
    return p


def main():
    p = build_parser()
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
