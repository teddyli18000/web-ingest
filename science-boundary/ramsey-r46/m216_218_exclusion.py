#!/usr/bin/env python3
"""Derive an exact 216--218 edge exclusion for a hypothetical R(4,6,36) graph.

Inputs are previously persisted exact campaign results:

* m217-structure.json: the exact-extrema relaxation first permits m=216, only
  with degree sequence 12^36.
* d12-anchor-orbits.json + d12-residual-symmetry.json: together they exhaust
  the unique A29/B101 gluing for every lucky degree-12 vertex, with every one
  of the 118 anchor orbits proved UNSAT.
* m217-fixed-pair-39.json: exact 39-orbit cover proving m=217 UNSAT.
* m218-structure.json: exact reduction of m=218 to 13 degree sequences.

The new observation is that the closed lucky-d12 campaign can be fed back into
m=218.  For m=218, a degree-12 vertex is lucky iff

    e(B)-e(A) <= 12(18-12)=72

or, using S(v)=m+e(A)-e(B), iff S(v)>=146.  Catalogue extrema already give
S(v)<=146, so after excluding lucky d=12 every degree-12 vertex has S<=145.
This kills 12 of the 13 surviving degree sequences by
sum_v S(v)=sum_v d(v)^2.  The sole survivor 12^32 13^4 is impossible because
S<=145 lets each degree-12 vertex meet at most one degree-13 vertex, giving at
most 32 cross edges, while four degree-13 vertices require at least
4*13-2*C(4,2)=40 cross edges.

At m=216 the only possible degree sequence is 12^36, where S=144 at every
vertex and the lucky threshold is 216-72=144.  Thus every vertex is lucky d=12,
so the already-complete d12 campaign excludes m=216 as well.  Together with
the exact m=217 campaign this proves any 36-vertex Ramsey(4,6) graph, if one
exists, has at least 219 edges.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"

# Same exact endpoint extrema used by m217_structure.py / m218_structure.py.
A_MAX = {11: 26, 12: 29, 13: 32, 14: 35, 15: 37, 16: 40, 17: 42}
B_MIN = {11: 116, 12: 101, 13: 88, 14: 77, 15: 68, 16: 57, 17: 50}


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def lucky_d12_closed() -> dict:
    anchor = load("d12-anchor-orbits.json")
    residual = load("d12-residual-symmetry.json")
    rows = anchor["rows"]
    assert anchor["attempted_count"] == 118
    assert len(rows) == 118
    unsat = sorted(int(r["branch_ordinal"]) for r in rows if r["status"] == "UNSAT")
    timeout = sorted(int(r["branch_ordinal"]) for r in rows if r["status"] == "TIMEOUT")
    assert len(unsat) == 104, len(unsat)
    assert len(timeout) == 14, len(timeout)
    assert sorted(residual["expected_ordinals"]) == timeout
    assert residual["complete"] is True
    assert residual["closed_unsat"] == 14
    assert residual["sat_count"] == 0
    assert residual["unknown_count"] == 0
    assert all(residual["decisions"][str(o)] == "UNSAT" for o in timeout)
    return {
        "anchor_orbits": 118,
        "anchor_unsat": len(unsat),
        "anchor_timeouts_closed_by_residual": len(timeout),
        "all_lucky_d12_unsat": True,
    }


def degree_square_sum(seq: dict[str, int]) -> int:
    return sum(int(d) * int(d) * int(n) for d, n in seq.items())


def upper_s_sum_after_d12(seq: dict[str, int]) -> int:
    # Exact m=218 per-degree catalogue upper bounds are m+A_MAX[d]-B_MIN[d].
    # The d=12 upper bound is strengthened from 146 to 145 by the complete
    # lucky-d12 exclusion.  Keep the formula here so future reuse cannot
    # silently inherit a hand-transcription error (the d=15 value is 187).
    upper = {d: 218 + A_MAX[d] - B_MIN[d] for d in A_MAX}
    assert upper == {11: 128, 12: 146, 13: 162, 14: 176, 15: 187, 16: 201, 17: 210}
    upper[12] = 145
    return sum(upper[int(d)] * int(n) for d, n in seq.items())


def derive() -> dict:
    d12 = lucky_d12_closed()

    m217_struct = load("m217-structure.json")
    assert m217_struct["edge_relaxation_first_feasible"] == 216
    assert m217_struct["m216_only_degree_sequence"] == {"12": 36}

    # m=216: 12-regular, hence S(v)=12*12=144.  Lucky threshold is 216-72=144.
    m216 = {
        "degree_sequence": {"12": 36},
        "S12": 144,
        "lucky_d12_threshold": 144,
        "excluded_by_complete_lucky_d12_campaign": True,
    }

    m217 = load("m217-fixed-pair-39.json")
    assert m217["branches_attempted"] == 39
    assert m217["all_unsat"] is True
    assert m217["found"] is False

    m218_struct = load("m218-structure.json")
    assert m218_struct["edges"] == 218
    assert m218_struct["survivor_count"] == 13
    killed = []
    survivors = []
    for seq in m218_struct["survivors"]:
        required = degree_square_sum(seq)
        upper = upper_s_sum_after_d12(seq)
        row = {
            "degree_sequence": seq,
            "sum_d_squared": required,
            "max_sum_S_after_no_lucky_d12": upper,
            "slack": upper - required,
        }
        if upper < required:
            killed.append(row)
        else:
            survivors.append(row)

    assert len(killed) == 12, len(killed)
    assert len(survivors) == 1, survivors
    assert survivors[0]["degree_sequence"] == {"12": 32, "13": 4}

    # In 12^32 13^4, for a degree-12 vertex S=144+t where t is its number of
    # degree-13 neighbours.  S<=145 therefore gives t<=1 and at most 32 cross
    # edges.  The four degree-13 vertices have total degree 52; even if all six
    # possible edges among them are present, at least 52-2*6=40 edges go to the
    # degree-12 class.  Contradiction.  (Using the forbidden K4 would only
    # strengthen this.)
    final = {
        "degree_sequence": {"12": 32, "13": 4},
        "cross_edges_upper_from_S12": 32,
        "cross_edges_lower_from_degree13": 40,
        "internal_13_edges_relaxed_upper": 6,
        "contradiction": True,
    }

    return {
        "campaign": "m216-m218-exclusion-via-closed-lucky-d12",
        "lucky_d12_evidence": d12,
        "m216": m216,
        "m217": {
            "exact_orbit_branches": 39,
            "all_unsat": True,
        },
        "m218": {
            "input_survivor_count": 13,
            "killed_by_sum_S_after_no_lucky_d12": killed,
            "remaining_before_cross_edge_contradiction": survivors,
            "final_cross_edge_contradiction": final,
            "excluded": True,
        },
        "conclusion": "Any R(4,6,36) graph, if one exists, has at least 219 edges.",
        "minimum_edges_remaining": 219,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    out = derive()
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
