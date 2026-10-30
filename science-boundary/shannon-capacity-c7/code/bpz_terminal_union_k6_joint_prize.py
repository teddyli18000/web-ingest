#!/usr/bin/env python3
"""Exact joint terminal-union + all-k6-gap core-release optimization.

The 18 record terminal basins share BB=B x B.  Their complete periphery union is
P=(X x Q) union (Q x X), with alpha(P)=5872 analytically.  Earlier support-prize
searches fixed one of the 18 terminal optima and charged every displaced
terminal point.  This model instead reoptimizes the terminal union and core
release simultaneously.

Candidate noncore universe:
    V = P union ((U x U) minus BB)
where U is the union of complete five-dimensional support pools of all 32 exact
k=6 clique-cover-gap owner sets.  Selecting v=(x,y) forces deletion of every
core point in (N[x] intersect B) x (N[y] intersect B).  Hard clauses enforce all
C7^10 conflicts inside V.  The exact objective is

    selected_noncore - deleted_core.

The public record is BB + 5872, so objective >=5873 is a verifier-candidate.
This is exact for the stated finite universe and does not assume a fixed
terminal code or a rectangular support defect.
"""
from __future__ import annotations
import argparse,json,os
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_global_k6_gap_union_prize import owner_sets
from bpz_joint_row_defects_maxsat import load_geometry

PINNED_COMMIT="c753408492dde92a239708986d16c15dbf6c3235"


def main():
    ap=argparse.ArgumentParser();ap.add_argument("tan_root",type=Path);ap.add_argument("k6_json",type=Path);ap.add_argument("output",type=Path);ap.add_argument("certificate",type=Path);a=ap.parse_args()
    root=a.tan_root.resolve();_base,ring,B,fam=load_geometry(root);B=set(B);Cs=owner_sets(a.k6_json)
    X=set(fam["N"])|set(fam["A"])|set(fam["D"]);Q=set(fam["H"])|set(fam["V"])
    if len(X)!=367 or len(Q)!=16:raise RuntimeError(("XQ",len(X),len(Q)))
    P={(x,q) for x in X for q in Q}|{(q,x) for q in Q for x in X}
    # The analytic terminal-union closure uses exactly this P.
    U={z for z in range(ring.n) if any((ring.NB[z]&B)<=C for C in Cs)}
    core={(x,y) for x in B for y in B}
    V=sorted(P|{(x,y) for x in U for y in U if (x,y) not in core});idx={p:i for i,p in enumerate(V)};n=len(V)
    # Precompute exact core support for factor vertices that actually occur.
    F={x for p in V for x in p};supp={x:tuple(sorted(ring.NB[x]&B)) for x in F}
    touched=set();losses=[]
    for x,y in V:
        L={(b,c) for b in supp[x] for c in supp[y]};losses.append(L);touched.update(L)
    touched=sorted(touched);bi={p:i for i,p in enumerate(touched)}
    w=WCNF();imp=0
    for i,L in enumerate(losses):
        for p in L:w.append([-(i+1),n+bi[p]+1]);imp+=1
    # Exact conflict graph on V.  Iterate only realized first/second coordinate
    # neighborhoods and use the product lookup table, avoiding O(|V|^2).
    first={x for x,_ in V};second={y for _,y in V};nfirst={x:ring.NB[x]&first for x in first};nsecond={y:ring.NB[y]&second for y in second}
    conflicts=0
    for i,(x,y) in enumerate(V):
        for u in nfirst[x]:
            for v in nsecond[y]:
                j=idx.get((u,v))
                if j is not None and j>i:w.append([-(i+1),-(j+1)]);conflicts+=1
    for i in range(n):w.append([i+1],weight=1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=1)
    with RC2(w,solver="g4",adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError("RC2 no model")
    pos={z for z in model if z>0};sel=[i for i in range(n) if i+1 in pos];lost={touched[j] for j in range(len(touched)) if n+j+1 in pos};forced=set()
    for i in sel:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(("loss mismatch",len(lost),len(forced)))
    selected=[V[i] for i in sel];objective=len(selected)-len(lost)
    # Independent structural replay of the returned model.
    for i,p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("selected conflict",p,z))
    retained_core=core-lost
    for p in selected:
        for z in retained_core:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("core conflict",p,z))
    score=len(retained_core)+len(selected);expected=128881+objective
    if score!=expected:raise RuntimeError(("score arithmetic",score,expected))
    candidate=False
    if objective>=5873:
        cand=retained_core|set(selected)
        def enc(p):return "".join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
        pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({"points":pts},separators=(",",":"))+"\n");candidate=True
    out={"method":"exact-joint-terminal-union-all-k6-gap-prize","source_commit":PINNED_COMMIT,"owner_sets":len(Cs),"X":len(X),"Q":len(Q),"terminal_union":len(P),"support_union_factor":len(U),"noncore_candidates":n,"touched_core":len(touched),"implications":imp,"conflict_clauses":conflicts,"selected_noncore":len(selected),"deleted_core":len(lost),"objective":objective,"record_periphery_target":5872,"score":score,"candidate_materialized":candidate,"candidate_score":score if candidate else None}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
