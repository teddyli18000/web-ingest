#!/usr/bin/env python3
"""Exact structural reduction for a hypothetical Ramsey(4,6,36) graph at 217 edges.

This uses only exact endpoint catalogue edge extrema and elementary counting.
For v, put A=N(v), B=V\(A union {v}), d=deg(v), m=|E(G)|, and
S(v)=sum_{u in N(v)} deg(u).  Edge decomposition gives

    S(v) = m + e(A) - e(B).

Complete R(3,6,d) catalogues and complete/extreme R(4,5,35-d) catalogues
therefore give rigorous intervals for S(v).  Summing S(v) over all vertices
gives sum d(v)^2.  We exhaust degree-count vectors n_11,...,n_17 exactly.

At m=217 the aggregate relaxation leaves 11 degree-count vectors.  A short
per-vertex argument eliminates every vector containing degree 11, and then
eliminates 12^35 14^1, leaving only 12^34 13^2.

For that last degree sequence, the two degree-13 vertices cannot be adjacent:
if they were, the neighbourhood of either consists of the other (isolated
inside the neighbourhood) plus a Ramsey(3,5,12) graph.  Its edge count would
need to be at least 28, while the complete R(3,5,12) catalogue has maximum 24.
Thus the two degree-13 vertices are nonadjacent, have disjoint 13-vertex
neighbourhoods P,Q, and leave 8 degree-12 vertices adjacent to neither.

Every x in P union Q then has S(x)=145, hence e(B_x)-e(A_x)=72.  Exact extrema
force e(A_x)=29 and e(B_x)=101: the unique A29/B101 local pair.  Consequently
for p of degree 13, every vertex of G[N(p)] has degree 4 or 5 inside N(p),
because the unique A29 graph has degree sequence 4^2 5^10.  The catalogue
scan mode below filters the complete R(3,6,13) catalogue for exactly those
possible 13-vertex neighbourhood types.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

DEGREES = tuple(range(11, 18))
# Exact extrema from complete R(3,6,d) catalogues and exact R(4,5,35-d)
# complete/extreme catalogues.  n=24 is complete; n=18..23 extreme archives
# contain the proven minimum and maximum edge strata.
A_MIN = {11: 8, 12: 11, 13: 15, 14: 20, 15: 25, 16: 32, 17: 40}
A_MAX = {11: 26, 12: 29, 13: 32, 14: 35, 15: 37, 16: 40, 17: 42}
B_MIN = {11: 116, 12: 101, 13: 88, 14: 77, 15: 68, 16: 57, 17: 50}
B_MAX = {11: 132, 12: 122, 13: 114, 14: 107, 15: 100, 16: 92, 17: 85}

A29_G6 = "K@G_wzbwuwZ_"


def decode_graph6(s: str) -> list[int]:
    s = s.strip()
    if s.startswith(">>graph6<<"):
        s = s[len(">>graph6<<"):]
    if not s:
        raise ValueError("empty graph6")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 supported")
    bits: list[int] = []
    for ch in s[1:]:
        x = ord(ch) - 63
        if not 0 <= x < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((x >> k) & 1 for k in range(5, -1, -1))
    need = n * (n - 1) // 2
    if len(bits) < need:
        raise ValueError("truncated graph6")
    adj = [0] * n
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
            p += 1
    return adj


def degrees(adj: list[int]) -> list[int]:
    return [x.bit_count() for x in adj]


def edges(adj: list[int]) -> int:
    return sum(degrees(adj)) // 2


def compositions(total: int, k: int, prefix: tuple[int, ...] = ()):
    if k == 1:
        yield prefix + (total,)
        return
    for x in range(total + 1):
        yield from compositions(total - x, k - 1, prefix + (x,))


def s_interval(d: int, m: int) -> tuple[int, int]:
    # S=m+a-b and every neighbour has degree in [11,17].
    lo = max(11 * d, m + A_MIN[d] - B_MAX[d])
    hi = min(17 * d, m + A_MAX[d] - B_MIN[d])
    return lo, hi


def aggregate_degree_vectors(m: int) -> list[tuple[int, ...]]:
    out = []
    for ns in compositions(36, len(DEGREES)):
        if sum(n * d for n, d in zip(ns, DEGREES)) != 2 * m:
            continue
        s2 = sum(n * d * d for n, d in zip(ns, DEGREES))
        lo = hi = 0
        for n, d in zip(ns, DEGREES):
            a, b = s_interval(d, m)
            lo += n * a
            hi += n * b
        if lo <= s2 <= hi:
            out.append(ns)
    return out


def vector_dict(ns: tuple[int, ...]) -> dict[str, int]:
    return {str(d): n for d, n in zip(DEGREES, ns) if n}


def reduce_217() -> dict:
    # Check the first feasible total edge count under the aggregate exact-extrema
    # relaxation.  198 is the trivial minimum from delta>=11.
    counts_by_m = {}
    first = None
    first_vectors = None
    for m in range(198, 218):
        vs = aggregate_degree_vectors(m)
        counts_by_m[str(m)] = len(vs)
        if vs and first is None:
            first, first_vectors = m, vs
    assert first == 216, (first, first_vectors)
    assert first_vectors == [(0, 36, 0, 0, 0, 0, 0)], first_vectors

    raw217 = aggregate_degree_vectors(217)
    assert len(raw217) == 11, raw217

    # At m=217 a degree-11 vertex has S<=127.  Relative to eleven degree-12
    # neighbours (sum 132), this requires at least five net -1 contributions
    # from degree-11 neighbours.  Every raw aggregate vector containing d=11
    # has n_11<=4, so one d=11 vertex can have at most n_11-1<=3 such
    # neighbours; positive-degree excess only makes the inequality harder.
    no11 = []
    killed11 = []
    for ns in raw217:
        n11 = ns[0]
        if n11:
            assert n11 <= 4
            assert s_interval(11, 217)[1] == 127
            # Maximal lowering from degree-11 neighbours is n11-1 < 5.
            killed11.append(ns)
        else:
            no11.append(ns)
    assert no11 == [
        (0, 34, 2, 0, 0, 0, 0),
        (0, 35, 0, 1, 0, 0, 0),
    ], no11

    # In 12^35 14^1, any degree-12 neighbour of the degree-14 vertex has
    # neighbour-degree sum at least 11*12+14=146, but S<=145.  The degree-14
    # vertex nevertheless needs 14 neighbours, contradiction.
    assert s_interval(12, 217)[1] == 145
    killed_14 = no11[1]
    survivor = no11[0]

    return {
        "edge_relaxation_first_feasible": first,
        "edge_relaxation_first_vectors": [vector_dict(x) for x in first_vectors],
        "counts_by_m_198_217": counts_by_m,
        "m216_only_degree_sequence": {"12": 36},
        "m217_aggregate_vector_count": len(raw217),
        "m217_aggregate_vectors": [vector_dict(x) for x in raw217],
        "m217_killed_by_degree11_local_sum": [vector_dict(x) for x in killed11],
        "m217_after_degree11": [vector_dict(x) for x in no11],
        "m217_killed_12_35_14_1": vector_dict(killed_14),
        "m217_only_degree_sequence": vector_dict(survivor),
        "s12_upper_at_217": 145,
        "s11_upper_at_217": 127,
    }


def iter_g6(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(">>"):
                continue
            yield s, decode_graph6(s)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def scan(args) -> dict:
    base = reduce_217()

    # Complete R(3,5,12) catalogue: in the adjacent-13 case the other degree-13
    # vertex is isolated inside A=N(p), so the remaining 12 vertices must be an
    # R(3,5,12) graph.  We authenticate all 12 records and record max edges.
    r35 = []
    for g6, adj in iter_g6(args.r35_12):
        if len(adj) != 12:
            raise AssertionError((g6, len(adj)))
        r35.append({"graph6": g6, "edges": edges(adj), "degree_sequence": sorted(degrees(adj))})
    assert len(r35) == 12, len(r35)
    r35_max = max(x["edges"] for x in r35)
    assert r35_max == 24, r35_max

    # If the two degree-13 vertices were adjacent, S=157, so b-a=217-157=60.
    # b>=88 forces a>=28, contradicting the R(3,5,12) maximum 24 above.
    adjacent_case = {
        "degree13_neighbor_sum_if_adjacent": 157,
        "b_minus_a": 60,
        "b_min": 88,
        "required_a_min": 28,
        "r35_12_max_edges": r35_max,
        "contradiction": True,
    }

    # Unique A29 graph used at every degree-12 vertex adjacent to one of the
    # two degree-13 vertices in the surviving 217-edge degree sequence.
    a29 = decode_graph6(A29_G6)
    a29_deg = sorted(degrees(a29))
    assert edges(a29) == 29
    assert Counter(a29_deg) == Counter({4: 2, 5: 10}), a29_deg

    # Filter the complete R(3,6,13) catalogue.  In the nonadjacent case each
    # degree-13 neighbourhood P has 13 degree-12 vertices.  For x in P, the
    # degree of p inside the unique A29=N(x) equals deg_{G[P]}(x), hence every
    # vertex of P must have degree 4 or 5.
    filtered = []
    hist = Counter()
    read = 0
    for g6, adj in iter_g6(args.r36_13):
        read += 1
        if len(adj) != 13:
            raise AssertionError((g6, len(adj)))
        ds = degrees(adj)
        e = sum(ds) // 2
        if e < 27:
            continue
        if all(d in (4, 5) for d in ds):
            filtered.append({"graph6": g6, "edges": e, "degree_sequence": sorted(ds)})
            hist[e] += 1
    assert read == 275086, read

    result = {
        **base,
        "m217_degree13_vertices_adjacent_impossible": adjacent_case,
        "m217_partition_nonadjacent": {"P": 13, "Q": 13, "R": 8},
        "m217_high_adjacent_degree12_vertices": 26,
        "m217_high_adjacent_local_pair": {"A_edges": 29, "B_edges": 101, "A_unique": True, "B_unique": True},
        "m217_R_vertices_local_pairs": [
            {"A_edges": 28, "B_edges": 101},
            {"A_edges": 29, "B_edges": 102},
        ],
        "unique_A29_degree_sequence": a29_deg,
        "r35_12": {
            "source_sha256": sha256(args.r35_12),
            "records": len(r35),
            "edge_histogram": dict(sorted(Counter(x["edges"] for x in r35).items())),
            "max_edges": r35_max,
        },
        "r36_13": {
            "source_sha256": sha256(args.r36_13),
            "records": read,
            "filtered_all_degrees_4_or_5_edges_ge_27_count": len(filtered),
            "filtered_edge_histogram": dict(sorted(hist.items())),
            "filtered": filtered,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "m217_only_degree_sequence": result["m217_only_degree_sequence"],
        "degree13_adjacent_impossible": True,
        "r36_13_filtered_count": len(filtered),
        "r36_13_filtered_edge_histogram": dict(sorted(hist.items())),
    }, sort_keys=True))
    return result


def self_test() -> None:
    assert edges(decode_graph6(A29_G6)) == 29
    r = reduce_217()
    assert r["m217_only_degree_sequence"] == {"12": 34, "13": 2}
    print("m217 structure self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("scan")
    p.add_argument("--r35-12", type=Path, required=True)
    p.add_argument("--r36-13", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
    else:
        scan(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
