#!/usr/bin/env python3
"""Diagnose the two-point UNSAT core from the product-level support3 injection SAT.

Run 41233022940 returned the assumption core
  (1504,1285), (1504,1025).
For each point, enumerate its full exact support rectangle, the cells still
allowed under the frozen regularxregular injection, and every frozen product
point that blocks each disallowed cell.  This identifies the smallest local
recoloring neighborhood worth releasing next.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bpz_product_level_injection_sat import build_instance, product_conflict

CORE = ((1504, 1285), (1504, 1025))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    ring, B, regular, exceptions, support, fmap, groups, variable, allowed, no_allowed = build_instance(args.tan_root.resolve())
    vi = {p: i for i, p in enumerate(variable)}
    details = []
    release_union = set()

    for p in CORE:
        if p not in vi:
            raise RuntimeError(("core point missing", p))
        x, y = p
        full = sorted((a, b) for a in support[x] for b in support[y])
        allow = set(allowed[vi[p]])
        cell_rows = []
        for c in full:
            a, b = c
            Ga = list(groups.get(a, ()))
            Gb = list(groups.get(b, ()))
            blockers = []
            if Ga and Gb:
                for u in Ga:
                    for v in Gb:
                        q = (u, v)
                        if not product_conflict(ring, p, q):
                            blockers.append(q)
                            release_union.add(q)
            if (c in allow) != (len(blockers) == 0):
                raise RuntimeError(("allowed/blocker drift", p, c, c in allow, blockers[:5]))
            cell_rows.append({
                "cell": list(c),
                "allowed": c in allow,
                "group_a_size": len(Ga),
                "group_b_size": len(Gb),
                "group_a": Ga,
                "group_b": Gb,
                "blocker_count": len(blockers),
                "blockers": [list(q) for q in blockers],
            })
        details.append({
            "point": list(p),
            "support_first": list(support[x]),
            "support_second": list(support[y]),
            "full_support_cells": len(full),
            "allowed_cells": [list(c) for c in sorted(allow)],
            "cells": cell_rows,
        })

    out = {
        "method": "product-level-injection-two-point-core-diagnostic",
        "source_run": 41233022940,
        "core_points": [list(p) for p in CORE],
        "core_points_conflict": product_conflict(ring, CORE[0], CORE[1]),
        "core_points_compatible": not product_conflict(ring, CORE[0], CORE[1]),
        "same_first_factor": CORE[0][0] == CORE[1][0],
        "details": details,
        "distinct_frozen_blockers_across_all_alternative_cells": len(release_union),
        "release_union": [list(q) for q in sorted(release_union)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("details", "release_union")}, sort_keys=True))
    for d in details:
        print(json.dumps({"point": d["point"], "supports": [d["support_first"], d["support_second"]], "allowed_cells": d["allowed_cells"], "blocker_counts": [[r["cell"], r["blocker_count"]] for r in d["cells"]]}, sort_keys=True))


if __name__ == "__main__":
    main()
