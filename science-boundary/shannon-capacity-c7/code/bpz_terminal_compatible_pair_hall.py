#!/usr/bin/env python3
"""Exact arbitrary-radius Hall sweep over compatible pairs of omitted BPZ blocks.

Each omitted terminal word uv contributes an independent actual candidate block
C_uv=(F_u x F_v)\\I. Whenever two such blocks have an independent *union* at
the real C7^10 vertex level (duplicates allowed and counted once), their union
is another independent candidate universe. Hall's deficiency theorem then
solves every exchange radius for that two-block universe in one maximum
matching:

    max_A (|A|-|N_I(A)|) = |C|-nu(C,I).

This strictly subsumes neutral-piece recombination for fully cross-compatible
block pairs and automatically handles overlapping candidate vertices and
individually negative pieces. Pairs whose candidate unions contain a genuine
cross-conflict are outside this exact slice.
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path

LABELS=("B","N","A","D","O","H","V")
RECORD_CODE=(("B","B"),("N","O"),("A","H"),("D","V"),("O","N"),("H","D"),("V","A"))
EXPECTED_SCORE=134_753


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
    if neigh!=zr:
        raise RuntimeError(("Hall witness mismatch",len(zl),len(zr),len(neigh)))
    return sorted(zl),sorted(zr)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tan_root",type=Path); ap.add_argument("output",type=Path); ap.add_argument("shot_dir",type=Path)
    args=ap.parse_args()
    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    base,_transform,_exchanges,axioms=load_base(root/"data"/"base_c7.json")
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    fam={"B":set(base.B.elements),"N":set(base.X0.elements),"A":set(base.XV.elements),"D":set(base.XH.elements),"O":set(base.R.elements),"H":set(base.PH.elements),"V":set(base.PV.elements)}
    sizes={k:len(v) for k,v in fam.items()}
    if sizes!={"B":359,"N":322,"A":19,"D":26,"O":8,"H":8,"V":8}: raise RuntimeError(("family-size drift",sizes))
    for lab,F in fam.items():
        for x in F:
            if (ring.NB[x]&F)-{x}: raise RuntimeError(("family not independent",lab,x))

    owner_pair=[]; owner={}
    for w in RECORD_CODE:
        for a in sorted(fam[w[0]]):
            for b in sorted(fam[w[1]]):
                p=(a,b)
                if p in owner: raise RuntimeError(("record overlap",w,p))
                owner[p]=len(owner_pair); owner_pair.append(p)
    if len(owner_pair)!=EXPECTED_SCORE: raise RuntimeError(("record score drift",len(owner_pair)))
    baseline=set(owner)

    nb_members={lab:[None]*ring.n for lab in LABELS}
    for lab in LABELS:
        F=fam[lab]
        for x in range(ring.n): nb_members[lab][x]=tuple(y for y in ring.NB[x] if y in F)
    blocker_cache={}
    def blockers(p):
        got=blocker_cache.get(p)
        if got is not None: return got
        a,b=p; out=[]
        for c,d in RECORD_CODE:
            for x in nb_members[c][a]:
                for y in nb_members[d][b]: out.append(owner[(x,y)])
        if len(out)!=len(set(out)): raise RuntimeError(("duplicate blocker",p))
        got=tuple(out); blocker_cache[p]=got; return got

    blocks=[]
    for u in LABELS:
        for v in LABELS:
            w=(u,v)
            if w in RECORD_CODE: continue
            S=set(); members={}; reach={}
            for a in fam[u]:
                for b in fam[v]:
                    p=(a,b)
                    if p in baseline: continue
                    S.add(p)
                    members[a]=members.get(a,0)|(1<<b)
                    reach[a]=reach.get(a,0)|ring.BITS[b]
            blocks.append({"word":"".join(w),"set":S,"members":members,"reach":reach})

    def cross_conflict_distinct(P,Q):
        if len(P["members"])>len(Q["members"]): P,Q=Q,P
        qm=Q["members"]
        for a,pbits in P["members"].items():
            pre=P["reach"][a]
            qsame=qm.get(a,0)
            if (pre & qsame) & ~pbits:
                return True
            qother=0
            for c in ring.NB[a]:
                if c!=a: qother |= qm.get(c,0)
            if pre & qother:
                return True
        return False

    pair_specs=[]; incompatible=0
    for i in range(len(blocks)):
        for j in range(i+1,len(blocks)):
            P,Q=blocks[i],blocks[j]
            if cross_conflict_distinct(P,Q):
                incompatible+=1; continue
            overlap=len(P["set"]&Q["set"]); usize=len(P["set"])+len(Q["set"])-overlap
            pair_specs.append((usize,-overlap,i,j))
    pair_specs.sort(reverse=True)

    results=[]; best=None
    for rank,(usize,neg_overlap,i,j) in enumerate(pair_specs):
        P,Q=blocks[i],blocks[j]
        union=sorted(P["set"]|Q["set"])
        if len(union)!=usize: raise RuntimeError("union size drift")
        adj=[blockers(p) for p in union]
        matching,pair_l,pair_r=hopcroft_karp(adj,len(owner_pair))
        deficiency=len(union)-matching
        rec={"word1":P["word"],"word2":Q["word"],"union_candidates":len(union),"candidate_overlap":-neg_overlap,"blocker_edges":sum(map(len,adj)),"matching":matching,"deficiency":deficiency}
        results.append(rec); print(json.dumps(rec,sort_keys=True),flush=True)
        if deficiency>0:
            zl,zr=hall_witness(adj,pair_l,pair_r)
            if len(zl)-len(zr)!=deficiency: raise RuntimeError(("deficiency mismatch",rec,len(zl),len(zr)))
            selected={union[k] for k in zl}; deleted={owner_pair[b] for b in zr}
            candidate_set=(baseline-deleted)|selected
            if len(candidate_set)!=EXPECTED_SCORE+deficiency: raise RuntimeError(("candidate size mismatch",len(candidate_set),deficiency))
            deleted_ids=set(zr)
            for k in zl:
                if not set(adj[k])<=deleted_ids: raise RuntimeError(("retained blocker",rank,k))
            win={**rec,"hall_left":len(zl),"hall_right":len(zr),"candidate_score":len(candidate_set)}
            if best is None or (deficiency,-len(zr))>(best[0],-best[1]): best=(deficiency,len(zr),win,candidate_set)

    status={"method":"exact-bpz-compatible-two-terminal-block-hall","record_score":EXPECTED_SCORE,"family_sizes":sizes,"omitted_blocks":len(blocks),"block_pairs_total":len(blocks)*(len(blocks)-1)//2,"cross_incompatible_pairs":incompatible,"cross_independent_pairs":len(pair_specs),"breakthrough":best is not None,"max_deficiency":max((r["deficiency"] for r in results),default=0),"best":None if best is None else best[2],"results":results}
    if best is not None:
        deficiency,_radius,rec,candidate_set=best; args.shot_dir.mkdir(parents=True,exist_ok=True)
        def point(pair):
            a,b=pair; return "".join(str(x) for x in (ring.decode(a)+ring.decode(b)))
        points=sorted(point(p) for p in candidate_set)
        if len(points)!=EXPECTED_SCORE+deficiency or len(points)!=len(set(points)): raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir/"certificate.json").write_text(json.dumps({"points":points},separators=(",",":"))+"\n")
        (args.shot_dir/"metadata.json").write_text(json.dumps({"method":status["method"],**rec},indent=2,sort_keys=True)+"\n")
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in status.items() if k!="results"},sort_keys=True))

if __name__=="__main__": main()
