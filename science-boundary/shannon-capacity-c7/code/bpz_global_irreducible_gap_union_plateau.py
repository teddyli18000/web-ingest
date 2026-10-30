#!/usr/bin/env python3
"""Exact lexicographic global prize search over irreducible support-gap pools.

Input is the output of bpz_gap_irreducibility_audit.py.  Complete five-dimensional
support pools of every outside-only irreducible case are unioned into U.  For each
of the 18 pinned BPZ terminal baselines, every point of U x U outside the baseline
is a candidate. Selecting a candidate pays exactly for all old baseline points it
conflicts with; candidate-candidate conflicts are hard. Thus arbitrary nonrectangular
mixtures and shared deletion costs are allowed.

Primary objective: selected_new - distinct_deleted_baseline.
Secondary objective: selected_new cardinality. A positive gain is a breakthrough
candidate; gain zero with a nonempty optimum gives a distant record-tie mother.
"""
from __future__ import annotations
import argparse,json,multiprocessing as mp,os
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery
G={}
def init_worker(s):
    global G;G=s

def solve_task(t):
    q,r,o=t;ring,B,fam,U,Uv,core=G['ring'],G['B'],G['fam'],G['U'],G['Uv'],G['core']
    P=terminal_periphery(fam,q,r,o);baseline=core|P
    if len(baseline)!=134753:raise RuntimeError(('baseline',len(baseline)))
    cand=sorted((x,y) for x in Uv for y in Uv if (x,y) not in baseline);idx={p:i for i,p in enumerate(cand)};byfirst={}
    for p in P:byfirst.setdefault(p[0],[]).append(p)
    fk=set(byfirst);losses=[]
    for x,y in cand:
        L={(a,b) for a in ring.NB[x]&B for b in ring.NB[y]&B}
        for a in ring.NB[x]&fk:
            for p in byfirst[a]:
                if p[1] in ring.NB[y]:L.add(p)
        if not L<=baseline:raise RuntimeError(('loss outside baseline',(x,y),len(L-baseline)))
        losses.append(L)
    n=len(cand);touched=sorted(set().union(*losses) if losses else set());bi={p:i for i,p in enumerate(touched)};w=WCNF()
    for i,L in enumerate(losses):
        for p in L:w.append([-(i+1),n+bi[p]+1])
    conflicts=0
    for i,(x,y) in enumerate(cand):
        for a in ring.NB[x]&U:
            for b in ring.NB[y]&U:
                j=idx.get((a,b))
                if j is not None and j>i:w.append([-(i+1),-(j+1)]);conflicts+=1
    M=n+1
    for i in range(n):w.append([i+1],weight=M+1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=M)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute()
    if model is None:raise RuntimeError(('RC2 no model',t))
    pos={z for z in model if z>0};si=[i for i in range(n) if i+1 in pos];lost={touched[j] for j in range(len(touched)) if n+j+1 in pos};forced=set()
    for i in si:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(('loss mismatch',len(lost),len(forced)))
    selected=[cand[i] for i in si];gain=len(selected)-len(lost)
    for i,p in enumerate(selected):
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in selected[i+1:]:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('new-new',p,z))
        for z in baseline-lost:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('retained',p,z))
    return {'q':q,'r':r,'terminal_orientation':o,'gain':gain,'selected':len(selected),'deleted':len(lost),'candidates':n,'touched_blockers':len(touched),'conflicts':conflicts,'selected_points':[list(p) for p in selected],'deleted_points':[list(p) for p in sorted(lost)]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('audit_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    audit=json.loads(a.audit_json.read_text());rows=audit.get('irreducible_positive',audit.get('irreducible',[]));k=int(audit['k']);Cs=[]
    for z in rows:
        C=frozenset(map(int,z['owners']))
        if len(C)!=k:raise RuntimeError(('owner count',k,C))
        if int(z.get('min_owner_intersection_at_alpha',0))!=0:raise RuntimeError(('not irreducible',C))
        if int(z.get('raw_gain',int(z['alpha'])-k))<=0:continue
        Cs.append(C)
    if not Cs:raise RuntimeError(('no irreducible positive cases',k))
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B);U={z for z in range(ring.n) if any((ring.NB[z]&B)<=C for C in Cs)};Uv=sorted(U);core={(x,y) for x in B for y in B};tasks=[(q,r,o) for q in ('O','H','V') for r in ('O','H','V') for o in (0,1)]
    state={'ring':ring,'B':B,'fam':fam,'U':U,'Uv':Uv,'core':core};workers=max(1,min(a.workers,4,len(tasks)));ctx=mp.get_context('fork')
    with ctx.Pool(workers,initializer=init_worker,initargs=(state,)) as p:outs=list(p.imap_unordered(solve_task,tasks,chunksize=1))
    outs.sort(key=lambda z:(z['gain'],z['selected'],-z['deleted']),reverse=True);best=outs[0]
    if best['selected']<=0:raise RuntimeError(('no nonempty optimum',best))
    P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);baseline=core|P;sel={tuple(p) for p in best['selected_points']};lost={tuple(p) for p in best['deleted_points']};cand=(baseline-lost)|sel
    if len(cand)!=134753+best['gain']:raise RuntimeError(('score',len(cand),best['gain']))
    def enc(p):return ''.join(str(z) for z in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    result={'method':'exact-lexicographic-global-irreducible-gap-union','k':k,'irreducible_owner_sets':len(Cs),'union_factor_pool':len(U),'scenario_count':len(outs),'workers':workers,'best':best,'top10':outs[:10],'candidate_score':len(pts)};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({x:y for x,y in result.items() if x!='top10'},sort_keys=True))
if __name__=='__main__':main()
