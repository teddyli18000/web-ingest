#!/usr/bin/env python3
"""Exact global amplification of the four distinct known minimum-killer k8 defects.

Each mode replaces eight core cells in one B-row (or column) by nine outside
points, for raw local gain +1.  All four modes arise from the independently
replayed known-pool k8 census and kill exactly BPZ private-pair colors
{0,4,5,6}.  Multiple rows may share peripheral blocker losses, so the correct
10D question is a joint prize optimization rather than summing per-defect killer
bounds.

This script reuses the audited weighted-MaxSAT machinery in
bpz_joint_row_defects_maxsat.py, but substitutes the four k8 modes and performs
an independent structural replay before writing any candidate certificate.
"""
from __future__ import annotations
import argparse,json,os
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import bpz_joint_row_defects_maxsat as J

K8_DEFECTS=[
 {'name':'k8a','owners':[1741,8888,10960,13248,13347,13600,13692,14040],
  'additions':[6494,10659,13297,13649,13684,14335,15959,16045,16147]},
 {'name':'k8b','owners':[1741,8888,10861,10960,13347,13600,13692,14040],
  'additions':[6494,10659,10910,13649,13684,14335,15959,16045,16147]},
 {'name':'k8c','owners':[1741,2433,8888,10960,13347,13600,13692,14040],
  'additions':[4492,6494,10659,13649,13684,14335,15959,16045,16147]},
 {'name':'k8d','owners':[8888,10861,10960,13248,13347,13600,13692,14040],
  'additions':[6494,10659,10910,13297,13649,13684,14335,15959,16045]},
]

def patched():
    J.PINNED_DEFECTS=K8_DEFECTS

def solve_task(t):
    patched();return J.solve_scenario(t)

def materialize(root:Path,best,out:Path)->int:
    patched();base,ring,B,fam=J.load_geometry(root)
    defects0=J.validate_defects(ring,B);defs={d['name']:d for d in defects0}
    P=J.terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);pv=sorted(P)
    selected=[(int(a),defs[name]) for a,name in best['selected']]
    loss={pv[j] for j in best['loss_indices']}
    removed=set();new=set()
    for a,d in selected:
        if best['axis']=='row':
            removed.update((a,c) for c in d['C']);new.update((a,y) for y in d['Y'])
        else:
            removed.update((c,a) for c in d['C']);new.update((y,a) for y in d['Y'])
    core={(a,b) for a in B for b in B}
    if not removed<=core or new&core:raise RuntimeError('candidate partition drift')
    if (new&P)-loss:raise RuntimeError(('new periphery point not charged',sorted((new&P)-loss)[:5]))
    kept=P-loss
    def cf10(x,y):return y[0] in ring.NB[x[0]] and y[1] in ring.NB[x[1]]
    for n in new:
        sb0=ring.NB[n[0]]&B;sb1=ring.NB[n[1]]&B
        if any((u,v) not in removed for u in sb0 for v in sb1):raise RuntimeError(('new-core',n))
        if any(cf10(n,p) for p in kept):raise RuntimeError(('new-periphery',n))
    nv=list(new)
    for i,x in enumerate(nv):
        for y in nv[i+1:]:
            if cf10(x,y):raise RuntimeError(('new-new',x,y))
    cand=(core-removed)|kept|new
    expected=134753+int(best['delta'])
    if len(cand)!=expected:raise RuntimeError(('score',len(cand),expected,len(new&P)))
    def enc(p):return ''.join(str(z) for z in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc(p) for p in cand)
    if len(pts)!=len(set(pts)):raise RuntimeError('duplicate points')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    return len(pts)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    root=a.tan_root.resolve();patched()
    # Validate modes once before spending solver time.
    _base,ring,B,_fam=J.load_geometry(root);validated=J.validate_defects(ring,B)
    if len(validated)!=4:raise RuntimeError(('mode count',len(validated)))
    tasks=[(str(root),q,r,o,axis) for q in ('O','H','V') for r in ('O','H','V') for o in (0,1) for axis in ('row','col')]
    workers=max(1,min(a.workers,len(tasks),4));results=[]
    if workers==1:
        for t in tasks:results.append(solve_task(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve_task,t) for t in tasks]
            for f in as_completed(fs):results.append(f.result())
    results.sort(key=lambda x:(x['delta'],x['selected_count'],-x['loss_count']),reverse=True);best=results[0]
    score=materialize(root,best,a.certificate) if best['delta']>0 else None
    status={'method':'exact-k8-min4-joint-row-prize-maxsat','mode_count':4,'scenario_count':len(results),'workers':workers,'best':best,'top10':results[:10],'candidate_materialized':best['delta']>0,'candidate_score':score}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(json.dumps(status,sort_keys=True))
if __name__=='__main__':main()
