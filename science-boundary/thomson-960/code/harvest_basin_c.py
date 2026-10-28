#!/usr/bin/env python3
"""Reproduce and persist the low C3 basin C from three equivalent R->A shear events."""
from __future__ import annotations
import argparse, json, pathlib, sys
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import search_composed_shears as scs


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots')
    ap.add_argument('--neighbor-json',required=True)
    ap.add_argument('--scale',type=float,default=0.95)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.few_shots)
    live_score,live_dir=scs.find_live(root)
    R=scs.cert_xyz(live_dir/'certificate.json')
    A=scs.float_xyz(pathlib.Path(args.neighbor_json))
    events,maperrs=scs.group_events(R,A)
    seq=[(0,1),(1,1),(2,1)]
    X=scs.make_start(R,events,seq,args.scale,'sequential')
    start=scs.raw_energy(X)
    E,Y,nit,ok=scs.stable_relax(X,maxiter=2200)
    cc=scs.coord_counts(Y)
    out={
      'source':'three C3-equivalent R->A shear events, sequential 0,1,2',
      'scale':args.scale,
      'live_score':live_score,
      'start_energy':start,
      'energy':E,
      'delta_vs_live':E-live_score,
      'nit':nit,
      'success':ok,
      'coord_counts':cc,
      'c3_mapping_max_errors':maperrs,
      'points':Y.tolist(),
    }
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
    print(f"C={E:.12f} dlive={E-live_score:+.12g} nit={nit} ok={ok} coord={cc}")
    if not (0.015 < E-live_score < 0.025):
        raise SystemExit('reproduced basin is not expected C energy window')

if __name__=='__main__':
    main()
