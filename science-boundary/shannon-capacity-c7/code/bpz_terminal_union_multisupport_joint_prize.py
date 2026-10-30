#!/usr/bin/env python3
"""Exact terminal-union + arbitrary audited support-family joint prize model.

Owner-set JSON inputs may be:
- neutral5 killer-audit outputs (`rows`, selecting min_owner_intersection == 0),
- generic gap irreducibility outputs (`irreducible_positive`), or
- cover-gap census outputs (`cover_gap_cases`) when explicitly desired.

All selected owner sets are unioned into a complete nonzero-support factor pool U.
The noncore candidate universe is
    P union ((U x U) minus BB),
where P=(X x Q) union (Q x X) is the complete 18-terminal periphery union.
The exact objective is selected_noncore - deleted_core; 5873 is the first
breakthrough value because |BB|=128881 and the record noncore optimum is 5872.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_joint_row_defects_maxsat import load_geometry

def read_owner_sets(paths):
    out=[];seen=set()
    for path in paths:
        d=json.loads(Path(path).read_text())
        rows=None
        if 'irreducible_positive' in d:
            rows=d['irreducible_positive']
        elif 'rows' in d:
            rows=[r for r in d['rows'] if int(r.get('min_owner_intersection',r.get('min_owner_intersection_at_alpha',1)))==0]
        elif 'cover_gap_cases' in d:
            rows=d['cover_gap_cases']
        else: raise RuntimeError(('unknown owner-set schema',str(path),sorted(d)[:20]))
        for r in rows:
            C=frozenset(map(int,r['owners']))
            if C and C not in seen:seen.add(C);out.append(C)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--owner-file',action='append',required=True,type=Path);a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B);Cs=read_owner_sets(a.owner_file)
    U={z for z in range(ring.n) if (ring.NB[z]&B) and any((ring.NB[z]&B)<=C for C in Cs)}
    X=set(fam['N'])|set(fam['A'])|set(fam['D']);Q=set(fam['H'])|set(fam['V'])
    if len(X)!=367 or len(Q)!=16:raise RuntimeError(('XQ',len(X),len(Q)))
    P={(x,q) for x in X for q in Q}|{(q,x) for q in Q for x in X};core={(x,y) for x in B for y in B}
    V=sorted(P|{(x,y) for x in U for y in U if (x,y) not in core});idx={p:i for i,p in enumerate(V)};n=len(V)
    factors={z for p in V for z in p};supp={z:tuple(sorted(ring.NB[z]&B)) for z in factors};losses=[];touched=set()
    for x,y in V:
        L={(b,c) for b in supp[x] for c in supp[y]};losses.append(L);touched.update(L)
    touched=sorted(touched);bi={p:i for i,p in enumerate(touched)};w=WCNF();imp=0
    for i,L in enumerate(losses):
        for p in L:w.append([-(i+1),n+bi[p]+1]);imp+=1
    first={x for x,_ in V};second={y for _,y in V};nf={x:ring.NB[x]&first for x in first};ns={y:ring.NB[y]&second for y in second};conf=0
    for i,(x,y) in enumerate(V):
        for u in nf[x]:
            for v in ns[y]:
                j=idx.get((u,v))
                if j is not None and j>i:w.append([-(i+1),-(j+1)]);conf+=1
    for i in range(n):w.append([i+1],weight=1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=1)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('RC2 no model')
    pos={z for z in model if z>0};si=[i for i in range(n) if i+1 in pos];deleted={touched[j] for j in range(len(touched)) if n+j+1 in pos};forced=set()
    for i in si:forced.update(losses[i])
    if deleted!=forced:raise RuntimeError(('deletion drift',len(deleted),len(forced)))
    selected=[V[i] for i in si];objective=len(selected)-len(deleted)
    if objective!=n-cost:raise RuntimeError(('objective drift',objective,n-cost))
    for i,p in enumerate(selected):
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in selected[i+1:]:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('new-new',p,z))
    retained=core-deleted
    for p in selected:
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in retained:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('new-core',p,z))
    score=len(retained)+len(selected);candidate=objective>=5873
    if score!=128881+objective:raise RuntimeError(('score',score,objective))
    if candidate:
        cand=retained|set(selected)
        def enc(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
        a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':sorted(enc(p) for p in cand)},separators=(',',':'))+'\n')
    out={'method':'exact-terminal-union-multisupport-joint-prize','owner_files':[str(p) for p in a.owner_file],'owner_sets':len(Cs),'support_union_factor':len(U),'terminal_union':len(P),'noncore_candidates':n,'touched_core':len(touched),'implications':imp,'conflict_clauses':conf,'selected_noncore':len(selected),'deleted_core':len(deleted),'objective':objective,'record_noncore_target':5872,'score':score,'candidate_materialized':candidate,'candidate_score':score if candidate else None}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
