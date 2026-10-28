#!/usr/bin/env python3
"""Robust entrypoint for bpz_t9_portable_extra_seeds.

Some portable verifier modules expose auxiliary containers whose outer length is
367 (for example U1's `boxes`) but which are not 367-point independent sets.
The original generic extractor intentionally treats any 367-shaped container as
a candidate and then aborts if one is not independent.  For discovery we want
the opposite policy: keep only independently revalidated 367-point objects,
then let the original scanner perform its normal validation/dedup/FFT replay.
"""

import sys

import bpz_t9_portable_extra_seeds as base


def conflict(a: int, b: int) -> bool:
    for _ in range(5):
        x, y = a % 7, b % 7
        a //= 7
        b //= 7
        if (x - y) % 7 not in (0, 1, 6):
            return False
    return True


def independent(points) -> bool:
    pts = tuple(points)
    if len(pts) != 367 or len(set(pts)) != 367:
        return False
    for i, a in enumerate(pts):
        for b in pts[i + 1 :]:
            if conflict(a, b):
                return False
    return True


_original_module_witnesses = base.module_witnesses


def filtered_module_witnesses(path):
    rows = _original_module_witnesses(path)
    kept = []
    ignored = []
    for name, points in rows:
        if independent(points):
            kept.append((name, points))
        else:
            ignored.append(name)
    if ignored:
        print(f"PORTABLE_AUX_IGNORED {path.name}: {ignored}", file=sys.stderr, flush=True)
    return kept


base.module_witnesses = filtered_module_witnesses
base.main()
