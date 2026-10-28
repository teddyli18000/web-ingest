#!/usr/bin/env python3
"""ODC-aware affine beam search for a 5-AND / <=12-linear p008 core.

The fixed 102-gate tail observes all nine core factors on states 1..15 and does
not observe them at state 0.  Earlier cost beams searched only the exact,
zero-preserving target functions.  This search enumerates the 16 coherent
completions of four independent target factors at state 0 and allows affine
(complemented) AND operands, which models XNOR-generated constants without
making the nonlinear-span search fully gate-topological.

A witness is only a candidate.  `full_mandatory_count <= 12` is a necessary
linear-gate count bound, not sufficient unless `zero_helper_closure` is true.
Any candidate still needs exact gate scheduling and the full 101-gate splice
verification before it can support a record claim.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import time

import search_core5_cost as base

MASK16 = 0xFFFF
CONST_CODE = 1 << 9  # final coordinate system: 4 inputs + 5 AND outputs + constant
BASIS_TARGET_INDICES = (0, 1, 2, 3)


def completion_data(pattern: int):
    """Return the coherent care-class completion induced by four basis bits."""
    basis_truths = [
        base.TARGETS[i] ^ (1 if ((pattern >> j) & 1) else 0)
        for j, i in enumerate(BASIS_TARGET_INDICES)
    ]
    target_basis = base.canonical_basis(tuple(base.STRIP[x] for x in basis_truths))
    assert len(target_basis) == 4

    completed = []
    for target in base.TARGETS:
        hits = []
        for cand in (target, target ^ 1):
            if not base.reduce_by_basis(base.STRIP[cand], target_basis):
                hits.append(cand)
        # For this factor system each four-basis completion determines exactly
        # one completion of every other care-restricted factor.
        assert len(hits) == 1, (pattern, target, hits)
        completed.append(hits[0])
    return tuple(completed), target_basis


def affine_coordinate_map(sources):
    """Map each affine function to (source XOR mask, constant bit)."""
    pairs = [(0, 0)]
    for i, value in enumerate(sources):
        old = pairs[:]
        pairs += [(truth ^ value, mask | (1 << i)) for truth, mask in old]
    out = {}
    for truth, mask in pairs:
        out[truth] = (mask, 0)
        out[truth ^ MASK16] = (mask, 1)
    return out


def toggle_const(form, bit):
    mask, const = form
    return (mask, const ^ bit)


def is_free(form):
    mask, const = form
    return const == 0 and base.is_unit(mask)


def form_weight(form):
    mask, const = form
    return mask.bit_count() + const


def form_code(form):
    mask, const = form
    return mask | (CONST_CODE if const else 0)


def candidate_pairs(nonlinear_basis, target_basis, cache):
    key = (nonlinear_basis, target_basis)
    if key in cache:
        return cache[key]

    function_space = base.span_values(base.canonical_basis(base.LINEAR_BASIS + nonlinear_basis))
    out = []
    for i in range(1, len(function_space)):
        u = function_space[i]
        for j in range(1, i):
            v = function_space[j]
            for cu in (0, 1):
                uu = u ^ (MASK16 if cu else 0)
                for cv in (0, 1):
                    vv = v ^ (MASK16 if cv else 0)
                    product = uu & vv
                    residue = base.STRIP[product]
                    if not residue or not base.reduce_by_basis(residue, nonlinear_basis):
                        continue
                    next_basis = base.canonical_basis(nonlinear_basis + (residue,))
                    if len(next_basis) != len(nonlinear_basis) + 1:
                        continue
                    out.append((u, v, cu, cv, product, next_basis))
    cache[key] = out
    return out


def target_forms(state, completed_targets):
    raw_ands, _mandatory, _ops = state
    coords = affine_coordinate_map(base.INPUTS + list(raw_ands))
    forms = []
    for target in completed_targets:
        form = coords.get(target)
        if form is None:
            return None
        forms.append(form)
    return tuple(forms)


def full_target_data(state, completed_targets):
    forms = target_forms(state, completed_targets)
    if forms is None:
        return None
    raw, mandatory, _ops = state
    full = set(mandatory)
    for form in forms:
        if not is_free(form):
            full.add(form)
    return forms, frozenset(full)


def stable_tie(raw_ands, mandatory, seed):
    # Reuse the base deterministic mixer, encoding affine forms into small ints.
    encoded = frozenset(mask | (const << 12) for mask, const in mandatory)
    return base.stable_tie(raw_ands, encoded, seed)


def state_score(state, seed):
    raw, mandatory, _ops = state
    return (
        len(mandatory),
        sum(form_weight(x) for x in mandatory),
        stable_tie(raw, mandatory, seed),
    )


def target_score(state, completed_targets, seed):
    data = full_target_data(state, completed_targets)
    if data is None:
        return (999, 999, 999, 999)
    _forms, full = data
    raw, mandatory, _ops = state
    return (
        len(full),
        len(mandatory),
        sum(form_weight(x) for x in full),
        stable_tie(raw, full, seed),
    )


def prune(states, beam, seed, completed_targets=None):
    unique = {}
    for state in states:
        unique[(state[0], state[1])] = state
    values = list(unique.values())
    if completed_targets is None:
        values.sort(key=lambda s: state_score(s, seed))
    else:
        values.sort(key=lambda s: target_score(s, completed_targets, seed))
    return values[:beam]


def zero_helper_closure(ops, target_form_list, full_mandatory):
    """Complete test when every linear gate must materialize a mandatory form."""
    if len(full_mandatory) != 12:
        return False, []

    available = {1 << i for i in range(4)}
    remaining = {form_code(x) for x in full_mandatory}
    sequence = []

    def close_allowed(current_source_count):
        changed = True
        while changed:
            changed = False
            allowed_source_mask = (1 << current_source_count) - 1
            for target in sorted(remaining):
                source_part = target & ((1 << 9) - 1)
                if source_part & ~allowed_source_mask:
                    continue
                found = None
                av = sorted(available)
                for ii, a in enumerate(av):
                    for b in av[ii + 1 :]:
                        if (a ^ b) == target:
                            found = ("XOR", a, b)
                            break
                        if (a ^ b ^ CONST_CODE) == target:
                            found = ("XNOR", a, b)
                            break
                    if found:
                        break
                if found:
                    available.add(target)
                    remaining.remove(target)
                    sequence.append((found[0], found[1], found[2], target))
                    changed = True
                    break

    for gate_i, (left, right) in enumerate(ops):
        close_allowed(4 + gate_i)
        lc, rc = form_code(left), form_code(right)
        if lc not in available or rc not in available:
            return False, sequence
        new_unit = 1 << (4 + gate_i)
        available.add(new_unit)
        sequence.append(("AND", lc, rc, new_unit))

    close_allowed(9)
    if any(form_code(x) not in available for x in target_form_list):
        return False, sequence
    return not remaining, sequence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--completion", type=int, required=True, choices=range(16))
    ap.add_argument("--beam", type=int, default=16)
    ap.add_argument("--bucket-factor", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    completed_targets, target_basis = completion_data(args.completion)
    states = {(): [((), frozenset(), ())]}
    pair_cache = {}
    log = []
    started = time.time()

    for depth in range(5):
        final = depth == 4
        buckets = collections.defaultdict(list)
        generated = 0
        for nonlinear_basis, witnesses in states.items():
            pairs = candidate_pairs(nonlinear_basis, target_basis, pair_cache)
            for raw_ands, mandatory, ops in witnesses:
                coords = affine_coordinate_map(base.INPUTS + list(raw_ands))
                for u, v, cu, cv, product, next_basis in pairs:
                    # A remaining AND can add at most one new nonlinear dimension.
                    join = base.canonical_basis(next_basis + target_basis)
                    remaining_ands = 5 - (depth + 1)
                    if len(join) - len(next_basis) > remaining_ands:
                        continue

                    left0 = coords.get(u)
                    right0 = coords.get(v)
                    if left0 is None or right0 is None:
                        continue
                    left = toggle_const(left0, cu)
                    right = toggle_const(right0, cv)

                    new_mandatory = set(mandatory)
                    if not is_free(left):
                        new_mandatory.add(left)
                    if not is_free(right):
                        new_mandatory.add(right)
                    if len(new_mandatory) > 12:
                        continue

                    state = (
                        raw_ands + (product,),
                        frozenset(new_mandatory),
                        ops + ((left, right),),
                    )
                    buckets[next_basis].append(state)
                    generated += 1
                    threshold = max(args.beam * args.bucket_factor, args.beam + 1)
                    if len(buckets[next_basis]) >= threshold:
                        buckets[next_basis] = prune(
                            buckets[next_basis],
                            args.beam,
                            args.seed + depth,
                            completed_targets if final else None,
                        )

        states = {
            basis: prune(
                bucket,
                args.beam,
                args.seed + depth,
                completed_targets if final else None,
            )
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
            counts = []
            for bucket in states.values():
                for state in bucket:
                    data = full_target_data(state, completed_targets)
                    if data:
                        counts.append(len(data[1]))
            row["full_mandatory_distribution"] = dict(sorted(collections.Counter(counts).items()))
            row["best_full_mandatory"] = min(counts) if counts else None
        log.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    candidates = []
    for nonlinear_basis, witnesses in states.items():
        for state in witnesses:
            raw_ands, mandatory, ops = state
            data = full_target_data(state, completed_targets)
            if data is None:
                continue
            forms, full = data
            if len(full) > 12:
                continue
            closure_ok, closure_sequence = zero_helper_closure(ops, forms, full)
            candidates.append({
                "completion": args.completion,
                "completed_target_bit0": [x & 1 for x in completed_targets],
                "full_mandatory_count": len(full),
                "operand_mandatory_count": len(mandatory),
                "mandatory_forms": [[m, c] for m, c in sorted(full)],
                "raw_ands": [f"0x{x:04x}" for x in raw_ands],
                "and_operands": [[[m, c] for m, c in pair] for pair in ops],
                "target_forms": [[m, c] for m, c in forms],
                "zero_helper_closure": closure_ok,
                "closure_sequence": [list(x) for x in closure_sequence],
                "nonlinear_basis": [f"0x{x:04x}" for x in nonlinear_basis],
            })

    candidates.sort(key=lambda x: (
        x["full_mandatory_count"],
        not x["zero_helper_closure"],
        x["operand_mandatory_count"],
        x["mandatory_forms"],
    ))
    summary = {
        "completion": args.completion,
        "completed_target_bit0": [x & 1 for x in completed_targets],
        "target_basis": [f"0x{x:04x}" for x in target_basis],
        "beam": args.beam,
        "seed": args.seed,
        "level_log": log,
        "best_full_mandatory": candidates[0]["full_mandatory_count"] if candidates else None,
        "candidate_count_le_12": len(candidates),
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
