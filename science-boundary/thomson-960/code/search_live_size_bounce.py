#!/usr/bin/env python3
"""Scout neighboring-size bounces from the live N=960 Thomson record.

Implements the unit-step core of Amore-Wales OSHBH (JCP 165, 164104, 2026)
but starts from the substantially better current Few Shots live record.

add mode:    960 -> 961 by adding at a low-individual-energy spherical Voronoi
             vertex, relax, then delete several high-contribution particles and
             relax back to 960.
remove mode: 960 -> 959 by deleting a high-contribution particle, relax, then
             add at several low-energy Voronoi vertices and relax back to 960.

The purpose is not to reproduce the published N=960 result.  Size change is a
qualitatively different barrier-crossing representation for the current record.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter
import numpy as np
from scipy.spatial import ConvexHull

import diagnose_soft_modes as sm
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology


def load_points(path):
    d=json.loads(pathlib.Path(path).read_text())
    pts=d.get('points') if isinstance(d,dict) else d
    x=np.asarray(pts,dtype=float); x/=np.linalg.norm(x,axis=1)[:,None]
    return d,x


def energy(x):
    q=sm.xyz_to_vars(x); e,_=sm.fg(q); return float(e)


def contributions(x):
    dots=np.clip(x@x.T,-1.0,1.0)
    r=np.sqrt(np.maximum(2.0-2.0*dots,1e-300)); np.fill_diagonal(r,np.inf)
    return np.sum(1.0/r,axis=1)


def voronoi_candidates(x):
    hull=ConvexHull(x)
    v=np.asarray(hull.equations[:,:3],dtype=float)
    v/=np.linalg.norm(v,axis=1)[:,None]
    # Outward hull normals are the spherical circumcentres of Delaunay faces.
    d=np.linalg.norm(v[:,None,:]-x[None,:,:],axis=2)
    indiv=np.sum(1.0/d,axis=1)
    order=np.argsort(indiv)
    rows=[]
    for rank,i in enumerate(order):
        rows.append({'rank':int(rank),'face_index':int(i),'triangle':[int(z) for z in hull.simplices[i]],
                     'individual_energy':float(indiv[i]),'point':v[i]})
    return rows


def coord_counts(x):
    deg,_=topology(x); c=Counter(map(int,deg)); return {str(k):int(v) for k,v in sorted(c.items())}


def relax(x,maxiter):
    e,raw,y,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(x),maxiter=maxiter)
    return {'energy':float(e),'raw_energy':float(raw),'points':y,'nit':int(nit),'success':bool(ok),'message':str(msg)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('live_json')
    ap.add_argument('--mode',choices=['add','remove'],required=True); ap.add_argument('--rank',type=int,required=True)
    ap.add_argument('--return-branches',type=int,default=4); ap.add_argument('--first-maxiter',type=int,default=2600)
    ap.add_argument('--return-maxiter',type=int,default=3200); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_points(args.live_json)
    if len(x0)!=960: raise ValueError('expected live N=960 seed')
    rows=[]

    if args.mode=='add':
        vc=voronoi_candidates(x0); sel=vc[args.rank]
        xstart=np.vstack([x0,np.asarray(sel['point'])[None,:]])
        first=relax(xstart,args.first_maxiter); x1=first['points']
        contrib=contributions(x1); order=list(map(int,np.argsort(-contrib)))
        # Avoid spending one return branch on the obvious exact reverse when the
        # newly inserted particle remains identifiable as the last label.
        order_nontrivial=[i for i in order if i!=len(x0)]
        chosen=order_nontrivial[:args.return_branches]
        print('FIRST add rank',args.rank,'tri',sel['triangle'],'indiv',sel['individual_energy'],
              'E961',f"{first['energy']:.12f}",'return_delete',[(i,float(contrib[i])) for i in chosen],flush=True)
        for j,i in enumerate(chosen):
            xr=np.delete(x1,i,axis=0); rr=relax(xr,args.return_maxiter); y=rr['points']
            rec={'branch':j,'delete_index':int(i),'delete_contribution':float(contrib[i]),
                 'energy':rr['energy'],'raw_energy':rr['raw_energy'],'delta_live':rr['energy']-args.live_score,
                 'coord_counts':coord_counts(y),'nit':rr['nit'],'success':rr['success'],'message':rr['message']}
            rows.append((rec,y.copy()))
            print('RETURN',j,'del',i,'E',f"{rr['energy']:.12f}",'dLive',f"{rr['energy']-args.live_score:+.9g}",rec['coord_counts'],flush=True)
        source={'mode':'add','rank':args.rank,'triangle':sel['triangle'],'individual_energy':sel['individual_energy'],
                'first_energy':first['energy'],'first_nit':first['nit']}
    else:
        contrib=contributions(x0); order=list(map(int,np.argsort(-contrib))); i=order[args.rank]
        xstart=np.delete(x0,i,axis=0); first=relax(xstart,args.first_maxiter); x1=first['points']
        vc=voronoi_candidates(x1); chosen=vc[:args.return_branches]
        print('FIRST remove rank',args.rank,'idx',i,'contrib',float(contrib[i]),
              'E959',f"{first['energy']:.12f}",'return_add',[(z['rank'],z['individual_energy'],z['triangle']) for z in chosen],flush=True)
        for j,z in enumerate(chosen):
            xr=np.vstack([x1,np.asarray(z['point'])[None,:]]); rr=relax(xr,args.return_maxiter); y=rr['points']
            rec={'branch':j,'add_rank':int(z['rank']),'add_triangle':z['triangle'],'add_individual_energy':z['individual_energy'],
                 'energy':rr['energy'],'raw_energy':rr['raw_energy'],'delta_live':rr['energy']-args.live_score,
                 'coord_counts':coord_counts(y),'nit':rr['nit'],'success':rr['success'],'message':rr['message']}
            rows.append((rec,y.copy()))
            print('RETURN',j,'add',z['triangle'],'E',f"{rr['energy']:.12f}",'dLive',f"{rr['energy']-args.live_score:+.9g}",rec['coord_counts'],flush=True)
        source={'mode':'remove','rank':args.rank,'delete_index':int(i),'delete_contribution':float(contrib[i]),
                'first_energy':first['energy'],'first_nit':first['nit']}

    rows.sort(key=lambda z:z[0]['energy']); serial=[]; seen=[]
    for rec,y in rows:
        rr=dict(rec)
        # Persist coordinates for scientifically interesting distinct endpoints,
        # including all sub-live candidates and the best few novel return basins.
        if len(serial)<4 or rec['energy']<args.live_score-2e-7:
            rr['points']=y.tolist()
        serial.append(rr)
    best=serial[0]['energy'] if serial else float('inf')
    out={'live_score':args.live_score,'source':source,'returns':serial,
         'best_energy':best,'best_delta_live':best-args.live_score}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('neighbor-size bounce produced candidate below live\n')

if __name__=='__main__': main()
