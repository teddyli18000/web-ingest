#!/usr/bin/env python3
"""Exact arbitrary-radius mixing of the BPZ 10D record with X x X.

The BPZ auxiliary set X is a 367-point independent set in C7^5, so J=X x X
is a 134689-point independent set in C7^10. Let I be the 134753-point BPZ/Gao
record built from BB,NO,AH,DV,ON,HD,VA. In the symmetric difference, conflicts
can occur only between C=J\\I and D=I\\J. Because |I|-|J|=64, |D|=|C|+64.

The largest independent set contained in I union J is solved exactly by one
bipartite maximum matching. Relative to I the possible gain is

    |C| - nu(C,D).

Thus a positive Hall deficiency is an immediate arbitrary-radius breakthrough;
a saturating matching proves that no recombination using only points of I union
J can beat I. The script materializes the reconstructed I as well as any winner
so the upstream Few Shots verifier can independently replay both.
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path

LABELS=("B","N","A","D","O","H","V")
RECORD_CODE=(("B","B"),("N","O"),("A","H"),("D","V"),("O","N"),("H","D"),("V","A"))
EXPECTED_I=134_753
EXPECTED_J=367*367


def hopcroft_karp(adj,n_right):
    n_left=len(adj); pair_l=[-1]*n_left; pair_r=[-1]*n_right; dist=[-1]*n_left
    sys.setrecursionlimit(max(1_000_000,2*n_left+1000))
    def bfs():
        q=deque(); found=False
        for u in range(n_left):
            if pair_l[u]<0: dist[u]=0; q.append(u)
            else: dist[u]=-1
        while q:
            u=q.popleft()
            for v in adj[u]:
                w=pair_r[v]
                if w<0: found=True
                elif dist[w]<0: dist[w]=dist[u]+1; q.append(w)
        return found
    def dfs(u):
        for v in adj[u]:
            w=pair_r[v]
            if w<0 or (dist[w]==dist[u]+1 and dfs(w)):
                pair_l[u]=v; pair_r[v]=u; return True
        dist[u]=-1; return False
    m=0
    while bfs():
        for u in range(n_left):
            if pair_l[u]<0 and dfs(u): m+=1
    return m,pair_l,pair_r


def hall_witness(adj,pair_l,pair_r):
    zl={u for u,v in enumerate(pair_l) if v<0}; zr=set(); q=deque(zl)
    while q:
        u=q.popleft(); mv=pair_l[u]
        for v in adj[u]:
            if v==mv or v in zr: continue
            zr.add(v); w=pair_r[v]
            if w>=0 and w not in zl: zl.add(w); q.append(w)
    neigh=set()
    for u in zl: neigh.update(adj[u])
    if neigh!=zr: raise RuntimeError(("Hall witness mismatch",len(zl),len(zr),len(neigh)))
    return sorted(zl),sorted(zr)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tan_root",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("shot_dir",type=Path)
    ap.add_argument("baseline_dir",type=Path)
    args=ap.parse_args()
    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    base,_transform,_exchanges,axioms=load_base(root/"data"/"base_c7.json")
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    fam={"B":set(base.B.elements),"N":set(base.X0.elements),"A":set(base.XV.elements),"D":set(base.XH.elements),"O":set(base.R.elements),"H":set(base.PH.elements),"V":set(base.PV.elements)}
    sizes={k:len(v) for k,v in fam.items()}
    if sizes!={"B":359,"N":322,"A":19,"D":26,"O":8,"H":8,"V":8}: raise RuntimeError(("family-size drift",sizes))

    X=set(base.X.elements)
    if len(X)!=367: raise RuntimeError(("X size drift",len(X)))
    for x in X:
        if (ring.NB[x]&X)-{x}: raise RuntimeError(("X not independent",x))

    baseline=set()
    for w in RECORD_CODE:
        for a in fam[w[0]]:
            for b in fam[w[1]]:
                p=(a,b)
                if p in baseline: raise RuntimeError(("record blocks overlap",w,p))
                baseline.add(p)
    if len(baseline)!=EXPECTED_I: raise RuntimeError(("record score drift",len(baseline)))

    J={(a,b) for a in X for b in X}
    if len(J)!=EXPECTED_J: raise RuntimeError(("X2 score drift",len(J)))
    overlap=baseline&J; left=sorted(J-baseline); right=sorted(baseline-J)
    if len(right)-len(left)!=EXPECTED_I-EXPECTED_J:
        raise RuntimeError(("symmetric-difference gap drift",len(left),len(right)))
    right_id={p:i for i,p in enumerate(right)}

    nb_members={lab:[None]*ring.n for lab in LABELS}
    for lab in LABELS:
        F=fam[lab]
        for x in range(ring.n): nb_members[lab][x]=tuple(y for y in ring.NB[x] if y in F)
    def blockers(p):
        a,b=p; out=[]
        for c,d in RECORD_CODE:
            for x in nb_members[c][a]:
                for y in nb_members[d][b]:
                    q=(x,y)
                    if q in overlap:
                        raise RuntimeError(("X2 candidate conflicts with common point",p,q))
                    rid=right_id.get(q)
                    if rid is None:
                        raise RuntimeError(("baseline neighbor missing from right difference",p,q))
                    out.append(rid)
        if len(out)!=len(set(out)): raise RuntimeError(("duplicate blocker",p))
        return out

    adj=[blockers(p) for p in left]
    matching,pair_l,pair_r=hopcroft_karp(adj,len(right))
    deficiency=len(left)-matching
    status={
        "method":"exact-bpz-record-vs-X2-bipartite-Hall",
        "record_score":len(baseline),"x2_score":len(J),"score_gap":len(baseline)-len(J),
        "intersection":len(overlap),"x2_only":len(left),"record_only":len(right),
        "blocker_edges":sum(map(len,adj)),"matching":matching,"deficiency":deficiency,
        "breakthrough":deficiency>0,"candidate_score":EXPECTED_I+deficiency if deficiency>0 else None,
    }

    def point(pair):
        a,b=pair; return "".join(str(x) for x in (ring.decode(a)+ring.decode(b)))
    args.baseline_dir.mkdir(parents=True,exist_ok=True)
    baseline_points=sorted(point(p) for p in baseline)
    (args.baseline_dir/"certificate.json").write_text(json.dumps({"points":baseline_points},separators=(",",":"))+"\n")

    if deficiency>0:
        zl,zr=hall_witness(adj,pair_l,pair_r)
        if len(zl)-len(zr)!=deficiency: raise RuntimeError(("deficiency mismatch",deficiency,len(zl),len(zr)))
        selected={left[i] for i in zl}; deleted={right[j] for j in zr}; deleted_ids=set(zr)
        for i in zl:
            if not set(adj[i])<=deleted_ids: raise RuntimeError(("retained blocker",i))
        candidate=(baseline-deleted)|selected
        if len(candidate)!=EXPECTED_I+deficiency: raise RuntimeError(("candidate size mismatch",len(candidate),deficiency))
        status.update({"hall_left":len(zl),"hall_right":len(zr)})
        args.shot_dir.mkdir(parents=True,exist_ok=True)
        points=sorted(point(p) for p in candidate)
        if len(points)!=len(set(points)): raise RuntimeError("certificate duplicate conversion")
        (args.shot_dir/"certificate.json").write_text(json.dumps({"points":points},separators=(",",":"))+"\n")
        (args.shot_dir/"metadata.json").write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")

    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps(status,sort_keys=True))

if __name__=="__main__": main()
