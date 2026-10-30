#!/usr/bin/env python3
"""Released-AND RNBP using Boyar-Peralta minimum-support distance.

This is a temporal-legality adaptation of the support-distance machinery in the
public Extended-BP RNBP optimizer. Targets are exact affine operands of the 33
ordered AND atoms plus the eight AES outputs. A target is unavailable while it
contains an unreleased AND atom. Helpers may use only signals already in S.
When both exact operands of an AND are present, its atom is released for free.

Distance is minimum support cardinality over S minus one. Because XNOR has the
same gate cost as XOR here, for support size >=2 we also allow a free affine
constant flip. Candidate XOR/XNOR pairs are scored by the exact one-step support
distance reductions they cause, then by the Extended-BP sum/norm criterion.

Finite distances are updated incrementally: one new helper is itself made from
two old signals, so it can lower minimum support by at most one. Full recursive
distance initialization is needed only for covered targets that are still INF.
This matches the public RNBP update semantics while avoiding a full recomputation
for every target after every gate.

Every completed candidate is independently checked on all 256 AES inputs.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import time

import released_and_skeleton as ras

INF=999


def init_sx(S):
    sx=[set() for _ in range(5)]
    sx[0]={0}
    for w in S:
        old=[set(x) for x in sx]
        sx[1].add(w)
        for k in range(2,5):
            sx[k].update({w^v for v in old[k-1]})
    return sx


def add_sx(sx,w):
    old=[set(x) for x in sx]
    sx[1].add(w)
    for k in range(2,5):
        sx[k].update({w^v for v in old[k-1]})


def covered_mask(S):
    m=0
    for s in S:m|=s
    return m


def exists_exact_support(S,sx,goal,k):
    if k<0:return False
    if k<=4:return goal in sx[k]
    # Extended-BP-style recursion: peel signals until a <=4 membership query.
    # If the base membership overlaps an already selected signal, the symmetric
    # difference is an even smaller valid representation; since distances are
    # initialized from low support upward, this cannot create a false minimum.
    xs=list(S); n=len(xs)
    def rec(i,v,r):
        if r<=4:return (goal^v) in sx[r]
        if n-i<r:return False
        if rec(i+1,v^xs[i],r-1):return True
        return rec(i+1,v,r)
    return rec(0,0,k)


def target_is_covered(S,t,C):
    mask=covered_mask(S)
    atom_part=t & (C-1)
    return (mask & atom_part)==atom_part


def min_distance(S,sx,t,C,max_support=9):
    if t in sx[1]:return 0
    if not target_is_covered(S,t,C):return INF
    for k in range(2,max_support+1):
        if exists_exact_support(S,sx,t,k) or exists_exact_support(S,sx,t^C,k):
            return k-1
    return INF


def candidate_reduces(S,sx,t,C,dist,w):
    """Whether adding pair-output w lowers known support distance by one."""
    if dist in (0,INF):return False
    # Old support = dist+1. Since w expands to two old signals (with an optional
    # affine constant flip), adding it can reduce support by at most one. A new
    # support of dist uses w plus dist-1 old signals.
    r=dist-1
    a=t^w
    if exists_exact_support(S,sx,a,r):return True
    # For r>=1, the final combination may use XNOR at no extra gate cost. For
    # r==0, t==w is already caught by the exact branch above; t==w^C is not a
    # zero-gate realization and therefore must not be accepted.
    if r>=1 and exists_exact_support(S,sx,a^C,r):return True
    return False


def pair_candidates(S,C):
    xs=list(S); out={}
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            v=a^b
            if v not in S:out.setdefault(v,("XOR",a,b))
            vn=v^C
            if vn not in S:out.setdefault(vn,("XNOR",a,b))
    return out


def target_rows(sk):
    rows=[]
    for i,ab in enumerate(sk["ands"]):
        rows.append((ab["a"],f"a{i}"))
        rows.append((ab["b"],f"b{i}"))
    for i,t in enumerate(sk["outputs"]):rows.append((t,f"y{i}"))
    return rows


def release_ready(sk,S,sx,names,gates,released):
    added=[]
    changed=True
    while changed:
        changed=False
        for i,ab in enumerate(sk["ands"]):
            atom=1<<(8+i)
            if i in released:continue
            if ab["a"] in S and ab["b"] in S:
                out=f"w{len(gates)}"
                gates.append({"op":"AND","a":names[ab["a"]],"b":names[ab["b"]],"out":out})
                S.add(atom);names[atom]=out;add_sx(sx,atom);released.add(i);added.append(i)
                changed=True
    return added


def initialize_covered_inf(Dist,targets,S,sx,C,max_support):
    """Initialize only INF targets whose nonlinear atom support is now legal."""
    mask=covered_mask(S)
    for i,d in enumerate(Dist):
        if d!=INF:continue
        t=targets[i]
        atom_part=t & (C-1)
        if (mask & atom_part)!=atom_part:continue
        Dist[i]=min_distance(S,sx,t,C,max_support)


def synthesize(base,seed,max_linear=67,max_support=9,elite=1):
    sk=ras.extract_skeleton(base);C=1<<sk["const_bit"]
    rows=target_rows(sk);targets=[t for t,_ in rows]
    rng=random.Random(seed)
    S={1<<i for i in range(8)};sx=init_sx(S)
    names={1<<i:f"x{i}" for i in range(8)}
    gates=[];released=set();linear=0;trace=[]
    release_ready(sk,S,sx,names,gates,released)
    Dist=[min_distance(S,sx,t,C,max_support) for t in targets]

    while linear<max_linear and any(d!=0 for d in Dist):
        # Any newly free nonlinear atoms can only make previously-uncovered INF
        # targets legal. Existing finite targets contain none of those atoms.
        added_ands=release_ready(sk,S,sx,names,gates,released)
        if added_ands:
            initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        if all(d==0 for d in Dist):break

        WD=pair_candidates(S,C)
        ones=[i for i,d in enumerate(Dist) if d==1]
        preempt=False
        reductions=None
        if ones:
            # Prefer a distance-1 target that is itself a legal pair output.
            choices=[i for i in ones if targets[i] in WD]
            if not choices:
                raise AssertionError(("distance1 without pair witness",ones))
            ti=choices[0];w=targets[ti];preempt=True
        else:
            finite=[d for d in Dist if 0<d<INF]
            if not finite:
                return None,{"status":"stuck_all_inf","seed":seed,"linear":linear,
                             "released_ands":len(released),"trace_tail":trace[-20:]}
            base_sum=sum(finite)
            scored=[]
            for w in WD:
                wr=[]
                for i,d in enumerate(Dist):
                    if 0<d<INF and candidate_reduces(S,sx,targets[i],C,d,w):
                        wr.append(i)
                if not wr:continue
                new_sum=base_sum-len(wr)
                # Extended-BP tie-break: maximize Euclidean norm after minimizing sum.
                norm=0
                wrset=set(wr)
                for i,d in enumerate(Dist):
                    if d in (0,INF):continue
                    nd=d-1 if i in wrset else d
                    norm+=nd*nd
                scored.append((new_sum,-norm,w,wr))
            if not scored:
                return None,{"status":"stuck_no_reducing_pair","seed":seed,"linear":linear,
                             "released_ands":len(released),"finite_distances":finite,
                             "trace_tail":trace[-20:]}
            scored.sort(key=lambda x:(x[0],x[1],x[2]))
            bestkey=scored[0][:2]
            pool=[x for x in scored if x[:2]==bestkey]
            pool=pool[:max(1,elite)] if elite>0 else pool
            _,_,w,reductions=rng.choice(pool)

        # Even a preemptive target helper may improve other finite targets; get
        # the exact one-step reduction set before mutating S/sx.
        if reductions is None:
            reductions=[i for i,d in enumerate(Dist)
                        if 0<d<INF and candidate_reduces(S,sx,targets[i],C,d,w)]

        op,a,b=WD[w]
        out=f"w{len(gates)}";gates.append({"op":op,"a":names[a],"b":names[b],"out":out})
        for i in reductions:
            Dist[i]-=1
        S.add(w);names[w]=out;add_sx(sx,w);linear+=1

        # A covered-but-too-distant INF target can become finite as the basis
        # improves, so test only those INF targets after each helper. This is the
        # expensive initialization path, but it is normally a small subset.
        initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        added_ands=release_ready(sk,S,sx,names,gates,released)
        if added_ands:
            initialize_covered_inf(Dist,targets,S,sx,C,max_support)

        rec={"linear":linear,"released_ands":len(released),
             "positive_sum":sum(d for d in Dist if 0<d<INF),
             "finite_remaining":sum(0<d<INF for d in Dist),
             "inf_remaining":sum(d==INF for d in Dist),
             "preemptive":preempt,"pair_candidates":len(WD),
             "reductions":len(reductions),"new_ands":added_ands}
        trace.append(rec)
        print(json.dumps({"progress":rec,"seed":seed}),flush=True)

    if any(d!=0 for d in Dist):
        return None,{"status":"budget_exhausted","seed":seed,"linear":linear,
                     "released_ands":len(released),"dist":Dist,"trace_tail":trace[-20:]}
    outs=[names[t] for t in sk["outputs"]]
    c=ras.prune({"gates":gates,"outputs":outs})
    ok=ras.independent_check(c)
    if not ok[0]:raise AssertionError(("AES check failed",ok))
    summary={"status":"found","seed":seed,"linear":linear,
             "released_ands":len(released),"candidate_gates":len(c["gates"]),
             "candidate_stats":dict(collections.Counter(g["op"] for g in c["gates"])),
             "verified_all_256":True,"trace_tail":trace[-20:]}
    return c,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--family",choices=sorted(ras.SOURCES),default="fs-101")
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--max-linear",type=int,default=67)
    ap.add_argument("--max-support",type=int,default=9)
    ap.add_argument("--elite",type=int,default=1)
    ap.add_argument("--out",required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.family);assert ras.independent_check(base)[0]
    t0=time.time();c,s=synthesize(base,args.seed,args.max_linear,args.max_support,args.elite)
    s["elapsed_s"]=round(time.time()-t0,3)
    if c is not None:(out/"candidate.json").write_text(json.dumps(c,indent=2)+"\n")
    (out/"summary.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in s.items() if k!="trace_tail"},sort_keys=True),flush=True)

if __name__=="__main__":main()
