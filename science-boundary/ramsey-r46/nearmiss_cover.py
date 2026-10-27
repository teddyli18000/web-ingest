#!/usr/bin/env python3
"""Exact conflict-cover/Hamming analysis for a 36-vertex R(4,6) near-miss.

Every valid repair must flip an edge inside each current K4 and a non-edge
inside each current independent 6-set.  This gives a finite hitting-set lower
bound before considering newly created defects.  The script finds the exact
minimum hitting sets and, by default, exhausts all repairs through one edge
beyond that minimum, exactly recounting K4s and independent 6-sets with bitsets.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

N = 36
FULL = (1 << N) - 1
Edge = tuple[int, int]


def load(path: Path) -> list[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))["adjacency"]
    if len(rows) != N or any(len(r) != N or set(r) - {"0", "1"} for r in rows):
        raise ValueError("expected a 36x36 binary adjacency matrix")
    for i in range(N):
        if rows[i][i] != "0": raise ValueError("loop")
        for j in range(i + 1, N):
            if rows[i][j] != rows[j][i]: raise ValueError("asymmetric matrix")
    return rows


def defects(rows: list[str]) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    k4 = [vs for vs in itertools.combinations(range(N), 4)
          if all(rows[a][b] == "1" for a, b in itertools.combinations(vs, 2))]
    i6 = [vs for vs in itertools.combinations(range(N), 6)
          if all(rows[a][b] == "0" for a, b in itertools.combinations(vs, 2))]
    return k4, i6


def repair_edges(vs: tuple[int, ...]) -> frozenset[Edge]:
    return frozenset(tuple(sorted(e)) for e in itertools.combinations(vs, 2))


def coverage_data(conflicts: list[frozenset[Edge]]):
    universe = sorted(set().union(*conflicts))
    coverage = {e: sum(1 << i for i, c in enumerate(conflicts) if e in c) for e in universe}
    return universe, coverage, (1 << len(conflicts)) - 1


def exact_hitting_sets(conflicts: list[frozenset[Edge]], size: int) -> set[tuple[Edge, ...]]:
    universe, coverage, full = coverage_data(conflicts)
    out: set[tuple[Edge, ...]] = set()

    def rec(mask: int, chosen: list[Edge]) -> None:
        if len(chosen) > size: return
        if mask == full:
            for extra in itertools.combinations([e for e in universe if e not in chosen], size - len(chosen)):
                out.add(tuple(sorted(chosen + list(extra))))
            return
        if len(chosen) == size: return
        missing = [i for i in range(len(conflicts)) if not (mask >> i) & 1]
        target = min(missing, key=lambda i: len(conflicts[i]))
        for edge in conflicts[target]:
            if edge not in chosen:
                rec(mask | coverage[edge], chosen + [edge])

    rec(0, [])
    return out


def minimum_hitting_sets(conflicts: list[frozenset[Edge]]) -> tuple[int, set[tuple[Edge, ...]]]:
    for size in range(len(conflicts) + 1):
        hits = exact_hitting_sets(conflicts, size)
        if hits: return size, hits
    raise AssertionError("no hitting set")


def bit_adjacency(rows: list[str]) -> list[int]:
    return [sum((c == "1") << j for j, c in enumerate(row)) for row in rows]


def count_cliques(adj: list[int], cand: int, k: int) -> int:
    if k == 0: return 1
    if cand.bit_count() < k: return 0
    out = 0
    while cand.bit_count() >= k:
        b = cand & -cand; v = b.bit_length() - 1; cand ^= b
        out += count_cliques(adj, cand & adj[v], k - 1)
    return out


def recount(base: list[int], chosen: tuple[Edge, ...]) -> tuple[int, int]:
    adj = base[:]
    for u, v in chosen:
        adj[u] ^= 1 << v; adj[v] ^= 1 << u
    comp = [FULL & ~adj[i] & ~(1 << i) for i in range(N)]
    return count_cliques(adj, FULL, 4), count_cliques(comp, FULL, 6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("seed", type=Path)
    ap.add_argument("--through-radius", type=int)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    rows = load(args.seed); base = bit_adjacency(rows)
    k4, i6 = defects(rows)
    conflicts = [repair_edges(vs) for vs in k4] + [repair_edges(vs) for vs in i6]
    universe, _, _ = coverage_data(conflicts)
    minimum, min_hits = minimum_hitting_sets(conflicts)
    through = args.through_radius if args.through_radius is not None else minimum + 1
    if through < minimum or through > minimum + 1:
        raise ValueError("this compact exhaustive implementation supports minimum or minimum+1")

    all_edges = [(u, v) for u in range(N) for v in range(u + 1, N)]
    outside = [e for e in all_edges if e not in set(universe)]
    per_radius = []
    valid = []
    global_best = None
    for radius in range(minimum, through + 1):
        repairs = set(exact_hitting_sets(conflicts, radius))
        if radius == minimum + 1:
            # A repair may spend one flip outside the original-conflict edge universe;
            # then its remaining minimum flips must be a minimum hitting set.
            for hit in min_hits:
                for extra in outside:
                    repairs.add(tuple(sorted(hit + (extra,))))
        best = None
        for chosen in repairs:
            a, b = recount(base, chosen); total = a + b
            record = (total, a, b, chosen)
            if best is None or record < best: best = record
            if total == 0: valid.append(chosen)
        assert best is not None
        if global_best is None or best < global_best: global_best = best
        per_radius.append({
            "radius": radius,
            "candidate_repairs": len(repairs),
            "best_total": best[0], "best_k4": best[1], "best_independent6": best[2],
            "best_edges": [list(e) for e in best[3]],
            "valid": any(recount(base, r) == (0, 0) for r in repairs),
        })

    result = {
        "seed_k4": len(k4), "seed_independent6": len(i6), "seed_total": len(k4) + len(i6),
        "repair_edge_universe": len(universe),
        "minimum_initial_conflict_hitting_edges": minimum,
        "minimum_hitting_sets": len(min_hits),
        "excluded_radius_through": through if not valid else min(len(v) for v in valid) - 1,
        "valid_repairs_found": len(valid),
        "per_radius": per_radius,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__": raise SystemExit(main())
