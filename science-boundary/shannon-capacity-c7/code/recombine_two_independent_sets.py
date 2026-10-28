#!/usr/bin/env python3
"""Exact recombination of two verifier-valid C7^10 independent sets.

If A and B are independent, every conflict inside A union B is between
L=A\B and R=B\A.  Thus the conflict graph on the difference sets is bipartite.
By Konig's theorem a maximum independent subset of A union B is obtained from
an exact maximum matching / minimum vertex cover.  Any score above the input
score is a genuine unrestricted recombination, not a bounded-radius exchange.
"""
import argparse
import collections
import json
from pathlib import Path


def conflict(a: str, b: str) -> bool:
    if len(a) != 10 or len(b) != 10:
        raise ValueError("expected 10-digit base-7 words")
    for x, y in zip(a, b):
        d = (int(x) - int(y)) % 7
        if d not in (0, 1, 6):
            return False
    return True


def load(path: Path) -> set[str]:
    obj = json.loads(path.read_text())
    pts = obj.get("points")
    if not isinstance(pts, list):
        raise ValueError(f"bad certificate {path}")
    s = set(pts)
    if len(s) != len(pts):
        raise ValueError(f"duplicate point in {path}")
    if any(len(p) != 10 or any(c not in "0123456" for c in p) for p in s):
        raise ValueError(f"bad point encoding in {path}")
    return s


def hopcroft_karp(adj: list[list[int]], nr: int):
    nl = len(adj)
    ml = [-1] * nl
    mr = [-1] * nr
    dist = [0] * nl
    INF = 10**9

    def bfs():
        q = collections.deque()
        found = False
        for u in range(nl):
            if ml[u] == -1:
                dist[u] = 0
                q.append(u)
            else:
                dist[u] = INF
        while q:
            u = q.popleft()
            for v in adj[u]:
                w = mr[v]
                if w == -1:
                    found = True
                elif dist[w] == INF:
                    dist[w] = dist[u] + 1
                    q.append(w)
        return found

    def dfs(u):
        for v in adj[u]:
            w = mr[v]
            if w == -1 or (dist[w] == dist[u] + 1 and dfs(w)):
                ml[u] = v
                mr[v] = u
                return True
        dist[u] = INF
        return False

    m = 0
    while bfs():
        for u in range(nl):
            if ml[u] == -1 and dfs(u):
                m += 1
    return m, ml, mr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    common = A & B
    L = sorted(A - B)
    R = sorted(B - A)
    ridx = {p: i for i, p in enumerate(R)}
    adj = [[] for _ in L]
    edges = []
    for i, x in enumerate(L):
        for j, y in enumerate(R):
            if conflict(x, y):
                adj[i].append(j)
                edges.append((i, j))

    matching, ml, mr = hopcroft_karp(adj, len(R))

    # Alternating reachability from unmatched left vertices: unmatched L->R,
    # matched R->L.  Konig cover = (L\ZL) union (R intersect ZR).
    zl = [False] * len(L)
    zr = [False] * len(R)
    q = collections.deque()
    for u in range(len(L)):
        if ml[u] == -1:
            zl[u] = True
            q.append(u)
    while q:
        u = q.popleft()
        for v in adj[u]:
            if ml[u] == v:  # only unmatched edges L->R
                continue
            if zr[v]:
                continue
            zr[v] = True
            w = mr[v]
            if w != -1 and not zl[w]:
                zl[w] = True
                q.append(w)

    cover_l = [i for i in range(len(L)) if not zl[i]]
    cover_r = [j for j in range(len(R)) if zr[j]]
    if len(cover_l) + len(cover_r) != matching:
        raise RuntimeError("Konig cover size mismatch")

    keep_l = [L[i] for i in range(len(L)) if zl[i]]
    keep_r = [R[j] for j in range(len(R)) if not zr[j]]
    out = common | set(keep_l) | set(keep_r)
    expected = len(common) + len(L) + len(R) - matching
    if len(out) != expected:
        raise RuntimeError("recombined score mismatch")

    # Difference-set replay: cover must hit every cross-conflict edge.
    kept_l_idx = {i for i in range(len(L)) if zl[i]}
    kept_r_idx = {j for j in range(len(R)) if not zr[j]}
    bad = [(i, j) for i, j in edges if i in kept_l_idx and j in kept_r_idx]
    if bad:
        raise RuntimeError(f"uncovered conflict edges: {bad[:8]}")

    baseline = max(len(A), len(B))
    st = {
        "method": "exact-bipartite-union-konig",
        "size_a": len(A),
        "size_b": len(B),
        "common": len(common),
        "left_only": len(L),
        "right_only": len(R),
        "cross_conflict_edges": len(edges),
        "matching_size": matching,
        "min_vertex_cover_size": len(cover_l) + len(cover_r),
        "union_size": len(A | B),
        "recombined_score": len(out),
        "gain_over_best_input": len(out) - baseline,
        "left_degrees": [len(x) for x in adj],
        "matching_pairs": [[L[i], R[v]] for i, v in enumerate(ml) if v != -1],
        "cover_left": [L[i] for i in cover_l],
        "cover_right": [R[j] for j in cover_r],
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    if len(out) > baseline:
        args.candidate.parent.mkdir(parents=True, exist_ok=True)
        args.candidate.write_text(json.dumps({"points": sorted(out)}, separators=(",", ":")) + "\n")
    print(json.dumps(st, sort_keys=True))


if __name__ == "__main__":
    main()
