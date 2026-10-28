#!/usr/bin/env python3
"""Machine-check the recorded lucky-degree-12 orbit closure.

This checks exact orbit coverage/accounting, regenerates the A29/B101 orbit
manifest from the pinned inputs, exercises the symmetry encoder self-tests,
and checks that every first-stage timeout is closed by a residual-symmetry
UNSAT result.

It is deliberately not an UNSAT proof-certificate checker: recorded solver
UNSAT statuses remain trusted computational results.  Use an independent
solver/proof-producing rerun for stronger solver-level certification.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIRST = HERE / "results" / "d12-anchor-orbits.json"
SECOND = HERE / "results" / "d12-residual-symmetry.json"
ORBIT_SCRIPT = HERE / "d12_anchor_orbit_dimacs.py"
A_CATALOG = HERE / "data" / "r36_12_e29.g6"
B_CATALOG = HERE / "data" / "r45extreme_n23_e101_unique.g6"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_structure_checks() -> dict:
    subprocess.run([sys.executable, str(ORBIT_SCRIPT), "self-test"], check=True)
    with tempfile.TemporaryDirectory(prefix="d12-closure-") as td:
        manifest_path = Path(td) / "manifest.json"
        subprocess.run(
            [
                sys.executable,
                str(ORBIT_SCRIPT),
                "manifest",
                "--a-catalog",
                str(A_CATALOG),
                "--b-catalog",
                str(B_CATALOG),
                "--output",
                str(manifest_path),
            ],
            check=True,
        )
        return load(manifest_path)


def aggregate_first_stage(first: dict) -> tuple[list[int], list[int], dict[int, int]]:
    by_ordinal: dict[int, list[dict]] = {i: [] for i in range(118)}
    for row in first["rows"]:
        ordinal = int(row["branch_ordinal"])
        if ordinal in by_ordinal:
            by_ordinal[ordinal].append(row)

    direct_unsat: list[int] = []
    unresolved: list[int] = []
    masks: dict[int, int] = {}
    for ordinal in range(118):
        rows = by_ordinal[ordinal]
        assert rows, f"missing first-stage rows for ordinal {ordinal}"
        row_masks = {int(r["anchor_mask"]) for r in rows}
        assert len(row_masks) == 1, (ordinal, row_masks)
        masks[ordinal] = next(iter(row_masks))
        statuses = {r["status"] for r in rows}
        assert "SAT" not in statuses, (ordinal, statuses)
        if "UNSAT" in statuses:
            direct_unsat.append(ordinal)
        elif statuses == {"TIMEOUT"}:
            unresolved.append(ordinal)
        else:
            raise AssertionError((ordinal, statuses))
    return direct_unsat, unresolved, masks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-structure-checks", action="store_true")
    args = ap.parse_args()

    manifest = None if args.skip_structure_checks else run_structure_checks()
    if manifest is not None:
        assert manifest["allowed_labelled_masks"] == 2873
        assert manifest["orbit_count"] == 118
        assert sum(manifest["orbit_sizes"]) == 2873
        assert manifest["aut_A_order"] == 576
        assert manifest["a_graph6"] == "K@G_wzbwuwZ_"
        assert manifest["b_graph6"] == "V?Q?d@cUCLHoH[[cROdaWFrDRqUTTDErGk^A^WQFhJ_?"

    first = load(FIRST)
    second = load(SECOND)

    assert first["campaign"] == "lucky-d12-unique-pair-anchor-orbits"
    assert first["allowed_labelled_masks"] == 2873
    assert first["branch_count"] == 118
    assert first["aut_A_order"] == 576
    assert first["attempted_count"] == 118
    assert sorted(map(int, first["attempted_ordinals"])) == list(range(118))
    assert first["sat_count"] == 0
    assert first["verified_sat_count"] == 0

    direct_unsat, unresolved, first_masks = aggregate_first_stage(first)
    assert len(direct_unsat) == 104, len(direct_unsat)
    assert len(unresolved) == 14, unresolved
    assert first["unsat_count"] == 104
    assert first["timeout_count"] == 14

    assert second["campaign"] == "lucky-d12-residual-symmetry-timeouts"
    targets = sorted(map(int, second["expected_ordinals"]))
    assert targets == unresolved, (targets, unresolved)
    assert second["complete"] is True
    assert second["closed_unsat"] == len(unresolved) == 14
    decisions = {int(k): v for k, v in second["decisions"].items()}
    assert set(decisions) == set(unresolved)
    assert set(decisions.values()) == {"UNSAT"}

    rows_by_ordinal: dict[int, list[dict]] = {k: [] for k in unresolved}
    for row in second["rows"]:
        ordinal = int(row["branch_ordinal"])
        if ordinal in rows_by_ordinal:
            rows_by_ordinal[ordinal].append(row)

    residual_closed: list[int] = []
    for ordinal in unresolved:
        rows = rows_by_ordinal[ordinal]
        assert rows, f"missing residual rows for ordinal {ordinal}"
        masks = {int(r["anchor_mask"]) for r in rows}
        assert masks == {first_masks[ordinal]}, (ordinal, masks, first_masks[ordinal])
        solved = [r for r in rows if r.get("status") == "UNSAT"]
        assert solved, f"ordinal {ordinal} not closed UNSAT"
        for row in solved:
            assert row.get("residual_mode") in {"all", "generators"}
            assert int(row.get("stabilizer_A_order", 0)) >= 1
            assert int(row.get("stabilizer_A_generators", 0)) >= 1
            if row["residual_mode"] == "generators":
                assert int(row["used_A_permutations"]) == int(row["stabilizer_A_generators"])
        residual_closed.append(ordinal)

    all_closed = set(direct_unsat) | set(residual_closed)
    assert all_closed == set(range(118))

    report = {
        "status": "PASS",
        "feasible_anchor_masks": 2873,
        "anchor_orbits": 118,
        "first_stage_unsat": len(direct_unsat),
        "first_stage_timeouts": len(unresolved),
        "residual_stage_unsat": len(residual_closed),
        "closed_orbits": len(all_closed),
        "sat_found": False,
        "scope": "coverage/orbit/symmetry checks plus recorded UNSAT accounting; not an UNSAT proof-certificate check",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
