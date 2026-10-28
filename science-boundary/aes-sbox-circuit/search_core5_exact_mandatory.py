#!/usr/bin/env python3
"""Exact mandatory-form lower-bound screen for zero-preserving 5-AND core decompositions.

Unlike the beam searches, this retains every non-dominated physical witness through
four AND gates.  The fifth-AND layer is streamed and sharded.  For each complete
5-AND witness generating the live-102 nine-factor space, it counts distinct non-unit
linear source masks required either as AND operands or as one of the nine factor
outputs.

A 5-AND / 12-linear-gate core can have at most 12 such distinct masks, because every
non-unit required wire must be created by some linear gate.  Therefore a complete
minimum of >=13 rules out 17 gates within this *zero-preserving, five-AND* family.
It is not a lower bound for affine/XNOR five-AND circuits or six-AND 17-gate circuits.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import time

import search_core5_cost as base


def dominate_same_raw(states):
    """For identical raw AND wires, discard mandatory supersets safely."""
    by_raw = collections.defaultdict(list)
    for raw, mandatory, ops in states:
        by_raw[raw].append((raw, mandatory, ops))
    kept = []
    for raw, group in by_raw.items():
        group.sort(key=lambda s: (len(s[1]), tuple(sorted(s[1]))))
        minima = []
        for state in group:
            mandatory = state[1]
            if any(old[1].issubset(mandatory) for old in minima):
                continue
            minima = [old for old in minima if not mandatory.issubset(old[1])]
            minima.append(state)
        kept.extend(minima)
    return kept


def build_exact_depth4():
    states = {(): [((), frozenset(), ())]}
    pair_cache = {}
    log = []
    started = time.time()
    for depth in range(4):
        buckets = collections.defaultdict(dict)
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
                    if len(new_mandatory) > 12:
                        continue
                    state = (
                        raw_ands + (product,),
                        frozenset(new_mandatory),
                        ops + ((left, right),),
                    )
                    key = (state[0], state[1])
                    buckets[next_basis][key] = state
                    generated += 1

        states = {}
        for basis, bucket in buckets.items():
            states[basis] = dominate_same_raw(list(bucket.values()))
        row = {
            "depth": depth + 1,
            "nonlinear_spans": len(states),
            "witnesses": sum(len(x) for x in states.values()),
            "generated": generated,
            "mandatory_distribution": dict(sorted(collections.Counter(
                len(state[1]) for group in states.values() for state in group
            ).items())),
            "elapsed_seconds": round(time.time() - started, 3),
        }
        log.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    return states, pair_cache, log


def target_masks_after_fifth(coords4, product, target):
    # Final primitive basis is the eight current sources plus the fifth raw AND.
    if target in coords4:
        return coords4[target]
    shifted = target ^ product
    if shifted in coords4:
        return coords4[shifted] | (1 << 8)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not 0 <= args.shard < args.shards:
        raise SystemExit("bad shard")

    started = time.time()
    states, pair_cache, prefix_log = build_exact_depth4()
    minimum = 999
    min_count = 0
    hits = []
    processed_states = 0
    fifth_candidates = 0
    full_distribution = collections.Counter()

    serial = 0
    for nonlinear_basis in sorted(states):
        pairs = base.candidate_pairs(nonlinear_basis, pair_cache)
        for raw_ands, mandatory, ops in states[nonlinear_basis]:
            take = (serial % args.shards) == args.shard
            serial += 1
            if not take:
                continue
            processed_states += 1
            coords = base.coordinate_map(base.INPUTS + list(raw_ands))
            for u, v, product, next_basis in pairs:
                fifth_candidates += 1
                left, right = coords[u], coords[v]
                full = set(mandatory)
                if not base.is_unit(left):
                    full.add(left)
                if not base.is_unit(right):
                    full.add(right)
                if len(full) > 12 and minimum <= len(full):
                    # Targets can only add masks, so this candidate cannot improve
                    # the current minimum.  Still do not use this prune before the
                    # first complete candidate establishes a minimum.
                    continue
                target_masks = []
                valid = True
                for target in base.TARGETS:
                    mask = target_masks_after_fifth(coords, product, target)
                    if mask is None:
                        valid = False
                        break
                    target_masks.append(mask)
                    if not base.is_unit(mask):
                        full.add(mask)
                if not valid:
                    continue
                count = len(full)
                full_distribution[count] += 1
                if count < minimum:
                    minimum = count
                    min_count = 0
                    hits = []
                    print(json.dumps({"NEW_MINIMUM": count}), flush=True)
                if count == minimum:
                    min_count += 1
                if count <= 12 and len(hits) < 200:
                    all_ops = ops + ((left, right),)
                    closure_ok = False
                    closure_sequence = []
                    if count == 12:
                        closure_ok, closure_sequence = base.mandatory_closure_zero_helper(
                            all_ops, tuple(target_masks), frozenset(full)
                        )
                    hit = {
                        "mandatory_count": count,
                        "mandatory_masks": sorted(full),
                        "raw_ands": [f"0x{x:04x}" for x in raw_ands + (product,)],
                        "and_operands": [list(x) for x in all_ops],
                        "target_masks": target_masks,
                        "nonlinear_basis": [f"0x{x:04x}" for x in next_basis],
                        "zero_helper_closure": closure_ok,
                        "closure_sequence": [list(x) for x in closure_sequence],
                    }
                    hits.append(hit)
                    print(json.dumps({"HIT": hit}, sort_keys=True), flush=True)

    summary = {
        "shard": args.shard,
        "shards": args.shards,
        "exact_depth4_witnesses_total": serial,
        "processed_depth4_witnesses": processed_states,
        "fifth_candidates": fifth_candidates,
        "minimum_mandatory": None if minimum == 999 else minimum,
        "minimum_witness_count_seen": min_count,
        "hits_le_12_saved": len(hits),
        "complete_count_distribution_seen": dict(sorted(full_distribution.items())),
        "prefix_log": prefix_log,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "hits.json").write_text(json.dumps(hits, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
