#!/usr/bin/env python3
"""Search fixed-field plane orientations for prelinear17 + middle15 = one-gate saving.

For each exact <=17 prelinear hit from search_plane_prelinear17, solve the residual
middle compensation problem.  Let p_i be the nine live-102 first products and A the
9->4 linear norm map with column masks [4,1,2,14,10,8,3,5,13].  Changing a plane
orientation replaces p_i by p_i' = p_i + off_i.  The live middle computes
A p + O using five injection roots.  We seek corrections c_i drawn from linear wires
already available after the candidate 17-gate prelinear network, with at most five
nonzero c_i, such that A c = O + A off.  Then the middle is exactly 10 pure combine
XORs plus <=5 injections, so prelinear17 + middle<=15 improves the live 102 circuit
to <=101 while retaining all nonlinear and output layers.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_prelinear17 as pre

COLS = [4, 1, 2, 14, 10, 8, 3, 5, 13]


def q_masks():
    x = [1 << i for i in range(8)]
    q = []
    q.append(x[5] ^ x[0])
    q.append(x[1] ^ x[5])
    q.append(q[1] ^ x[2])
    q.append(q[2] ^ x[0])
    q.append(q[2] ^ x[6])
    q.append(x[0] ^ x[1])
    q.append(q[5] ^ x[4])
    q.append(q[6] ^ q[4])
    q.append(q[7] ^ x[3])
    q.append(q[8] ^ x[7])
    q.append(q[9] ^ q[3])
    q.append(q[9] ^ q[5])
    q.append(q[10] ^ x[4])
    q.append(q[11] ^ x[6])
    q.append(q[12] ^ x[5])
    q.append(q[12] ^ q[0])
    q.append(q[14] ^ q[8])
    q.append(q[16] ^ q[10])
    q.append(q[17] ^ q[15])
    return x, q


X, Q = q_masks()
PLANES = pre.live_planes()  # local choice 0 is the live-102 operand pair.
# The five live middle injection roots:
# q37=q18^x3, q27=q21^q12, q28=q22^x2, q32=q24^q1, q30=q25^q14.
BASE_CORRECTION = [0] * 9
BASE_CORRECTION[0] = X[3]
BASE_CORRECTION[3] = Q[12]
BASE_CORRECTION[4] = X[2]
BASE_CORRECTION[6] = Q[1]
BASE_CORRECTION[7] = Q[14]


def contribution(col, value):
    out = [0, 0, 0, 0]
    for j in range(4):
        if (col >> j) & 1:
            out[j] ^= value
    return out


def xor4(a, b):
    return [a[i] ^ b[i] for i in range(4)]


def desired_delta(choices):
    delta = [0, 0, 0, 0]
    for i, value in enumerate(BASE_CORRECTION):
        delta = xor4(delta, contribution(COLS[i], value))
    for i, (pair, choice) in enumerate(zip(PLANES, choices)):
        a, b = pair
        off = 0 if choice == 0 else (a if choice == 1 else b)
        if off:
            delta = xor4(delta, contribution(COLS[i], off))
    return delta


def available_from_hit(hit):
    available = set(pre.INPUTS)
    for _a, _b, out in hit["linear_sequence"]:
        available.add(out)
    return sorted(available)


def zsel(z3, idx, values, bits=8):
    expr = z3.BitVecVal(values[0], bits)
    for k in range(1, len(values)):
        expr = z3.If(idx == k, z3.BitVecVal(values[k], bits), expr)
    return expr


def solve_corrections(z3, choices, available, timeout_ms=2000):
    values = [0] + [x for x in available if x]
    s = z3.Solver()
    s.set(timeout=timeout_ms)
    selectors = []
    cvals = []
    for i in range(9):
        sel = z3.Int(f"s{i}")
        s.add(sel >= 0, sel < len(values))
        selectors.append(sel)
        cvals.append(zsel(z3, sel, values))
    s.add(z3.Sum([z3.If(sel == 0, 0, 1) for sel in selectors]) <= 5)

    want = desired_delta(choices)
    for j in range(4):
        terms = [cvals[i] for i in range(9) if (COLS[i] >> j) & 1]
        expr = terms[0]
        for term in terms[1:]:
            expr = expr ^ term
        s.add(expr == z3.BitVecVal(want[j], 8))

    result = s.check()
    if result != z3.sat:
        return {"solver": str(result), "reason": s.reason_unknown() if result == z3.unknown else None}
    m = s.model()
    selected = [values[m.eval(sel).as_long()] for sel in selectors]
    support = sum(x != 0 for x in selected)

    # Independent integer check.
    check = [0, 0, 0, 0]
    for i, value in enumerate(selected):
        if value:
            check = xor4(check, contribution(COLS[i], value))
    assert check == want, (check, want)
    return {"solver": "sat", "support": support, "corrections": selected, "delta": want}


def enumerate_hits(prefix):
    planes = pre.live_planes()
    first = prefix // 3
    second = prefix % 3
    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        targets = set()
        for plane, choice in zip(planes, choices):
            targets.update(pre.orient(plane, choice))
        targets = frozenset(targets - pre.INPUTS)
        n = len(targets)
        if n > 17:
            continue
        ok, helpers, sequence = pre.feasible(targets, 17 - n)
        if not ok:
            continue
        yield {
            "orientations": list(choices),
            "target_count": n,
            "helpers": list(helpers),
            "linear_sequence": [list(x) for x in sequence],
            "targets": sorted(targets),
        }


def main():
    import z3

    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", type=int, required=True)
    ap.add_argument("--timeout-ms", type=int, default=2000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.prefix not in range(9):
        raise SystemExit("prefix 0..8")

    started = time.time()
    tested_hits = 0
    solver_counts = {}
    winners = []
    best_support = 99
    for hit in enumerate_hits(args.prefix):
        tested_hits += 1
        available = available_from_hit(hit)
        result = solve_corrections(z3, hit["orientations"], available, args.timeout_ms)
        solver_counts[result["solver"]] = solver_counts.get(result["solver"], 0) + 1
        if result["solver"] == "sat":
            best_support = min(best_support, result["support"])
            winner = dict(hit)
            winner.update(result)
            winners.append(winner)
            print(json.dumps({"WINNER": winner}, sort_keys=True), flush=True)

    winners.sort(key=lambda x: (x["support"], x["target_count"], x["orientations"]))
    summary = {
        "prefix": args.prefix,
        "prelinear17_hits_tested": tested_hits,
        "solver_counts": solver_counts,
        "winners": len(winners),
        "best_support": None if best_support == 99 else best_support,
        "best_total_pre_middle": None if best_support == 99 else 17 + 10 + best_support,
        "seconds": round(time.time() - started, 3),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "winners.json").write_text(json.dumps(winners, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
