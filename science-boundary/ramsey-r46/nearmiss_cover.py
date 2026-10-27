#!/usr/bin/env python3
"""Exact conflict-cover analysis for a 36-vertex R(4,6) near-miss.

Any valid graph obtained by flipping edges of the input must flip at least one
edge inside each current K4 and at least one non-edge inside each current
independent 6-set.  Therefore the flipped edges must hit every current defect.
This script computes the exact minimum hitting number, enumerates all hitting
sets at that minimum size, applies them, and exactly recounts the resulting
Ramsey defects.  If every minimum hitting set still has a defect, then no valid
graph exists within that Hamming radius (and smaller radii are excluded by the
hitting-number lower bound).
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

N = 36
Edge = tuple[int, int]


def load(path: Path) -> list[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))["adjacency"]
    if len(rows) != N or any(len(r) != N or set(r) - {"0", "1"} for r in rows):
        raise ValueError("expected a 36x36 binary adjacency matrix")
    for i in range(N):
        if rows[i][i] != "0":
            raise ValueError("loop")
        for j in range(i + 1, N):
            if rows[i][j] != rows[j][i]:
                raise ValueError("asymmetric matrix")
    return rows


def defects(rows: list[str]) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    k4 = [
        vs
        for vs in itertools.combinations(range(N), 4)
        if all(rows[a][b] == "1" for a, b in itertools.combinations(vs, 2))
    ]
    i6 = [
        vs
        for vs in itertools.combinations(range(N), 6)
        if all(rows[a][b] == "0" for a, b in itertools.combinations(vs, 2))
    ]
    return k4, i6


def repair_edges(vs: tuple[int, ...]) -> frozenset[Edge]:
    return frozenset(tuple(sorted(e)) for e in itertools.combinations(vs, 2))


def minimum_hitting_sets(conflicts: list[frozenset[Edge]]) -> tuple[int, list[tuple[Edge, ...]]]:
    universe = sorted(set().union(*conflicts))
    full = (1 << len(conflicts)) - 1
    coverage = {
        edge: sum(1 << i for i, conflict in enumerate(conflicts) if edge in conflict)
        for edge in universe
    }
    for size in range(len(conflicts) + 1):
        hits = []
        for chosen in itertools.combinations(universe, size):
            mask = 0
            for edge in chosen:
                mask |= coverage[edge]
            if mask == full:
                hits.append(chosen)
        if hits:
            return size, hits
    raise AssertionError("finite conflict family has no hitting set")


def flip(rows: list[str], chosen: tuple[Edge, ...]) -> list[str]:
    out = [list(r) for r in rows]
    for u, v in chosen:
        bit = "0" if out[u][v] == "1" else "1"
        out[u][v] = out[v][u] = bit
    return ["".join(r) for r in out]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("seed", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    rows = load(args.seed)
    k4, i6 = defects(rows)
    conflicts = [repair_edges(vs) for vs in k4] + [repair_edges(vs) for vs in i6]
    minimum, hitting_sets = minimum_hitting_sets(conflicts)
    trials = []
    for chosen in hitting_sets:
        repaired = flip(rows, chosen)
        new_k4, new_i6 = defects(repaired)
        trials.append(
            {
                "edges": [list(e) for e in chosen],
                "k4": len(new_k4),
                "independent6": len(new_i6),
                "total": len(new_k4) + len(new_i6),
            }
        )
    result = {
        "seed_k4": len(k4),
        "seed_independent6": len(i6),
        "seed_total": len(k4) + len(i6),
        "repair_edge_universe": len(set().union(*conflicts)),
        "minimum_initial_conflict_hitting_edges": minimum,
        "minimum_hitting_sets": len(hitting_sets),
        "trials": trials,
        "valid_at_minimum_radius": any(t["total"] == 0 for t in trials),
        "excluded_radius_through": minimum if all(t["total"] != 0 for t in trials) else minimum - 1,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
