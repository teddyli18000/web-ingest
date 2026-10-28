#!/usr/bin/env python3
"""Exact mandatory-form screen for rank-5 ODC completions in a six-AND p008 core.

The merged 102-gate AES circuit falls to 101 if its fixed four-input/nine-factor
18-gate core is replaced by 17 gates.  In the 6-AND + 11-linear case, consider
zero-state completions whose nine normalized targets have nonlinear quotient rank
five.  Exhaustion of all 512 completions shows that 496 of them share one common
five-dimensional target space U.

Every possible first-AND nonlinear class is outside U.  Therefore, in the
quotient-rank-six case, the first AND uniquely fixes the final six-dimensional
envelope E = span(U, r0).  There are exactly 35 such envelopes.

For one first-class index this script exactly enumerates physical affine/XNOR
states whose six independent AND classes stay in E.  It tracks normalized raw AND
truth tables, their zero-state phases, and every distinct non-free affine source
form that must be materialized for AND operands.  A safe optimistic lower bound on
remaining target materialization prunes states that cannot fit in 11 linear gates.
After the sixth AND, all 496 rank-five completion patterns are tested exactly.

`--prefix-shard/--prefix-shards` partitions the complete depth-two physical
frontier.  Distinct depth-two states never merge after that point, so all shards
together are a disjoint complete search for the selected first class.

A completed shard with `hits_le_11 == 0` is an exclusion for that shard.  Timeouts
or cancelled jobs are not exclusions.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import time

import search_core5_affine_mandatory as affine
import search_core5_cost as base

ONES = 0xFFFF
CARE_NONZERO = 0xFFFE
MAX_LINEAR = 11


def rank5_space_and_patterns():
    by_space = collections.defaultdict(list)
    for pattern in range(1 << 9):
        norms = tuple(
            base.TARGETS[i] ^ (CARE_NONZERO if ((pattern >> i) & 1) else 0)
            for i in range(9)
        )
        basis = base.canonical_basis(tuple(base.STRIP[x] for x in norms))
        by_space[basis].append(pattern)
    rank5 = [(basis, pats) for basis, pats in by_space.items() if len(basis) == 5]
    assert len(rank5) == 1
    basis, patterns = rank5[0]
    assert len(patterns) == 496
    return basis, tuple(patterns)


TARGET5, RANK5_PATTERNS = rank5_space_and_patterns()


def first_classes():
    function_space = base.span_values(base.LINEAR_BASIS)
    residues = set()
    for i in range(1, len(function_space)):
        for j in range(i):
            residue = base.STRIP[function_space[i] & function_space[j]]
            if residue:
                residues.add(residue)
    out = tuple(sorted(residues))
    assert len(out) == 35
    assert all(base.reduce_by_basis(r, TARGET5) for r in out)
    return out


FIRST_CLASSES = first_classes()


def candidate_pairs(nonlinear_basis, envelope_values, cache):
    if nonlinear_basis in cache:
        return cache[nonlinear_basis]
    function_space = base.span_values(
        base.canonical_basis(tuple(base.INPUTS) + nonlinear_basis + (ONES,))
    )
    out = []
    for i in range(1, len(function_space)):
        left = function_space[i]
        for j in range(i):
            right = function_space[j]
            actual = left & right
            residue = base.STRIP[actual]
            if not residue or not base.reduce_by_basis(residue, nonlinear_basis):
                continue
            if residue not in envelope_values:
                continue
            next_basis = base.canonical_basis(nonlinear_basis + (residue,))
            if len(next_basis) != len(nonlinear_basis) + 1:
                continue
            phase = actual & 1
            normalized = actual ^ (ONES if phase else 0)
            out.append((left, right, normalized, phase, next_basis, residue))
    cache[nonlinear_basis] = tuple(out)
    return cache[nonlinear_basis]


def dominate_mandatory(sets):
    values = sorted(set(sets), key=lambda s: (len(s), tuple(sorted(s))))
    minima = []
    for mandatory in values:
        if any(old.issubset(mandatory) for old in minima):
            continue
        minima = [old for old in minima if not mandatory.issubset(old)]
        minima.append(mandatory)
    return minima


def optimistic_linear_lower_bound(raw_norms, raw_phases, mandatory, nonlinear_basis):
    """Safe lower bound on final distinct linear forms.

    A target already equal to a source wire, or already equal to a mandatory form,
    adds no new gate.  Every other target costs at least one distinct linear form
    unless a future independent AND itself becomes that target.  Since all rank-5
    completion target residues lie in U, at most dim(span(B,U))-dim(B) such targets
    can become future raw AND sources.
    """
    sources = tuple(base.INPUTS) + raw_norms
    source_phases = (0, 0, 0, 0) + raw_phases
    coords = base.coordinate_map(list(sources))

    additions = 0
    for target in base.TARGETS:
        covered = False
        for phase in (0, 1):
            normalized = target ^ (CARE_NONZERO if phase else 0)
            mask = coords.get(normalized)
            if mask is None:
                continue
            form = (mask, phase)
            if affine.is_free_form(form, source_phases) or form in mandatory:
                covered = True
                break
        if not covered:
            additions += 1

    join_rank = len(base.canonical_basis(nonlinear_basis + TARGET5))
    future_raw_targets = max(0, join_rank - len(nonlinear_basis))
    return len(mandatory) + max(0, additions - future_raw_targets)


def advance(states, depth, first_residue, envelope_values, pair_cache):
    # basis -> {(raw_norms, raw_phases): [minimal mandatory sets]}
    buckets = collections.defaultdict(lambda: collections.defaultdict(list))
    generated = 0
    for nonlinear_basis, source_groups in states.items():
        pairs = candidate_pairs(nonlinear_basis, envelope_values, pair_cache)
        for (raw_norms, raw_phases), mandatory_sets in source_groups.items():
            normalized_sources = tuple(base.INPUTS) + raw_norms
            source_phases = (0, 0, 0, 0) + raw_phases
            coords = affine.affine_coordinate_map(normalized_sources)
            for left, right, product_norm, product_phase, next_basis, residue in pairs:
                if depth == 0 and residue != first_residue:
                    continue
                left_form = coords[left]
                right_form = coords[right]
                for mandatory in mandatory_sets:
                    full = affine.add_required(mandatory, left_form, source_phases)
                    full = affine.add_required(full, right_form, source_phases)
                    if len(full) > MAX_LINEAR:
                        continue
                    next_raws = raw_norms + (product_norm,)
                    next_phases = raw_phases + (product_phase,)
                    if optimistic_linear_lower_bound(next_raws, next_phases, full, next_basis) > MAX_LINEAR:
                        continue
                    buckets[next_basis][(next_raws, next_phases)].append(full)
                    generated += 1

    out = {}
    for basis, source_groups in buckets.items():
        out[basis] = {
            key: dominate_mandatory(values)
            for key, values in source_groups.items()
        }
    return out, generated


def shard_depth2(states, shard, shards):
    flat = []
    for basis in sorted(states):
        for key in sorted(states[basis]):
            for mandatory in states[basis][key]:
                flat.append((basis, key, mandatory))
    selected = [row for i, row in enumerate(flat) if (i % shards) == shard]
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for basis, key, mandatory in selected:
        out[basis][key].append(mandatory)
    return {
        basis: {key: dominate_mandatory(values) for key, values in groups.items()}
        for basis, groups in out.items()
    }, len(flat), len(selected)


def final_minimum(states, envelope):
    best = 999
    hit_count = 0
    first_hit = None
    groups = states.get(envelope, {})
    for (raw_norms, raw_phases), mandatory_sets in groups.items():
        normalized_sources = tuple(base.INPUTS) + raw_norms
        source_phases = (0, 0, 0, 0) + raw_phases
        coords = base.coordinate_map(list(normalized_sources))
        target_forms = []
        for target in base.TARGETS:
            options = {}
            for phase in (0, 1):
                normalized = target ^ (CARE_NONZERO if phase else 0)
                mask = coords.get(normalized)
                if mask is not None:
                    options[phase] = (mask, phase)
            target_forms.append(options)
        if any(not options for options in target_forms):
            continue

        for mandatory in mandatory_sets:
            for pattern in RANK5_PATTERNS:
                full = set(mandatory)
                valid = True
                for i, options in enumerate(target_forms):
                    phase = (pattern >> i) & 1
                    form = options.get(phase)
                    if form is None:
                        valid = False
                        break
                    if not affine.is_free_form(form, source_phases):
                        full.add(form)
                    if len(full) > MAX_LINEAR:
                        valid = False
                        break
                if not valid:
                    continue
                count = len(full)
                best = min(best, count)
                if count <= MAX_LINEAR:
                    hit_count += 1
                    if first_hit is None:
                        first_hit = {
                            "completion_pattern": pattern,
                            "completion_pattern_binary": f"{pattern:09b}",
                            "mandatory_count": count,
                            "raw_norms": [f"0x{x:04x}" for x in raw_norms],
                            "raw_phases": list(raw_phases),
                            "mandatory_forms": [list(x) for x in sorted(full)],
                        }
    return (None if best == 999 else best), hit_count, first_hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-index", type=int, required=True, choices=range(35))
    ap.add_argument("--prefix-shard", type=int, default=0)
    ap.add_argument("--prefix-shards", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not 0 <= args.prefix_shard < args.prefix_shards:
        raise SystemExit("bad prefix shard")

    started = time.time()
    first_residue = FIRST_CLASSES[args.first_index]
    envelope = base.canonical_basis(TARGET5 + (first_residue,))
    assert len(envelope) == 6
    envelope_values = set(base.span_values(envelope))
    pair_cache = {}

    states = {(): {((), ()): [frozenset()]}}
    log = []
    depth2_total = depth2_selected = None
    for depth in range(6):
        states, generated = advance(
            states, depth, first_residue, envelope_values, pair_cache
        )
        if depth == 1 and args.prefix_shards > 1:
            states, depth2_total, depth2_selected = shard_depth2(
                states, args.prefix_shard, args.prefix_shards
            )
        row = {
            "depth": depth + 1,
            "nonlinear_bases": len(states),
            "source_tuples": sum(len(g) for g in states.values()),
            "physical_states": sum(
                len(ms) for g in states.values() for ms in g.values()
            ),
            "generated": generated,
            "elapsed_seconds": round(time.time() - started, 3),
        }
        log.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        if not states:
            break

    minimum, hits, first_hit = final_minimum(states, envelope)
    summary = {
        "first_index": args.first_index,
        "first_residue": f"0x{first_residue:04x}",
        "envelope": [f"0x{x:04x}" for x in envelope],
        "rank5_completion_patterns": len(RANK5_PATTERNS),
        "prefix_shard": args.prefix_shard,
        "prefix_shards": args.prefix_shards,
        "depth2_physical_states_total": depth2_total,
        "depth2_physical_states_selected": depth2_selected,
        "minimum_mandatory": minimum,
        "hits_le_11": hits,
        "frontier_empty": not states,
        "level_log": log,
        "elapsed_seconds": round(time.time() - started, 3),
        "scope": (
            "exact mandatory-form screen for quotient-rank-six, six-AND cores "
            "over all 496 rank-five zero-state completions in the selected first-AND envelope"
        ),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "first_hit.json").write_text(json.dumps(first_hit, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
