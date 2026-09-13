#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from astra_piv.config import load_config
from astra_piv.robustness_v2 import temporal_dependence_report, temporal_block_jackknife_v2, random_contiguous_deletion_stability, write_robustness_outputs


def main():
    p=argparse.ArgumentParser(description="ASTRA temporal robustness stress test")
    p.add_argument("--pool-csv",required=True); p.add_argument("--reliability-npy"); p.add_argument("--config",default="configs/publication_q1.yaml"); p.add_argument("--methods",nargs="+",required=True); p.add_argument("--n",type=int,required=True); p.add_argument("--blocks",type=int,default=5); p.add_argument("--stress-repeats",type=int,default=50); p.add_argument("--delete-fraction",type=float,default=0.15); p.add_argument("--output-dir",required=True)
    args=p.parse_args(); pool=pd.read_csv(args.pool_csv); reliability=np.load(args.reliability_npy) if args.reliability_npy else None; cfg=load_config(args.config)
    dependence=temporal_dependence_report(pool)
    jdf,jmeta=temporal_block_jackknife_v2(pool,args.methods,args.n,cfg,reliability=reliability,blocks=args.blocks)
    sdf,smeta=random_contiguous_deletion_stability(pool,args.methods,args.n,cfg,reliability=reliability,delete_fraction=args.delete_fraction,repeats=args.stress_repeats)
    write_robustness_outputs(args.output_dir,dependence,jdf,jmeta,sdf,smeta)
    print(json.dumps({"dependence":dependence,"jackknife":jmeta,"stress":smeta},indent=2))


if __name__=="__main__": main()
