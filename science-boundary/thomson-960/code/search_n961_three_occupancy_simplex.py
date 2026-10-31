#!/usr/bin/env python3
"""Track distinct N=960 basin sheets into a constant-total N961 occupancy simplex.

The shared N961 hub has three useful deletion labels:
  886 -> live record R,
  960 -> nearby A,
  380 -> a higher but still 24-dislocation basin H.

For each deletion endpoint, construct an exact fractional N961 vertex by
re-inserting the deleted hub particle as a zero-charge ghost.  Thus the active
960 unit charges are already at a genuine N960 local minimum and the total
charge is exactly 960.  Then continue that local minimum toward the common
simplex center while keeping

    q886 + q960 + q380 = 2

and every other charge equal to one.  Equivalently the three charge deficiencies
sum to one, so total charge remains exactly 960 throughout.

If R/A/H continuations reach geometrically or energetically distinct minima at
the same center occupancy (2/3,2/3,2/3), the auxiliary occupancy landscape has
multiple sheets at identical parameters.  Projecting each center state back to
ordinary N960 by deleting each distinguished label tests whether any sheet has
a new low-energy exit.

This avoids the total-charge confound of independent two-charge rectangular
loops and directly probes the multistability implied by the observed endpoint
hysteresis.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from collections import Counter

import numpy as np

import search_live_size_bounce as sbounce
import search_size_beam as sbeam
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_n961_occupancy_exchange import sig_json

LABELS = (886, 960, 380)
KNOWN = {
    'R': 444368.3924061973,
    'A': 444368.3956862258,
    'B': 444368.4029728613,
    'D': 444368.41099308443,
    'e432': 444368.4322496275,
    'H380': 444368.6474273098,
}


def classify(e: float, live: float) -> str:
    refs = dict(KNOWN); refs['R'] = float(live)
    name, err = min(((n, abs(float(e)-v)) for n,v in refs.items()), key=lambda z:z[1])
    return name if err < 2e-6 else 'novel'


def insert_row(x: np.ndarray, idx: int, row: np.ndarray) -> np.ndarray:
    return np.insert(np.asarray(x,float), int(idx), np.asarray(row,float), axis=0)


def project(x961: np.ndarray, delete_idx: int, live: float, maxiter: int):
    z = np.delete(np.asarray(x961,float), int(delete_idx), axis=0)
    e, y, nit, ok = sbeam.stable_relax(z, maxiter)
    return {
        'delete_index': int(delete_idx), 'energy': float(e),
        'delta_live': float(e-live), 'class': classify(e,live),
        'signature': sig_json(y), 'nit': int(nit), 'success': bool(ok),
        'points': y.tolist(),
    }


def parse_schedule(text: str):
    vals=[float(z) for z in text.split(',') if z.strip()]
    if not vals or abs(vals[0])>1e-12 or abs(vals[-1]-1)>1e-12:
        raise ValueError('schedule must start at 0 and end at 1')
    if any(v<0 or v>1 for v in vals) or any(vals[i+1] < vals[i]-1e-14 for i in range(len(vals)-1)):
        raise ValueError('schedule must be monotone in [0,1]')
    return vals


def charges_on_path(zero_label: int, s: float) -> np.ndarray:
    # deficiency vertex has d_zero=1. Center has all deficiencies 1/3.
    q=np.ones(961,float)
    for lab in LABELS:
        d0 = 1.0 if lab == zero_label else 0.0
        d = (1.0-s)*d0 + s/3.0
        q[lab] = 1.0-d
    if abs(float(np.sum(q))-960.0) > 2e-10:
        raise RuntimeError(f'charge conservation failure {np.sum(q)}')
    return q


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('A_json')
    ap.add_argument('--zero-label',type=int,choices=list(LABELS),required=True)
    ap.add_argument('--schedule',default='0,.08,.16,.28,.42,.58,.72,.84,.92,1')
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--hub-maxiter',type=int,default=3200)
    ap.add_argument('--vertex-maxiter',type=int,default=4200)
    ap.add_argument('--weighted-maxiter',type=int,default=2200)
    ap.add_argument('--project-maxiter',type=int,default=3600)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    _,A=sbounce.load_points(pathlib.Path(args.A_json))
    vc=sbounce.voronoi_candidates(A); sel=vc[3]
    hub=sbounce.relax(np.vstack([A,np.asarray(sel['point'])[None,:]]),args.hub_maxiter)
    xhub=np.asarray(hub['points'],float)
    if abs(float(hub['energy'])-445303.247369582)>5e-4:
        raise RuntimeError(f'unexpected hub {hub["energy"]}')
    print('HUB',f"{hub['energy']:.12f}",'tri',sel['triangle'],flush=True)

    # Hard-delete the selected hub label and fully repolish the ordinary N960 endpoint.
    e0,y0,nit0,ok0=sbeam.stable_relax(np.delete(xhub,args.zero_label,axis=0),args.vertex_maxiter)
    vclass=classify(e0,args.live_score)
    print('VERTEX_ENDPOINT','zero',args.zero_label,vclass,f'{e0:.12f}',
          f'dLive={e0-args.live_score:+.9g}',sig_json(y0)['coord'],flush=True)

    # Reinsert the hub coordinate as a zero-charge ghost at the original label.
    x=insert_row(y0,args.zero_label,xhub[args.zero_label])
    schedule=parse_schedule(args.schedule)
    trace=[]
    for s in schedule:
        q=charges_on_path(args.zero_label,s)
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x,q,args.weighted_maxiter)
        rec={
            's':float(s),'q886':float(q[886]),'q960':float(q[960]),'q380':float(q[380]),
            'total_charge':float(np.sum(q)),'weighted_energy':float(ew),
            'gradient_rms':float(grms),'nit':int(nit),'success':bool(ok),'message':str(msg),
            'sig_del886':sig_json(np.delete(x,886,axis=0)),
            'sig_del960':sig_json(np.delete(x,960,axis=0)),
            'sig_del380':sig_json(np.delete(x,380,axis=0)),
        }
        trace.append(rec)
        print('STEP',f's={s:.6g}',f'q=({q[886]:.6g},{q[960]:.6g},{q[380]:.6g})',
              f'Ew={ew:.12f}',f'grms={grms:.3g}','nit',nit,'ok',ok,flush=True)

    center=x.copy()
    projections=[]
    for di in LABELS:
        pr=project(center,di,args.live_score,args.project_maxiter)
        projections.append(pr)
        print('CENTER_PROJECT','del',di,pr['class'],f"{pr['energy']:.12f}",
              f"dLive={pr['delta_live']:+.9g}",pr['signature']['coord'],flush=True)

    best=min(projections,key=lambda r:r['energy'])
    out={
        'live_score':float(args.live_score),'zero_label':int(args.zero_label),
        'vertex_endpoint':{'energy':float(e0),'delta_live':float(e0-args.live_score),'class':vclass,
                           'signature':sig_json(y0),'nit':int(nit0),'success':bool(ok0)},
        'hub_energy':float(hub['energy']),'hub_triangle':sel['triangle'],
        'schedule':schedule,'trace':trace,
        'center_charges':{'886':2/3,'960':2/3,'380':2/3},
        'center_weighted_energy':float(trace[-1]['weighted_energy']),
        'center_weighted_grms':float(trace[-1]['gradient_rms']),
        'center_points':center.tolist(),'projections':projections,
        'best_projection':{k:v for k,v in best.items() if k!='points'},
    }
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best['energy'] < args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(best,separators=(',',':'))+'\n')

if __name__=='__main__':
    main()
