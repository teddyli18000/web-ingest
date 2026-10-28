#!/usr/bin/env python3
"""Exact necessary structural reduction for a hypothetical 219-edge R(4,6,36) graph.

This feeds the already-complete lucky-degree-12 UNSAT campaign back into the
edge-count/degree-sum identities.

For v, put d=deg(v), A=N(v), B=V\(A union {v}), and
S(v)=sum_{u in N(v)} deg(u).  Then

    S(v) = m + e(A) - e(B).

At m=219, the exact catalogue extrema permit 158 aggregate degree-count
vectors.  A degree-12 vertex is lucky exactly when e(B)-e(A)<=72, equivalently
S(v)>=147.  Since the complete lucky-d12 campaign is UNSAT, every degree-12
vertex in a hypothetical graph must therefore satisfy S(v)<=146.  This reduces
the aggregate vectors to 46.

A degree-11 vertex has S<=129.  Relative to eleven degree-12 neighbours
(baseline 132), every such vertex needs at least three degree-11 neighbours;
higher-degree neighbours only increase S.  Hence n11=1,2,3 are impossible,
and n11=4 would make the four degree-11 vertices induce K4.  This leaves 23
vectors.

When n11=0, write w(u)=deg(u)-12 for each high vertex u (degree >12).  For a
degree-12 vertex x,

    S(x)=144 + sum_{u in N(x), deg(u)>12} w(u) <= 146,

so the total weighted incidence from degree-12 vertices to the high set is at
most 2*n12.  The high vertices demand weighted incidence

    sum_u w(u)deg(u) - sum_{uv in E(H)} (w(u)+w(v)),

where H is their induced graph.  H is K4-free.  For the seven n11=0 vectors
(the high set has at most six vertices), we exhaust all labelled K4-free H
exactly and maximize the internal weighted term.  Five vectors still demand
more weighted cross-incidence than the degree-12 class can supply.  Only
12^30 13^6 and 12^31 13^4 14^1 survive this relaxation.

For n11=5, the induced graph L on the five degree-11 vertices has minimum
degree at least three and is K4-free.  Its complement therefore has maximum
degree at most one, and cannot have fewer than two edges (else L contains K4),
so L is K5 minus a matching of size two.  Four vertices have L-degree 3; for
each, S<=129 forces all eight external neighbours to have degree 12, hence
S=129 and the exact local pair (e(A),e(B))=(26,116).  This records a finite
extreme-catalogue target for the next gluing reduction.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DEGREES = tuple(range(11, 18))
A_MIN = {11: 8, 12: 11, 13: 15, 14: 20, 15: 25, 16: 32, 17: 40}
A_MAX = {11: 26, 12: 29, 13: 32, 14: 35, 15: 37, 16: 40, 17: 42}
B_MIN = {11: 116, 12: 101, 13: 88, 14: 77, 15: 68, 16: 57, 17: 50}
B_MAX = {11: 132, 12: 122, 13: 114, 14: 107, 15: 100, 16: 92, 17: 85}


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def lucky_d12_closed() -> bool:
    anchor = load("d12-anchor-orbits.json")
    residual = load("d12-residual-symmetry.json")
    assert anchor["attempted_count"] == 118
    by = {int(r["branch_ordinal"]): r["status"] for r in anchor["rows"]}
    assert len(by) == 118
    timeouts = sorted(o for o, status in by.items() if status == "TIMEOUT")
    assert sum(status == "UNSAT" for status in by.values()) == 104
    assert len(timeouts) == 14
    assert sorted(residual["expected_ordinals"]) == timeouts
    assert residual["complete"] is True
    assert residual["closed_unsat"] == 14
    assert residual["sat_count"] == 0 and residual["unknown_count"] == 0
    assert all(residual["decisions"][str(o)] == "UNSAT" for o in timeouts)
    return True


def compositions(total: int, k: int, prefix: tuple[int, ...] = ()):
    if k == 1:
        yield prefix + (total,)
        return
    for x in range(total + 1):
        yield from compositions(total - x, k - 1, prefix + (x,))


def s_interval(d: int, m: int) -> tuple[int, int]:
    return (
        max(11 * d, m + A_MIN[d] - B_MAX[d]),
        min(17 * d, m + A_MAX[d] - B_MIN[d]),
    )


def vector_dict(ns: tuple[int, ...]) -> dict[str, int]:
    return {str(d): n for d, n in zip(DEGREES, ns) if n}


def aggregate_vectors(m: int, *, no_lucky_d12: bool = False) -> list[tuple[int, ...]]:
    out = []
    for ns in compositions(36, len(DEGREES)):
        if sum(n * d for n, d in zip(ns, DEGREES)) != 2 * m:
            continue
        required = sum(n * d * d for n, d in zip(ns, DEGREES))
        lo = 0
        hi = 0
        for n, d in zip(ns, DEGREES):
            a, b = s_interval(d, m)
            if no_lucky_d12 and d == 12:
                # m=219: lucky iff S>=147, and all lucky d12 are excluded.
                b = min(b, 146)
            lo += n * a
            hi += n * b
        if lo <= required <= hi:
            out.append(ns)
    return out


def contains_k4(n: int, edges: set[tuple[int, int]]) -> bool:
    for q in itertools.combinations(range(n), 4):
        if all(tuple(sorted(e)) in edges for e in itertools.combinations(q, 2)):
            return True
    return False


def max_high_internal_weight(high_degrees: list[int]) -> tuple[int, int]:
    """Exact max of sum_(uv in E(H))(w_u+w_v) over labelled K4-free H.

    Used only for n11=0 survivors, where |H|<=6, so at most 2^15 graphs.
    Returns (maximum weight, number of edges in one maximizing graph).
    """
    n = len(high_degrees)
    pairs = list(itertools.combinations(range(n), 2))
    weights = [d - 12 for d in high_degrees]
    best = -1
    best_edges = -1
    for mask in range(1 << len(pairs)):
        es = {pairs[i] for i in range(len(pairs)) if (mask >> i) & 1}
        if contains_k4(n, es):
            continue
        score = sum(weights[i] + weights[j] for i, j in es)
        if score > best:
            best = score
            best_edges = len(es)
    return best, best_edges


def reduce_219() -> dict:
    assert lucky_d12_closed()
    m = 219
    intervals = {str(d): list(s_interval(d, m)) for d in DEGREES}
    assert intervals["11"] == [121, 129]
    assert intervals["12"] == [132, 147]

    raw = aggregate_vectors(m)
    assert len(raw) == 158, len(raw)
    after_d12 = aggregate_vectors(m, no_lucky_d12=True)
    assert len(after_d12) == 46, len(after_d12)

    killed_small_n11 = []
    after_n11 = []
    for ns in after_d12:
        n11 = ns[0]
        if 1 <= n11 <= 3:
            killed_small_n11.append({
                "degree_sequence": vector_dict(ns),
                "reason": "S11<=129 forces at least three degree-11 neighbours",
            })
        elif n11 == 4:
            killed_small_n11.append({
                "degree_sequence": vector_dict(ns),
                "reason": "four degree-11 vertices would have to induce K4",
            })
        else:
            after_n11.append(ns)
    assert len(after_n11) == 23, len(after_n11)

    n11_zero = [ns for ns in after_n11 if ns[0] == 0]
    assert len(n11_zero) == 7
    weighted_rows = []
    n11_zero_survivors = []
    for ns in n11_zero:
        seq = dict(zip(DEGREES, ns))
        high = []
        for d in range(13, 18):
            high.extend([d] * seq[d])
        assert len(high) <= 6
        gross = sum((d - 12) * d for d in high)
        best_internal, best_internal_edges = max_high_internal_weight(high)
        min_cross_demand = gross - best_internal
        capacity = 2 * seq[12]
        survives = min_cross_demand <= capacity
        row = {
            "degree_sequence": vector_dict(ns),
            "high_degrees": high,
            "gross_weighted_high_degree": gross,
            "max_internal_weight_over_K4_free_high_graphs": best_internal,
            "maximizer_edge_count": best_internal_edges,
            "min_weighted_cross_demand": min_cross_demand,
            "degree12_weighted_cross_capacity": capacity,
            "survives": survives,
        }
        weighted_rows.append(row)
        if survives:
            n11_zero_survivors.append(ns)
    assert [vector_dict(x) for x in n11_zero_survivors] == [
        {"12": 30, "13": 6},
        {"12": 31, "13": 4, "14": 1},
    ]

    n11_five = [ns for ns in after_n11 if ns[0] == 5]
    assert [vector_dict(x) for x in n11_five] == [
        {"11": 5, "12": 20, "13": 11},
        {"11": 5, "12": 21, "13": 9, "14": 1},
        {"11": 5, "12": 22, "13": 7, "14": 2},
    ]

    return {
        "edges": m,
        "lucky_d12_complete_unsat_used": True,
        "s_intervals_before_no_lucky_d12": intervals,
        "degree12_upper_after_no_lucky_d12": 146,
        "aggregate_vector_count": len(raw),
        "after_no_lucky_d12_count": len(after_d12),
        "after_no_lucky_d12": [vector_dict(x) for x in after_d12],
        "killed_n11_1_to_4_count": len(killed_small_n11),
        "killed_n11_1_to_4": killed_small_n11,
        "after_degree11_local_count": len(after_n11),
        "after_degree11_local": [vector_dict(x) for x in after_n11],
        "n11_zero_weighted_capacity": weighted_rows,
        "n11_zero_survivor_count": len(n11_zero_survivors),
        "n11_zero_survivors": [vector_dict(x) for x in n11_zero_survivors],
        "n11_eq_5": {
            "degree_sequence_count": len(n11_five),
            "degree_sequences": [vector_dict(x) for x in n11_five],
            "induced_degree11_graph": "K5 minus a matching of size 2",
            "induced_degree_sequence": [3, 3, 3, 3, 4],
            "four_degree3_vertices_external_neighbours": "eight degree-12 vertices",
            "four_degree3_vertices_S": 129,
            "forced_local_A_edges": 26,
            "forced_local_B_edges": 116,
            "complete_A26_types": 2,
            "complete_B116_types": 9,
        },
        "interpretation": "necessary exact structural reduction only; remaining vectors are not claimed realizable",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    d = reduce_219()
    text = json.dumps(d, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps({
        "aggregate": d["aggregate_vector_count"],
        "after_no_lucky_d12": d["after_no_lucky_d12_count"],
        "after_degree11_local": d["after_degree11_local_count"],
        "n11_zero_survivors": d["n11_zero_survivors"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
