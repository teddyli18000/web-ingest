#!/usr/bin/env python3
"""Rigorous cheap lower bound for jointly decoupled front/final product planes.

The merged-102 AES construction uses one ternary basis choice in each of nine
rank-two product planes both before the first nine norm ANDs and before the final
18 ANDs.  `search_decoupled_final_planes.py` already proves that changing only the
final choices cannot reach 101.  This program studies the genuinely broader family
in which the nine front choices `f` and nine final choices `g` are independent.

Naively this is 3^18 pairs.  At the live field transform the three nonzero forms
{a,b,a+b} belonging to different product planes are disjoint, so the number of
non-input prelinear operand targets in the union of front/final choices is a sum of
nine local ternary costs.  The final-output target count depends only on `g`, while
the abstract minimum middle correction support depends only on `f`.

For every front vector f we compute exactly

    min_g [ pre_union_target_count(f,g) + output_target_count(g) ]

by a nine-dimensional ternary min-plus transform in O(3^9 * 9 * 3), then add the
exact abstract middle-support lower bound for f.  This avoids enumerating 3^18.

The result is a rigorous *lower bound* only:
- distinct target counts underestimate exact two-input XOR/XNOR synthesis cost;
- middle correction values are allowed to be arbitrary byte masks and are not
  charged as additional prelinear targets.
Therefore an LB > 36 excludes a retained-18-core 101 circuit in this family, while
an LB <= 36 is only a survivor requiring exact synthesis.
"""
from __future__ import annotations

import collections
import itertools
import json
import pathlib

import scan_semilinear_frontier as frontier
import search_plane_prelinear17 as lin
import search_semilinear_outer as outer

LIVE_C = 0x1B
LIVE_K = 4
DIM = 9
CHOICES = tuple(itertools.product(range(3), repeat=DIM))
N = 3**DIM
STRIDES = tuple(3 ** (DIM - 1 - i) for i in range(DIM))


def target_set(pairs, choices, *, dual=False):
    out = set()
    for pair, choice in zip(pairs, choices):
        out.update(
            outer.dual_columns(pair, choice)
            if dual else outer.orient(pair, choice)
        )
    return out


def index_of(choices):
    return sum(value * stride for value, stride in zip(choices, STRIDES))


def choice_at(index):
    out = []
    for stride in STRIDES:
        out.append((index // stride) % 3)
    return tuple(out)


def local_union_costs(planes):
    """Per-plane non-input target counts for every (front,final) local choice."""
    triples = []
    matrices = []
    for pair in planes:
        a, b = pair
        triple = {a, b, a ^ b}
        assert len(triple) == 3
        triples.append(triple)
        matrix = []
        for front_choice in range(3):
            row = []
            for final_choice in range(3):
                targets = set(outer.orient(pair, front_choice))
                targets.update(outer.orient(pair, final_choice))
                row.append(len(targets - lin.INPUTS - {0}))
            matrix.append(tuple(row))
        matrices.append(tuple(matrix))

    # This is the key separability condition.  If convention changes ever make
    # two planes share a form, the min-plus decomposition would no longer be valid.
    for i in range(DIM):
        for j in range(i):
            assert triples[i].isdisjoint(triples[j]), (i, j, triples[i] & triples[j])
    assert len(set().union(*triples)) == 27
    return tuple(matrices)


def minplus_over_final(base_cost, local):
    """Return h[f] = min_g base_cost[g] + sum_i local[i][f_i][g_i]."""
    assert len(base_cost) == N
    h = list(base_cost)
    for axis, stride in enumerate(STRIDES):
        block = 3 * stride
        new = [10**9] * N
        matrix = local[axis]
        for block_start in range(0, N, block):
            for offset in range(stride):
                values = [h[block_start + y * stride + offset] for y in range(3)]
                for x in range(3):
                    new[block_start + x * stride + offset] = min(
                        values[y] + matrix[x][y] for y in range(3)
                    )
        h = new
    return h


def recover_best_finals(front_choices, wanted, output_counts, local):
    """Brute-force only the tiny global-best front set to make witnesses explicit."""
    hits = []
    for gi, final_choices in enumerate(CHOICES):
        pre_union = sum(
            local[i][front_choices[i]][final_choices[i]] for i in range(DIM)
        )
        value = pre_union + output_counts[gi]
        if value == wanted:
            hits.append({
                "final_orientations": list(final_choices),
                "pre_union_target_count": pre_union,
                "output_target_count": output_counts[gi],
            })
    return hits


def main():
    planes, outpairs, corrections = outer.transported_data(LIVE_C, LIVE_K)
    local = local_union_costs(planes)

    output_counts = []
    for choices in CHOICES:
        targets = target_set(outpairs, choices, dual=True)
        output_counts.append(len(targets - lin.INPUTS - {0}))

    h = minplus_over_final(output_counts, local)
    histogram = collections.Counter()
    support_histogram = collections.Counter()
    fronts_le_36 = []
    global_best = 10**9
    global_fronts = []

    for fi, front_choices in enumerate(CHOICES):
        delta = outer.desired_delta(planes, corrections, front_choices)
        support, positions = frontier.middle_support_lb(delta)
        support_histogram[support] += 1
        lb = support + h[fi]
        histogram[lb] += 1
        row = {
            "front_index": fi,
            "front_orientations": list(front_choices),
            "middle_support_lb": support,
            "middle_support_positions": list(positions),
            "best_pre_union_plus_output_target_count": h[fi],
            "variable_cost_lb": lb,
            "total_gate_lb": 65 + lb,
        }
        if lb <= 36:
            fronts_le_36.append(row)
        if lb < global_best:
            global_best = lb
            global_fronts = [row]
        elif lb == global_best:
            global_fronts.append(row)

    # The global-best set is small enough to recover every minimizing final vector
    # directly, providing an independently inspectable witness for the transform.
    global_pairs = []
    for row in global_fronts:
        front = tuple(row["front_orientations"])
        finals = recover_best_finals(
            front,
            row["best_pre_union_plus_output_target_count"],
            output_counts,
            local,
        )
        global_pairs.append({**row, "best_finals": finals})

    # Regression: the live coupled orientation is in the model and its cheap bound
    # is intentionally below the real 102 score because correction values/helper
    # wires are not fully charged here.
    zero = (0,) * DIM
    zero_i = index_of(zero)
    zero_support, _ = frontier.middle_support_lb(
        outer.desired_delta(planes, corrections, zero)
    )
    zero_lb = zero_support + h[zero_i]

    summary = {
        "front_vectors": N,
        "implicit_front_final_pairs": N * N,
        "plane_forms_pairwise_disjoint": True,
        "support_histogram": dict(sorted(support_histogram.items())),
        "joint_lb_histogram": dict(sorted(histogram.items())),
        "global_best_variable_cost_lb": global_best,
        "global_best_total_gate_lb": 65 + global_best,
        "global_best_fronts": len(global_fronts),
        "fronts_with_some_pair_lb_le_36": len(fronts_le_36),
        "live_zero_front_best_lb": zero_lb,
        "proof_scope": (
            "rigorous target-count plus abstract-middle-support lower bound for all "
            "3^18 jointly decoupled front/final plane choices at the live 0x1b*x^16 field transform"
        ),
    }

    # Reproducibility regressions from the complete live-family computation.
    assert summary["front_vectors"] == 19683
    assert summary["implicit_front_final_pairs"] == 387420489
    assert summary["support_histogram"] == {3: 324, 4: 19359}
    assert summary["joint_lb_histogram"] == {
        31: 12, 32: 1349, 33: 5260, 34: 7083, 35: 4450, 36: 1367, 37: 162
    }
    assert global_best == 31
    assert len(global_fronts) == 12
    assert len(fronts_le_36) == 19521
    # At all twelve global minima the minimizing final choice is unique and equals
    # the front choice: the new decoupling freedom does not create the LB=31 tip.
    assert all(
        len(row["best_finals"]) == 1
        and row["best_finals"][0]["final_orientations"] == row["front_orientations"]
        for row in global_pairs
    )

    print(json.dumps(summary, sort_keys=True))
    print(json.dumps({"GLOBAL_BEST_PAIRS": global_pairs}, sort_keys=True))

    out = pathlib.Path("science-boundary/aes-sbox-circuit/joint-decoupled-lb.json")
    out.write_text(json.dumps({
        "summary": summary,
        "global_best_pairs": global_pairs,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
