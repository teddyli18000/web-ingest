#!/usr/bin/env python3
"""Exact fixed-field 101 screen over all nine product-plane orientations.

For the live 102 field transform, a 101 circuit with the retained 18-gate core and
18 final ANDs is possible if an orientation simultaneously has:
  * prelinear network <=17 gates,
  * middle = 10 fixed norm-combine XORs + <=4 correction injections,
  * output transpose network <=15 gates (hence output <=25 by transposition).
These costs sum to 17+9+14+18+18+25 = 101.

The prelinear and output tests use the exact helper-closure search from
search_plane_prelinear17.  The middle support test is a tiny finite-domain Z3 model
with corrections restricted to wires already materialized by the 17-gate prelinear
network.  This is a complete screen of this fixed-field, retained-core family for the
(17,<=4,<=15) cost regime.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_prelinear17 as pre
import search_plane_middle5 as mid

# Columns of the live output linear map, q60..q77 -> [y0..y7].
# Pair i is (column of first plane operand * factor_i,
#            column of second plane operand * factor_i).
OUTPUT_COLUMNS = [
    200, 230, 68, 227, 185, 8, 113, 183, 241,
    17, 64, 245, 128, 16, 84, 1, 136, 19,
]
OUTPUT_PAIRS = list(zip(OUTPUT_COLUMNS[:9], OUTPUT_COLUMNS[9:]))


def dual_columns(pair, choice):
    a, b = pair
    if choice == 0:
        return a, b
    if choice == 1:
        # New plane operands (u, u+v); old (u,v)=(u',u'+v').
        return a ^ b, b
    # New plane operands (u+v, v); old (u,v)=(u'+v',v').
    return a, a ^ b


def output15_sequence(choices):
    targets = set()
    for pair, choice in zip(OUTPUT_PAIRS, choices):
        targets.update(dual_columns(pair, choice))
    targets = frozenset(targets - pre.INPUTS)
    n = len(targets)
    if n > 15:
        return None
    ok, helpers, sequence = pre.feasible(targets, 15 - n)
    if not ok:
        return None
    return {
        "target_count": n,
        "helpers": list(helpers),
        "linear_sequence": [list(x) for x in sequence],
        "targets": sorted(targets),
    }


def solve_middle4(z3, choices, available, timeout_ms):
    values = [0] + [x for x in available if x]
    s = z3.Solver()
    s.set(timeout=timeout_ms)
    selectors, cvals = [], []
    for i in range(9):
        sel = z3.Int(f"s{i}")
        s.add(sel >= 0, sel < len(values))
        selectors.append(sel)
        cvals.append(mid.zsel(z3, sel, values))
    s.add(z3.Sum([z3.If(sel == 0, 0, 1) for sel in selectors]) <= 4)
    want = mid.desired_delta(choices)
    for j in range(4):
        terms = [cvals[i] for i in range(9) if (mid.COLS[i] >> j) & 1]
        expr = terms[0]
        for term in terms[1:]:
            expr = expr ^ term
        s.add(expr == z3.BitVecVal(want[j], 8))
    result = s.check()
    if result != z3.sat:
        return {"solver": str(result), "reason": s.reason_unknown() if result == z3.unknown else None}
    model = s.model()
    selected = [values[model.eval(sel).as_long()] for sel in selectors]
    support = sum(x != 0 for x in selected)
    assert support <= 4
    check = [0, 0, 0, 0]
    for i, value in enumerate(selected):
        if value:
            check = mid.xor4(check, mid.contribution(mid.COLS[i], value))
    assert check == want
    return {"solver": "sat", "support": support, "corrections": selected, "delta": want}


def main():
    import z3

    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", type=int, required=True)
    ap.add_argument("--timeout-ms", type=int, default=1500)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.prefix not in range(9):
        raise SystemExit("prefix 0..8")

    first, second = divmod(args.prefix, 3)
    start = time.time()
    counts = {
        "orientations": 0,
        "prelinear17": 0,
        "prelinear17_output15": 0,
        "middle_sat": 0,
        "middle_unsat": 0,
        "middle_unknown": 0,
    }
    winners = []

    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        counts["orientations"] += 1

        pre_targets = set()
        for plane, choice in zip(pre.PLANES if hasattr(pre, "PLANES") else pre.live_planes(), choices):
            pre_targets.update(pre.orient(plane, choice))
        pre_targets = frozenset(pre_targets - pre.INPUTS)
        npre = len(pre_targets)
        if npre > 17:
            continue
        ok, helpers, sequence = pre.feasible(pre_targets, 17 - npre)
        if not ok:
            continue
        counts["prelinear17"] += 1
        pre_hit = {
            "target_count": npre,
            "helpers": list(helpers),
            "linear_sequence": [list(x) for x in sequence],
            "targets": sorted(pre_targets),
        }

        out_hit = output15_sequence(choices)
        if out_hit is None:
            continue
        counts["prelinear17_output15"] += 1

        available = set(pre.INPUTS)
        for _a, _b, out in pre_hit["linear_sequence"]:
            available.add(out)
        result = solve_middle4(z3, choices, sorted(available), args.timeout_ms)
        counts[f"middle_{result['solver']}"] = counts.get(f"middle_{result['solver']}", 0) + 1
        if result["solver"] != "sat":
            continue
        winner = {
            "orientations": list(choices),
            "prelinear": pre_hit,
            "output_transpose": out_hit,
            "middle": result,
            "claimed_component_costs": {
                "prelinear": 17,
                "first_and": 9,
                "middle": 10 + result["support"],
                "core": 18,
                "final_and": 18,
                "output": 25,
                "total_upper_bound": 17 + 9 + 10 + result["support"] + 18 + 18 + 25,
            },
        }
        winners.append(winner)
        print(json.dumps({"WINNER101": winner}, sort_keys=True), flush=True)

    summary = {
        "prefix": args.prefix,
        "counts": counts,
        "winners": len(winners),
        "seconds": round(time.time() - start, 3),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "winners.json").write_text(json.dumps(winners, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
