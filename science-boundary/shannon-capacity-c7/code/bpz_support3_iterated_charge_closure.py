#!/usr/bin/env python3
"""Repair/audit the first support-3 residual by iterated charge-overlap closure.

Let R be the 425 support<=2 outside factors with the certified owner-clique map
f, and E the four support-3 exceptions from the first minimal injection
obstruction.  For a regular product candidate q=(u,v), the product injection
charges q to m(q)=(f(u),f(v)).

The first residual kept every exception-containing candidate and regular pairs
whose charge cell lies in the exception footprint.  That reduction was unsound
because a retained regular candidate can touch the charge cell of an omitted
regular candidate outside the original footprint.

This script repairs the separation mechanically.  Starting from the original
retained set, it repeatedly adds every regular pair whose charge cell is touched
by the exact support rectangle of any currently retained candidate.  At the
fixed point, every omitted regular candidate has a charge cell outside the
entire retained footprint.  Hence in any independent set, omitted candidates
can again be injected into distinct core cells disjoint from all retained
support costs.

The script then computes an exact maximum-closure upper bound on the retained
family, ignoring all new-new conflicts.  If that upper bound is <=0, the full
(R union E)^2 family is rigorously closed at nonpositive raw core gain.  If it
is positive, the output identifies the repaired residual size and a selected
closure witness for a subsequent exact conflict-aware optimization.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

import bpz_joint_row_defects_maxsat as J
from bpz_support3_first_mus_residual_prize import (
    EXCEPTIONS,
    build_support2_assignment,
)
from bpz_amplify_row_defects import Dinic


def max_closure(cellsets):
    touched = sorted(set().union(*cellsets)) if cellsets else []
    bi = {p: i for i, p in enumerate(touched)}
    n, m = len(cellsets), len(touched)
    s, t = n + m, n + m + 1
    g = Dinic(t + 1)
    inf = n + m + 10
    for i, cells in enumerate(cellsets):
        g.add(s, i, 1)
        for c in cells:
            g.add(i, n + bi[c], inf)
    for j in range(m):
        g.add(n + j, t, 1)
    cut = g.flow(s, t)
    side = g.source_side(s)
    chosen = [i for i in range(n) if i in side]
    used = set()
    for i in chosen:
        used.update(cellsets[i])
    gain = len(chosen) - len(used)
    if gain != n - cut:
        raise RuntimeError(("closure-objective-drift", gain, n - cut))
    return gain, chosen, used, touched


def rect(su, sv):
    return tuple((a, b) for a in su for b in sv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    a = ap.parse_args()
    root = a.tan_root.resolve()

    _base, ring, B0, _fam = J.load_geometry(root)
    B = set(B0)
    regular, support, fmap = build_support2_assignment(ring, B)
    for z in EXCEPTIONS:
        support[z] = tuple(sorted(ring.NB[z] & B))
        if len(support[z]) != 3:
            raise RuntimeError(("exception-support", z, support[z]))
    factors = regular + list(EXCEPTIONS)

    # Original exception footprint and original residual.
    k0 = set()
    for e in EXCEPTIONS:
        for u in factors:
            k0.update(rect(support[e], support[u]))
            k0.update(rect(support[u], support[e]))

    exception_pairs = set()
    for e in EXCEPTIONS:
        for u in factors:
            exception_pairs.add((e, u))
            exception_pairs.add((u, e))

    retained_regular = set()
    for u in regular:
        fu = fmap[u]
        for v in regular:
            if (fu, fmap[v]) in k0:
                retained_regular.add((u, v))

    retained = set(exception_pairs) | retained_regular
    active = set()
    for u, v in retained:
        active.update(rect(support[u], support[v]))

    history = []
    iteration = 0
    while True:
        iteration += 1
        add = []
        for u in regular:
            fu = fmap[u]
            for v in regular:
                q = (u, v)
                if q in retained_regular:
                    continue
                if (fu, fmap[v]) in active:
                    add.append(q)
        if not add:
            history.append({
                "iteration": iteration,
                "new_regular_pairs": 0,
                "retained_candidates": len(retained),
                "active_core_cells": len(active),
            })
            break
        new_cells = set()
        for q in add:
            retained_regular.add(q)
            retained.add(q)
            new_cells.update(rect(support[q[0]], support[q[1]]))
        before = len(active)
        active.update(new_cells)
        history.append({
            "iteration": iteration,
            "new_regular_pairs": len(add),
            "retained_candidates": len(retained),
            "new_active_core_cells": len(active) - before,
            "active_core_cells": len(active),
        })

    # Fixed-point proof checks.
    omitted = []
    bad_charge = []
    for u in regular:
        fu = fmap[u]
        for v in regular:
            q = (u, v)
            if q in retained_regular:
                continue
            omitted.append(q)
            c = (fu, fmap[v])
            if c in active:
                bad_charge.append((q, c))
    if bad_charge:
        raise RuntimeError(("closure-not-fixed", bad_charge[:3]))

    candidates = sorted(retained)
    cellsets = [rect(support[u], support[v]) for u, v in candidates]
    gain, chosen_idx, used, touched = max_closure(cellsets)
    chosen = [candidates[i] for i in chosen_idx]

    out = {
        "method": "iterated-support3-charge-overlap-closure",
        "regular_factors": len(regular),
        "exceptions": list(EXCEPTIONS),
        "factor_universe": len(factors),
        "full_product_candidates": len(factors) * len(factors),
        "original_exception_footprint_cells": len(k0),
        "original_retained_candidates": len(exception_pairs | {
            (u, v) for u in regular for v in regular if (fmap[u], fmap[v]) in k0
        }),
        "iterations": history,
        "fixed_retained_candidates": len(candidates),
        "fixed_retained_regular_pairs": len(retained_regular),
        "fixed_omitted_regular_pairs": len(omitted),
        "fixed_active_core_cells": len(active),
        "omitted_charge_cells_disjoint_from_active": True,
        "closure_upper_gain": gain,
        "closure_selected": len(chosen),
        "closure_activated_core_cells": len(used),
        "closure_touched_core_cells": len(touched),
        "closed_nonpositive": gain <= 0,
    }
    if gain > 0:
        out["closure_selected_candidates"] = [list(q) for q in chosen]
        out["closure_activated_cells"] = [list(c) for c in sorted(used)]

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("closure_selected_candidates", "closure_activated_cells")}, sort_keys=True))


if __name__ == "__main__":
    main()
