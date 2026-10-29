#!/usr/bin/env python3
"""Exact one-BB-hole + global 18-basin-periphery search for C7^10.

The 18 BPZ terminal-optimal 134753 constructions share BB=B x B, |B|=359,
and each contributes 5872 peripheral vertices.  Let P be the union of all 18
peripheries.  This script allows an arbitrary independent subset of P, deletes
one core point d=(b,c), and augments P by every non-core vertex whose *entire*
conflict footprint against BB is exactly {d}.

For z in C7^5 write S(z)=N[z] intersect B and W_b={z:S(z)={b}}.  A 10D point
(u,v) has BB-footprint S(u) x S(v), so the points unlocked by deleting d=(b,c)
are exactly W_b x W_c; the core point d itself is excluded from additions.

For each selected core hole the real induced C7^10 conflict graph on

    P union ((W_b x W_c) \ BB)

is solved exactly with MiniCard for at least 5874 peripheral points.  Together
with 128880 retained BB points this is a 134754 certificate.

The search is exact for every hole it tests.  It intentionally does NOT include
fixed-BB-compatible vertices outside P; exploiting those is entangled with the
open alpha(C7^5)>=368 frontier.  Use --start/--count to shard the eligible holes
(sorted by number of newly unlocked candidates).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BB_SIZE=359*359
RECORD_SCORE=134_753
KNOWN_PERIPH=RECORD_SCORE-BB_SIZE  # 5872
TARGET_PERIPH=KNOWN_PERIPH+2       # delete one BB point, need net +1 overall


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tan_root",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("shot_dir",type=Path)
    ap.add_argument("--start",type=int,default=0)
    ap.add_argument("--count",type=int,default=100)
    args=ap.parse_args()
    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    from pysat.solvers import Minicard  # type: ignore

    data_path=root/"data"/"base_c7.json"
    raw=json.loads(data_path.read_text())
    base,_transform,_exchanges,axioms=load_base(data_path)
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    I=set(map(int,raw["I0"])); X=set(map(int,raw["X"]))
    pairs=[tuple(map(int,p)) for p in raw["private_pairs"]]
    owners={a for a,_ in pairs}; B=I-owners
    PH=set(map(int,raw["PH"])); PV=set(map(int,raw["PV"])); Q=PH|PV
    if len(B)!=359 or len(X)!=367 or len(Q)!=16:
        raise RuntimeError(("base size drift",len(B),len(X),len(Q)))
    if B!=set(base.B.elements) or X!=set(base.X.elements):
        raise RuntimeError("raw/load_base mismatch")

    # Exact five-dimensional support classes against B.
    support_owner={}
    singleton=defaultdict(list)
    safe=set()
    for z in range(ring.n):
        S=ring.NB[z]&B
        if not S:
            safe.add(z)
        elif len(S)==1:
            b=next(iter(S)); support_owner[z]=b; singleton[b].append(z)
    if set(singleton)!=B:
        raise RuntimeError(("singleton owner coverage drift",len(singleton),len(B)))
    if safe!=Q:
        raise RuntimeError(("safe set is not private endpoint set",len(safe),len(Q),sorted(safe^Q)))

    # Full union of the 18 terminal-optimal peripheries.  The direct formula XQ|QX
    # is independently checked against explicit terminal-code materialization.
    P={(x,q) for x in X for q in Q}|{(q,x) for q in Q for x in X}
    fam={"B":B,"N":set(base.X0.elements),"A":set(base.XV.elements),
         "D":set(base.XH.elements),"O":set(base.R.elements),"H":PH,"V":PV}
    explicit=set(); known_peripheries=[]
    for q in ("O","H","V"):
        for r in ("O","H","V"):
            for orient in (0,1):
                words=(
                    (("N",q),("A","H"),("D","V"),(r,"N"),("H","D"),("V","A"))
                    if orient==0 else
                    (("N",q),("A","V"),("D","H"),(r,"N"),("H","A"),("V","D"))
                )
                S=set()
                for a,b in words: S.update((u,v) for u in fam[a] for v in fam[b])
                if len(S)!=KNOWN_PERIPH: raise RuntimeError(("periphery score drift",q,r,orient,len(S)))
                explicit|=S; known_peripheries.append(S)
    if explicit!=P:
        raise RuntimeError(("18-basin union != XQ|QX",len(explicit),len(P),len(explicit^P)))
    if any((u in B and v in B) for u,v in P):
        raise RuntimeError("periphery overlaps BB")

    pverts=sorted(P); np=len(pverts); pid={p:i for i,p in enumerate(pverts)}

    # Build the exact conflict graph on P once.  Variables are 1-based.
    p_by_first=defaultdict(dict)
    for i,(u,v) in enumerate(pverts): p_by_first[u][v]=i
    p_clauses=[]; p_edges=0
    for i,(u,v) in enumerate(pverts):
        for a in ring.NB[u]:
            row=p_by_first.get(a)
            if not row: continue
            for b,j in row.items():
                if j>i and b in ring.NB[v]:
                    p_clauses.append((-(i+1),-(j+1))); p_edges+=1

    # Known 5872-point peripheries must replay as independent in this graph.
    for k,S in enumerate(known_peripheries):
        ids={pid[p] for p in S}
        for a,b in p_clauses:
            if (-a-1) in ids and (-b-1) in ids:
                raise RuntimeError(("known periphery conflict",k,-a-1,-b-1))

    # Eligible one-core holes need at least two non-core unlocked points; otherwise
    # P's known optimum 5872 cannot reach the 5874 target even before conflicts.
    holes=[]
    for b in sorted(B):
        wb=singleton[b]
        for c in sorted(B):
            wc=singleton[c]
            new_count=len(wb)*len(wc)-1  # exclude the deleted core point (b,c)
            if new_count>=2:
                holes.append((new_count,b,c))
    holes.sort(key=lambda x:(-x[0],x[1],x[2]))
    lo=max(0,args.start); hi=min(len(holes),lo+max(0,args.count))

    def conflict(a,b):
        (u,v),(x,y)=a,b
        return x in ring.NB[u] and y in ring.NB[v]

    results=[]; winner=None
    for rank in range(lo,hi):
        new_count,b,c=holes[rank]
        T={(u,v) for u in singleton[b] for v in singleton[c] if not (u in B and v in B)}
        if len(T)!=new_count:
            raise RuntimeError(("unlocked count drift",rank,b,c,len(T),new_count))
        if T&P:
            raise RuntimeError(("singleton unlocked set overlaps fixed periphery",rank,len(T&P)))
        tverts=sorted(T); nt=len(tverts); n=np+nt
        if n<TARGET_PERIPH:
            results.append({"rank":rank,"core":[b,c],"unlocked":nt,"sat":False,"reason":"candidate_count_below_target"})
            continue

        solver=Minicard(bootstrap_with=[list(cl) for cl in p_clauses])
        # T-T conflicts.
        t_by_first=defaultdict(dict)
        for j,(u,v) in enumerate(tverts): t_by_first[u][v]=j
        tt_edges=0; pt_edges=0
        for j,(u,v) in enumerate(tverts):
            for a in ring.NB[u]:
                row=t_by_first.get(a)
                if row:
                    for d,k in row.items():
                        if k>j and d in ring.NB[v]:
                            solver.add_clause([-(np+j+1),-(np+k+1)]); tt_edges+=1
                prow=p_by_first.get(a)
                if prow:
                    for d,i in prow.items():
                        if d in ring.NB[v]:
                            solver.add_clause([-(np+j+1),-(i+1)]); pt_edges+=1
        solver.add_atmost([-(i+1) for i in range(n)], n-TARGET_PERIPH)
        # Seed toward a known optimum P basin plus all currently compatible T points.
        seed={pid[p] for p in known_peripheries[0]}
        phases=[(i+1 if i in seed else -(i+1)) for i in range(np)]
        phases.extend(np+j+1 for j in range(nt))
        try: solver.set_phases(phases)
        except Exception: pass
        sat=solver.solve(); model=solver.get_model() if sat else None; solver.delete()
        rec={"rank":rank,"core":[b,c],"left_singleton":len(singleton[b]),"right_singleton":len(singleton[c]),
             "unlocked":nt,"p_vertices":np,"p_edges":p_edges,"pt_edges":pt_edges,"tt_edges":tt_edges,"sat":bool(sat)}
        if sat:
            positive={z for z in model if 1<=z<=n}
            chosenP={pverts[z-1] for z in positive if z<=np}
            chosenT={tverts[z-np-1] for z in positive if z>np}
            chosen=chosenP|chosenT
            if len(chosen)<TARGET_PERIPH:
                raise RuntimeError(("SAT model below target",rank,len(chosen)))
            # Replay exact candidate independence and BB footprint condition.
            chosen_list=sorted(chosen)
            for i,a in enumerate(chosen_list):
                for d in chosen_list[i+1:]:
                    if conflict(a,d): raise RuntimeError(("SAT replay conflict",rank,a,d))
            core=(b,c)
            for u,v in chosenT:
                footprint=(ring.NB[u]&B, ring.NB[v]&B)
                if footprint!=({b},{c}): raise RuntimeError(("wrong core footprint",rank,(u,v),footprint,core))
            candidate={(u,v) for u in B for v in B}; candidate.remove(core); candidate|=chosen
            if len(candidate)<134754:
                raise RuntimeError(("candidate score below breakthrough",rank,len(candidate)))
            rec.update({"selected_periphery":len(chosen),"selected_P":len(chosenP),"selected_unlocked":len(chosenT),"candidate_score":len(candidate)})
            winner=(rec,candidate); results.append(rec)
            break
        results.append(rec)
        print(json.dumps(rec,sort_keys=True),flush=True)

    status={
        "method":"exact-one-BB-hole-plus-18-basin-periphery-union-sat",
        "record_score":RECORD_SCORE,"bb_size":BB_SIZE,"known_periphery":KNOWN_PERIPH,
        "target_periphery":TARGET_PERIPH,"safe_size":len(safe),"periphery_union_vertices":np,
        "periphery_conflict_edges":p_edges,"eligible_core_holes":len(holes),
        "slice_start":lo,"slice_end":hi,"tested":len(results),
        "breakthrough":winner is not None,"winner":None if winner is None else winner[0],
        "results":results,
        "scope_note":"exact for tested core holes over P=(union of 18 terminal-optimal peripheries) plus the complete singleton-footprint unlock set for that one deleted BB point; fixed-BB candidates outside P are intentionally excluded",
    }

    if winner is not None:
        rec,candidate=winner; args.shot_dir.mkdir(parents=True,exist_ok=True)
        def point(pair):
            u,v=pair
            # Pinned Tandon half codes use least-significant coordinate first.  The
            # Few Shots graph is invariant under reversing the five coordinates in
            # each half, so standard base-7 rendering is a valid graph isomorphism.
            val=u+(7**5)*v; ds=[]
            for _ in range(10): val,d=divmod(val,7); ds.append(str(d))
            return ''.join(reversed(ds))
        points=sorted(point(p) for p in candidate)
        if len(points)!=len(candidate) or len(points)!=len(set(points)):
            raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir/"certificate.json").write_text(json.dumps({"points":points},separators=(",",":"))+"\n")
        (args.shot_dir/"metadata.json").write_text(json.dumps({"method":status["method"],**rec},indent=2,sort_keys=True)+"\n")

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in status.items() if k!="results"},sort_keys=True))

if __name__=="__main__": main()
