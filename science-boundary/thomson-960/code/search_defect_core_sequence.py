#!/usr/bin/env python3
"""Beam search over sequential nucleation of target defect cores.

For a source/target pair such as D2 -> live, identify target 5-7 cores not
present in the source after same-type defect matching.  Starting from the
aligned source minimum, activate one unused target core at a time using the
source->target log displacement localized around that core, fully relax, and
retain a small energy-ranked/diverse beam.  This searches the discrete order of
scar nucleation/reconnection rather than assuming all target cores move at once.
"""
from __future__ import annotations
import argparse,json,pathlib
from dataclasses import dataclass
import numpy as np

import search_topology_morph as tm
import search_defect_core_transfer as dc


@dataclass
class Node:
    points: np.ndarray
    energy: float
    coord: dict
    used: tuple[int,...]
    path: list[dict]


def key_used(used):
    return tuple(sorted(used))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=28)
    ap.add_argument('--radii',default='0.10,0.18')
    ap.add_argument('--alphas',default='0.45,0.80,1.15')
    ap.add_argument('--beam',type=int,default=6); ap.add_argument('--per-used',type=int,default=2)
    ap.add_argument('--maxiter',type=int,default=3000); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    source=dc.load(args.source_json); target=dc.load(args.target_json)
    ds0=dc.degrees(source); dt=dc.degrees(target)
    sm,perm,rms,mrms=dc.align(source,target,args.seed,args.starts)
    ds=ds0[perm]
    cores=dc.unmatched_target_cores(sm,ds,target,dt)
    if not cores:
        raise RuntimeError('no unmatched target cores')
    radii=[float(z) for z in args.radii.split(',') if z]
    alphas=[float(z) for z in args.alphas.split(',') if z]
    e0=tm.raw_energy(sm); c0=tm.coord_counts(sm)
    beam=[Node(sm,e0,c0,tuple(),[])]
    all_rows=[]; best=(e0,sm.copy(),c0,[],tuple())
    print('START',e0,c0,'target',tm.raw_energy(target),tm.coord_counts(target),'cores',len(cores),
          'nn',rms,'assign',mrms,flush=True)
    for j,c in enumerate(cores):
        print('CORE',j,'i5',c['i5'],'i7',c['i7'],'center',c['center'].tolist(),flush=True)

    for depth in range(1,len(cores)+1):
        candidates=[]
        for parent_id,node in enumerate(beam):
            unused=[j for j in range(len(cores)) if j not in node.used]
            # Recompute source->target field from the relaxed current node while
            # preserving the established particle correspondence.
            v=dc.log_field(node.points,target)
            for core_id in unused:
                center=[cores[core_id]['center']]
                for r in radii:
                    w=dc.weights(node.points,center,r)
                    for a in alphas:
                        x=dc.exp_field(node.points,v,a,w)
                        estart=tm.raw_energy(x)
                        e,y,nit,ok=tm.relax(x,maxiter=args.maxiter)
                        cc=tm.coord_counts(y); used=tuple(node.used+(core_id,))
                        step={'depth':depth,'core':core_id,'radius':r,'alpha':a,
                              'start_energy':estart,'energy':e,'delta_live':e-args.live_score,
                              'coord_counts':cc,'nit':nit,'success':ok}
                        path=node.path+[step]
                        row=dict(step); row['parent']=parent_id; row['used']=list(used)
                        all_rows.append(row)
                        candidates.append(Node(y,e,cc,used,path))
                        print('STEP',depth,'parent',parent_id,'core',core_id,'r',r,'a',a,
                              'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,flush=True)
                        if e < best[0]: best=(e,y.copy(),cc,path,used)
        # Dedup near-identical minima within each used-core set. Keep a small
        # number per combinatorial state, then a global energy beam.
        groups={}
        for n in sorted(candidates,key=lambda z:z.energy):
            k=key_used(n.used); g=groups.setdefault(k,[])
            if any(abs(n.energy-z.energy)<2e-6 and n.coord==z.coord for z in g):
                continue
            if len(g)<args.per_used: g.append(n)
        pool=[n for g in groups.values() for n in g]
        pool.sort(key=lambda z:z.energy)
        beam=pool[:args.beam]
        print('BEAM',depth,[(n.energy,n.coord,list(n.used)) for n in beam],flush=True)
        if not beam: break

    final=[]
    seen=[]
    for n in sorted(beam,key=lambda z:z.energy):
        if any(abs(n.energy-z['energy'])<2e-6 and n.coord==z['coord_counts'] for z in seen): continue
        z={'energy':n.energy,'delta_live':n.energy-args.live_score,'coord_counts':n.coord,
           'used':list(n.used),'path':n.path,'points':n.points.tolist()}
        seen.append(z); final.append(z)
    out={'seed':args.seed,'source_energy':e0,'source_coord':c0,
         'target_energy':tm.raw_energy(target),'target_coord':tm.coord_counts(target),
         'particle_nn_rms':rms,'assignment_rms':mrms,
         'cores':[{'i5':c['i5'],'i7':c['i7'],'center':c['center'].tolist()} for c in cores],
         'rows':all_rows,'final_beam':final,
         'best_energy':best[0],'best_delta_live':best[0]-args.live_score,
         'best_coord':best[2],'best_used':list(best[4]),'best_path':best[3]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    pathlib.Path(str(args.out)+'.best.json').write_text(
        json.dumps({'name':'defect-core-sequence-best','energy':best[0],'coord_counts':best[2],
                    'used':list(best[4]),'path':best[3],'points':best[1].tolist()},separators=(',',':'))+'\n')
    if best[0] < args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(
            json.dumps({'name':'defect-core-sequence-candidate','energy':best[0],
                        'coord_counts':best[2],'points':best[1].tolist()},separators=(',',':'))+'\n')

if __name__=='__main__': main()
