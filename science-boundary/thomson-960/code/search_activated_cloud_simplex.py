#!/usr/bin/env python3
"""Search the activated e432->B/A/R defect-cloud simplex near the basin junction.

The three labeled e432->B/A/R geodesics pass through closely related activated
38/896/26 triangulations near t ~= 0.492.  Instead of mixing relaxed minima,
construct those *activated* states, use the B-activated state as a local sphere
base point, and scan linear combinations/extrapolations of the log fields toward
the A- and R-activated states.  Every point is then fully relaxed.

This tests whether alternative orderings of the small central Delaunay-event
set expose a fourth basin not visible on any one endpoint interpolation.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.spatial import ConvexHull

import search_topology_morph as tm
import search_defect_core_transfer as dc


def load(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError('expected 960 labeled points')
    x=np.asarray(p,float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def exp_vec(base,v):
    a=np.linalg.norm(v,axis=1); out=np.empty_like(base)
    small=a<1e-12
    out[small]=base[small]+v[small]
    q=~small
    out[q]=np.cos(a[q])[:,None]*base[q]+(np.sin(a[q])/a[q])[:,None]*v[q]
    return out/np.linalg.norm(out,axis=1)[:,None]


def activated(source,target,t):
    v=dc.log_field(source,target)
    return exp_vec(source,t*v)


def edge_set(x):
    h=ConvexHull(x); es=set()
    for tri in h.simplices:
        a,b,c=map(int,tri)
        es.add(tuple(sorted((a,b)))); es.add(tuple(sorted((b,c)))); es.add(tuple(sorted((c,a))))
    return es


def rms_log(v):
    return float(np.sqrt(np.mean(np.sum(v*v,axis=1))))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('B_json'); ap.add_argument('A_json'); ap.add_argument('R_json')
    ap.add_argument('--t0',type=float,default=0.492)
    ap.add_argument('--alphas',default='-1.2,-0.8,-0.4,0,0.35,0.7,1.0,1.3,1.7,2.1,2.6')
    ap.add_argument('--betas',default='-1.0,-0.6,-0.3,0,0.25,0.5,0.75,1.0,1.25,1.5,1.8,2.2')
    ap.add_argument('--maxiter',type=int,default=3200)
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    S=load(args.source_json); B=load(args.B_json); A=load(args.A_json); R=load(args.R_json)
    XB=activated(S,B,args.t0); XA=activated(S,A,args.t0); XR=activated(S,R,args.t0)
    vA=dc.log_field(XB,XA); vR=dc.log_field(XB,XR)
    na=float(np.sqrt(np.sum(vA*vA))); nr=float(np.sqrt(np.sum(vR*vR)))
    cos=float(np.sum(vA*vR)/(na*nr))
    eB=edge_set(XB); eA=edge_set(XA); eR=edge_set(XR)
    geom={
        't0':args.t0,
        'B_energy':tm.raw_energy(XB),'A_energy':tm.raw_energy(XA),'R_energy':tm.raw_energy(XR),
        'B_coord':tm.coord_counts(XB),'A_coord':tm.coord_counts(XA),'R_coord':tm.coord_counts(XR),
        'B_to_A_rms':rms_log(vA),'B_to_R_rms':rms_log(vR),'A_R_log_cos_at_B':cos,
        'edge_diff_BA':len(eB-eA),'edge_diff_BR':len(eB-eR),'edge_diff_AR':len(eA-eR),
    }
    print('GEOM',geom,flush=True)

    alphas=[float(z) for z in args.alphas.split(',') if z]
    betas=[float(z) for z in args.betas.split(',') if z]
    rows=[]; saved=[]
    for a in alphas:
        for b in betas:
            x=exp_vec(XB,a*vA+b*vR)
            startE=tm.raw_energy(x); startcc=tm.coord_counts(x)
            e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
            row={'alpha_A':a,'beta_R':b,'start_energy':startE,'start_coord':startcc,
                 'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,
                 'nit':nit,'success':ok}
            rows.append(row)
            print('TRY a',a,'b',b,'start',f'{startE:.9f}','scc',startcc,
                  'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,'nit',nit,flush=True)
            if e<args.live_score+0.35 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                saved.append({'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,
                              'alpha_A':a,'beta_R':b,'points':y.tolist()})
    saved.sort(key=lambda z:z['energy'])
    best=min(rows,key=lambda z:z['energy']) if rows else None
    out={'geometry':geom,'rows':rows,'distinct_low_basins':saved[:32],
         'best_energy':best['energy'] if best else None,
         'best_delta_live':best['delta_live'] if best else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
