#!/usr/bin/env python3
"""Constructive R(4,6) search: SAT-UNSAT-core guided relaxation of both cores.

Uses two valid induced halves but unlike fixed-half synthesis, progressively
unfreezes *intra-half edges* exposed by SAT assumption conflicts.
Every added K4/I6 clause is universally sound, and every accepted witness
is independently recounted. Timed out means unknown, not impossible.
"""
import argparse, itertools, json, random, threading, time
from collections import Counter
from pathlib import Path
from pysat.solvers import Glucose4
from pysat.card import CardEnc, EncType
from independent_halves_cadical import graph

def complement(a):
    full=(1<<len(a))-1
    return [full&~r&~(1<<i) for i,r in enumerate(a)]

def witnesses(a, k, cap, rng):
    n=len(a); order=list(range(n)); rng.shuffle(order)
    b=[sum(1<<j for j,v in enumerate(order) if a[u]>>v&1) for u in order]
    out=[]
    def rec(cand, chosen):
        remaining=k-len(chosen)
        if not remaining:
            out.append(tuple(sorted(order[i] for i in chosen)))
            return len(out)>=cap
        while cand.bit_count()>=remaining:
            bit=cand&-cand;u=bit.bit_length()-1;cand^=bit
            if rec(cand&b[u],chosen+(u,)):
                return True
        return False
    rec((1<<n)-1,())
    return out

def matrix(a):
    return ["".join("1" if a[i]>>j&1 else "0" for j in range(len(a)))
            for i in range(len(a))]

def recount(a):
    # Separate from capped randomized enumeration.
    n=len(a);full=(1<<n)-1
    def f(g,c,k):
        if not k:return 1
        s=0
        while c.bit_count()>=k:
            bit=c&-c;u=bit.bit_length()-1;c^=bit
            s+=f(g,c&g[u],k-1)
        return s
    return f(a,full,4),f(complement(a),full,6)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["control35","fusion36","overlap36"],required=True)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--baseline",type=Path,required=True)
    ap.add_argument("--outdir",type=Path,required=True)
    ap.add_argument("--seconds",type=int,default=360)
    ap.add_argument("--batch",type=int,default=1800)
    ap.add_argument("--unfreeze-batch",type=int,default=5)
    ap.add_argument("--max-unfreeze",type=int,default=80)
    args=ap.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    rng=random.Random(args.seed)
    baseline=json.loads(args.baseline.read_text())["adjacency"]
    seed,n1,source=graph(args.mode,rng,baseline)
    n=len(seed)
    pairs=list(itertools.combinations(range(n),2))
    variables={p:i+1 for i,p in enumerate(pairs)}
    fixed=[variables[i,j] if seed[i]>>j&1 else -variables[i,j]
           for i,j in pairs if i<n1 and j<n1 or i>=n1 and j>=n1]
    fixed_initial=len(fixed)
    all_degree=[[variables[min(i,j),max(i,j)] for j in range(n) if i!=j]
                for i in range(n)]
    best=14 if n==36 else 100000
    stats=Counter()
    impact=Counter()
    seen=set()
    started=time.monotonic()
    status="UNKNOWN"
    with Glucose4() as solver:
        top=len(pairs)
        for e in all_degree:
            for method,bound in ((CardEnc.atmost,17),(CardEnc.atleast,n-25)):
                cnf=method(lits=e,bound=bound,top_id=top,encoding=EncType.seqcounter)
                solver.append_formula(cnf.clauses)
                top=cnf.nv
        stats["auxiliary_variables"]=top-len(pairs)
        timer=threading.Timer(args.seconds,solver.interrupt)
        timer.start()
        for iteration in range(1,1801):
            if time.monotonic()-started>=args.seconds:
                break
            ok=solver.solve_limited(assumptions=fixed,expect_interrupt=True)
            if ok is None:
                break
            if ok is False:
                stats["unsat_core_relaxations"]+=1
                core=solver.get_core() or []
                left=args.max_unfreeze-(fixed_initial-len(fixed))
                if not core or left<=0:
                    status="FIXED_EDGE_RELAXATION_LIMIT"
                    break
                rng.shuffle(core)
                core.sort(key=lambda x:impact[abs(x)],reverse=True)
                chosen=set(core[:min(args.unfreeze_batch,left)])
                fixed=[x for x in fixed if x not in chosen]
                print(json.dumps({"step":iteration,"event":"release-core-edges",
                     "core_size":len(core),"released":len(chosen),
                     "fixed_remaining":len(fixed)}),flush=True)
                continue
            model=set(x for x in solver.get_model() if x>0)
            a=[0]*n
            for (u,v),q in variables.items():
                if q in model:
                    a[u]|=1<<v;a[v]|=1<<u
            k4=witnesses(a,4,args.batch,rng)
            i6=witnesses(complement(a),6,args.batch,rng)
            stats["sat_models"]+=1
            if not k4 and not i6:
                assert recount(a)==(0,0)
                (args.outdir/"certificate.json").write_text(
                    json.dumps({"adjacency":matrix(a)})+"\n")
                status="SAT_VERIFIED"
                break
            if len(k4)<args.batch and len(i6)<args.batch and len(k4)+len(i6)<best:
                # Full recount to avoid falsely promising a new near-miss.
                exact=recount(a)
                assert sum(exact)==len(k4)+len(i6)
                best=sum(exact)
                (args.outdir/"best-nearmiss.json").write_text(
                    json.dumps({"adjacency":matrix(a)})+"\n")
                print(json.dumps({"step":iteration,"event":"IMPROVED",
                    "K4":exact[0],"I6":exact[1],"defects":best}),flush=True)
            added=0
            for bad,k in ((k4,4),(i6,6)):
                for vertices in bad:
                    ee=[variables[u,v] for u,v in itertools.combinations(vertices,2)]
                    clause=tuple(-q for q in ee) if k==4 else tuple(ee)
                    if clause in seen:continue
                    seen.add(clause)
                    solver.add_clause(list(clause))
                    for q in ee:impact[q]+=1
                    added+=1
            stats["ramsey_clauses"]+=added
            # Proactively escape frozen-parent basins before UNSAT is reached.
            # Conditional core relaxation alone did not fire in the first campaign:
            # all runs kept all 306 original fixed edges for their entire budget.
            if stats["sat_models"] % 4 == 0:
                left=args.max_unfreeze-(fixed_initial-len(fixed))
                if left>0:
                    ranking=sorted(fixed,key=lambda z:(-impact[abs(z)],rng.random()))
                    take=set(ranking[:min(args.unfreeze_batch,left)])
                    fixed=[z for z in fixed if z not in take]
                    stats["proactive_released_edges"]+=len(take)
                    print(json.dumps({"step":iteration,
                        "event":"proactive-witness-edge-release",
                        "released":len(take),"fixed_remaining":len(fixed),
                        "sampled_K4":len(k4),"sampled_I6":len(i6)}),flush=True)
            if iteration<=5 or iteration%25==0:
                print(json.dumps({"step":iteration,"event":"separate",
                    "K4_sample":len(k4),"I6_sample":len(i6),"added":added,
                    "fixed":len(fixed),"seconds":round(time.monotonic()-started,1)}),
                    flush=True)
            if added==0:
                status="STALLED"
                break
        timer.cancel()
    result={"mode":args.mode,"seed":args.seed,"status":status,
            "source":source,"n":n,"original_fixed_edges":fixed_initial,
            "fixed_edges_remaining":len(fixed),"best_defects":best,
            "stats":dict(stats),"seconds":round(time.monotonic()-started,2),
            "method":"witness-guided-proactive-mutable-halves-lazy-ramsey"}
    (args.outdir/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print("SUMMARY",json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
