#!/usr/bin/env python3
"""Constructive counterexample-guided SAT with conflict-driven edge release.

Goal: find a complete 36-vertex graph with fewer K4/I6 forbidden sets than
a known 12-defect parent. Freeze original edges with SAT assumptions, not
permanent clauses. If assumptions cause UNSAT, release members of the core;
if SAT returns a graph with too many defects, add those exact witnesses to
the optimization model. No hard degree constraints apply to nonzero-defect
near misses. A found witness is independently recounted.
"""
import argparse
import itertools
import json
import random
import threading
import time
from collections import Counter
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.solvers import Glucose4

N = 36
FULL = (1 << N) - 1
PAIRS = tuple(itertools.combinations(range(N), 2))
VARS = {e:i+1 for i,e in enumerate(PAIRS)}


def read(path):
    rows=json.loads(path.read_text())["adjacency"]
    assert len(rows)==N and all(len(x)==N for x in rows)
    assert all(rows[u][u]=="0" and rows[u][v]==rows[v][u]
               for u in range(N) for v in range(N))
    return [sum(1<<v for v,z in enumerate(r) if z=="1") for r in rows]


def complement(g):
    return [FULL & ~g[i] & ~(1<<i) for i in range(N)]


def enumerate_cliques(g,k,limit):
    found=[]
    def rec(c,verts):
        if len(found)==limit:
            return True
        if len(verts)==k:
            found.append(verts)
            return len(found)==limit
        while c.bit_count()>=k-len(verts):
            bit=c&-c
            u=bit.bit_length()-1
            c^=bit
            if rec(c&g[u],verts+(u,)):
                return True
        return False
    rec(FULL,())
    return found


def count_cliques(g,k,c):
    if k==0:
        return 1
    ans=0
    while c.bit_count()>=k:
        bit=c&-c
        u=bit.bit_length()-1
        c^=bit
        ans+=count_cliques(g,k-1,c&g[u])
    return ans


def get_model_graph(model):
    true=set(z for z in model if z>0)
    rows=[0]*N
    for (u,v),var in VARS.items():
        if var in true:
            rows[u]|=1<<v
            rows[v]|=1<<u
    return rows


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--target",type=int,default=11)
    p.add_argument("--seconds",type=int,default=240)
    p.add_argument("--round-seconds",type=int,default=12)
    p.add_argument("--release",type=int,default=5)
    p.add_argument("--max-free",type=int,default=200)
    p.add_argument("--max-distance",type=int,default=0)
    p.add_argument("--root",type=int)
    p.add_argument("--witness-cap",type=int,default=450)
    p.add_argument("--control",action="store_true")
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    rng=random.Random(args.seed)
    original=read(args.parent)
    original_counts=(count_cliques(original,4,FULL),
                     count_cliques(complement(original),6,FULL))
    initial_defects=sum(original_counts)
    assert 1<=initial_defects<=100
    if args.control:
        args.target=initial_defects
    original_values={q:(q if original[e[0]]>>e[1]&1 else -q)
                     for e,q in VARS.items()}
    hard_fixed=[]
    if args.root is None:
        frozen=original_values.copy()
    else:
        root=args.root
        near={u for u in range(N) if original[root]>>u&1}
        far=set(range(N))-{root}-near
        # Preserve the exact valid local rooted A/B structure, including
        # all edges touching the chosen root.
        assert all(root not in w for w in enumerate_cliques(original,4,10000))
        assert all(any(u in near for u in w) and any(u in far for u in w)
                   for w in enumerate_cliques(original,4,10000))
        cross={VARS[(u,v) if u<v else (v,u)]
               for u in near for v in far}
        hard_fixed=[lit for q,lit in original_values.items() if q not in cross]
        frozen={q:lit for q,lit in original_values.items() if q in cross}
    permitted_count=len(frozen)
    known=set()
    for k,g in ((4,original),(6,complement(original))):
        for w in enumerate_cliques(g,k,100000):
            known.add((k,w))
    assert len(known)==initial_defects
    start=time.monotonic()
    roundnum=0
    best=initial_defects
    stats=Counter()
    summary={}
    while time.monotonic()-start<args.seconds and roundnum<1000:
        roundnum+=1
        witness_list=sorted(known)
        penalties=[len(VARS)+i+1 for i in range(len(witness_list))]
        top=len(VARS)+len(penalties)
        with Glucose4() as solver:
            for lit in hard_fixed:
                solver.add_clause([lit])
            for (k,vertices),pvar in zip(witness_list,penalties):
                clause=[-VARS[e] if k==4 else VARS[e]
                        for e in itertools.combinations(vertices,2)]
                solver.add_clause(clause+[pvar])
            card=CardEnc.atmost(lits=penalties,bound=args.target,
                                top_id=top,encoding=EncType.seqcounter)
            solver.append_formula(card.clauses)
            if args.max_distance:
                flip_lits=[-q if original[e[0]]>>e[1]&1 else q
                           for e,q in VARS.items()]
                distcard=CardEnc.atmost(
                    lits=flip_lits,bound=args.max_distance,
                    top_id=card.nv,encoding=EncType.seqcounter)
                solver.append_formula(distcard.clauses)
            assumption=list(frozen.values())
            # Prefer the parent structure without freezing it permanently.
            solver.set_phases(list(original_values.values()))
            clock=threading.Timer(args.round_seconds,solver.interrupt)
            clock.start()
            sat=solver.solve_limited(assumptions=assumption,expect_interrupt=True)
            clock.cancel()
            if sat is False:
                stats["UNSAT"]+=1
                core=solver.get_core() or []
                if not core or len(frozen)==0 or permitted_count-len(frozen)>=args.max_free:
                    summary["status"]="RELAXATION_LIMIT"
                    break
                impact=Counter()
                for k,vs in known:
                    for edge in itertools.combinations(vs,2):
                        impact[VARS[edge]]+=1
                core_unique=list(set(abs(x) for x in core))
                rng.shuffle(core_unique)
                core_unique.sort(key=lambda x:impact[x],reverse=True)
                chosen=core_unique[:min(args.release,len(core_unique),
                                         args.max_free-(permitted_count-len(frozen)))]
                for q in chosen:
                    del frozen[q]
                stats["released"]+=len(chosen)
                if roundnum<8 or roundnum%5==0:
                    print("RELAX",json.dumps({"round":roundnum,"core":len(core),
                        "released":chosen,"free_edges":permitted_count-len(frozen),
                        "known_witnesses":len(known)}),flush=True)
                continue
            if sat is None:
                stats["UNKNOWN"]+=1
                # Solvers with long UNKNOWN phases are not useful to this
                # constructive candidate objective; free more high-impact edges.
                impact=Counter()
                for k,vs in known:
                    for e in itertools.combinations(vs,2):
                        impact[VARS[e]]+=1
                ranking=[q for q in frozen]
                rng.shuffle(ranking)
                ranking.sort(key=lambda q:impact[q],reverse=True)
                chosen=ranking[:min(args.release,args.max_free-
                                      (permitted_count-len(frozen)))]
                for q in chosen:
                    del frozen[q]
                stats["released"]+=len(chosen)
                if not chosen:
                    summary["status"]="UNKNOWN_AT_MAX_FREE"
                    break
                continue
            stats["SAT"]+=1
            candidate=get_model_graph(solver.get_model())
            witness4=enumerate_cliques(candidate,4,args.witness_cap)
            witness6=enumerate_cliques(complement(candidate),6,args.witness_cap)
            exact=len(witness4)<args.witness_cap and len(witness6)<args.witness_cap
            sampled_total=len(witness4)+len(witness6)
            distance=sum((candidate[i]^original[i]).bit_count()
                         for i in range(N))//2
            if args.max_distance:
                assert distance<=args.max_distance
            if exact:
                if "min_candidate_score" not in summary or sampled_total<summary["min_candidate_score"]:
                    summary["min_candidate_score"]=sampled_total
                    summary["min_candidate_distance"]=distance
            if exact and sampled_total<best:
                k4=count_cliques(candidate,4,FULL)
                i6=count_cliques(complement(candidate),6,FULL)
                assert k4==len(witness4) and i6==len(witness6)
                assert k4+i6<best
                best=k4+i6
                rows=["".join("1" if candidate[u]>>v&1 else "0" for v in range(N))
                      for u in range(N)]
                (args.outdir/"best36.json").write_text(
                    json.dumps({"adjacency":rows},indent=2)+"\n")
                print("IMPROVED",json.dumps({"round":roundnum,"K4":k4,"I6":i6,
                    "free":permitted_count-len(frozen),"elapsed":round(time.monotonic()-start,2)}),
                    flush=True)
            if exact and sampled_total<=args.target:
                summary["status"]="CONSTRUCTED"
                break
            candidates={(4,w) for w in witness4}|{(6,w) for w in witness6}
            fresh=candidates-known
            if not fresh:
                summary["status"]="STALLED_NO_NEW_CLAUSES"
                break
            known.update(fresh)
            stats["new_witnesses"]+=len(fresh)
            if roundnum<10 or roundnum%5==0:
                print("SEPARATE",json.dumps({"round":roundnum,
                    "free_edges":permitted_count-len(frozen),"k4_sample":len(witness4),
                    "i6_sample":len(witness6),"added":len(fresh),
                    "known_total":len(known),"distance":distance,
                    "elapsed":round(time.monotonic()-start,1)}),
                    flush=True)
            if args.control:
                summary["status"]="CONTROL_PASSED"
                break
    if not summary.get("status"):
        summary["status"]="BUDGET_EXHAUSTED"
    summary.update(campaign="core-guided-exact-score-counterexample-construction",
        seed=args.seed,source=str(args.parent),target=args.target,
        max_distance=args.max_distance,root=args.root,
        permitted_free_edges=permitted_count,
        initial_defects=initial_defects,initial_K4=original_counts[0],
        initial_I6=original_counts[1],
        rounds=roundnum,free_edges=permitted_count-len(frozen),
        known_witnesses=len(known),best_defects=best,stats=dict(stats),
        seconds=round(time.monotonic()-start,2))
    (args.outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("SUMMARY",json.dumps(summary,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
