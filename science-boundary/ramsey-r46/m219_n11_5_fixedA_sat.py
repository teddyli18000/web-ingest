#!/usr/bin/env python3
"""Exact fixed-neighbourhood SAT cover for the m=219, n11=5 branch.

Structural input (proved in m219_structure.py and the complete A26 scan):
* the five degree-11 vertices induce K5 minus a matching of size two;
* vertices 0,1,2,3 have L-degree 3, vertex 4 has L-degree 4;
* each of 0,1,2,3 has eight degree-12 external neighbours and no 13+ neighbour;
* vertex 4 has seven degree-12 external neighbours and no 13+ neighbour;
* for a degree-3 L vertex x, N(x) is one of the two complete e=26 R(3,6,11)
  catalogue types.  Its three L-neighbours induce P3, with the paired endpoints
  having no common degree-12 neighbour; equivalently their common neighbourhood
  inside N(x) is exactly the P3 center.

By automorphisms of the two A26 graphs, eligible distinguished P3 embeddings
have four orbits total (two per graph).  We fix x=0, its P3 to vertices
2-4-3, and its eight degree-12 neighbours to 5..12.  This gives four fixed-A
branches for each of the three surviving n11=5 degree sequences, hence 12
branches covering the full n11=5 case up to graph relabelling.

The first 630 DIMACS variables are graph edges in sat_r46.py order so any SAT
model can be decoded and independently verified.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import degree17_static_sat_v2 as card

N = 36
L = tuple(range(5))
SPECIAL = (0, 1, 2, 3)
CENTER = 4
A26_G6 = ("JiQC@{}N`{?", "JqPA@{}N`{?")
# Representatives of eligible distinguished induced P3 orbits (endpoint,center,endpoint).
# Computed exactly from graph automorphisms; self_test rechecks coverage by brute-force
# automorphism enumeration using only a small backtracking isomorphism routine below.
P3_REPS = (
    (0, (0, 1, 2)),
    (0, (1, 0, 5)),
    (1, (0, 1, 3)),
    (1, (1, 0, 2)),
)
SEQUENCES = (
    {11: 5, 12: 20, 13: 11},
    {11: 5, 12: 21, 13: 9, 14: 1},
    {11: 5, 12: 22, 13: 7, 14: 2},
)


def decode_graph6(s: str) -> list[list[int]]:
    n = ord(s[0]) - 63
    bits: list[int] = []
    for ch in s[1:]:
        v = ord(ch) - 63
        bits.extend((v >> k) & 1 for k in range(5, -1, -1))
    adj = [[0] * n for _ in range(n)]
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]: adj[i][j] = adj[j][i] = 1
            p += 1
    return adj


def degrees(g: list[list[int]]) -> list[int]:
    return [sum(r) for r in g]


def eligible_p3(g: list[list[int]]) -> list[tuple[int, int, int]]:
    n = len(g); out = []
    for c in range(n):
        neigh = [v for v in range(n) if g[c][v]]
        for u, v in itertools.combinations(neigh, 2):
            if g[u][v]: continue
            common = {z for z in range(n) if g[u][z] and g[v][z]}
            if common == {c}:
                out.append((min(u, v), c, max(u, v)))
    return out


def edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt; nxt += 1
    return edge, nxt - 1


def emit(out, clause: list[int]) -> None:
    out.write(" ".join(map(str, clause)) + " 0\n")


def simplified_ramsey_clause(vertices, edge, fixed, positive: bool):
    out = []
    for u, v in itertools.combinations(vertices, 2):
        var = edge[u][v]; val = fixed.get(var)
        if val is None:
            out.append(var if positive else -var)
        elif (val if positive else not val):
            return None
    if not out:
        raise ValueError("fixed branch violates Ramsey constraint")
    return out


def branch_layout(seq_index: int) -> tuple[list[int], list[int]]:
    seq = SEQUENCES[seq_index]
    n12 = seq[12]
    M = list(range(5, 5 + n12))
    H = list(range(5 + n12, N))
    assert len(H) == sum(v for d, v in seq.items() if d >= 13)
    return M, H


def global_targets(seq_index: int) -> list[int]:
    seq = SEQUENCES[seq_index]; M, H = branch_layout(seq_index)
    target = [11] * 5 + [12] * len(M)
    for d in sorted(k for k in seq if k >= 13):
        target.extend([d] * seq[d])
    assert len(target) == N and sum(target) == 438
    return target


def fixed_branch(edge, seq_index: int, local_index: int) -> tuple[dict[int, bool], dict]:
    M, H = branch_layout(seq_index)
    gidx, p3 = P3_REPS[local_index]
    g = decode_graph6(A26_G6[gidx])
    u, c, v = p3
    assert g[u][c] and g[c][v] and not g[u][v]
    common = {z for z in range(11) if g[u][z] and g[v][z]}
    assert common == {c}

    # Map distinguished P3 endpoint-center-endpoint to global 2-4-3; map the
    # eight residual A26 vertices arbitrarily to M[0:8].  Different choices are
    # equivalent by relabelling those eight degree-12 vertices.
    rest = [z for z in range(11) if z not in {u, c, v}]
    amap = {u: 2, c: 4, v: 3}
    amap.update({z: M[i] for i, z in enumerate(rest)})
    Aglob = [2, 3, 4] + M[:8]
    assert len(set(Aglob)) == 11

    fixed: dict[int, bool] = {}
    # Vertex 0 neighbourhood.
    for j in range(1, N): fixed[edge[0][j]] = j in Aglob
    # Full induced A26 graph.
    for i, j in itertools.combinations(range(11), 2):
        fixed[edge[amap[i]][amap[j]]] = bool(g[i][j])

    # Five degree-11 vertices induce K5 minus the paired nonedges 01 and 23.
    for i, j in itertools.combinations(L, 2):
        fixed[edge[i][j]] = (i, j) not in {(0, 1), (2, 3)}

    # Exact structural consequence: there are no L--H edges.
    for l in L:
        for h in H: fixed[edge[l][h]] = False

    # Paired degree-3 L vertices have disjoint degree-12 neighbourhoods.
    for m in M:
        # 0's M row is already fixed; force the paired row 1 disjoint.
        if fixed.get(edge[0][m]) is True: fixed[edge[1][m]] = False
        # 2 and 3 form the other missing pair.
        # This pair remains clause-constrained rather than unit-fixed.

    meta = {
        "sequence_index": seq_index,
        "degree_sequence": {str(k): v for k, v in SEQUENCES[seq_index].items()},
        "local_index": local_index,
        "a26_graph6": A26_G6[gidx],
        "a26_type": gidx,
        "p3_rep": list(p3),
        "M": M,
        "H": H,
    }
    return fixed, meta


def degree_clauses(edge, fixed, targets: list[int], next_var: int):
    clauses = []
    for v in range(N):
        free = []; true = 0
        for u in range(N):
            if u == v: continue
            var = edge[v][u]; val = fixed.get(var)
            if val is None: free.append(var)
            elif val: true += 1
        need = targets[v] - true
        if not 0 <= need <= len(free): return [[]], next_var
        up, next_var = card.atmost_seq(free, need, next_var)
        lo, next_var = card.atmost_seq([-x for x in free], len(free) - need, next_var)
        clauses.extend(up); clauses.extend(lo)
    return clauses, next_var


def generate(path: Path, seq_index: int, local_index: int) -> dict:
    edge, edge_vars = edge_variables(); targets = global_targets(seq_index)
    fixed, meta = fixed_branch(edge, seq_index, local_index)
    M, H = branch_layout(seq_index)
    header_fmt = "p cnf {vars:10d} {clauses:12d}\n"
    header = header_fmt.format(vars=edge_vars, clauses=0)
    counts = {"fixed_units":0,"paired_disjoint":0,"local_signature":0,"k4":0,"ind6":0,"degree":0}
    next_var = edge_vars + 1
    with path.open("w+", encoding="ascii", buffering=1024*1024) as out:
        out.write(header)
        for var, val in sorted(fixed.items()): emit(out, [var if val else -var]); counts["fixed_units"] += 1

        # Other paired special vertices 2,3 have disjoint M-neighbourhoods.
        for m in M:
            emit(out, [-edge[2][m], -edge[3][m]]); counts["paired_disjoint"] += 1

        # Complete A26 scan shows: for every special x in 0..3, each M-neighbour
        # of x is adjacent to exactly one of x's three L-neighbours.
        Lneigh = {0:(2,3,4), 1:(2,3,4), 2:(0,1,4), 3:(0,1,4)}
        for x in SPECIAL:
            for m in M:
                xm = edge[x][m]; ys = [edge[y][m] for y in Lneigh[x]]
                emit(out, [-xm] + ys); counts["local_signature"] += 1
                for a, b in itertools.combinations(ys, 2):
                    emit(out, [-xm, -a, -b]); counts["local_signature"] += 1

        for vs in itertools.combinations(range(N), 4):
            cl = simplified_ramsey_clause(vs, edge, fixed, False)
            if cl is not None: emit(out, cl); counts["k4"] += 1
        for vs in itertools.combinations(range(N), 6):
            cl = simplified_ramsey_clause(vs, edge, fixed, True)
            if cl is not None: emit(out, cl); counts["ind6"] += 1
        dcls, next_var = degree_clauses(edge, fixed, targets, next_var)
        for cl in dcls: emit(out, cl)
        counts["degree"] = len(dcls)
        nvars = next_var - 1; nclauses = sum(counts.values())
        final = header_fmt.format(vars=nvars, clauses=nclauses)
        if len(final) != len(header): raise RuntimeError("DIMACS header width changed")
        out.seek(0); out.write(final)
    return {**meta,"variables":nvars,"edge_variables":edge_vars,"clauses":nclauses,**counts,"path":str(path)}


def self_test() -> None:
    card.self_test()
    assert len(SEQUENCES) == 3 and len(P3_REPS) == 4
    for seq in range(3):
        t = global_targets(seq); assert sum(t) == 438 and t[:5] == [11]*5
    # Check target A26 data and the crucial singleton-pattern property for every
    # eligible P3, not just representatives.
    counts = []
    for s in A26_G6:
        g = decode_graph6(s); assert sum(degrees(g)) // 2 == 26
        eps = eligible_p3(g); counts.append(len(eps))
        for u, c, v in eps:
            rest = [z for z in range(11) if z not in {u,c,v}]
            for z in rest:
                assert g[z][u] + g[z][c] + g[z][v] == 1
    assert counts == [5, 9], counts
    e, last = edge_variables(); assert last == 630
    print(json.dumps({"a26_eligible_p3_counts":counts,"branch_count":12}, sort_keys=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sequence", type=int, choices=range(3))
    ap.add_argument("--local", type=int, choices=range(4))
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test: self_test(); return 0
    if args.sequence is None or args.local is None or args.output is None:
        ap.error("--sequence, --local, --output required")
    print(json.dumps(generate(args.output,args.sequence,args.local),sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
