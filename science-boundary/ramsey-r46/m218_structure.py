#!/usr/bin/env python3
"""Exact necessary structural reduction for a hypothetical 218-edge R(4,6,36) graph.

For every vertex v let d=deg(v), A=N(v), B=V\(A union {v}), m=|E(G)|,
and S(v)=sum_{u in N(v)} deg(u).  The exact edge decomposition is

    S(v) = m + e(A) - e(B).

Complete R(3,6,d) catalogue extrema and exact R(4,5,35-d) edge extrema give
rigorous per-degree intervals for S(v).  Summing S(v) over all vertices gives
sum d(v)^2, so degree-count vectors n_11,...,n_17 can be exhausted exactly.

At m=218 the aggregate interval relaxation leaves 51 vectors.  Elementary
per-vertex consequences reduce those to 13:

* A degree-11 vertex has S<=128.  Relative to eleven degree-12 neighbours
  (sum 132), it must have at least four degree-11 neighbours, even before any
  higher-degree neighbours are counted.  Hence n_11=1..4 is impossible.
* If n_11=5, every degree-11 vertex must be adjacent to all four other
  degree-11 vertices, so those five vertices induce K5, contradicting K4-free.
* With n_11=0, a degree-12 vertex has S<=146.  It therefore cannot be adjacent
  to a degree-15 or degree-16 vertex, since one such neighbour already raises
  the baseline neighbour-degree sum 12*12=144 by 3 or 4.  This eliminates the
  aggregate vectors 12^34 13^1 15^1 and 12^35 16^1 because the unique high
  vertex cannot acquire its required degree using the remaining high vertices.

For n_11=6 an additional exact fact is recorded: the induced graph H on the
six degree-11 vertices has minimum degree at least four.  Since H is K4-free,
its complement has maximum degree at most one and independence number at most
three.  The complement must therefore be a perfect matching, so H=K_{2,2,2}.
Every degree-11 vertex then has exactly four degree-11 neighbours and seven
degree-12 neighbours, S=128, forcing its local pair to the extreme strata
(e(A),e(B))=(26,116).  This does not yet eliminate the four n_11=6 degree
vectors, but converts them into a finite extreme-catalogue gluing problem.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEGREES = tuple(range(11, 18))
A_MIN = {11: 8, 12: 11, 13: 15, 14: 20, 15: 25, 16: 32, 17: 40}
A_MAX = {11: 26, 12: 29, 13: 32, 14: 35, 15: 37, 16: 40, 17: 42}
B_MIN = {11: 116, 12: 101, 13: 88, 14: 77, 15: 68, 16: 57, 17: 50}
B_MAX = {11: 132, 12: 122, 13: 114, 14: 107, 15: 100, 16: 92, 17: 85}


def compositions(total: int, k: int, prefix: tuple[int, ...] = ()):
    if k == 1:
        yield prefix + (total,)
        return
    for x in range(total + 1):
        yield from compositions(total - x, k - 1, prefix + (x,))


def s_interval(d: int, m: int) -> tuple[int, int]:
    lo = max(11 * d, m + A_MIN[d] - B_MAX[d])
    hi = min(17 * d, m + A_MAX[d] - B_MIN[d])
    return lo, hi


def aggregate_vectors(m: int) -> list[tuple[int, ...]]:
    out = []
    for ns in compositions(36, len(DEGREES)):
        if sum(n * d for n, d in zip(ns, DEGREES)) != 2 * m:
            continue
        sum_d2 = sum(n * d * d for n, d in zip(ns, DEGREES))
        lo = sum(n * s_interval(d, m)[0] for n, d in zip(ns, DEGREES))
        hi = sum(n * s_interval(d, m)[1] for n, d in zip(ns, DEGREES))
        if lo <= sum_d2 <= hi:
            out.append(ns)
    return out


def as_dict(ns: tuple[int, ...]) -> dict[str, int]:
    return {str(d): n for d, n in zip(DEGREES, ns) if n}


def reduce_218() -> dict:
    m = 218
    raw = aggregate_vectors(m)
    assert len(raw) == 51, len(raw)

    killed_low = []
    after_low = []
    for ns in raw:
        n = dict(zip(DEGREES, ns))
        if 1 <= n[11] <= 4:
            killed_low.append({
                "degree_sequence": as_dict(ns),
                "reason": "each degree-11 vertex needs at least four degree-11 neighbours",
            })
        elif n[11] == 5:
            killed_low.append({
                "degree_sequence": as_dict(ns),
                "reason": "five degree-11 vertices would induce K5",
            })
        else:
            after_low.append(ns)

    assert len(killed_low) == 36, len(killed_low)
    assert len(after_low) == 15, len(after_low)

    killed_high = []
    survivors = []
    for ns in after_low:
        n = dict(zip(DEGREES, ns))
        if n[11] == 0 and n[12] == 34 and n[13] == 1 and n[15] == 1:
            killed_high.append({
                "degree_sequence": as_dict(ns),
                "reason": "without degree-11 offsets, degree-12 vertices cannot neighbour the unique degree-15 vertex",
            })
        elif n[11] == 0 and n[12] == 35 and n[16] == 1:
            killed_high.append({
                "degree_sequence": as_dict(ns),
                "reason": "without degree-11 offsets, degree-12 vertices cannot neighbour the unique degree-16 vertex",
            })
        else:
            survivors.append(ns)

    expected = [
        {"12": 32, "13": 4},
        {"12": 33, "13": 2, "14": 1},
        {"12": 34, "14": 2},
        {"11": 6, "12": 20, "13": 10},
        {"11": 6, "12": 21, "13": 8, "14": 1},
        {"11": 6, "12": 22, "13": 6, "14": 2},
        {"11": 6, "12": 23, "13": 4, "14": 3},
        {"11": 7, "12": 18, "13": 11},
        {"11": 7, "12": 19, "13": 9, "14": 1},
        {"11": 7, "12": 20, "13": 7, "14": 2},
        {"11": 8, "12": 16, "13": 12},
        {"11": 8, "12": 17, "13": 10, "14": 1},
        {"11": 9, "12": 14, "13": 13},
    ]
    got = [as_dict(ns) for ns in survivors]
    assert got == expected, (got, expected)

    n11_six = [as_dict(ns) for ns in survivors if ns[0] == 6]
    assert len(n11_six) == 4

    return {
        "edges": m,
        "s_intervals": {str(d): list(s_interval(d, m)) for d in DEGREES},
        "aggregate_vector_count": len(raw),
        "aggregate_vectors": [as_dict(ns) for ns in raw],
        "killed_n11_le_5_count": len(killed_low),
        "killed_n11_le_5": killed_low,
        "killed_isolated_high_count": len(killed_high),
        "killed_isolated_high": killed_high,
        "survivor_count": len(survivors),
        "survivors": got,
        "n11_eq_6": {
            "survivor_count": len(n11_six),
            "survivors": n11_six,
            "induced_graph": "K_{2,2,2}",
            "induced_edges": 12,
            "degree11_to_degree12_edges": 42,
            "degree11_to_higher_edges": 0,
            "S11": 128,
            "forced_local_A_edges": 26,
            "forced_local_B_edges": 116,
            "complete_A26_types": 2,
            "complete_B116_types": 9,
        },
        "interpretation": "necessary exact structural reduction only; surviving degree sequences are not claimed realizable",
    }


def self_test() -> None:
    d = reduce_218()
    assert d["aggregate_vector_count"] == 51
    assert d["survivor_count"] == 13
    assert d["n11_eq_6"]["induced_graph"] == "K_{2,2,2}"
    print(json.dumps({
        "aggregate": d["aggregate_vector_count"],
        "survivors": d["survivor_count"],
        "n11_eq_6": d["n11_eq_6"]["survivor_count"],
    }, sort_keys=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    d = reduce_218()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "aggregate_vector_count": d["aggregate_vector_count"],
        "survivor_count": d["survivor_count"],
        "survivors": d["survivors"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
