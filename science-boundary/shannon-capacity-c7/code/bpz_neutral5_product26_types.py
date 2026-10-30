#!/usr/bin/env python3
"""Exact type-reduced screen for neutral k=5 support-product supermultiplicativity.

There are exactly 2003 connected five-owner supports C for which the complete
5D pool Y_C has alpha=5 and contains an induced C5.  Individually these are
neutral: deleting five B points cannot add six.  Two such neutral defects could
still interact through a strong product if

    alpha(Y_A strong-product Y_C) >= 26 > 5*5.

This script first quotients the 2003 conflict graphs by exact *unrooted* graph
isomorphism (root labels are irrelevant to the relaxed product alpha), then
checks every unordered type pair by an exact SAT decision for an independent
set of size at least 26 in the strong product.

This is deliberately a relaxation of the full ten-dimensional prize problem:
it ignores baseline overlap and all peripheral losses.  Therefore UNSAT for a
type pair rigorously excludes every concrete owner-set pair of those graph
types.  Any SAT pair is only a survivor and must later be replayed with the
actual BPZ baseline/periphery objective.
"""
from __future__ import annotations

import argparse
import itertools
import json
import multiprocessing as mp
import os
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

G = {}


def conflict5(a: int, b: int) -> bool:
    if a == b:
        return True
    for _ in range(5):
        x, y = a % 7, b % 7
        a //= 7
        b //= 7
        if (x - y) % 7 not in (0, 1, 6):
            return False
    return True


def alpha_and_c5(pool):
    v = list(pool)
    n = len(v)
    compat = [0] * n
    conf = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if conflict5(v[i], v[j]):
                conf[i] |= 1 << j
                conf[j] |= 1 << i
            else:
                compat[i] |= 1 << j
                compat[j] |= 1 << i
    best = 0

    def dfs(mask, d):
        nonlocal best
        if d + mask.bit_count() <= best:
            return
        if not mask:
            best = max(best, d)
            return
        mm = mask
        pick = (mm & -mm).bit_length() - 1
        bd = -1
        while mm:
            b = mm & -mm
            i = b.bit_length() - 1
            deg = (conf[i] & mask).bit_count()
            if deg > bd:
                bd = deg
                pick = i
            mm -= b
        dfs(mask & ~(1 << pick), d)
        dfs(mask & compat[pick], d + 1)

    dfs((1 << n) - 1, 0)
    c5 = False
    if n >= 5:
        for sub in itertools.combinations(range(n), 5):
            mask = sum(1 << i for i in sub)
            if all((conf[i] & mask).bit_count() == 2 for i in sub):
                c5 = True
                break
    return best, c5


def graph_closed_masks(pool):
    v = list(pool)
    n = len(v)
    out = [1 << i for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if conflict5(v[i], v[j]):
                out[i] |= 1 << j
                out[j] |= 1 << i
    return tuple(out)


def init_worker(types):
    global G
    G = {"types": types}


def sat_pair(task):
    ia, ib = task
    from pysat.card import CardEnc, EncType
    from pysat.solvers import Solver

    A = G["types"][ia]["closed"]
    B = G["types"][ib]["closed"]
    na, nb = len(A), len(B)
    n = na * nb
    if n < 26:
        return None

    clauses = []
    # Conflict relation in the strong product, including equality in each factor.
    for i in range(na):
        ka = [k for k in range(na) if (A[i] >> k) & 1]
        for j in range(nb):
            u = i * nb + j
            lb = [l for l in range(nb) if (B[j] >> l) & 1]
            for k in ka:
                base = k * nb
                for l in lb:
                    v = base + l
                    if v > u:
                        clauses.append([-(u + 1), -(v + 1)])
    card = CardEnc.atleast(
        lits=list(range(1, n + 1)),
        bound=26,
        top_id=n,
        encoding=EncType.totalizer,
    )
    clauses.extend(card.clauses)
    with Solver(name="g4", bootstrap_with=clauses) as s:
        ok = s.solve()
        if not ok:
            return None
        model = {z for z in s.get_model() if z > 0 and z <= n}
    chosen = sorted(model)
    if len(chosen) < 26:
        raise RuntimeError(("SAT cardinality drift", ia, ib, len(chosen)))
    # Retain only 26 witness vertices; SAT may set more than the requested bound.
    witness = []
    for z in chosen[:26]:
        q = z - 1
        witness.append([q // nb, q % nb])
    return {
        "type_a": ia,
        "type_b": ib,
        "pool_a": na,
        "pool_b": nb,
        "witness26": witness,
        "clauses": len(clauses),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()

    import networkx as nx
    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore

    p = root / "data" / "base_c7.json"
    raw = json.loads(p.read_text())
    base, _t, _e, ax = load_base(p)
    if not all(ax.values()):
        raise RuntimeError({k: v for k, v in ax.items() if not v})
    ring = base.ring
    I = set(map(int, raw["I0"]))
    R = {int(x) for x, _ in raw["private_pairs"]}
    B = I - R

    groups = defaultdict(list)
    for z in range(ring.n):
        S = tuple(sorted(ring.NB[z] & B))
        if S and len(S) <= 5:
            groups[S].append(z)
    edges = [frozenset(s) for s in groups if 2 <= len(s) <= 5]
    inc = defaultdict(list)
    for e in edges:
        for u in e:
            inc[u].append(e)
    seen = set(edges)
    q = deque(edges)
    while q:
        S = q.popleft()
        if len(S) >= 5:
            continue
        es = set()
        for u in S:
            es.update(inc[u])
        for e in es:
            U = S | e
            if len(U) <= 5 and U not in seen:
                seen.add(U)
                q.append(U)

    def pool(C):
        out = []
        for r in range(1, 6):
            for s in itertools.combinations(C, r):
                out.extend(groups.get(tuple(s), ()))
        return tuple(sorted(set(out)))

    cases = []
    six = []
    for C in sorted(tuple(sorted(s)) for s in seen if len(s) == 5):
        P = pool(C)
        al, c5 = alpha_and_c5(P)
        if al >= 6:
            six.append((C, al))
        elif al == 5 and c5:
            cases.append((C, P))
    known6 = ((1644, 13347, 13600, 13692, 14040), 6)
    if six != [known6] or len(cases) != 2003:
        raise RuntimeError(("neutral-five self-check", len(cases), six))

    # Exact unrooted isomorphism quotient.
    buckets = defaultdict(list)
    for C, P in cases:
        g = nx.Graph()
        g.add_nodes_from(range(len(P)))
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if conflict5(P[i], P[j]):
                    g.add_edge(i, j)
        h = nx.weisfeiler_lehman_graph_hash(g, iterations=4)
        placed = False
        for t in buckets[h]:
            if nx.is_isomorphic(g, t["graph"]):
                t["count"] += 1
                placed = True
                break
        if not placed:
            buckets[h].append({"graph": g, "count": 1, "owners": C, "pool": P})

    types = []
    for h, arr in buckets.items():
        for t in arr:
            types.append({
                "hash": h,
                "count": t["count"],
                "owners": list(t["owners"]),
                "pool": list(t["pool"]),
                "closed": graph_closed_masks(t["pool"]),
                "pool_size": len(t["pool"]),
                "edges": t["graph"].number_of_edges(),
            })
    types.sort(key=lambda x: (-x["count"], -x["pool_size"], x["owners"]))

    tasks = [(i, j) for i in range(len(types)) for j in range(i, len(types))]
    workers = max(1, min(args.workers, 4))
    survivors = []
    state = [{"closed": t["closed"]} for t in types]
    ctx = mp.get_context("fork")
    if workers == 1:
        init_worker(state)
        for task in tasks:
            z = sat_pair(task)
            if z is not None:
                survivors.append(z)
    else:
        with ctx.Pool(workers, initializer=init_worker, initargs=(state,)) as P:
            for z in P.imap_unordered(sat_pair, tasks, chunksize=4):
                if z is not None:
                    survivors.append(z)
    survivors.sort(key=lambda z: (z["type_a"], z["type_b"]))

    public_types = [{k: v for k, v in t.items() if k != "closed"} for t in types]
    out = {
        "method": "exact-unrooted-neutral5-product26-sat-screen",
        "neutral_cases": len(cases),
        "unrooted_types": len(types),
        "type_pairs_tested": len(tasks),
        "sat26_type_pairs": len(survivors),
        "multiplicity_histogram": {str(k): v for k, v in sorted(Counter(t["count"] for t in types).items())},
        "survivors": survivors,
        "types": public_types,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("survivors", "types")}, sort_keys=True))
    print("sat26_type_pairs", len(survivors))


if __name__ == "__main__":
    main()
