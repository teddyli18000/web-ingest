#!/usr/bin/env python3
"""Audit the exact 217-edge exclusion.

The original structural note skipped one explicit lemma in prose: in the only
surviving degree sequence 12^34 13^2, no degree-12 vertex can be adjacent to
both degree-13 vertices.  This follows immediately from the local edge
identity and the exact A/B endpoint extrema:

    S(x)=12*12+2=146,
    e(B_x)-e(A_x)=217-146=71,

but every degree-12 local pair satisfies e(B_x)-e(A_x)>=101-29=72.

That lemma makes the two high-vertex neighborhoods disjoint.  If the high
vertices were adjacent, each is therefore isolated inside the other's
13-vertex neighborhood; deleting it leaves an R(3,5,12) graph.  The complete
R(3,5,12) catalogue has at most 24 edges, while the edge identity requires at
least 28, a contradiction.  Hence the high vertices are nonadjacent and the
39 fixed A29/B101 orbit branches are a complete cover.

This script checks that structural accounting and the recorded 39-branch
UNSAT cover.  It is not an UNSAT proof-certificate checker; use the independent
solver crosscheck for solver-level redundancy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import m217_fixed_pair_sat as fixed
import m217_structure as structure

HERE = Path(__file__).resolve().parent
STRUCTURE_RESULT = HERE / "results" / "m217-structure.json"
PAIR_RESULT = HERE / "results" / "m217-fixed-pair-39.json"
A_CATALOG = HERE / "data" / "r36_12_e29.g6"
B_CATALOG = HERE / "data" / "r45extreme_n23_e101_unique.g6"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--structure-result", type=Path, default=STRUCTURE_RESULT)
    ap.add_argument("--pair-result", type=Path, default=PAIR_RESULT)
    args = ap.parse_args()

    reduction = structure.reduce_217()
    assert reduction["edge_relaxation_first_feasible"] == 216
    assert reduction["m216_only_degree_sequence"] == {"12": 36}
    assert reduction["m217_only_degree_sequence"] == {"12": 34, "13": 2}

    # Missing-but-essential common-neighbour lemma.
    common_low_S = 12 * 12 + 2
    common_low_difference = 217 - common_low_S
    endpoint_min_difference = structure.B_MIN[12] - structure.A_MAX[12]
    assert common_low_S == 146
    assert common_low_difference == 71
    assert endpoint_min_difference == 72
    assert common_low_difference < endpoint_min_difference

    scan = load(args.structure_result)
    assert scan["m217_only_degree_sequence"] == {"12": 34, "13": 2}
    assert scan["r35_12"]["records"] == 12
    assert scan["r35_12"]["max_edges"] == 24
    assert sum(map(int, scan["r35_12"]["edge_histogram"].values())) == 12

    # If p~q, the common-neighbour lemma makes q isolated in A=N(p).
    # S(p)=13 + 12*12=157, so b-a=60.  b>=88 forces a>=28,
    # but isolated q means A-q is an R(3,5,12) graph with <=24 edges.
    adjacent_high_S = 13 + 12 * 12
    adjacent_b_minus_a = 217 - adjacent_high_S
    required_a = structure.B_MIN[13] - adjacent_b_minus_a
    assert adjacent_high_S == 157
    assert adjacent_b_minus_a == 60
    assert required_a == 28
    assert required_a > scan["r35_12"]["max_edges"]

    ag6, A, bg6, B = fixed.load_pair(A_CATALOG, B_CATALOG)
    manifest = fixed.orbit_manifest(A, B)
    reps = [tuple(map(int, p)) for p in manifest["representative_pairs"]]
    assert ag6 == structure.A29_G6
    assert len(reps) == 39
    assert manifest["aut_A_order"] == 576
    assert manifest["aut_B_order"] == 2
    assert len(manifest["A_vertex_orbits"]) == 3
    assert len(manifest["B_vertex_orbits"]) == 13

    result = load(args.pair_result)
    assert result["campaign"] == "m217-fixed-A29-B101-orbit-pair"
    assert result["branches_attempted"] == 39
    assert result["all_unsat"] is True
    assert result["found"] is False

    by_ordinal: dict[int, list[dict]] = {i: [] for i in range(39)}
    for row in result["rows"]:
        ordinal = int(row["branch_ordinal"])
        assert ordinal in by_ordinal, ordinal
        by_ordinal[ordinal].append(row)
    duplicates = {k: len(v) for k, v in by_ordinal.items() if len(v) != 1}
    assert not duplicates, duplicates

    for ordinal, (high_a, high_b) in enumerate(reps):
        row = by_ordinal[ordinal][0]
        assert row["status"] == "UNSAT", (ordinal, row["status"])
        assert int(row["high_A"]) == high_a
        assert int(row["high_B"]) == high_b
        assert row["a_graph6"] == ag6
        assert row["b_graph6"] == bg6
        assert int(row["aut_A_order"]) == 576
        assert int(row["aut_B_order"]) == 2
        assert sum(map(int, row["row_targets"])) == 75
        assert sum(map(int, row["col_targets"])) == 75

    report = {
        "status": "PASS",
        "m217_degree_sequence": {"12": 34, "13": 2},
        "common_degree12_neighbor_impossible": True,
        "common_neighbor_edge_difference": 71,
        "degree12_endpoint_min_difference": 72,
        "degree13_vertices_adjacent_impossible": True,
        "r35_12_max_edges": 24,
        "adjacent_case_required_A_edges": 28,
        "fixed_pair_branches": 39,
        "recorded_unsat_branches": 39,
        "scope": "structural proof and recorded branch accounting; not an UNSAT proof-certificate check",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
