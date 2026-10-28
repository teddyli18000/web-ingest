#!/usr/bin/env python3
"""Necessary degree-capacity statistics for the degree-11 endpoint of R(4,6,36).

Fix a hypothetical vertex v of degree 11.  Let A=N(v), |A|=11, and let B be
the 24 non-neighbours.  Then A is an R(3,6,11) graph and B is an R(4,5,24)
graph.  For a fixed pair (A,B), every cross edge contributes once to the total
cross degree on each side.  Since every vertex of a hypothetical R(4,6,36)
graph must have degree in [11,17], each catalog graph induces a necessary
interval for the total number of A-B edges.

For a in A: 11 <= 1 + deg_A(a) + cross(a) <= 17.
For b in B: 11 <= deg_B(b) + cross(b) <= 17.

A pair can only be feasible if these two total-cross-edge intervals overlap.
This script computes exact distributions over complete graph6 catalogues.  It
is only a necessary-condition filter; survivors are not claimed extendable.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path


def decode_graph6(line: str) -> list[int]:
    s = line.strip()
    if not s:
        raise ValueError("empty graph6 line")
    if s.startswith(">>"):
        raise ValueError("graph6 header lines are not supported")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 format is supported")
    bits: list[int] = []
    for ch in s[1:]:
        x = ord(ch) - 63
        if not 0 <= x < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((x >> k) & 1 for k in range(5, -1, -1))
    need = n * (n - 1) // 2
    if len(bits) < need:
        raise ValueError("truncated graph6 record")
    deg = [0] * n
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                deg[i] += 1
                deg[j] += 1
            p += 1
    return deg


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def interval_a(deg: list[int]) -> tuple[int, int]:
    if len(deg) != 11:
        raise ValueError("A catalogue must contain 11-vertex graphs")
    lo = sum(max(0, 10 - d) for d in deg)
    hi = sum(min(24, 16 - d) for d in deg)
    return lo, hi


def interval_b(deg: list[int]) -> tuple[int, int]:
    if len(deg) != 24:
        raise ValueError("B catalogue must contain 24-vertex graphs")
    lo = sum(max(0, 11 - d) for d in deg)
    hi = sum(min(11, 17 - d) for d in deg)
    return lo, hi


def scan(path: Path, side: str) -> dict:
    interval = interval_a if side == "A" else interval_b
    n_expected = 11 if side == "A" else 24
    count = 0
    edges_hist: collections.Counter[int] = collections.Counter()
    interval_hist: collections.Counter[tuple[int, int]] = collections.Counter()
    min_deg_hist: collections.Counter[int] = collections.Counter()
    max_deg_hist: collections.Counter[int] = collections.Counter()
    degree_sequence_hist: collections.Counter[tuple[int, ...]] = collections.Counter()
    records: list[tuple[int, int]] = []
    with path.open("r", encoding="ascii") as f:
        for raw in f:
            if not raw.strip():
                continue
            deg = decode_graph6(raw)
            if len(deg) != n_expected:
                raise ValueError(f"unexpected {len(deg)}-vertex graph in {side} catalogue")
            count += 1
            e = sum(deg) // 2
            iv = interval(deg)
            edges_hist[e] += 1
            interval_hist[iv] += 1
            min_deg_hist[min(deg)] += 1
            max_deg_hist[max(deg)] += 1
            degree_sequence_hist[tuple(sorted(deg))] += 1
            records.append(iv)
    if not count:
        raise ValueError("empty catalogue")
    return {
        "count": count,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "edges_hist": dict(sorted(edges_hist.items())),
        "interval_hist": {f"{a}:{b}": c for (a, b), c in sorted(interval_hist.items())},
        "min_deg_hist": dict(sorted(min_deg_hist.items())),
        "max_deg_hist": dict(sorted(max_deg_hist.items())),
        "degree_sequence_classes": len(degree_sequence_hist),
        "records": records,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path, required=True, help="complete R(3,6,11) graph6 catalogue")
    ap.add_argument("--b", type=Path, required=True, help="complete R(4,5,24) graph6 catalogue")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    A = scan(args.a, "A")
    B = scan(args.b, "B")
    a_intervals = sorted(set(A.pop("records")))
    b_records = B.pop("records")

    def compatible(iv: tuple[int, int]) -> bool:
        l, u = iv
        return any(max(l, al) <= min(u, au) for al, au in a_intervals)

    b_survive = sum(compatible(iv) for iv in b_records)
    b_reject = len(b_records) - b_survive
    global_a_lo = min(x for x, _ in a_intervals)
    global_a_hi = max(y for _, y in a_intervals)
    compatible_edge_totals = sorted({
        t
        for al, au in a_intervals
        for t in range(al, au + 1)
    })

    out = {
        "interpretation": "necessary degree-capacity filter only; survival does not imply a valid gluing",
        "A": A,
        "B": B,
        "A_unique_cross_intervals": [list(x) for x in a_intervals],
        "A_global_cross_interval": [global_a_lo, global_a_hi],
        "A_possible_cross_totals": compatible_edge_totals,
        "B_survive_any_A_interval": b_survive,
        "B_rejected_all_A_intervals": b_reject,
        "B_rejection_fraction": b_reject / len(b_records),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "A_count": A["count"],
        "B_count": B["count"],
        "A_unique_intervals": len(a_intervals),
        "A_global_cross_interval": out["A_global_cross_interval"],
        "B_survive": b_survive,
        "B_reject": b_reject,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
