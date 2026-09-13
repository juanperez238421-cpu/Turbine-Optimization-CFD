#!/usr/bin/env python3
"""Inspect real exported CFD files before any publication rendering."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pyvista as pv


def read_any(path: Path):
    try:
        obj = pv.read(path)
    except Exception:
        obj = pv.get_reader(str(path)).read()
    if isinstance(obj, pv.MultiBlock):
        blocks = [b for b in obj if b is not None and getattr(b, 'n_points', 0) > 0]
        obj = pv.MultiBlock(blocks).combine(merge_points=False) if len(blocks) > 1 else blocks[0]
    return obj


def describe_array(arr):
    a = np.asarray(arr)
    finite = np.isfinite(a)
    flat = a[finite]
    return {
        'shape': list(a.shape),
        'finite_fraction': float(finite.mean()) if finite.size else None,
        'min': float(flat.min()) if flat.size else None,
        'max': float(flat.max()) if flat.size else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', type=Path)
    ap.add_argument('--json', dest='json_path', type=Path)
    args = ap.parse_args()
    ds = read_any(args.file)
    report = {
        'file': str(args.file),
        'n_points': ds.n_points,
        'n_cells': ds.n_cells,
        'bounds': list(ds.bounds),
        'point_data': {k: describe_array(v) for k, v in ds.point_data.items()},
        'cell_data': {k: describe_array(v) for k, v in ds.cell_data.items()},
    }
    print(json.dumps(report, indent=2))
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
