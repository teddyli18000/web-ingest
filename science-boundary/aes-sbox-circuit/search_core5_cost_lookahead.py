#!/usr/bin/env python3
"""Target-aware beam variant of search_core5_cost.py.

The first four multiplicative levels are scored by already-mandatory operand forms.
At the fifth AND, where all nine live-102 target factors are representable, beam
ranking uses the *full* mandatory set including the target-output forms.  This fixes
the main myopia of the first cost beam without increasing the nonlinear search space.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import time

import search_core5_cost as base


def full_target_data(state):
    raw_ands, mandatory, ops = state
    coords = base.coordinate_map(base.INPUTS + list(raw_ands))
    if any(target not in coords for target in base.TARGETS):
        return None
    target_masks = tuple(coords[target] for target in base.TARGETS)
    full = set(mandatory)
    for mask in target_masks:
        if not base.is_unit(mask):
            full.add(mask)
    return target_masks, frozenset(full)


def target_score(state, seed):
    data = full_target_data(state)
    if data is None:
        return (999, 999, 999, 999)
    _targets, full = data
    raw, mandatory, _ops = state
    return (
        len(full),
        len(mandatory),
        sum(x.bit_count() for x in full),
        base.stable_tie(raw, full, seed),
    )


def prune(states, beam, seed, final=False):
    unique = {}
    for state in states:
        unique[(state[0], state[1])] = state
    values = list(unique.values())
    values.sort(key=(lambda s: target_score(s, seed)) if final else (lambda s: base.state_score(s, seed)))
    return values[:beam]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--beam", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--bucket-factor", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    states = {(): [((), frozenset(), ())]}
    pair_cache = {}
    log = []
    started = time.time()

    for depth in range(5):
        final = depth == 4
        buckets = collections.defaultdict(list)
        generated = 0
        for nonlinear_basis, witnesses in states.items():
            pairs = base.candidate_pairs(nonlinear_basis, pair_cache)
            for raw_ands, mandatory, ops in witnesses:
                coords = base.coordinate_map(base.INPUTS + list(raw_ands))
                for u, v, product, next_basis in pairs:
                    left, right = coords[u], coords[v]
                    new_mandatory = set(mandatory)
                    if not base.is_unit(left):
                        new_mandatory.add(left)
                    if not base.is_unit(right):
                        new_mandatory.add(right)
                    # Operand forms alone are a hard lower bound on linear gates.
                    if len(new_mandatory) > 12:
                        continue
                    state = (
                        raw_ands + (product,),
                        frozenset(new_mandatory),
                        ops + ((left, right),),
                    )
                    bucket = buckets[next_basis]
                    bucket.append(state)
                    generated += 1
                    threshold = max(args.beam * args.bucket_factor, args.beam + 1)
                    if len(bucket) >= threshold:
                        buckets[next_basis] = prune(
                            bucket, args.beam, args.seed + depth, final=final
                        )

        states = {
            basis: prune(bucket, args.beam, args.seed + depth, final=final)
            for basis, bucket in buckets.items()
        }
        operand_dist = collections.Counter(
            len(state[1]) for bucket in states.values() for state in bucket
        )
        row = {
            "depth": depth + 1,
            "nonlinear_spans": len(states),
            "witnesses": sum(len(x) for x in states.values()),
            "generated": generated,
            "operand_mandatory_distribution": dict(sorted(operand_dist.items())),
            "elapsed_seconds": round(time.time() - started, 3),
        }
        if final:
            full_counts = []
            for bucket in states.values():
                for state in bucket:
                    data = full_target_data(state)
                    if data:
                        full_counts.append(len(data[1]))
            row["full_mandatory_distribution"] = dict(
                sorted(collections.Counter(full_counts).items())
            )
            row["best_full_mandatory"] = min(full_counts) if full_counts else None
        log.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    candidates = []
    for nonlinear_basis, witnesses in states.items():
        for state in witnesses:
            raw_ands, mandatory, ops = state
            data = full_target_data(state)
            if data is None:
                continue
            target_masks, full_mandatory = data
            closure_ok = False
            sequence = []
            if len(full_mandatory) == 12:
                closure_ok, sequence = base.mandatory_closure_zero_helper(
                    ops, target_masks, full_mandatory
                )
            candidates.append({
                "mandatory_count": len(full_mandatory),
                "operand_mandatory_count": len(mandatory),
                "mandatory_masks": sorted(full_mandatory),
                "raw_ands": [f"0x{x:04x}" for x in raw_ands],
                "and_operands": [list(x) for x in ops],
                "target_masks": list(target_masks),
                "zero_helper_closure": closure_ok,
                "closure_sequence": [list(x) for x in sequence],
                "nonlinear_basis": [f"0x{x:04x}" for x in nonlinear_basis],
            })

    candidates.sort(key=lambda x: (
        x["mandatory_count"],
        not x["zero_helper_closure"],
        x["operand_mandatory_count"],
        x["mandatory_masks"],
    ))
    summary = {
        "seed": args.seed,
        "beam": args.beam,
        "target_residues": [f"0x{x:04x}" for x in base.TARGET_RESIDUES],
        "target_nonlinear_rank": len(base.TARGET_BASIS),
        "level_log": log,
        "best_full_mandatory": candidates[0]["mandatory_count"] if candidates else None,
        "candidate_count_le_12": sum(x["mandatory_count"] <= 12 for x in candidates),
        "full_mandatory_distribution": dict(sorted(collections.Counter(x["mandatory_count"] for x in candidates).items())),
        "zero_helper_closure_count": sum(x["zero_helper_closure"] for x in candidates),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "candidates.json").write_text(json.dumps(candidates[:200], indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
