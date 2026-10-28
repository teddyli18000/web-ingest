#!/usr/bin/env python3
"""Exact mandatory-form screen for affine/XNOR five-AND p008 core circuits.

This extends `search_core5_exact_mandatory.py` beyond zero-preserving internal
circuits.  The fixed 102 tail permits arbitrary values for the nine core factors at
core state 0000.  `prove_core5_rank5_completions.py` shows that 496/512 completion
patterns already need at least six ANDs; the remaining 16 patterns have nonlinear
quotient rank four.  This script handles one of those rank-4 patterns exactly.

Normalize every wire f to f' = f XOR f(0000), and track its phase f(0000)
separately.  XOR/XNOR both normalize to XOR, while an AND of actual affine operands
is evaluated exactly as a 16-bit truth table and then normalized again.  Thus
internal XNOR phases and complemented AND operands are fully represented.

For a physical state we remember the normalized raw AND outputs, their phases, and
the set of distinct non-free affine source forms that must exist as AND operands.
An affine form is encoded as (source-XOR mask, phase).  It is free exactly when it
is an existing source wire with its actual phase; every other distinct form needs
at least one linear XOR/XNOR gate.  For identical raw source wires/phases,
mandatory supersets are safely dominated.

After the fifth AND, the selected zero-state completion fixes each target's
normalized truth table and actual phase.  Target forms are added to the mandatory
set.  Therefore an exact minimum >=13 rules out `5 AND + 12 linear = 17` gates for
that completion pattern.  A <=12 hit is only a necessary-count witness and would
still need scheduling/closure synthesis before becoming a circuit.
"""
from __future__ import annotations

import argparse
import collections
import functools
import json
import pathlib
import time

import search_core5_cost as base

ONES = 0xFFFF
CARE_NONZERO = 0xFFFE
MAX_LINEAR = 12


def rank4_cases():
    cases = []
    for pattern in range(1 << 9):
        norms = tuple(
            base.TARGETS[i] ^ (CARE_NONZERO if ((pattern >> i) & 1) else 0)
            for i in range(9)
        )
        residues = tuple(base.STRIP[x] for x in norms)
        basis = base.canonical_basis(residues)
        if len(basis) == 4:
            cases.append((pattern, norms, basis))
    assert len(cases) == 16
    return cases


def affine_coordinate_map(normalized_sources):
    zero = base.coordinate_map(list(normalized_sources))
    out = {}
    for truth, mask in zero.items():
        out[truth] = (mask, 0)
        out[truth ^ ONES] = (mask, 1)
    assert len(out) == 2 * len(zero)
    return out


def source_index(unit_mask):
    return unit_mask.bit_length() - 1


def is_free_form(form, source_phases):
    mask, phase = form
    if not base.is_unit(mask):
        return False
    return phase == source_phases[source_index(mask)]


def add_required(mandatory, form, source_phases):
    if is_free_form(form, source_phases):
        return mandatory
    out = set(mandatory)
    out.add(form)
    return frozenset(out)


def dominate_same_sources(states):
    """For identical normalized/raw phased sources, keep mandatory-set minima."""
    by_sources = collections.defaultdict(list)
    for state in states:
        raw_norms, raw_phases, mandatory, ops = state
        by_sources[(raw_norms, raw_phases)].append(state)
    kept = []
    for _sources, group in by_sources.items():
        group.sort(key=lambda s: (len(s[2]), tuple(sorted(s[2]))))
        minima = []
        for state in group:
            mandatory = state[2]
            if any(old[2].issubset(mandatory) for old in minima):
                continue
            minima = [old for old in minima if not mandatory.issubset(old[2])]
            minima.append(state)
        kept.extend(minima)
    return kept


def candidate_pairs(nonlinear_basis, target_basis, cache):
    key = nonlinear_basis
    if key in cache:
        return cache[key]

    target_join = base.canonical_basis(nonlinear_basis + target_basis)
    if len(target_join) > 5:
        cache[key] = ()
        return ()
    allowed = set(base.span_values(target_join)) if len(target_join) == 5 else None

    function_space = base.span_values(
        base.canonical_basis(tuple(base.INPUTS) + nonlinear_basis + (ONES,))
    )
    out = []
    for i in range(1, len(function_space)):
        left = function_space[i]
        for j in range(i):
            right = function_space[j]
            product_actual = left & right
            residue = base.STRIP[product_actual]
            if not residue or not base.reduce_by_basis(residue, nonlinear_basis):
                continue
            if allowed is not None and residue not in allowed:
                continue
            next_basis = base.canonical_basis(nonlinear_basis + (residue,))
            if len(base.canonical_basis(next_basis + target_basis)) > 5:
                continue
            phase = product_actual & 1
            product_norm = product_actual ^ (ONES if phase else 0)
            out.append((left, right, product_norm, phase, next_basis))
    cache[key] = tuple(out)
    return cache[key]


def target_mask_after_fifth(coords4_zero, product_norm, target_norm):
    if target_norm in coords4_zero:
        return coords4_zero[target_norm]
    shifted = target_norm ^ product_norm
    if shifted in coords4_zero:
        return coords4_zero[shifted] | (1 << 8)
    return None


def build_exact_depth4(target_basis):
    # state = (raw normalized AND truths, raw phases, mandatory affine forms, ops)
    states = {(): [((), (), frozenset(), ())]}
    pair_cache = {}
    log = []
    started = time.time()

    for depth in range(4):
        buckets = collections.defaultdict(dict)
        generated = 0
        for nonlinear_basis, witnesses in states.items():
            pairs = candidate_pairs(nonlinear_basis, target_basis, pair_cache)
            for raw_norms, raw_phases, mandatory, ops in witnesses:
                normalized_sources = tuple(base.INPUTS) + raw_norms
                source_phases = (0, 0, 0, 0) + raw_phases
                coords = affine_coordinate_map(normalized_sources)
                for left_truth, right_truth, product_norm, product_phase, next_basis in pairs:
                    left_form = coords[left_truth]
                    right_form = coords[right_truth]
                    full = add_required(mandatory, left_form, source_phases)
                    full = add_required(full, right_form, source_phases)
                    if len(full) > MAX_LINEAR:
                        continue
                    state = (
                        raw_norms + (product_norm,),
                        raw_phases + (product_phase,),
                        full,
                        ops + ((left_form, right_form),),
                    )
                    key = (state[0], state[1], state[2])
                    buckets[next_basis][key] = state
                    generated += 1

        states = {}
        for basis, bucket in buckets.items():
            states[basis] = dominate_same_sources(list(bucket.values()))
        row = {
            "depth": depth + 1,
            "nonlinear_spans": len(states),
            "witnesses": sum(len(x) for x in states.values()),
            "generated": generated,
            "mandatory_distribution": dict(sorted(collections.Counter(
                len(state[2]) for group in states.values() for state in group
            ).items())),
            "pair_cache_entries": len(pair_cache),
            "elapsed_seconds": round(time.time() - started, 3),
        }
        log.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
    return states, pair_cache, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int, required=True, choices=range(16))
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not 0 <= args.shard < args.shards:
        raise SystemExit("bad shard")

    pattern, target_norms, target_basis = rank4_cases()[args.case]
    target_phases = tuple((pattern >> i) & 1 for i in range(9))

    started = time.time()
    states, pair_cache, prefix_log = build_exact_depth4(target_basis)
    minimum = 999
    min_count = 0
    hits = []
    processed_states = 0
    fifth_candidates = 0
    complete_distribution = collections.Counter()

    serial = 0
    for nonlinear_basis in sorted(states):
        pairs = candidate_pairs(nonlinear_basis, target_basis, pair_cache)
        for raw_norms, raw_phases, mandatory, ops in states[nonlinear_basis]:
            take = (serial % args.shards) == args.shard
            serial += 1
            if not take:
                continue
            processed_states += 1
            normalized_sources = tuple(base.INPUTS) + raw_norms
            source_phases4 = (0, 0, 0, 0) + raw_phases
            coords_affine = affine_coordinate_map(normalized_sources)
            coords_zero = base.coordinate_map(list(normalized_sources))

            for left_truth, right_truth, product_norm, product_phase, next_basis in pairs:
                fifth_candidates += 1
                left_form = coords_affine[left_truth]
                right_form = coords_affine[right_truth]
                full = add_required(mandatory, left_form, source_phases4)
                full = add_required(full, right_form, source_phases4)
                if len(full) > MAX_LINEAR and minimum <= len(full):
                    continue

                source_phases5 = source_phases4 + (product_phase,)
                target_forms = []
                valid = True
                for target_norm, target_phase in zip(target_norms, target_phases):
                    mask = target_mask_after_fifth(coords_zero, product_norm, target_norm)
                    if mask is None:
                        valid = False
                        break
                    form = (mask, target_phase)
                    target_forms.append(form)
                    full = add_required(full, form, source_phases5)
                if not valid:
                    continue

                count = len(full)
                complete_distribution[count] += 1
                if count < minimum:
                    minimum = count
                    min_count = 0
                    hits = []
                    print(json.dumps({"NEW_MINIMUM": count}), flush=True)
                if count == minimum:
                    min_count += 1
                if count <= MAX_LINEAR and len(hits) < 200:
                    hit = {
                        "mandatory_count": count,
                        "mandatory_forms": [list(x) for x in sorted(full)],
                        "raw_norms": [f"0x{x:04x}" for x in raw_norms + (product_norm,)],
                        "raw_phases": list(raw_phases + (product_phase,)),
                        "and_operand_forms": [
                            [[a[0], a[1]], [b[0], b[1]]]
                            for a, b in ops + ((left_form, right_form),)
                        ],
                        "target_forms": [list(x) for x in target_forms],
                        "nonlinear_basis": [f"0x{x:04x}" for x in next_basis],
                    }
                    hits.append(hit)
                    print(json.dumps({"HIT": hit}, sort_keys=True), flush=True)

    summary = {
        "case": args.case,
        "completion_pattern": pattern,
        "completion_pattern_binary": f"{pattern:09b}",
        "shard": args.shard,
        "shards": args.shards,
        "exact_depth4_witnesses_total": serial,
        "processed_depth4_witnesses": processed_states,
        "fifth_candidates": fifth_candidates,
        "minimum_mandatory": None if minimum == 999 else minimum,
        "minimum_witness_count_seen": min_count,
        "hits_le_12_saved": len(hits),
        "complete_count_distribution_seen": dict(sorted(complete_distribution.items())),
        "prefix_log": prefix_log,
        "elapsed_seconds": round(time.time() - started, 3),
        "scope": (
            "exact mandatory-form lower bound for this rank-4 zero-state completion, "
            "including arbitrary internal affine/XNOR phases"
        ),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "hits.json").write_text(json.dumps(hits, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
