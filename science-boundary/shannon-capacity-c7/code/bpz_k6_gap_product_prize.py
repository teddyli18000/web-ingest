#!/usr/bin/env python3
"""Exact terminal-prize replay for surviving k6 x k6 support products.

Consumes the irreducible k6 audit plus bpz_k6_gap_product37.py output.  For each
SAT rooted-type pair, replay every concrete ordered owner-set embedding and all
18 public BPZ terminal optima.  The 6x6 core rectangle is deleted (cost 36),
and the exact unlocked layer

    (Y_A strong-product Y_C) minus (A x C)

is optimized jointly with the terminal/periphery points it forces us to delete.
The objective is selected_new - distinct_terminal_blockers.  A value >=37 gives
score >=134754.  Maximum closure (ignoring new-new conflicts) is used only as a
rigorous upper-bound gate; positive gates are solved exactly with weighted
MaxSAT.  Any >=37 candidate is structurally replayed into a full certificate for
independent upstream verification.
"""
from __future__ import annotations

import argparse
import itertools
import json
import multiprocessing as mp
import os
import sys
from collections import defaultdict
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


def init_worker(state):
    global G
    G = state


def closure_gain(losses):
    # Maximum closure via the already-audited Dinic implementation.
    from bpz_amplify_row_defects import Dinic

    touched = sorted(set().union(*losses) if losses else set())
    loc = {p: i for i, p in enumerate(touched)}
    ll = [{loc[p] for p in L} for L in losses]
    n, m = len(ll), len(touched)
    s, t = n + m, n + m + 1
    d = Dinic(t + 1)
    inf = n + m + 10
    for i, L in enumerate(ll):
        d.add(s, i, 1)
        for j in L:
            d.add(i, n + j, inf)
    for j in range(m):
        d.add(n + j, t, 1)
    return n - d.flow(s, t), len(touched)


def solve_task(task):
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    from bpz_joint_row_defects_maxsat import terminal_periphery

    ia, ib, ai, bi, q, r, orient = task
    ring, B, fam = G["ring"], G["B"], G["fam"]
    A = G["members"][ia][ai]
    C = G["members"][ib][bi]
    PA, PC = G["pools"][A], G["pools"][C]

    P = terminal_periphery(fam, q, r, orient)
    Bcore = G["Bcore"]
    baseline = Bcore | P
    if len(baseline) != 134753:
        raise RuntimeError(("baseline", q, r, orient, len(baseline)))
    deleted_core = {(a, c) for a in A for c in C}
    if len(deleted_core) != 36 or not deleted_core <= Bcore:
        raise RuntimeError(("core rectangle", A, C, len(deleted_core)))

    # Exact unlocked layer for this rectangle.  Support-zero factors are not in
    # Y_A/Y_C; terminal-safe points stay in the baseline rather than being new.
    cand = sorted({(x, y) for x in PA for y in PC} - deleted_core - baseline)
    if len(cand) < 37:
        return {"key": list(task), "relax_gain": len(cand), "exact_gain": None,
                "candidates": len(cand), "status": "size-closed"}

    byfirst = {}
    for p in P:
        byfirst.setdefault(p[0], []).append((p[1], p))
    first = set(byfirst)

    losses = []
    for x, y in cand:
        L = set()
        # Core conflicts are exactly within the deleted A x C rectangle by the
        # definition of Y_A and Y_C, so only terminal/periphery blockers remain.
        for a in ring.NB[x] & first:
            for b, z in byfirst[a]:
                if b in ring.NB[y]:
                    L.add(z)
        losses.append(L)

    relax, touched = closure_gain(losses)
    if relax < 37:
        return {"key": list(task), "relax_gain": relax, "exact_gain": None,
                "candidates": len(cand), "touched_blockers": touched,
                "status": "closure-closed"}

    n = len(cand)
    w = WCNF()
    dv = {}
    def bv(p):
        if p not in dv:
            dv[p] = n + len(dv) + 1
        return dv[p]

    for i, L in enumerate(losses):
        for p in L:
            w.append([-(i + 1), bv(p)])

    conflicts = 0
    # Exact strong-product conflicts among newly unlocked points.
    for i, (x, y) in enumerate(cand):
        nx = ring.NB[x]
        ny = ring.NB[y]
        for j in range(i + 1, n):
            u, v = cand[j]
            if u in nx and v in ny:
                w.append([-(i + 1), -(j + 1)])
                conflicts += 1

    for i in range(n):
        w.append([i + 1], weight=1)
    for z in dv.values():
        w.append([-z], weight=1)

    with RC2(w, solver="g4", adapt=True, exhaust=True, incr=False, verbose=0) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError(("RC2 no model", task))
    pos = {z for z in model if z > 0}
    selected = [cand[i] for i in range(n) if i + 1 in pos]
    lost = {p for p, z in dv.items() if z in pos}
    gain = n - cost
    if gain != len(selected) - len(lost):
        raise RuntimeError(("objective", task, gain, len(selected), len(lost)))
    if gain > relax:
        raise RuntimeError(("relax bound", task, gain, relax))
    return {
        "key": list(task), "relax_gain": relax, "exact_gain": gain,
        "candidates": n, "touched_blockers": touched, "conflicts": conflicts,
        "selected": [list(p) for p in selected], "lost": [list(p) for p in sorted(lost)],
        "status": "exact-rc2", "score": 134753 - 36 + gain,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("audit_json", type=Path)
    ap.add_argument("product37_json", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()

    import networkx as nx
    from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery

    audit = json.loads(args.audit_json.read_text())
    prod = json.loads(args.product37_json.read_text())
    survivors = prod.get("survivors", [])
    if not survivors:
        out = {"method": "exact-k6-gap-product-terminal-prize", "raw_survivors": 0,
               "tasks": 0, "positive": 0, "candidate_materialized": False}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
        print(json.dumps(out, sort_keys=True))
        return

    root = args.tan_root.resolve()
    _base, ring, B, fam = load_geometry(root)
    B = set(B)
    Bcore = {(x, y) for x in B for y in B}

    groups = defaultdict(list)
    for z in range(ring.n):
        S = tuple(sorted(ring.NB[z] & B))
        if S and len(S) <= 6:
            groups[S].append(z)

    def pool_for(C):
        P = []
        for rr in range(1, 7):
            for s in itertools.combinations(C, rr):
                P.extend(groups.get(tuple(s), ()))
        return tuple(sorted(set(P)))

    # Build representative rooted type graphs from product37 output.
    nm = nx.algorithms.isomorphism.categorical_node_match("root", False)
    type_graphs = []
    for t in prod["types"]:
        C = tuple(t["owners"]); P = tuple(t["pool"]); cs = set(C)
        g = nx.Graph()
        for i, z in enumerate(P):
            g.add_node(i, root=(z in cs))
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if conflict5(P[i], P[j]):
                    g.add_edge(i, j)
        type_graphs.append(g)

    members = [[] for _ in type_graphs]
    pools = {}
    for row in audit.get("irreducible", []):
        C = tuple(sorted(map(int, row["owners"])))
        P = pool_for(C); pools[C] = P; cs = set(C)
        g = nx.Graph()
        for i, z in enumerate(P):
            g.add_node(i, root=(z in cs))
        for i in range(len(P)):
            for j in range(i + 1, len(P)):
                if conflict5(P[i], P[j]):
                    g.add_edge(i, j)
        hit = [i for i, h in enumerate(type_graphs) if len(h) == len(g) and
               h.number_of_edges() == g.number_of_edges() and nx.is_isomorphic(g, h, node_match=nm)]
        if len(hit) != 1:
            raise RuntimeError(("type assignment", C, hit))
        members[hit[0]].append(C)

    # Check type multiplicities against the raw product screen.
    for i, t in enumerate(prod["types"]):
        if len(members[i]) != int(t["count"]):
            raise RuntimeError(("multiplicity drift", i, len(members[i]), t["count"]))

    survivor_pairs = {(int(s["type_a"]), int(s["type_b"])) for s in survivors}
    concrete = set()
    for ia, ib in survivor_pairs:
        for A in members[ia]:
            for C in members[ib]:
                concrete.add((ia, ib, A, C))
                if ia != ib:
                    concrete.add((ib, ia, C, A))

    # Store concrete owner tuples by type/member index for compact multiprocessing tasks.
    member_index = [{C: j for j, C in enumerate(ms)} for ms in members]
    task_prefix = []
    for ia, ib, A, C in sorted(concrete):
        task_prefix.append((ia, ib, member_index[ia][A], member_index[ib][C]))
    terminals = [(q, r, o) for q in ("O", "H", "V") for r in ("O", "H", "V") for o in (0, 1)]
    tasks = [p + t for p in task_prefix for t in terminals]

    state = {"ring": ring, "B": B, "fam": fam, "Bcore": Bcore,
             "members": members, "pools": pools}
    workers = max(1, min(args.workers, 4, len(tasks) if tasks else 1))
    ctx = mp.get_context("fork")
    rows = []
    if workers == 1:
        init_worker(state)
        rows = [solve_task(t) for t in tasks]
    else:
        with ctx.Pool(workers, initializer=init_worker, initargs=(state,)) as proc:
            rows = list(proc.imap_unordered(solve_task, tasks, chunksize=1))
    rows.sort(key=lambda z: (z.get("exact_gain") if z.get("exact_gain") is not None else -999,
                             z.get("relax_gain", -999)), reverse=True)
    best = rows[0] if rows else None

    materialized = False
    score = None
    if best is not None and best.get("exact_gain") is not None and int(best["exact_gain"]) >= 37:
        ia, ib, ai, bi, q, r, orient = best["key"]
        A = members[ia][ai]; C = members[ib][bi]
        Pterm = terminal_periphery(fam, q, r, orient)
        baseline = Bcore | Pterm
        deleted_core = {(a, c) for a in A for c in C}
        lost = {tuple(p) for p in best["lost"]}
        selected = {tuple(p) for p in best["selected"]}
        cand = (baseline - deleted_core - lost) | selected
        score = len(cand)
        if score != 134753 - 36 + int(best["exact_gain"]):
            raise RuntimeError(("materialized score", score, best))
        # Independent structural replay before writing the certificate.
        sv = list(cand)
        for i, p in enumerate(sv):
            for z in sv[i + 1:]:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                    raise RuntimeError(("materialized conflict", p, z))
        def enc(p):
            return "".join(str(d) for d in (ring.decode(p[0]) + ring.decode(p[1])))
        pts = sorted(enc(p) for p in cand)
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
        materialized = True

    out = {
        "method": "exact-k6-gap-product-terminal-prize",
        "raw_survivor_type_pairs": len(survivor_pairs),
        "concrete_ordered_pairs": len(task_prefix),
        "tasks": len(tasks),
        "closure_open": sum(r.get("relax_gain", 0) >= 37 for r in rows),
        "exact_solved": sum(r.get("status") == "exact-rc2" for r in rows),
        "positive": sum((r.get("exact_gain") or -999) >= 37 for r in rows),
        "best": best,
        "top20": rows[:20],
        "candidate_materialized": materialized,
        "candidate_score": score,
        "workers": workers,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "top20"}, sort_keys=True))


if __name__ == "__main__":
    main()
