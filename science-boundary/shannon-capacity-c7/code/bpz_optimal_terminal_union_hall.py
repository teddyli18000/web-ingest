#!/usr/bin/env python3
"""Exact recombination of all BPZ terminal-code optima at score 134753.

The seven BPZ five-dimensional families are B,N,A,D,O,H,V.  Instead of fixing
the familiar seven-word Gao code

    BB, NO, AH, DV, ON, HD, VA,

this script derives the *actual* family separation graph from the pinned base
sets, enumerates every maximal compatible length-2 terminal code, and retains
all codes whose exact product-block weight is the optimum 134753.

For every pair J1,J2 of distinct optimum ten-dimensional sets, J1 and J2 are
independent and have equal size.  Hence all edges in G[J1 union J2] lie across
the symmetric difference L=J1\\J2, R=J2\\J1.  One bipartite maximum matching
therefore solves the best possible recombination inside their union exactly:

    alpha(G[J1 union J2]) = |J2| + |L| - nu(L,R).

Any Hall deficiency gives an immediate >134753 certificate; saturation proves
that particular pair union cannot beat the record.  This is an arbitrary-radius
exact test, not a local-exchange heuristic.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter, deque
from pathlib import Path

LABELS=("B","N","A","D","O","H","V")
EXPECTED_SCORE=134_753
EXPECTED_OPTIMA=18


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


def bron_kerbosch_maximal(adj):
    out=[]
    def bk(R,P,X):
        if not P and not X:
            out.append(tuple(sorted(R))); return
        U=P|X
        u=max(U,key=lambda z:len(P&adj[z])) if U else None
        todo=sorted(P-(adj[u] if u is not None else set()))
        for v in todo:
            bk(R+(v,),P&adj[v],X&adj[v])
            P.remove(v); X.add(v)
    bk(tuple(),set(range(len(adj))),set())
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tan_root",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("shot_dir",type=Path)
    args=ap.parse_args()
    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    base,_transform,_exchanges,axioms=load_base(root/"data"/"base_c7.json")
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    fam={
        "B":set(base.B.elements),"N":set(base.X0.elements),
        "A":set(base.XV.elements),"D":set(base.XH.elements),
        "O":set(base.R.elements),"H":set(base.PH.elements),
        "V":set(base.PV.elements),
    }
    sizes={k:len(v) for k,v in fam.items()}
    if sizes!={"B":359,"N":322,"A":19,"D":26,"O":8,"H":8,"V":8}:
        raise RuntimeError(("family-size drift",sizes))

    # Derive exact symmetric family-separation relation from the explicit sets.
    separated={a:set() for a in LABELS}
    family_independent={}
    for a in LABELS:
        F=fam[a]
        family_independent[a]=all(not ((ring.NB[x]&F)-{x}) for x in F)
        if not family_independent[a]: raise RuntimeError(("family not independent",a))
    for i,a in enumerate(LABELS):
        for b in LABELS[i+1:]:
            A,B=fam[a],fam[b]
            ok=all(not (ring.NB[x]&B) for x in A)
            ok2=all(not (ring.NB[y]&A) for y in B)
            if ok!=ok2: raise RuntimeError(("asymmetric separation",a,b))
            if ok:
                separated[a].add(b); separated[b].add(a)

    words=[(a,b) for a in LABELS for b in LABELS]
    def compatible_word(x,y):
        return y[0] in separated[x[0]] or y[1] in separated[x[1]]
    wadj=[set() for _ in words]
    for i in range(len(words)):
        for j in range(i+1,len(words)):
            if compatible_word(words[i],words[j]):
                wadj[i].add(j); wadj[j].add(i)
    maximal=bron_kerbosch_maximal(wadj)
    def code_weight(code):
        return sum(sizes[words[i][0]]*sizes[words[i][1]] for i in code)
    best_weight=max(map(code_weight,maximal))
    opt_codes=[c for c in maximal if code_weight(c)==best_weight]
    if best_weight!=EXPECTED_SCORE or len(opt_codes)!=EXPECTED_OPTIMA:
        raise RuntimeError(("terminal optimum drift",best_weight,len(opt_codes)))

    # Materialize each optimum from disjoint compatible product blocks.
    sets=[]; code_meta=[]
    for ci,code in enumerate(opt_codes):
        S=set(); block_sizes={}
        for wi in code:
            a,b=words[wi]; before=len(S)
            for x in fam[a]:
                for y in fam[b]: S.add((x,y))
            added=len(S)-before; expected=sizes[a]*sizes[b]
            if added!=expected: raise RuntimeError(("compatible blocks overlap",ci,a,b,added,expected))
            block_sizes[a+b]=expected
        if len(S)!=EXPECTED_SCORE: raise RuntimeError(("materialized optimum score drift",ci,len(S)))
        h=hashlib.sha256()
        for a,b in sorted(S): h.update(a.to_bytes(2,"little")); h.update(b.to_bytes(2,"little"))
        sets.append(S)
        code_meta.append({"index":ci,"code":["".join(words[i]) for i in code],"block_sizes":block_sizes,"pair_hash":h.hexdigest()})

    # Deduplicate in case distinct abstract codes materialize to the same actual set.
    unique=[]; seen={}
    abstract_to_unique=[]
    for ci,S in enumerate(sets):
        key=frozenset(S)
        uid=seen.get(key)
        if uid is None:
            uid=len(unique); seen[key]=uid; unique.append(S)
        abstract_to_unique.append(uid)
    if len(unique)<2: raise RuntimeError(("all optimum terminal codes materialized identically",len(unique)))

    def conflict_adj(left,right):
        # right first-coordinate -> {second -> right-id}; enumerate exact 243x243
        # strong-product neighborhood using the 5D closed-neighborhood tables.
        by_first={}
        for rid,(a,b) in enumerate(right): by_first.setdefault(a,{})[b]=rid
        adj=[]; edges=0
        for a,b in left:
            row=[]
            nb_b=ring.NB[b]
            for c in ring.NB[a]:
                dmap=by_first.get(c)
                if not dmap: continue
                # Iterate the smaller object: dmap is sparse in these symmetric differences.
                for d,rid in dmap.items():
                    if d in nb_b: row.append(rid)
            row=sorted(set(row)); edges+=len(row); adj.append(row)
        return adj,edges

    results=[]; best=None
    for i in range(len(unique)):
        for j in range(i+1,len(unique)):
            A=unique[i]; B=unique[j]
            left=sorted(A-B); right=sorted(B-A)
            if len(left)!=len(right): raise RuntimeError(("equal-score symmetric difference mismatch",i,j,len(left),len(right)))
            if not left:
                results.append({"left":i,"right":j,"difference_each":0,"matching":0,"deficiency":0,"blocker_edges":0})
                continue
            adj,edges=conflict_adj(left,right)
            matching,pair_l,pair_r=hopcroft_karp(adj,len(right))
            deficiency=len(left)-matching
            rec={"left":i,"right":j,"difference_each":len(left),"blocker_edges":edges,"matching":matching,"deficiency":deficiency}
            if deficiency>0:
                zl,zr=hall_witness(adj,pair_l,pair_r)
                if len(zl)-len(zr)!=deficiency: raise RuntimeError(("deficiency mismatch",i,j,deficiency,len(zl),len(zr)))
                selected={left[k] for k in zl}; deleted={right[k] for k in zr}; candidate=(B-deleted)|selected
                if len(candidate)!=EXPECTED_SCORE+deficiency: raise RuntimeError(("candidate score mismatch",i,j,len(candidate),deficiency))
                deleted_ids=set(zr)
                for k in zl:
                    if not set(adj[k])<=deleted_ids: raise RuntimeError(("retained cross blocker",i,j,k))
                rec.update({"hall_left":len(zl),"hall_right":len(zr),"candidate_score":len(candidate)})
                if best is None or (deficiency,-len(zr))>(best[0],-best[1]): best=(deficiency,len(zr),rec,candidate)
            results.append(rec); print(json.dumps(rec,sort_keys=True),flush=True)

    results.sort(key=lambda r:(-r["deficiency"],r["difference_each"],r["left"],r["right"]))
    status={
        "method":"exact-bpz-optimal-terminal-code-union-hall",
        "family_sizes":sizes,
        "family_separation":{k:sorted(v) for k,v in separated.items()},
        "maximal_terminal_codes":len(maximal),
        "terminal_optimum":best_weight,
        "optimal_abstract_codes":len(opt_codes),
        "unique_materialized_optima":len(unique),
        "abstract_to_unique":abstract_to_unique,
        "codes":code_meta,
        "pair_tests":len(unique)*(len(unique)-1)//2,
        "max_deficiency":max((r["deficiency"] for r in results),default=0),
        "breakthrough":best is not None,
        "best":None if best is None else best[2],
        "results":results,
    }

    if best is not None:
        deficiency,_radius,rec,candidate=best; args.shot_dir.mkdir(parents=True,exist_ok=True)
        def point(pair):
            a,b=pair; return "".join(str(x) for x in (ring.decode(a)+ring.decode(b)))
        points=sorted(point(p) for p in candidate)
        if len(points)!=EXPECTED_SCORE+deficiency or len(points)!=len(set(points)): raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir/"certificate.json").write_text(json.dumps({"points":points},separators=(",",":"))+"\n")
        (args.shot_dir/"metadata.json").write_text(json.dumps({"method":status["method"],**rec},indent=2,sort_keys=True)+"\n")

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in status.items() if k not in ("results","codes")},sort_keys=True))

if __name__=="__main__": main()
