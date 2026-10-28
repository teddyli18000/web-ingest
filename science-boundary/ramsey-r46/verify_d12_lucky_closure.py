#!/usr/bin/env python3
"""Machine-check the recorded lucky-degree-12 orbit closure.

This checks coverage/accounting and reruns the orbit/stabilizer self-test.  It
is deliberately not an UNSAT proof checker: the recorded solver statuses are
trusted inputs unless independently regenerated with a proof-producing solver.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIRST = HERE / "results" / "d12-anchor-orbits.json"
SECOND = HERE / "results" / "d12-residual-symmetry.json"
ORBIT_SCRIPT = HERE / "d12_anchor_orbit_dimacs.py"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-self-test", action="store_true")
    args = ap.parse_args()

    if not args.skip_self_test:
        subprocess.run([sys.executable, str(ORBIT_SCRIPT), "--self-test"], check=True)

    first = load(FIRST)
    second = load(SECOND)

    assert first["branch"] == "lucky-d12-unique-pair-anchor-orbits"
    assert first["feasible_masks"] == 2873
    assert first["orbit_count"] == 118
    assert first["orbit_size_sum"] == 2873
    assert first["attempted_count"] == 118
    assert first["sat_count"] == 0
    assert first["verified_sat_count"] == 0

    # Raw rows contain reruns; status_by_ordinal is the authoritative first-stage
    # aggregate.  Do not count the raw rows directly.
    status = {int(k): v for k, v in first["status_by_ordinal"].items()}
    assert set(status) == set(range(118))
    direct_unsat = sorted(k for k, v in status.items() if v == "UNSAT")
    unresolved = sorted(k for k, v in status.items() if v == "TIMEOUT")
    other = {k: v for k, v in status.items() if v not in {"UNSAT", "TIMEOUT"}}
    assert not other, other
    assert len(direct_unsat) == 104
    assert len(unresolved) == 14
    assert first["unsat_count"] == 104
    assert first["timeout_count"] == 14

    expected_unresolved = [0, 1, 3, 9, 17, 19, 28, 30, 46, 69, 70, 71, 73, 88]
    assert unresolved == expected_unresolved

    assert second["branch"] == "lucky-d12-anchor-residual-symmetry"
    targets = sorted(int(x) for x in second["target_ordinals"])
    assert targets == unresolved
    assert second["complete"] is True
    assert second["closed_unsat"] == 14

    rows_by_ordinal: dict[int, list[dict]] = {k: [] for k in unresolved}
    for row in second["rows"]:
        ordinal = int(row["ordinal"])
        if ordinal in rows_by_ordinal:
            rows_by_ordinal[ordinal].append(row)

    residual_closed = []
    for ordinal in unresolved:
        rows = rows_by_ordinal[ordinal]
        assert rows, f"missing residual rows for ordinal {ordinal}"
        masks = {int(r["anchor_mask"]) for r in rows}
        assert len(masks) == 1, (ordinal, masks)
        # At least one sound residual-symmetry encoding must have solved UNSAT.
        solved = [r for r in rows if r.get("status") == "UNSAT"]
        assert solved, f"ordinal {ordinal} not closed UNSAT"
        for row in solved:
            assert row.get("residual_mode") in {"all", "generators"}
            assert int(row.get("stabilizer_A_order", 0)) >= 1
            assert int(row.get("generator_count", 0)) >= 1
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
        "scope": "recorded-result coverage and symmetry/orbit self-test; not an UNSAT proof certificate checker",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
