#!/usr/bin/env python3
"""Return from the proven A->N961 interface using non-greedy topology classes.

The A rank-3 Voronoi insertion (triangle 599,282,502) relaxes to an N=961
minimum with 35/903/23 coordination.  Standard OSHBH return ranking by particle
energy is heavily biased: the first 32 deletion candidates are all degree 5,
and 30/32 relax to 23-dislocation N=960 minima.  This search deliberately
changes the return representation by selecting candidates of one requested
N=961 coordination degree (6 or 7), ranked by energy contribution within that
class, then fully relaxing the returned N=960 structures.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

from search_live_size_bounce import load_points,voronoi_candidates,relax,contributions,coord_counts
from search_e564_defect_flip_parallel import topology


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('A_json')
    ap.add_argument('--target-degree',type=int,choices=[6,7],required=True)
    ap.add_argument('--branches',type=int,default=10); ap.add_argument('--insert-rank',type=int,default=3)
    ap.add_argument('--first-maxiter',type=int,default=3000); ap.add_argument('--return-maxiter',type=int,default=3400)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True)
    args=ap.parse_args()

    _,x0=load_points(args.A_json)
    vc=voronoi_candidates(x0); ins=vc[args.insert_rank]
    xstart=np.vstack([x0,np.asarray(ins['point'])[None,:]])
    first=relax(xstart,args.first_maxiter); x1=first['points']
    deg,_=topology(x1); c=contributions(x1)
    candidates=[int(i) for i in np.argsort(-c) if int(deg[i])==args.target_degree]
    chosen=candidates[:args.branches]
    print('FIRST','rank',args.insert_rank,'tri',ins['triangle'],'E961',f"{first['energy']:.12f}",
          'cc',coord_counts(x1),'target_degree',args.target_degree,
          'chosen',[(i,float(c[i])) for i in chosen],flush=True)

    rows=[]
    for j,i in enumerate(chosen):
        xr=np.delete(x1,i,axis=0); rr=relax(xr,args.return_maxiter); y=rr['points']
        rec={'branch':j,'delete_index':i,'source_degree':int(deg[i]),'delete_contribution':float(c[i]),
             'energy':rr['energy'],'raw_energy':rr['raw_energy'],'delta_live':rr['energy']-args.live_score,
             'coord_counts':coord_counts(y),'nit':rr['nit'],'success':rr['success'],'message':rr['message']}
        rows.append((rec,y.copy()))
        print('RETURN',j,'del',i,'deg',deg[i],'E',f"{rr['energy']:.12f}",
              'dLive',f"{rr['energy']-args.live_score:+.9g}",rec['coord_counts'],flush=True)
    rows.sort(key=lambda z:z[0]['energy'])
    serial=[]
    for k,(rec,y) in enumerate(rows):
        r=dict(rec)
        # Preserve coordinates for every sub-live candidate and the best
        # topology-diverse endpoints so follow-up does not require rerunning.
        if rec['energy']<args.live_score-2e-7 or k<6 or rec['coord_counts']=={'5':36,'6':900,'7':24}:
            r['points']=y.tolist()
        serial.append(r)
    best=serial[0]['energy'] if serial else float('inf')
    out={'live_score':args.live_score,'insert_rank':args.insert_rank,'insert_triangle':ins['triangle'],
         'N961_energy':first['energy'],'N961_coord':coord_counts(x1),'target_degree':args.target_degree,
         'returns':serial,'best_energy':best,'best_delta_live':best-args.live_score}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('topology-stratified return candidate below live\n')

if __name__=='__main__': main()
