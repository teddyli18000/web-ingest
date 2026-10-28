#!/usr/bin/env python3
"""Exact necessary-condition filter for the maximum-degree-12 R(4,6,36) branch.

Let v have degree 12, A=N(v) (|A|=12), and B be the 23 non-neighbours.
Then A is a Ramsey(3,6,12) graph, B is a Ramsey(4,5,23) graph, and every
vertex of the full graph has degree 11 or 12.

For b in B write X_b=N(b)∩A.  Every X_b must hit every independent 5-set
of A, otherwise b together with such a 5-set is an independent 6-set.  For
an independent 4-set P of A, the vertices b whose X_b misses P form a clique
in B; since B is K4-free, at most three columns can miss P.  Therefore

    sum_b q_|X_b|(A) <= 3 i_4(A),

where q_s(A) is the minimum number of independent 4-sets missed by a size-s
subset of A that hits every independent 5-set, and i_4(A) is the number of
independent 4-sets of A.

This program computes q_s exactly for each catalogue A and minimizes the
left-hand side over a RELAXATION of all possible B degree sequences.  If even
that relaxed minimum exceeds 3 i_4(A), that A type is rigorously impossible.
The relaxation uses only the published exact lower edge bound e(B)>=101 and
the elementary Ramsey degree range 5<=d_B<=12; it never assumes a complete
catalogue of Ramsey(4,5,23) graphs.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import math
from collections import Counter
from pathlib import Path

INF = 10**12
N_A = 12
FULL = (1 << N_A) - 1


def decode_graph6(line: str) -> tuple[list[int], int]:
    s = line.strip()
    if s.startswith(">>graph6<<"):
        s = s[len(">>graph6<<") :]
    if not s:
        raise ValueError("empty graph6 record")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 records are supported")
    need = n * (n - 1) // 2
    bits: list[int] = []
    for ch in s[1:]:
        v = ord(ch) - 63
        if not 0 <= v < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((v >> shift) & 1 for shift in range(5, -1, -1))
        if len(bits) >= need:
            break
    if len(bits) < need:
        raise ValueError("truncated graph6 record")
    adj = [0] * n
    p = 0
    edges = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
                edges += 1
            p += 1
    return adj, edges


def iter_catalog(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as f:
        for raw_index, line in enumerate(f):
            s = line.strip()
            if not s or (s.startswith(">>") and not s.startswith(">>graph6<<")):
                continue
            adj, edges = decode_graph6(s)
            yield raw_index, s, adj, edges


def independent_table(adj: list[int]) -> list[bool]:
    n = len(adj)
    out = [False] * (1 << n)
    out[0] = True
    for mask in range(1, 1 << n):
        bit = mask & -mask
        v = bit.bit_length() - 1
        rest = mask ^ bit
        out[mask] = out[rest] and not (adj[v] & rest)
    return out


def subset_independent_counts(indep: list[bool], k: int, n: int) -> list[int]:
    """For every mask C, count independent k-subsets contained in C."""
    arr = [0] * (1 << n)
    for mask, ok in enumerate(indep):
        if ok and mask.bit_count() == k:
            arr[mask] = 1
    for bit in range(n):
        step = 1 << bit
        for mask in range(1 << n):
            if mask & step:
                arr[mask] += arr[mask ^ step]
    return arr


def q_profile(adj: list[int]) -> tuple[list[int], list[int], int, int]:
    if len(adj) != N_A:
        raise ValueError(f"expected n={N_A}, got {len(adj)}")
    indep = independent_table(adj)
    if any(indep[sum(1 << v for v in vs)] for vs in itertools.combinations(range(N_A), 6)):
        raise ValueError("catalogue A contains an independent 6-set")
    # A should be triangle-free in R(3,6,12).
    for i in range(N_A):
        if adj[i] & sum((1 << j) for j in range(i + 1, N_A) if (adj[i] >> j) & 1):
            pass
    f4 = subset_independent_counts(indep, 4, N_A)
    f5 = subset_independent_counts(indep, 5, N_A)
    i4 = f4[FULL]
    i5 = f5[FULL]
    q = [INF] * (N_A + 1)
    witness = [-1] * (N_A + 1)
    # X hits every independent 5-set iff C=A\X contains none.
    for c in range(1 << N_A):
        if f5[c] != 0:
            continue
        s = N_A - c.bit_count()
        missed4 = f4[c]
        if missed4 < q[s]:
            q[s] = missed4
            witness[s] = FULL ^ c
    return q, witness, i4, i5


def group_costs(q: list[int], max_x: int, max_n: int = 23) -> list[list[int]]:
    allowed = [(x, q[x]) for x in range(max_x + 1) if q[x] < INF]
    dp = [[INF] * (max_n * max_x + 1) for _ in range(max_n + 1)]
    dp[0][0] = 0
    for n in range(max_n):
        for total, base in enumerate(dp[n]):
            if base >= INF:
                continue
            for x, cost in allowed:
                nt = total + x
                if nt < len(dp[n + 1]):
                    cand = base + cost
                    if cand < dp[n + 1][nt]:
                        dp[n + 1][nt] = cand
    return dp


def best_relaxed_capacity(a_edges: int, q: list[int], i4: int) -> dict:
    # Degree-11 B vertices have x=11-d_B in 0..6; degree-12 vertices have
    # x=12-d_B in 0..7.  Here 5<=d_B follows from R(4,4)=18, and d_B<=12
    # follows from the full graph's maximum degree 12.
    dp11 = group_costs(q, 6)
    dp12 = group_costs(q, 7)
    threshold = 3 * i4
    best = None
    b_hi = min(122, a_edges + 78)
    for b_edges in range(101, b_hi + 1):
        for t_a in range(13):
            # t_a/t_b are counts of degree-12 vertices in A/B.  v itself has
            # degree 12.  Cross-edge double counting gives the formulas below.
            t_b = 2 * (b_edges - a_edges) - 133 + t_a
            if not 0 <= t_b <= 23:
                continue
            cross = 120 + t_a - 2 * a_edges
            if cross != 253 + t_b - 2 * b_edges:
                raise AssertionError("cross-edge identity mismatch")
            n11 = 23 - t_b
            n12 = t_b
            lo = max(0, cross - (len(dp12[n12]) - 1))
            hi = min(cross, len(dp11[n11]) - 1)
            cost = INF
            split = None
            for s11 in range(lo, hi + 1):
                s12 = cross - s11
                if not 0 <= s12 < len(dp12[n12]):
                    continue
                cand = dp11[n11][s11] + dp12[n12][s12]
                if cand < cost:
                    cost = cand
                    split = (s11, s12)
            if best is None or cost < best[0]:
                best = (cost, b_edges, t_a, t_b, cross, split)
    if best is None:
        return {
            "threshold": threshold,
            "best_cost": None,
            "capacity_slack": None,
            "ruled_out": True,
            "reason": "no relaxed degree/count state",
        }
    cost, b_edges, t_a, t_b, cross, split = best
    if cost >= INF:
        return {
            "threshold": threshold,
            "best_cost": None,
            "capacity_slack": None,
            "ruled_out": True,
            "reason": "no cross-size assignment can hit all independent 5-sets",
            "best_state": {"b_edges": b_edges, "t_a": t_a, "t_b": t_b, "cross_edges": cross},
        }
    return {
        "threshold": threshold,
        "best_cost": cost,
        # Positive slack means the necessary inequality can still hold.
        "capacity_slack": threshold - cost,
        "ruled_out": cost > threshold,
        "reason": "capacity inequality" if cost > threshold else "survives relaxed capacity inequality",
        "best_state": {
            "b_edges": b_edges,
            "t_a": t_a,
            "t_b": t_b,
            "cross_edges": cross,
            "sum_x_degree11_B": split[0] if split else None,
            "sum_x_degree12_B": split[1] if split else None,
        },
    }


def analyze(path: Path, wanted_edges: int) -> dict:
    selected = 0
    ruled = 0
    survivors: list[int] = []
    tau_hist = Counter()
    slack_hist = Counter()
    closest = []
    for raw_index, g6, adj, edges in iter_catalog(path):
        if len(adj) != N_A or edges != wanted_edges:
            continue
        ordinal = selected
        selected += 1
        # R(3,6,12) catalogue authentication: triangle-free.
        if any((adj[u] & adj[v]) for u in range(N_A) for v in range(u + 1, N_A) if (adj[u] >> v) & 1):
            raise ValueError(f"raw_index={raw_index}: triangle in claimed R(3,6,12) graph")
        q, witness, i4, i5 = q_profile(adj)
        tau = next((s for s, val in enumerate(q) if val < INF), None)
        if tau is None:
            raise AssertionError("no transversal of independent 5-sets")
        tau_hist[str(tau)] += 1
        cap = best_relaxed_capacity(edges, q, i4)
        if cap["ruled_out"]:
            ruled += 1
        else:
            survivors.append(ordinal)
        slack = cap.get("capacity_slack")
        slack_hist["none" if slack is None else str(slack)] += 1
        detail = {
            "raw_index": raw_index,
            "ordinal": ordinal,
            "graph6": g6,
            "i4": i4,
            "i5": i5,
            "tau5": tau,
            "q": [None if x >= INF else x for x in q[:8]],
            "q_witness_masks": [None if x < 0 else x for x in witness[:8]],
            **cap,
        }
        # Keep the 30 cases closest to violation, with survivors first and then
        # smallest absolute margins.  This is diagnostic only; survivor ordinals
        # below are the complete machine-readable continuation set.
        rank = (0 if not cap["ruled_out"] else 1, abs(slack) if slack is not None else INF)
        closest.append((rank, detail))
        closest.sort(key=lambda x: x[0])
        if len(closest) > 30:
            closest.pop()
    return {
        "method": "D12 independent-4 miss capacity inequality with relaxed B degrees",
        "catalog": str(path),
        "a_edges": wanted_edges,
        "selected_types": selected,
        "ruled_out_types": ruled,
        "survivor_count": len(survivors),
        "survivor_ordinals": survivors,
        "tau5_histogram": dict(sorted(tau_hist.items(), key=lambda kv: int(kv[0]))),
        "capacity_slack_histogram": dict(sorted(slack_hist.items(), key=lambda kv: (kv[0] == "none", int(kv[0]) if kv[0] != "none" else 0))),
        "closest_cases": [d for _, d in closest],
    }


def brute_q(adj: list[int]) -> list[int]:
    indep4 = []
    indep5 = []
    for k, out in ((4, indep4), (5, indep5)):
        for vs in itertools.combinations(range(len(adj)), k):
            mask = sum(1 << v for v in vs)
            if all(not ((adj[u] >> v) & 1) for u, v in itertools.combinations(vs, 2)):
                out.append(mask)
    q = [INF] * (len(adj) + 1)
    full = (1 << len(adj)) - 1
    for x in range(full + 1):
        if any(not (x & p) for p in indep5):
            continue
        missed = sum(not (x & p) for p in indep4)
        q[x.bit_count()] = min(q[x.bit_count()], missed)
    return q


def self_test() -> None:
    # Deterministic family of 12-vertex graphs; compare the zeta-transform q_s
    # computation with a direct definition.
    for salt in range(6):
        adj = [0] * N_A
        for i in range(N_A):
            for j in range(i + 1, N_A):
                if ((i * 17 + j * 11 + salt * 7) % 13) < 4:
                    adj[i] |= 1 << j
                    adj[j] |= 1 << i
        q, _, _, _ = q_profile(adj)
        assert q == brute_q(adj), (salt, q, brute_q(adj))

    # Check group DP against exhaustive products on small cardinalities.
    q = [7, 5, 3, 2, 1, 0, 0, 0] + [INF] * 5
    dp = group_costs(q, 3, max_n=4)
    for n in range(5):
        brute = {}
        for xs in itertools.product(range(4), repeat=n):
            brute[sum(xs)] = min(brute.get(sum(xs), INF), sum(q[x] for x in xs))
        for total, cost in brute.items():
            assert dp[n][total] == cost, (n, total, dp[n][total], cost)
    print("d12 capacity filter self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("analyze")
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--edge-count", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    result = analyze(args.catalog, args.edge_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"survivor_ordinals", "closest_cases", "capacity_slack_histogram"}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
