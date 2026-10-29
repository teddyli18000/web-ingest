#!/usr/bin/env python3
"""Exclude the global-LB31 tip of the jointly decoupled live plane family.

`screen_joint_decoupled_lb.py` reduces all 3^18 independent front/final plane
choices at the live field transform to a rigorous cheap lower-bound frontier.  The
global minimum is variable-cost LB=31 and is attained by exactly twelve front
vectors.  For every one of those twelve, the minimizing final vector is unique and
equal to the front vector, with component target counts

    pre-union targets = 15,
    abstract middle support = 3,
    output targets = 13.

This script restores the exact correction byte values on the unique three-position
middle support.  They add three distinct prelinear targets, so the unavoidable
physical target counts become

    prelinear targets = 18,
    middle support = 3,
    output targets = 13,

for a base variable cost of 34.  A 101-gate circuit has variable budget 36, hence
at most TWO helper-only XOR/XNOR gates may be used across the prelinear and output
networks combined.

Using the exact helper-closure linear synthesizer already used throughout the p008
workspace, we prove that for every one of the twelve cases BOTH the prelinear and
output target sets individually fail with <=2 helper gates.  Thus each case already
needs at least 3 helper gates in either network, and no LB31 joint-decoupled pair can
reach 101.
"""
from __future__ import annotations

import json

import scan_semilinear_frontier as frontier
import screen_joint_decoupled_lb as joint
import search_plane_prelinear17 as lin
import search_semilinear_exactcorr as exactcorr
import search_semilinear_outer as outer


def noninput_targets(values):
    return frozenset(set(values) - lin.INPUTS - {0})


def exact_linear_feasible_with_helpers(targets, helpers):
    targets = noninput_targets(targets)
    ok, helper_wires, sequence = lin.feasible(targets, helpers)
    return {
        "ok": bool(ok),
        "target_count": len(targets),
        "helper_budget": helpers,
        "helper_wires": list(helper_wires),
        "sequence": [list(x) for x in sequence],
    }


def main():
    planes, outpairs, corrections = outer.transported_data(joint.LIVE_C, joint.LIVE_K)
    local = joint.local_union_costs(planes)

    output_counts = []
    for choices in joint.CHOICES:
        targets = joint.target_set(outpairs, choices, dual=True)
        output_counts.append(len(targets - lin.INPUTS - {0}))
    h = joint.minplus_over_final(output_counts, local)

    cases = []
    for fi, front_choices in enumerate(joint.CHOICES):
        delta = outer.desired_delta(planes, corrections, front_choices)
        support, positions = frontier.middle_support_lb(delta)
        lb = support + h[fi]
        if lb != 31:
            continue

        best_finals = joint.recover_best_finals(
            front_choices, h[fi], output_counts, local
        )
        assert len(best_finals) == 1
        final_choices = tuple(best_finals[0]["final_orientations"])
        assert final_choices == front_choices
        assert support == 3

        correction_values = exactcorr.unique_corrections_for_support(positions, delta)
        assert correction_values is not None
        assert len(correction_values) == 3 and all(correction_values)

        pre_targets = joint.target_set(planes, front_choices, dual=False)
        # front==final at the global optimum, so the union adds no extra operands.
        pre_targets.update(correction_values)
        out_targets = joint.target_set(outpairs, final_choices, dual=True)

        pre_noninput = noninput_targets(pre_targets)
        out_noninput = noninput_targets(out_targets)
        assert len(pre_noninput) == 18
        assert len(out_noninput) == 13
        assert len(pre_noninput) + support + len(out_noninput) == 34

        # 101 permits variable cost 36, hence only two helper gates beyond the 34
        # compulsory target/support gates.  Showing either network alone needs at
        # least three helpers is enough; both happen to do so in every case.
        pre2 = exact_linear_feasible_with_helpers(pre_noninput, 2)
        out2 = exact_linear_feasible_with_helpers(out_noninput, 2)
        assert not pre2["ok"]
        assert not out2["ok"]

        row = {
            "front_orientations": list(front_choices),
            "final_orientations": list(final_choices),
            "support_positions": list(positions),
            "correction_values": list(correction_values),
            "pre_target_count": len(pre_noninput),
            "output_target_count": len(out_noninput),
            "middle_support": support,
            "compulsory_variable_gates": 34,
            "remaining_helper_budget_for_101": 2,
            "pre_feasible_with_2_helpers": pre2["ok"],
            "output_feasible_with_2_helpers": out2["ok"],
        }
        cases.append(row)
        print(json.dumps({"EXCLUDED": row}, sort_keys=True), flush=True)

    summary = {
        "global_lb31_cases": len(cases),
        "excluded": sum(
            (not row["pre_feasible_with_2_helpers"])
            or (not row["output_feasible_with_2_helpers"])
            for row in cases
        ),
        "both_networks_individually_need_at_least_3_helpers": sum(
            (not row["pre_feasible_with_2_helpers"])
            and (not row["output_feasible_with_2_helpers"])
            for row in cases
        ),
        "conclusion": (
            "all global-LB31 jointly decoupled front/final plane pairs at the live "
            "field transform are impossible within 101 gates"
        ),
    }
    assert summary == {
        "global_lb31_cases": 12,
        "excluded": 12,
        "both_networks_individually_need_at_least_3_helpers": 12,
        "conclusion": (
            "all global-LB31 jointly decoupled front/final plane pairs at the live "
            "field transform are impossible within 101 gates"
        ),
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
