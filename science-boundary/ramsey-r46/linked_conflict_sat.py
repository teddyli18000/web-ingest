#!/usr/bin/env python3
"""Constructive Ramsey R(4,6) SAT over coupled conflict/linkage edge sets.

Unlike whole-vertex-regrowth, use one consistent variable pool containing
K4-destruction edges and edges that can repair independent six-sets created
by deleting those red edges. Enforce an *exact* <=target bound on all current
and potential forbidden K4/I6 via penalty variables, plus hard degree limits.
"""
import argparse
import collections
import itertools
import json
import random
import threading
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.solvers import Glucose4

N = 36
FULL = (1 << N) - 1
PAIRS = list(itertools.combinations(range(N), 2))


def cliques(graph, k, candidates=FULL):
    out = []
    def rec(cand, vertices):
        if len(vertices) == k:
            out.append(vertices)
            return
        while cand.bit_count() >= k - len(vertices):
            bit = cand & -cand
            u = bit.bit_length() - 1
            cand ^= bit
            rec(cand & graph[u], vertices + (u,))
    rec(candidates, ())
    return out


def count(graph, k, candidates=FULL):
    if k == 0:
        return 1
    ans = 0
    while candidates.bit_count() >= k:
        b = candidates & -candidates
        u = b.bit_length() - 1
        candidates ^= b
        ans += count(graph, k-1, candidates & graph[u])
    return ans


def read(path):
    rows = json.loads(path.read_text())["adjacency"]
    assert len(rows) == N and all(len(s) == N for s in rows)
    assert all(rows[i][i] == "0" and rows[i][j] == rows[j][i]
               for i in range(N) for j in range(N))
    return [sum(1 << i for i, c in enumerate(s) if c == "1") for s in rows]


def complement(a):
    return [FULL & ~a[i] & ~(1 << i) for i in range(N)]


def potential_blue(a, red_edge):
    co = complement(a)
    u,v = red_edge
    common = co[u] & co[v]
    return [(u,v) + vs for vs in cliques(co, 4, common)]


def choose_edges(a, red_n, blue_n, seed, parents):
    rng = random.Random(seed)
    red4 = cliques(a, 4)
    assert len(red4) == 12 and count(complement(a), 6) == 0
    support = collections.Counter(pair for q in red4
                                  for pair in itertools.combinations(q, 2))
    # Greedy cover ensures every original K4 offers at least one movable red edge.
    uncovered = list(red4)
    red = set()
    while uncovered:
        e = max(support, key=lambda x: (
            sum(e[0] in q and e[1] in q for q in uncovered),
            -rng.random()))
        red.add(e)
        uncovered = [q for q in uncovered if not (e[0] in q and e[1] in q)]
    # Low independent-six creation risk is helpful when breaking K4s.
    exposure = {}
    for e in support:
        exposure[e] = len(potential_blue(a, e))
    optional = sorted((e for e in support if e not in red),
                      key=lambda e: (
                          -(support[e] * 20 / (1 + exposure[e])),
                          rng.random()))
    red.update(optional[:max(0, red_n - len(red))])
    repair_support = collections.Counter()
    for e in red:
        for witness in potential_blue(a, e):
            repair_support.update(x for x in itertools.combinations(
                sorted(witness), 2) if (a[x[0]] >> x[1] & 1) == 0)
    # Potentially useful repair additions are those that cover many
    # newly exposed independent six-sets with few K4 side effects.
    def make_red4(e):
        u,v = e
        common = a[u] & a[v]
        return sum((a[w] & common & ~((1 << (w+1)) - 1)).bit_count()
                   for w in range(N) if common >> w & 1)
    missing = sorted(repair_support,
                     key=lambda e:(-repair_support[e]/(1+make_red4(e)),
                                   rng.random()))
    blue = set(missing[:blue_n])
    # Cross-family edges expose recombination directions the single-elite
    # witness-based linkage score would otherwise miss.
    for parent in parents:
        b = read(parent)
        blue.update(e for e in PAIRS if e in support and (a[e[0]] >> e[1] & 1) !=
                    (b[e[0]] >> e[1] & 1))
    return sorted(red | blue), {
        "red_edges": len(red),
        "repair_edges": len(blue),
        "original_k4": len(red4),
        "potential_I6_from_selected_red": sum(exposure[e] for e in red),
        "initial_distinct_red_cover": len(support),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--elite", type=Path, required=True)
    ap.add_argument("--other-parents", type=Path, nargs="*", default=[])
    ap.add_argument("--red", type=int, default=35)
    ap.add_argument("--repair", type=int, default=35)
    ap.add_argument("--rng", type=int, required=True)
    ap.add_argument("--target", type=int, default=11)
    ap.add_argument("--seconds", type=int, default=180)
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    a = read(args.elite)
    edges, selection = choose_edges(
        a, args.red, args.repair, args.rng, args.other_parents)
    v = {e:i+1 for i,e in enumerate(edges)}
    fixed = {e:bool(a[e[0]] >> e[1] & 1) for e in PAIRS if e not in v}
    counters = {"k4":0,"i6":0,"fixed_bad":0,"degree_clauses":0}
    with Glucose4() as s:
        top = len(v)
        for vertex in range(N):
            base = sum(int(z) for e,z in fixed.items() if vertex in e)
            inc = [num for e,num in v.items() if vertex in e]
            lo, hi = max(0,11-base), min(len(inc),17-base)
            if lo>len(inc) or hi<0:
                s.add_clause([])
                continue
            for fn, bound in ((CardEnc.atleast,lo),(CardEnc.atmost,hi)):
                cnf=fn(lits=inc,bound=bound,top_id=top,encoding=EncType.seqcounter)
                s.append_formula(cnf.clauses)
                top=max(top,cnf.nv)
                counters["degree_clauses"]+=len(cnf.clauses)
        penalty = []
        for k in (4,6):
            for subset in itertools.combinations(range(N),k):
                lits=[]
                killed=False
                for e in itertools.combinations(subset,2):
                    number=v.get(e)
                    if number is not None:
                        lits.append(-number if k==4 else number)
                    elif fixed[e]!=(k==4):
                        killed=True
                        break
                if killed:continue
                if not lits:
                    counters["fixed_bad"]+=1
                    continue
                top+=1
                penalty.append(top)
                s.add_clause(lits+[top])
                counters["k4" if k==4 else "i6"]+=1
        budget=args.target-counters["fixed_bad"]
        if budget<0:s.add_clause([])
        else:
            bound=CardEnc.atmost(lits=penalty,bound=budget,
                                 top_id=top,encoding=EncType.seqcounter)
            s.append_formula(bound.clauses)
            top=max(top,bound.nv)
        stat = dict(campaign="linked-K4-I6-construction",
                    source=str(args.elite),seed=args.rng,
                    selection=selection,red=args.red,repair=args.repair,
                    variable_edges=len(edges),ramsey_soft=len(penalty),
                    fixed_bad=counters["fixed_bad"],degree_clauses=counters["degree_clauses"],
                    budget=budget,top_var=top,elapsed_prep=round(time.monotonic()-start,2))
        print("MODEL_READY",json.dumps(stat,sort_keys=True),flush=True)
        timer=threading.Timer(args.seconds,s.interrupt)
        timer.start()
        result=s.solve_limited(expect_interrupt=True)
        timer.cancel()
        stat["status"]="SAT" if result is True else (
            "UNSAT_THIS_LINKAGE" if result is False else "UNKNOWN")
        stat["elapsed_seconds"]=round(time.monotonic()-start,2)
        if result is True:
            model={u for u in s.get_model() if u>0}
            new=[0]*N
            for (u,w),edge in fixed.items():
                if edge:new[u]|=1<<w;new[w]|=1<<u
            for (u,w),q in v.items():
                if q in model:new[u]|=1<<w;new[w]|=1<<u
            four=count(new,4);six=count(complement(new),6)
            assert four+six<=args.target,(four,six)
            stat["K4"],stat["I6"]=four,six
            rows=["".join("1" if new[i] >> j & 1 else "0" for j in range(N))
                  for i in range(N)]
            (args.outdir/"candidate36.json").write_text(
                json.dumps({"adjacency":rows},indent=2)+"\n")
        (args.outdir/"summary.json").write_text(json.dumps(stat,indent=2)+"\n")
        print("SUMMARY",json.dumps(stat,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
