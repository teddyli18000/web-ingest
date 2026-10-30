#!/usr/bin/env python3
"""Exact rooted-type screen for 6-owner clique-cover-gap products.

Input is the irreducibility audit produced by bpz_k6_gap_irreducibility_audit.py.
For every genuinely irreducible 6->7 support defect C, reconstruct

    Y_C = {z in C7^5 : empty != N[z] intersect B subseteq C}.

Two 6-owner core rectangles delete 36 points A x C.  A raw ten-dimensional
core-release improvement therefore requires an independent set of at least 37
vertices in

    (Y_A strong-product Y_C) minus (A x C).

We quotient the irreducible factors by exact rooted graph isomorphism, where
vertices belonging to the six deleted owners are colored as roots.  This color
is essential: the removed root x root cells must be preserved by the quotient.
Every unordered rooted-type pair is then decided exactly by SAT with a
cardinality >=37 constraint.  UNSAT closes every concrete owner-set pair of
those two rooted types.  SAT is only a survivor and must later be replayed with
the full 134753-point terminal/periphery prize objective and upstream verifier.
"""
from __future__ import annotations

import argparse
import itertools
import json
import multiprocessing as mp
import os
import sys
from collections import Counter, defaultdict
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


def closed_masks(pool: tuple[int, ...]) -> tuple[int, ...]:
    n = len(pool)
    out = [1 << i for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if conflict5(pool[i], pool[j]):
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

    A = G["types"][ia]
    B = G["types"][ib]
    ca, cb = A["closed"], B["closed"]
    ra, rb = A["root_mask"], B["root_mask"]
    na, nb = len(ca), len(cb)

    # Variable 0 means excluded root x root core cell.  Other entries are
    # consecutive SAT variables for the genuinely unlocked layer.
    var = [[0] * nb for _ in range(na)]
    coords: list[tuple[int, int]] = []
    nv = 0
    for i in range(na):
        for j in range(nb):
            if ((ra >> i) & 1) and ((rb >> j) & 1):
                continue
            nv += 1
            var[i][j] = nv
            coords.append((i, j))
    if nv < 37:
        return None

    clauses: list[list[int]] = []
    # Strong-product conflict: closed-neighborhood relation in both factors.
    # Generate each hard edge once using factor closed masks, rather than an
    # O(n^2) all-pairs scan over product vertices.
    for u, (i, j) in enumerate(coords, start=1):
        ma = ca[i]
        while ma:
            ba = ma & -ma
            ma -= ba
            k = ba.bit_length() - 1
            mb = cb[j]
            while mb:
                bb = mb & -mb
                mb -= bb
                l = bb.bit_length() - 1
                v = var[k][l]
                if v > u:
                    clauses.append([-u, -v])

    card = CardEnc.atleast(
        lits=list(range(1, nv + 1)),
        bound=37,
        top_id=nv,
        encoding=EncType.totalizer,
    )
    clauses.extend(card.clauses)
    with Solver(name="g4", bootstrap_with=clauses) as s:
        ok = s.solve()
        if not ok:
            return None
        pos = {z for z in s.get_model() if 0 < z <= nv}
    chosen = [coords[z - 1] for z in sorted(pos)]
    if len(chosen) < 37:
        raise RuntimeError(("cardinality drift", ia, ib, len(chosen)))
    chosen = chosen[:37]
    return {
        "type_a": ia,
        "type_b": ib,
        "pool_a": na,
        "pool_b": nb,
        "product_candidates": nv,
        "hard_clauses": len(clauses),
        "witness37_indices": [list(x) for x in chosen],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("audit_json", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()

    import networkx as nx

    audit = json.loads(args.audit_json.read_text())
    irr = audit.get("irreducible", [])
    if audit.get("input_gap_cases") != 32:
        raise RuntimeError(("expected 32 k6 gap cases", audit.get("input_gap_cases")))

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
    Bset = I - R

    # Exact support groups up to size six are enough to reconstruct every Y_C.
    groups: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for z in range(ring.n):
        S = tuple(sorted(ring.NB[z] & Bset))
        if S and len(S) <= 6:
            groups[S].append(z)

    cases = []
    for row in irr:
        C = tuple(sorted(map(int, row["owners"])))
        if len(C) != 6 or len(set(C)) != 6:
            raise RuntimeError(("bad owners", C))
        pool = []
        for r in range(1, 7):
            for s in itertools.combinations(C, r):
                pool.extend(groups.get(tuple(s), ()))
        P = tuple(sorted(set(pool)))
        roots = set(C)
        if not roots <= set(P):
            raise RuntimeError(("owner not in pool", C, sorted(roots - set(P))))
        if len(P) != int(row["pool_size"]):
            raise RuntimeError(("pool drift", C, len(P), row["pool_size"]))
        cases.append((C, P))

    # Exact rooted graph-isomorphism quotient.  A root is any vertex in C;
    # individual root labels need not be fixed because A x C removes all 36
    # root-root cells symmetrically.
    nm = nx.algorithms.isomorphism.categorical_node_match("root", False)
    buckets = defaultdict(list)
    for C, P in cases:
        cs = set(C)
        g = nx.Graph()
        for i, z in enumerate(P):
            g.add_node(i, root=(z in cs))
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if conflict5(P[i], P[j]):
                    g.add_edge(i, j)
        h = nx.weisfeiler_lehman_graph_hash(g, node_attr="root", iterations=4)
        placed = False
        for t in buckets[h]:
            if nx.is_isomorphic(g, t["graph"], node_match=nm):
                t["count"] += 1
                t["examples"].append((C, P))
                placed = True
                break
        if not placed:
            buckets[h].append({"graph": g, "count": 1, "examples": [(C, P)]})

    types = []
    for h, arr in buckets.items():
        for t in arr:
            C, P = t["examples"][0]
            root_mask = 0
            cs = set(C)
            for i, z in enumerate(P):
                if z in cs:
                    root_mask |= 1 << i
            if root_mask.bit_count() != 6:
                raise RuntimeError(("root count", C, root_mask.bit_count()))
            types.append({
                "hash": h,
                "count": t["count"],
                "owners": list(C),
                "pool": list(P),
                "pool_size": len(P),
                "edges": t["graph"].number_of_edges(),
                "root_mask": root_mask,
                "closed": closed_masks(P),
            })
    types.sort(key=lambda x: (-x["count"], -x["pool_size"], x["owners"]))

    tasks = [(i, j) for i in range(len(types)) for j in range(i, len(types))]
    workers = max(1, min(args.workers, 4, len(tasks) if tasks else 1))
    state = [{"closed": t["closed"], "root_mask": t["root_mask"]} for t in types]
    survivors = []
    if tasks:
        ctx = mp.get_context("fork")
        if workers == 1:
            init_worker(state)
            for task in tasks:
                z = sat_pair(task)
                if z is not None:
                    survivors.append(z)
        else:
            with ctx.Pool(workers, initializer=init_worker, initargs=(state,)) as proc:
                for z in proc.imap_unordered(sat_pair, tasks, chunksize=1):
                    if z is not None:
                        survivors.append(z)
    survivors.sort(key=lambda z: (z["type_a"], z["type_b"]))

    public_types = []
    for t in types:
        public_types.append({
            "hash": t["hash"],
            "count": t["count"],
            "owners": t["owners"],
            "pool": t["pool"],
            "pool_size": t["pool_size"],
            "edges": t["edges"],
        })
    out = {
        "method": "exact-rooted-k6-gap-product37-sat",
        "input_gap_cases": audit.get("input_gap_cases"),
        "irreducible_cases": len(cases),
        "rooted_types": len(types),
        "type_pairs_tested": len(tasks),
        "sat37_type_pairs": len(survivors),
        "type_multiplicity_histogram": {
            str(k): v for k, v in sorted(Counter(t["count"] for t in types).items())
        },
        "survivors": survivors,
        "types": public_types,
        "workers": workers,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("survivors", "types")}, sort_keys=True))
    print("sat37_type_pairs", len(survivors))


if __name__ == "__main__":
    main()
