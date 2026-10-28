#!/usr/bin/env python3
"""Exact net-gain optimization over every addition visited by a plateau walk.

Input TRACE is emitted by the asserted trace patch of
`c7_10d_private_guided_walk.cpp`.  Each accepted outside point y is accompanied
by the complete set N_B(y) of original baseline vertices confusable with y.

We optimize over the union of the verified baseline B and all unique visited
additions A.  Variables x_a choose additions.  Variables r_b mark touched
baseline points removed.  Hard clauses enforce

  x_a -> r_b              for every b in N_B(a),
  not(x_a and x_c)        for every confusable addition pair.

Soft unit clauses reward each chosen addition and each touched baseline point
not removed.  Therefore the exact RC2 objective is precisely

  |B| + #chosen additions - #removed baseline points.

This searches arbitrary recombinations of all points ever accepted by the walk,
not merely any one endpoint or bounded exchange radius.  A target hit is
materialized for independent Few Shots verification.
"""
import argparse
import json
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

BASELINE_SIZE = 134_753
TARGET = 134_754


def load_ids(path: Path) -> list[int]:
    a = [int(x) for x in path.read_text().split()]
    if len(a) != BASELINE_SIZE or len(set(a)) != BASELINE_SIZE:
        raise ValueError(f"baseline size/duplicate drift: {len(a)} {len(set(a))}")
    if any(x < 0 or x >= 7**10 for x in a):
        raise ValueError("baseline id out of range")
    return a


def digits10(z: int) -> tuple[int, ...]:
    d = []
    for _ in range(10):
        d.append(z % 7)
        z //= 7
    if z:
        raise ValueError("id too large")
    return tuple(reversed(d))


def encode(z: int) -> str:
    return "".join(map(str, digits10(z)))


def conflict_digits(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    for x, y in zip(a, b):
        if (x - y) % 7 not in (0, 1, 6):
            return False
    return True


def addition_edges(adds: list[int]):
    # For ~2k walk additions, O(m^2) with early coordinate exits is small and
    # simpler to replay independently than another 7^10 transform.
    ds = [digits10(x) for x in adds]
    edges = []
    degree = [0] * len(adds)
    for i in range(len(adds)):
        ai = ds[i]
        for j in range(i + 1, len(adds)):
            if conflict_digits(ai, ds[j]):
                edges.append((i, j))
                degree[i] += 1
                degree[j] += 1
    return edges, degree


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline_ids", type=Path)
    ap.add_argument("trace", type=Path)
    ap.add_argument("candidate_ids", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--target", type=int, default=TARGET)
    args = ap.parse_args()

    baseline = load_ids(args.baseline_ids)
    bset = set(baseline)
    traced: dict[int, frozenset[int]] = {}
    accepted_lines = 0
    for line in args.trace.read_text().splitlines():
        if not line.strip():
            continue
        z = [int(x) for x in line.split()]
        y, nb = z[0], frozenset(z[1:])
        accepted_lines += 1
        if any(b not in bset for b in nb):
            raise RuntimeError("trace contains non-baseline neighbor")
        old = traced.get(y)
        if old is not None and old != nb:
            raise RuntimeError(f"baseline-neighbor trace drift for {y}")
        traced[y] = nb

    # Original-baseline points need no addition variable: keeping them is already
    # represented by the baseline/removal side of the optimization.
    adds = sorted(y for y in traced if y not in bset)
    if not adds:
        raise RuntimeError("trace has no outside additions")
    neighbors = [traced[y] for y in adds]
    if any(not nb for nb in neighbors):
        raise RuntimeError("outside traced addition has zero baseline blockers")

    touched = sorted(set().union(*neighbors))
    tidx = {b: i for i, b in enumerate(touched)}
    edges, degree = addition_edges(adds)

    # x variables: 1..m. r variables: m+1..m+T, true means baseline removal.
    m = len(adds)
    def rv(b: int) -> int:
        return m + 1 + tidx[b]

    w = WCNF()
    implication_clauses = 0
    for i, nb in enumerate(neighbors):
        xv = i + 1
        for b in nb:
            w.append([-xv, rv(b)])
            implication_clauses += 1
    for i, j in edges:
        w.append([-(i + 1), -(j + 1)])
    for i in range(m):
        w.append([i + 1], weight=1)
    for b in touched:
        w.append([-rv(b)], weight=1)

    with RC2(w, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = int(rc2.cost)
    if model is None:
        raise RuntimeError("RC2 returned no model")
    pos = {v for v in model if v > 0}
    chosen = [adds[i] for i in range(m) if i + 1 in pos]
    removed = [b for b in touched if rv(b) in pos]
    score = BASELINE_SIZE + len(chosen) - len(removed)

    # Exact replay of the logical model.
    rset = set(removed)
    for i, y in enumerate(adds):
        if i + 1 in pos and not neighbors[i] <= rset:
            raise RuntimeError("selected addition has undeleted baseline blocker")
    chosen_idx = [i for i in range(m) if i + 1 in pos]
    cset = set(chosen_idx)
    bad_edges = [(i, j) for i, j in edges if i in cset and j in cset]
    if bad_edges:
        raise RuntimeError(f"selected addition conflicts: {bad_edges[:8]}")

    # Independent objective replay. Total soft clauses are m+T and RC2 cost is
    # unsatisfied soft weight.  Satisfied-soft objective equals chosen + unremoved.
    soft_sat = m + len(touched) - cost
    if soft_sat != len(chosen) + len(touched) - len(removed):
        raise RuntimeError("RC2 cost replay mismatch")

    st = {
        "method": "exact-plateau-visited-union-maxsat",
        "baseline_size": BASELINE_SIZE,
        "target": args.target,
        "accepted_trace_lines": accepted_lines,
        "unique_traced_points": len(traced),
        "unique_outside_additions": m,
        "touched_baseline_vertices": len(touched),
        "baseline_incidence_clauses": implication_clauses,
        "addition_conflict_edges": len(edges),
        "addition_degree_min": min(degree, default=0),
        "addition_degree_max": max(degree, default=0),
        "addition_degree_sum": sum(degree),
        "rc2_cost": cost,
        "chosen_additions": len(chosen),
        "removed_baseline": len(removed),
        "net_gain": len(chosen) - len(removed),
        "score": score,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")

    if score >= args.target:
        out = (bset - rset) | set(chosen)
        if len(out) != score:
            raise RuntimeError("candidate size drift")
        args.candidate_ids.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_ids.write_text("".join(f"{x}\n" for x in sorted(out)))
    print(json.dumps(st, sort_keys=True))


if __name__ == "__main__":
    main()
