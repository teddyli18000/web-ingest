#!/usr/bin/env python3
"""Cost-aware search for a 5-AND / <=12-XOR realization of the live p008 core factors.

The nonlinear search is exact at the span level, but the physical-witness search is a
beam heuristic.  A state remembers actual raw AND truth tables and the set of distinct
non-unit linear forms that have become mandatory as AND operands.  States are grouped
by nonlinear span and only the cheapest `--beam` witnesses per span are retained.

All functions are four-variable 16-bit truth tables.  We restrict to zero-preserving
XOR/AND cores.  A successful witness with 5 AND + 12 XOR gates would replace the
current 18-gate / 6-AND core and yield a 101-gate AES S-box after splicing into the
live 102-gate construction.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import time

TARGET_NAMES = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]


def mobius16(x: int) -> int:
    x ^= (x & 0x5555) << 1
    x ^= (x & 0x3333) << 2
    x ^= (x & 0x0F0F) << 4
    x ^= (x & 0x00FF) << 8
    return x & 0xFFFF


def strip_linear_slow(x: int) -> int:
    anf = mobius16(x)
    anf &= ~0x0117 & 0xFFFF  # monomial masks 0,1,2,4,8
    return mobius16(anf)


STRIP = [strip_linear_slow(x) for x in range(1 << 16)]


def var(i: int) -> int:
    return sum((((x >> i) & 1) << x) for x in range(16))


INPUTS = [var(i) for i in range(4)]


def source_targets():
    a, b, c, d = INPUTS
    q42 = a & b
    q43 = q42 ^ c
    q44 = q43 & d
    q45 = b ^ q44
    q46 = q42 & c
    q47 = d ^ q46
    q48 = a & q47
    q49 = q43 ^ q48
    q50 = q48 ^ b
    q51 = q49 & q50
    q52 = q51 ^ a
    q53 = q52 ^ q49
    q54 = q45 & q53
    q55 = q54 ^ q47
    q56 = q55 ^ q49
    q57 = q53 ^ q45
    q58 = q56 ^ q57
    q59 = q55 ^ q45
    return [q45, q59, q52, q57, q53, q49, q58, q55, q56]


TARGETS = source_targets()
TARGET_RESIDUES = [STRIP[x] for x in TARGETS]


def canonical_basis(vectors):
    rows = [0] * 16
    for x in vectors:
        y = x
        for p in range(15, -1, -1):
            if not ((y >> p) & 1):
                continue
            if rows[p]:
                y ^= rows[p]
                continue
            for q in range(p - 1, -1, -1):
                if rows[q] and ((y >> q) & 1):
                    y ^= rows[q]
            p = y.bit_length() - 1
            for q in range(p + 1, 16):
                if rows[q] and ((rows[q] >> p) & 1):
                    rows[q] ^= y
            rows[p] = y
            break
    return tuple(x for x in rows if x)


def reduce_by_basis(x, basis):
    y = x
    for v in reversed(basis):
        if (y >> (v.bit_length() - 1)) & 1:
            y ^= v
    return y


def span_values(basis):
    values = [0]
    for v in basis:
        values += [x ^ v for x in values]
    return values


TARGET_BASIS = canonical_basis(TARGET_RESIDUES)
LINEAR_BASIS = canonical_basis(INPUTS)


def coordinate_map(sources):
    pairs = [(0, 0)]
    for i, value in enumerate(sources):
        old = pairs[:]
        pairs += [(truth ^ value, mask | (1 << i)) for truth, mask in old]
    return dict(pairs)


def is_unit(mask):
    return mask > 0 and (mask & (mask - 1)) == 0


def candidate_pairs(nonlinear_basis, cache):
    if nonlinear_basis in cache:
        return cache[nonlinear_basis]

    target_join = canonical_basis(nonlinear_basis + TARGET_BASIS)
    allowed = set(span_values(target_join)) if len(target_join) == 5 else None
    function_space = span_values(canonical_basis(LINEAR_BASIS + nonlinear_basis))
    out = []
    for i in range(1, len(function_space)):
        u = function_space[i]
        for j in range(1, i):
            v = function_space[j]
            product = u & v
            residue = STRIP[product]
            if not residue or not reduce_by_basis(residue, nonlinear_basis):
                continue
            if allowed is not None and residue not in allowed:
                continue
            next_basis = canonical_basis(nonlinear_basis + (residue,))
            out.append((u, v, product, next_basis))
    cache[nonlinear_basis] = out
    return out


def stable_tie(raw_ands, mandatory, seed):
    h = (0x9E3779B97F4A7C15 ^ seed) & ((1 << 64) - 1)
    for x in raw_ands:
        h ^= (x + 0x9E3779B97F4A7C15 + ((h << 6) & ((1 << 64) - 1)) + (h >> 2)) & ((1 << 64) - 1)
    for x in sorted(mandatory):
        h ^= (x * 0x100000001B3) & ((1 << 64) - 1)
        h = ((h << 13) | (h >> 51)) & ((1 << 64) - 1)
    return h


def state_score(state, seed):
    raw_ands, mandatory, _ops = state
    return (
        len(mandatory),
        sum(x.bit_count() for x in mandatory),
        stable_tie(raw_ands, mandatory, seed),
    )


def prune_bucket(states, beam, seed):
    # Exact duplicates are useless.  Keep the cheapest witnesses while retaining
    # tie diversity through a seed-dependent deterministic hash.
    unique = {}
    for state in states:
        unique[(state[0], state[1])] = state
    values = list(unique.values())
    values.sort(key=lambda s: state_score(s, seed))
    return values[:beam]


def mandatory_closure_zero_helper(ops, target_masks, mandatory):
    """Check exact one-gate-per-mandatory-form realizability (no helper-only XORs)."""
    available = {1 << i for i in range(4)}
    remaining = set(mandatory)
    sequence = []

    def close_allowed(current_source_count):
        changed = True
        while changed:
            changed = False
            for target in sorted(remaining):
                if target >> current_source_count:
                    continue
                found = None
                av = sorted(available)
                for i, a in enumerate(av):
                    for b in av[i + 1 :]:
                        if (a ^ b) == target:
                            found = (a, b)
                            break
                    if found:
                        break
                if found:
                    available.add(target)
                    remaining.remove(target)
                    sequence.append(("XOR", found[0], found[1], target))
                    changed = True
                    break

    for gate_i, (left, right) in enumerate(ops):
        close_allowed(4 + gate_i)
        if left not in available or right not in available:
            return False, sequence
        new_unit = 1 << (4 + gate_i)
        available.add(new_unit)
        sequence.append(("AND", left, right, new_unit))
    close_allowed(9)
    if any(mask not in available for mask in target_masks):
        return False, sequence
    return not remaining, sequence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--beam", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--bucket-factor", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    del rng  # tie diversity is deterministic through `seed`; no global hash dependence.

    # state = (raw AND truth tables, mandatory non-unit source masks, AND operand masks)
    states = {(): [((), frozenset(), ())]}
    pair_cache = {}
    log = []
    started = time.time()

    for depth in range(5):
        buckets = collections.defaultdict(list)
        generated = 0
        for nonlinear_basis, witnesses in states.items():
            pairs = candidate_pairs(nonlinear_basis, pair_cache)
            for raw_ands, mandatory, ops in witnesses:
                coords = coordinate_map(INPUTS + list(raw_ands))
                for u, v, product, next_basis in pairs:
                    left, right = coords[u], coords[v]
                    new_mandatory = set(mandatory)
                    if not is_unit(left):
                        new_mandatory.add(left)
                    if not is_unit(right):
                        new_mandatory.add(right)
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
                    if len(bucket) >= max(args.beam * args.bucket_factor, args.beam + 1):
                        buckets[next_basis] = prune_bucket(bucket, args.beam, args.seed + depth)

        states = {
            basis: prune_bucket(bucket, args.beam, args.seed + depth)
            for basis, bucket in buckets.items()
        }
        mand_dist = collections.Counter(
            len(state[1]) for bucket in states.values() for state in bucket
        )
        row = {
            "depth": depth + 1,
            "nonlinear_spans": len(states),
            "witnesses": sum(len(x) for x in states.values()),
            "generated": generated,
            "mandatory_distribution": dict(sorted(mand_dist.items())),
            "elapsed_seconds": round(time.time() - started, 3),
        }
        log.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    candidates = []
    for nonlinear_basis, witnesses in states.items():
        for raw_ands, mandatory, ops in witnesses:
            coords = coordinate_map(INPUTS + list(raw_ands))
            if any(target not in coords for target in TARGETS):
                continue
            target_masks = tuple(coords[target] for target in TARGETS)
            full_mandatory = set(mandatory)
            for mask in target_masks:
                if not is_unit(mask):
                    full_mandatory.add(mask)
            if len(full_mandatory) > 12:
                continue
            closure_ok = False
            sequence = []
            if len(full_mandatory) == 12:
                closure_ok, sequence = mandatory_closure_zero_helper(
                    ops, target_masks, frozenset(full_mandatory)
                )
            candidate = {
                "mandatory_count": len(full_mandatory),
                "mandatory_masks": sorted(full_mandatory),
                "raw_ands": [f"0x{x:04x}" for x in raw_ands],
                "and_operands": [list(x) for x in ops],
                "target_masks": list(target_masks),
                "zero_helper_closure": closure_ok,
                "closure_sequence": [list(x) for x in sequence],
                "nonlinear_basis": [f"0x{x:04x}" for x in nonlinear_basis],
            }
            candidates.append(candidate)

    candidates.sort(key=lambda x: (x["mandatory_count"], not x["zero_helper_closure"], x["mandatory_masks"]))
    summary = {
        "seed": args.seed,
        "beam": args.beam,
        "target_residues": [f"0x{x:04x}" for x in TARGET_RESIDUES],
        "target_nonlinear_rank": len(TARGET_BASIS),
        "level_log": log,
        "candidate_count_le_12": len(candidates),
        "mandatory_count_distribution": dict(sorted(collections.Counter(x["mandatory_count"] for x in candidates).items())),
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
