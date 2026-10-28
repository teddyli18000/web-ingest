#!/usr/bin/env python3
"""Complete rank-3/support-5 correction search for the retained-core p008 family.

`search_semilinear_support5.py` covers the 117 five-position supports whose middle
columns have rank four.  Exactly nine five-position supports have rank three.  For
those, the correction system (when consistent) has two free bytes z,w, so a naive
search would try 65536 assignments per support/orientation.

This script is complete while usually enumerating far fewer assignments.  For a
fixed orientation the 101 budget is

    prelinear + output_transpose <= 31             (support = 5),

so after exact output synthesis the prelinear budget determines how many *new
 distinct* correction masks can be introduced beyond the base plane operands and
primary inputs.  Write each of the five corrections as

    f_i(z,w) = base_i XOR alpha_i*z XOR beta_i*w.

If the five values use at most R new masks, where R is the remaining target-count
slack, then unless the number of distinct symbolic f_i expressions is already <=R,
at least one of the following must hold:

* f_i equals an already-free mask (input or base operand target), or
* f_i equals f_j for two non-identical symbolic expressions.

Each event fixes one of z, w, or z XOR w to one byte.  We enumerate the union of
all such one-equation families (256 points each), deduplicate, apply the exact
new-target-count test, then exact-synthesize the augmented prelinear target set.
If symbolic duplicate expressions alone make every assignment target-count
admissible, we explicitly enumerate all 65536 pairs.  Thus no target-count-feasible
rank-3/support-5 assignment is omitted.

A positive <=101 component witness still requires materialization into a full
certificate and independent + official verification.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_prelinear17 as lin
import search_plane_middle5 as mid
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


def parameterize_rank3(indices, want):
    columns = [mid.COLS[i] for i in indices]
    if rank(columns) != 3:
        return None

    kernel = [m for m in range(1, 1 << 5) if xor_columns(columns, m) == 0]
    assert len(kernel) == 3
    k1, k2 = kernel[0], kernel[1]
    assert k1 != k2 and (k1 ^ k2) in kernel

    base = [0] * 5
    for bit in range(8):
        rhs = sum((((want[j] >> bit) & 1) << j) for j in range(4))
        sols = [m for m in range(1 << 5) if xor_columns(columns, m) == rhs]
        if not sols:
            return None
        assert len(sols) == 4
        chosen = min(sols)
        for i in range(5):
            if (chosen >> i) & 1:
                base[i] |= 1 << bit

    coeff = [(((k1 >> i) & 1), ((k2 >> i) & 1)) for i in range(5)]
    # For the nine rank-3 physical supports every correction position depends on
    # at least one of the two free bytes.  Keep the assertion explicit so a later
    # change of the middle columns cannot silently invalidate event generation.
    assert all(a or b for a, b in coeff)
    return tuple(base), tuple(coeff)


def correction_values(base, coeff, z, w):
    return tuple(
        b ^ (z if a else 0) ^ (w if c else 0)
        for b, (a, c) in zip(base, coeff)
    )


def orientation_targets(planes, choices):
    targets = set()
    for pair, choice in zip(planes, choices):
        targets.update(outer.orient(pair, choice))
    return targets


def output_targets(outpairs, choices):
    targets = set()
    for pair, choice in zip(outpairs, choices):
        targets.update(outer.dual_columns(pair, choice))
    return targets


def add_equation(families, pair, rhs):
    """Add nontrivial byte equation alpha*z XOR beta*w = rhs."""
    a, b = pair
    if not (a or b):
        return
    families.setdefault((a, b), set()).add(rhs)


def candidate_pairs(base, coeff, free_masks, max_new):
    """Return a complete candidate set under the distinct-new-mask budget."""
    symbolic = set(zip(base, coeff))
    if max_new >= len(symbolic):
        # Symbolic duplicates alone can fit the target-count budget, so no event
        # need hold.  Enumerate the full affine solution family in this rare case.
        return range(1 << 16), True

    families = {}

    # Membership events f_i in free_masks.
    for b0, pair in zip(base, coeff):
        for value in free_masks:
            add_equation(families, pair, b0 ^ value)

    # Collision events f_i == f_j.  Identical symbolic expressions are automatic
    # and give no equation; non-identical expressions yield one of z=K, w=K,
    # z^w=K.
    for i in range(5):
        for j in range(i + 1, 5):
            pair = (coeff[i][0] ^ coeff[j][0], coeff[i][1] ^ coeff[j][1])
            rhs = base[i] ^ base[j]
            if pair == (0, 0):
                assert rhs != 0 or (base[i], coeff[i]) == (base[j], coeff[j])
                continue
            add_equation(families, pair, rhs)

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
                    w = z ^ rhs
                    marked[(z << 8) | w] = 1
    return (i for i, hit in enumerate(marked) if hit), False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--k", type=int, required=True, choices=range(8))
    ap.add_argument("--prefix", type=int, required=True, choices=range(9))
    ap.add_argument("--max-pre", type=int, default=19)
    ap.add_argument("--max-out", type=int, default=17)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    planes, outpairs, base_corrections = outer.transported_data(args.c, args.k)
    first, second = divmod(args.prefix, 3)
    support_sets = [
        inds for inds in itertools.combinations(range(9), 5)
        if rank([mid.COLS[i] for i in inds]) == 3
    ]
    assert len(support_sets) == 9

    started = time.time()
    counts = {
        "orientations": 0,
        "output_infeasible": 0,
        "base_pre_infeasible": 0,
        "support_sets": 0,
        "support_inconsistent": 0,
        "generated_pairs": 0,
        "full_pair_fallbacks": 0,
        "zero_assignment_component": 0,
        "new_target_pruned": 0,
        "duplicate_target_set": 0,
        "prelinear_infeasible": 0,
        "candidates_101": 0,
    }
    best_total = 10**9
    best = []

    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        counts["orientations"] += 1

        pre_base = orientation_targets(planes, choices)
        base_noninput = frozenset(pre_base - lin.INPUTS - {0})
        npre = len(base_noninput)
        out_base = output_targets(outpairs, choices)

        # Five middle injections leave pre + output_transpose <=31.
        out_cap = min(args.max_out, 31 - npre)
        if out_cap < 0:
            counts["output_infeasible"] += 1
            continue
        out_hit = outer.linear_min(out_base, out_cap)
        if out_hit is None:
            counts["output_infeasible"] += 1
            continue

        pre_cap = min(args.max_pre, 31 - out_hit["cost"])
        if npre > pre_cap:
            counts["base_pre_infeasible"] += 1
            continue
        base_pre_hit = outer.linear_min(pre_base, pre_cap)
        if base_pre_hit is None:
            counts["base_pre_infeasible"] += 1
            continue

        max_new = pre_cap - npre
        free_masks = frozenset(set(pre_base) | set(lin.INPUTS)) - {0}
        want = tuple(outer.desired_delta(planes, base_corrections, choices))
        seen_targets = set()
        exact_cache = {}

        for inds in support_sets:
            counts["support_sets"] += 1
            param = parameterize_rank3(inds, want)
            if param is None:
                counts["support_inconsistent"] += 1
                continue
            base, coeff = param
            pairs, full = candidate_pairs(base, coeff, free_masks, max_new)
            if full:
                counts["full_pair_fallbacks"] += 1

            for packed in pairs:
                counts["generated_pairs"] += 1
                z, w = packed >> 8, packed & 0xFF
                values = correction_values(base, coeff, z, w)
                if any(v == 0 for v in values):
                    counts["zero_assignment_component"] += 1
                    continue

                novel = set(values) - set(free_masks)
                if len(novel) > max_new:
                    counts["new_target_pruned"] += 1
                    continue

                targets = frozenset((set(pre_base) | set(values)) - lin.INPUTS - {0})
                if len(targets) > pre_cap:
                    counts["new_target_pruned"] += 1
                    continue
                if targets in seen_targets:
                    counts["duplicate_target_set"] += 1
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

                variable = pre_hit["cost"] + 5 + out_hit["cost"]
                total = 65 + variable
                witness = {
                    "c": args.c,
                    "k": args.k,
                    "orientations": list(choices),
                    "support_positions": list(inds),
                    "rank": 3,
                    "free_bytes": [z, w],
                    "correction_values": list(values),
                    "middle_delta": list(want),
                    "prelinear": pre_hit,
                    "output_transpose": out_hit,
                    "variable_cost": variable,
                    "total_gate_upper_bound": total,
                    "component_costs": {
                        "prelinear": pre_hit["cost"],
                        "first_and": 9,
                        "middle": 15,
                        "core": 18,
                        "final_and": 18,
                        "output": 10 + out_hit["cost"],
                    },
                }
                if total < best_total:
                    best_total = total
                    best = [witness]
                    print(json.dumps({"NEW_BEST": witness}, sort_keys=True), flush=True)
                elif total == best_total and len(best) < 200:
                    best.append(witness)
                if total <= 101:
                    counts["candidates_101"] += 1
                    print(json.dumps({"CANDIDATE_101": witness}, sort_keys=True), flush=True)

    summary = {
        "c": args.c,
        "k": args.k,
        "prefix": args.prefix,
        "counts": counts,
        "best_total_gate_upper_bound": None if best_total == 10**9 else best_total,
        "best_witnesses_saved": len(best),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": (
            "complete for rank-3 five-position correction supports at this transform/prefix, "
            "subject only to exact linear-synthesis routines used by search_semilinear_outer"
        ),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
