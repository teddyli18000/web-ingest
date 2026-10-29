#!/usr/bin/env python3
"""Exact materialization search for the 136 helper-frontier score-35 pairs.

`enumerate_joint_decoupled_score35.cpp` lists every independently oriented
front/final plane pair at the live 0x1b*x^16 field transform whose rigorous
0/1-helper lower bound is 35.  This script restores the actual middle correction
byte values and exact two-input XOR/XNOR synthesis costs.

For a score-35 pair only the minimum middle support s and s+1 can possibly fit the
36-gate variable budget, because the pre/output lower bounds are independent of
correction values.  Correction systems are solved exactly.  Supports with nullity
0, 1, or 2 are complete; the two-free-byte case uses the same complete event
reduction as `search_semilinear_support5_rank3.py` before exact linear synthesis.

Any printed CANDIDATE_101 is a concrete component-level witness and must still be
materialized into a full circuit and independently + officially verified.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import pathlib
import time

import screen_joint_decoupled_lb as joint
import search_plane_middle5 as mid
import search_plane_prelinear17 as lin
import search_semilinear_outer as outer


def rank(columns):
    basis = []
    for x in columns:
        y = x
        for b in basis:
            y = min(y, y ^ b)
        if y:
            basis.append(y)
            basis.sort(reverse=True)
    return len(basis)


def xor_columns(columns, selector):
    out = 0
    for i, col in enumerate(columns):
        if (selector >> i) & 1:
            out ^= col
    return out


def kernel_basis(columns):
    s = len(columns)
    kernel = [m for m in range(1, 1 << s) if xor_columns(columns, m) == 0]
    basis = []
    for x in kernel:
        y = x
        for b in basis:
            y = min(y, y ^ b)
        if y:
            basis.append(y)
            basis.sort(reverse=True)
    return tuple(basis)


def parameterize(indices, want):
    """Return base byte vector and <=2 free-byte coefficient vectors."""
    columns = [mid.COLS[i] for i in indices]
    s = len(columns)
    r = rank(columns)
    nullity = s - r
    if nullity > 2:
        return None
    kb = kernel_basis(columns)
    assert len(kb) == nullity

    base = [0] * s
    for bit in range(8):
        rhs = sum((((want[j] >> bit) & 1) << j) for j in range(4))
        sols = [m for m in range(1 << s) if xor_columns(columns, m) == rhs]
        if not sols:
            return None
        assert len(sols) == (1 << nullity)
        chosen = min(sols)
        for i in range(s):
            if (chosen >> i) & 1:
                base[i] |= 1 << bit

    coeff = tuple(tuple((k >> i) & 1 for k in kb) for i in range(s))
    return tuple(base), coeff


def values_for(base, coeff, free):
    out = []
    for b, c in zip(base, coeff):
        v = b
        for flag, z in zip(c, free):
            if flag:
                v ^= z
        out.append(v)
    return tuple(out)


def candidate_free_assignments(base, coeff, free_masks, max_new):
    """Complete target-count-feasible free-byte candidates for nullity <=2."""
    t = len(coeff[0]) if coeff else 0
    if t == 0:
        return [()], False

    symbolic = set(zip(base, coeff))
    if max_new >= len(symbolic):
        if t == 1:
            return ((z,) for z in range(256)), True
        if t == 2:
            return ((z, w) for z in range(256) for w in range(256)), True
        raise AssertionError(t)

    if t == 1:
        zs = set()
        for b0, c in zip(base, coeff):
            if not c[0]:
                continue
            for value in free_masks:
                zs.add(b0 ^ value)
        for i in range(len(base)):
            for j in range(i + 1, len(base)):
                dc = coeff[i][0] ^ coeff[j][0]
                rhs = base[i] ^ base[j]
                if dc:
                    zs.add(rhs)
        return ((z,) for z in sorted(zs)), False

    if t == 2:
        families = {}

        def add_equation(pair, rhs):
            if pair == (0, 0):
                return
            families.setdefault(pair, set()).add(rhs)

        for b0, c in zip(base, coeff):
            for value in free_masks:
                add_equation(c, b0 ^ value)
        for i in range(len(base)):
            for j in range(i + 1, len(base)):
                pair = (coeff[i][0] ^ coeff[j][0], coeff[i][1] ^ coeff[j][1])
                rhs = base[i] ^ base[j]
                add_equation(pair, rhs)

        marked = bytearray(1 << 16)
        for (a, b), constants in families.items():
            for rhs in constants:
                if (a, b) == (1, 0):
                    z = rhs
                    start = z << 8
                    for w in range(256):
                        marked[start | w] = 1
                elif (a, b) == (0, 1):
                    w = rhs
                    for z in range(256):
                        marked[(z << 8) | w] = 1
                else:
                    assert (a, b) == (1, 1)
                    for z in range(256):
                        marked[(z << 8) | (z ^ rhs)] = 1
        return ((p >> 8, p & 0xFF) for p, hit in enumerate(marked) if hit), False

    raise AssertionError(t)


def orientation_union_targets(planes, front, final):
    targets = set()
    for pair, choice in zip(planes, front):
        targets.update(outer.orient(pair, choice))
    for pair, choice in zip(planes, final):
        targets.update(outer.orient(pair, choice))
    return targets


def output_targets(outpairs, final):
    targets = set()
    for pair, choice in zip(outpairs, final):
        targets.update(outer.dual_columns(pair, choice))
    return targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.pairs)))
    assert len(rows) == 136
    planes, outpairs, corrections = outer.transported_data(joint.LIVE_C, joint.LIVE_K)

    counts = {
        "pairs": len(rows),
        "support_systems": 0,
        "inconsistent_supports": 0,
        "nullity_gt2": 0,
        "free_assignments": 0,
        "zero_components": 0,
        "target_count_pruned": 0,
        "duplicate_target_sets": 0,
        "prelinear_infeasible": 0,
        "candidates_101": 0,
    }
    best_total = 10**9
    best = []
    pair_summaries = []
    started = time.time()

    for row in rows:
        front_id = int(row["front_id"])
        final_id = int(row["final_id"])
        min_support = int(row["middle_support"])
        pre_lb = int(row["pre_lb"])
        out_lb = int(row["output_lb"])
        assert pre_lb + min_support + out_lb == 35

        front = joint.choice_at(front_id)
        final = joint.choice_at(final_id)
        pre_base = orientation_union_targets(planes, front, final)
        base_noninput = frozenset(pre_base - lin.INPUTS - {0})
        out_base = output_targets(outpairs, final)

        # Find the exact minimum output cost once.  The helper frontier guarantees
        # a useful solution well below this generous cap for every score-35 row.
        out_hit = outer.linear_min(out_base, 24)
        assert out_hit is not None
        want = tuple(outer.desired_delta(planes, corrections, front))

        pair_best = 10**9
        pair_hits = 0
        for support in (min_support, min_support + 1):
            # A larger support would push the rigorous score-35 lower bound above 36.
            if pre_lb + support + out_lb > 36 or support > 9:
                continue
            pre_cap = 36 - support - out_hit["cost"]
            if pre_cap < len(base_noninput):
                counts["target_count_pruned"] += 1
                continue
            if outer.linear_min(pre_base, pre_cap) is None:
                counts["prelinear_infeasible"] += 1
                continue

            free_masks = frozenset(set(pre_base) | set(lin.INPUTS)) - {0}
            max_new = pre_cap - len(base_noninput)
            seen_targets = set()
            exact_cache = {}

            for inds in itertools.combinations(range(9), support):
                counts["support_systems"] += 1
                param = parameterize(inds, want)
                if param is None:
                    # Distinguish inconsistent systems from deliberately unsupported
                    # nullity>2 cases by checking rank/nullity first.
                    nullity = support - rank([mid.COLS[i] for i in inds])
                    if nullity > 2:
                        counts["nullity_gt2"] += 1
                    else:
                        counts["inconsistent_supports"] += 1
                    continue
                base, coeff = param
                candidates, _full = candidate_free_assignments(base, coeff, free_masks, max_new)

                for free in candidates:
                    counts["free_assignments"] += 1
                    values = values_for(base, coeff, free)
                    if any(v == 0 for v in values):
                        counts["zero_components"] += 1
                        continue
                    novel = set(values) - set(free_masks)
                    if len(novel) > max_new:
                        counts["target_count_pruned"] += 1
                        continue
                    targets = frozenset((set(pre_base) | set(values)) - lin.INPUTS - {0})
                    if len(targets) > pre_cap:
                        counts["target_count_pruned"] += 1
                        continue
                    if targets in seen_targets:
                        counts["duplicate_target_sets"] += 1
                        continue
                    seen_targets.add(targets)
                    if targets in exact_cache:
                        pre_hit = exact_cache[targets]
                    else:
                        pre_hit = outer.linear_min(targets, pre_cap)
                        exact_cache[targets] = pre_hit
                    if pre_hit is None:
                        counts["prelinear_infeasible"] += 1
                        continue

                    variable = pre_hit["cost"] + support + out_hit["cost"]
                    total = 65 + variable
                    pair_best = min(pair_best, total)
                    witness = {
                        "front_id": front_id,
                        "final_id": final_id,
                        "front_orientations": list(front),
                        "final_orientations": list(final),
                        "support_positions": list(inds),
                        "correction_values": list(values),
                        "free_bytes": list(free),
                        "middle_delta": list(want),
                        "prelinear": pre_hit,
                        "output_transpose": out_hit,
                        "variable_cost": variable,
                        "total_gate_upper_bound": total,
                    }
                    if total < best_total:
                        best_total = total
                        best = [witness]
                        print(json.dumps({"NEW_BEST": witness}, sort_keys=True), flush=True)
                    elif total == best_total and len(best) < 200:
                        best.append(witness)
                    if total <= 101:
                        counts["candidates_101"] += 1
                        pair_hits += 1
                        print(json.dumps({"CANDIDATE_101": witness}, sort_keys=True), flush=True)

        pair_summaries.append({
            "front_id": front_id,
            "final_id": final_id,
            "minimum_support": min_support,
            "best_total_gate_upper_bound": None if pair_best == 10**9 else pair_best,
            "candidates_101": pair_hits,
        })

    summary = {
        "counts": counts,
        "best_total_gate_upper_bound": None if best_total == 10**9 else best_total,
        "best_witnesses_saved": len(best),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": (
            "complete for all score-35 pairs whenever considered correction supports have nullity <=2; "
            "supports above minimum+1 are rigorously excluded by the helper-frontier lower bound"
        ),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "pairs.json").write_text(json.dumps(pair_summaries, indent=2) + "\n")
    (out / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
