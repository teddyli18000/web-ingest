#!/usr/bin/env python3
"""Audit exact hard deletions from the reconstructed shared N=961 hub.

This is a control for fractional-occupancy experiments.  In particular, the
label 960 is the particle inserted into A before the N961 relaxation, but after
relaxing to the common hub it is not guaranteed that deleting that same label
returns to A.  Test the key labels directly without any fractional continuation.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

from search_live_size_bounce import load_points,voronoi_candidates,relax as size_relax
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology
from collections import Counter
import diagnose_soft_modes as sm

KNOWN={'R':444368.3924061973,'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443}

def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def classify(e):
    n,err=min(((k,abs(float(e)-v)) for k,v in KNOWN.items()),key=lambda z:z[1])
    return n if err<2e-6 else 'novel'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_json'); ap.add_argument('--indices',default='886,960')
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True)
    args=ap.parse_args()
    _,a=load_points(pathlib.Path(args.a_json)); sel=voronoi_candidates(a)[3]
    hub=size_relax(np.vstack([a,np.asarray(sel['point'],float)[None,:]]),3200); x=np.asarray(hub['points'],float)
    print('HUB',hub['energy'],'tri',sel['triangle'],'cc',counts(x),flush=True)
    rows=[]
    for idx in [int(z) for z in args.indices.split(',') if z.strip()]:
        z=np.delete(x,idx,axis=0)
        e,raw,y,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(z),maxiter=5000)
        row={'delete_index':idx,'energy':float(e),'raw_energy':float(raw),'delta_live':float(e-args.live_score),
             'class':classify(e),'coord_counts':counts(y),'nit':int(nit),'success':bool(ok),'message':str(msg),
             'points':y.tolist()}
        rows.append(row)
        print('DELETE',idx,row['class'],f'{e:.12f}','dLive',f"{row['delta_live']:+.9g}",'cc',row['coord_counts'],flush=True)
    pathlib.Path(args.out).write_text(json.dumps({'hub_energy':float(hub['energy']),'rows':rows},separators=(',',':'))+'\n')

if __name__=='__main__': main()
