#!/usr/bin/env python3
"""Joint semilinear / plane-orientation outer search for a 101-gate AES S-box.

This keeps the live-102 18-gate inversion core and both nonlinear product layers,
but transports the construction through a semilinear input map

    P(x) = c * x^(2^k),  c != 0,

then jointly chooses the three equivalent orientations of each of the nine first
product planes.  For each orientation this script synthesizes:

* the prelinear operand network exactly (for one minimum helper realization);
* the middle offset corrections over wires available from that realization; and
* the transposed output network exactly.

With the fixed nonlinear layers, total gate count is

    65 + prelinear + middle_support + output_transpose.

Thus <=101 requires `prelinear + middle_support + output_transpose <= 36`.

The linear-network tests use the exact helper-closure search in
`search_plane_prelinear17.py`.  The middle finite-domain solve is exact for the
selected prelinear realization.  A negative result is therefore a strong screen,
but is not a global exclusion when a target set has helper slack: a different
minimum prelinear helper can expose a different correction wire.  Any positive
result is a concrete component witness that must still be materialized into a full
certificate and verified on all 256 AES inputs.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_prelinear17 as lin
import search_plane_middle5 as mid

P0_C = 0x1B
P0_K = 4
MASK8 = 0xFF
OUTPUT_COLUMNS_102 = [
    200, 230, 68, 227, 185, 8, 113, 183, 241,
    17, 64, 245, 128, 16, 84, 1, 136, 19,
]


def gf_mul(a: int, b: int) -> int:
    r = 0
    for _ in range(8):
        if b & 1:
            r ^= a
        hi = a & 0x80
        a = (a << 1) & MASK8
        if hi:
            a ^= 0x1B
        b >>= 1
    return r


def frobenius(a: int, k: int) -> int:
    for _ in range(k % 8):
        a = gf_mul(a, a)
    return a


def p_value(x: int, c: int, k: int) -> int:
    return gf_mul(c, frobenius(x, k))


def parity(x: int) -> int:
    return x.bit_count() & 1


def pullback_mask(c: int, k: int, internal_mask: int) -> int:
    """Mask on x whose parity equals internal_mask dot P(x)."""
    out = 0
    for i in range(8):
        if parity(internal_mask & p_value(1 << i, c, k)):
            out |= 1 << i
    return out


P0_PULLBACK_TO_INTERNAL = {
    pullback_mask(P0_C, P0_K, internal): internal for internal in range(256)
}
assert len(P0_PULLBACK_TO_INTERNAL) == 256


def transport_mask(mask_at_p0: int, c: int, k: int) -> int:
    internal = P0_PULLBACK_TO_INTERNAL[mask_at_p0]
    return pullback_mask(c, k, internal)


def rotl8(x: int, r: int) -> int:
    return ((x << r) | (x >> (8 - r))) & MASK8


def aes_affine_linear(x: int) -> int:
    return x ^ rotl8(x, 1) ^ rotl8(x, 2) ^ rotl8(x, 3) ^ rotl8(x, 4)


AES_L_INV = {aes_affine_linear(x): x for x in range(256)}
assert len(AES_L_INV) == 256


def q_map(value: int, c: int, k: int) -> int:
    """Output compensation Q = L o F^(8-k) o M_c o L^-1."""
    z = AES_L_INV[value]
    z = gf_mul(c, z)
    z = frobenius(z, (8 - k) % 8)
    return aes_affine_linear(z)


Q0_INV = {q_map(x, P0_C, P0_K): x for x in range(256)}
assert len(Q0_INV) == 256


def output_transport(value_at_p0: int, c: int, k: int) -> int:
    return q_map(Q0_INV[value_at_p0], c, k)


def orient(pair, choice):
    a, b = pair
    if choice == 0:
        return a, b
    if choice == 1:
        return a, a ^ b
    return a ^ b, b


def dual_columns(pair, choice):
    a, b = pair
    if choice == 0:
        return a, b
    if choice == 1:
        return a ^ b, b
    return a, a ^ b


def transported_data(c: int, k: int):
    planes = [
        (transport_mask(a, c, k), transport_mask(b, c, k))
        for a, b in lin.live_planes()
    ]
    outcols = [output_transport(v, c, k) for v in OUTPUT_COLUMNS_102]
    outpairs = list(zip(outcols[:9], outcols[9:]))
    corrections = [
        transport_mask(v, c, k) if v else 0 for v in mid.BASE_CORRECTION
    ]
    return planes, outpairs, corrections


def linear_min(targets, max_cost: int):
    targets = frozenset(set(targets) - lin.INPUTS - {0})
    n = len(targets)
    if n > max_cost:
        return None
    for cost in range(n, max_cost + 1):
        ok, helpers, sequence = lin.feasible(targets, cost - n)
        if ok:
            return {
                "cost": cost,
                "target_count": n,
                "helpers": list(helpers),
                "sequence": [list(x) for x in sequence],
                "targets": sorted(targets),
            }
    return None


def available_from_linear(hit):
    available = set(lin.INPUTS)
    for _a, _b, out in hit["sequence"]:
        available.add(out)
    return sorted(available)


def contribution(col, value):
    return [value if (col >> j) & 1 else 0 for j in range(4)]


def xor4(a, b):
    return [a[i] ^ b[i] for i in range(4)]


def desired_delta(planes, corrections, choices):
    delta = [0, 0, 0, 0]
    for i, value in enumerate(corrections):
        if value:
            delta = xor4(delta, contribution(mid.COLS[i], value))
    for i, (pair, choice) in enumerate(zip(planes, choices)):
        a, b = pair
        off = 0 if choice == 0 else (a if choice == 1 else b)
        if off:
            delta = xor4(delta, contribution(mid.COLS[i], off))
    return delta


def zsel(z3, idx, values):
    expr = z3.BitVecVal(values[0], 8)
    for i in range(1, len(values)):
        expr = z3.If(idx == i, z3.BitVecVal(values[i], 8), expr)
    return expr


def solve_middle(z3, planes, corrections, choices, available, max_support, timeout_ms):
    values = [0] + [x for x in available if x]
    want = desired_delta(planes, corrections, choices)
    for support_bound in range(max_support + 1):
        s = z3.Solver()
        s.set(timeout=timeout_ms)
        selectors, cvals = [], []
        for i in range(9):
            sel = z3.Int(f"m_{support_bound}_{i}")
            s.add(sel >= 0, sel < len(values))
            selectors.append(sel)
            cvals.append(zsel(z3, sel, values))
        s.add(z3.Sum([z3.If(sel == 0, 0, 1) for sel in selectors]) <= support_bound)
        for j in range(4):
            terms = [cvals[i] for i in range(9) if (mid.COLS[i] >> j) & 1]
            expr = terms[0]
            for term in terms[1:]:
                expr = expr ^ term
            s.add(expr == z3.BitVecVal(want[j], 8))
        result = s.check()
        if result == z3.unknown:
            return {"solver": "unknown", "reason": s.reason_unknown(), "bound": support_bound}
        if result == z3.sat:
            model = s.model()
            selected = [values[model.eval(sel).as_long()] for sel in selectors]
            actual = sum(v != 0 for v in selected)
            check = [0, 0, 0, 0]
            for i, value in enumerate(selected):
                if value:
                    check = xor4(check, contribution(mid.COLS[i], value))
            assert check == want
            return {
                "solver": "sat",
                "support": actual,
                "corrections": selected,
                "delta": want,
            }
    return {"solver": "unsat", "max_support": max_support, "delta": want}


def main():
    import z3

    ap = argparse.ArgumentParser()
    ap.add_argument("--c", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--k", type=int, required=True, choices=range(8))
    ap.add_argument("--prefix", type=int, required=True, choices=range(9))
    ap.add_argument("--timeout-ms", type=int, default=1500)
    ap.add_argument("--max-pre", type=int, default=19)
    ap.add_argument("--max-out", type=int, default=17)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not 1 <= args.c <= 255:
        raise SystemExit("c must be 1..255")

    planes, outpairs, corrections = transported_data(args.c, args.k)
    first, second = divmod(args.prefix, 3)
    started = time.time()
    counts = {
        "orientations": 0,
        "lower_bound_pruned": 0,
        "output_infeasible": 0,
        "pre_infeasible": 0,
        "middle_sat": 0,
        "middle_unsat": 0,
        "middle_unknown": 0,
    }
    best_total = 10**9
    best = []

    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        counts["orientations"] += 1

        pre_targets = set()
        for pair, choice in zip(planes, choices):
            pre_targets.update(orient(pair, choice))
        npre = len(pre_targets - lin.INPUTS - {0})

        out_targets = set()
        for pair, choice in zip(outpairs, choices):
            out_targets.update(dual_columns(pair, choice))
        nout = len(out_targets - lin.INPUTS - {0})

        # Middle support is nonnegative, so target counts alone can prune.
        if npre + nout > 36:
            counts["lower_bound_pruned"] += 1
            continue

        # Synthesize output first; it is independent of the prelinear helper choice.
        out_cap = min(args.max_out, 36 - npre)
        out_hit = linear_min(out_targets, out_cap)
        if out_hit is None:
            counts["output_infeasible"] += 1
            continue

        pre_cap = min(args.max_pre, 36 - out_hit["cost"])
        pre_hit = linear_min(pre_targets, pre_cap)
        if pre_hit is None:
            counts["pre_infeasible"] += 1
            continue

        support_cap = 36 - pre_hit["cost"] - out_hit["cost"]
        if support_cap < 0:
            counts["lower_bound_pruned"] += 1
            continue
        available = available_from_linear(pre_hit)
        middle_hit = solve_middle(
            z3, planes, corrections, choices, available, support_cap, args.timeout_ms
        )
        counts[f"middle_{middle_hit['solver']}"] = counts.get(
            f"middle_{middle_hit['solver']}", 0
        ) + 1
        if middle_hit["solver"] != "sat":
            continue

        variable = pre_hit["cost"] + middle_hit["support"] + out_hit["cost"]
        total = 65 + variable
        witness = {
            "c": args.c,
            "k": args.k,
            "orientations": list(choices),
            "prelinear": pre_hit,
            "middle": middle_hit,
            "output_transpose": out_hit,
            "variable_cost": variable,
            "total_gate_upper_bound": total,
        }
        if total < best_total:
            best_total = total
            best = [witness]
            print(json.dumps({"NEW_BEST": witness}, sort_keys=True), flush=True)
        elif total == best_total and len(best) < 100:
            best.append(witness)
        if total <= 101:
            print(json.dumps({"CANDIDATE_101": witness}, sort_keys=True), flush=True)

    summary = {
        "c": args.c,
        "k": args.k,
        "prefix": args.prefix,
        "counts": counts,
        "best_total_gate_upper_bound": None if best_total == 10**9 else best_total,
        "best_witnesses_saved": len(best),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": "candidate-complete only for the selected minimum prelinear helper realization per orientation",
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
