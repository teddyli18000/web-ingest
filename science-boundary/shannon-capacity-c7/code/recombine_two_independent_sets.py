#!/usr/bin/env python3
"""Exact recombination of two verifier-valid C7^10 independent sets.

If A and B are independent, every conflict inside A union B is between
L=A\B and R=B\A. Thus the conflict graph on the difference sets is bipartite.
By Konig's theorem a maximum independent subset of A union B is obtained from
an exact maximum matching / minimum vertex cover.

Cross edges are recovered exactly with a base-7 trie over R.  For a left word
x, trie traversal follows only the three allowed digits x_i-1,x_i,x_i+1 at
each coordinate, but prunes nonexistent R prefixes.  This avoids O(|L||R|)
when two boundary states differ substantially.
"""
import argparse
import collections
import json
import sys
from pathlib import Path


def conflict(a: str, b: str) -> bool:
    if len(a) != 10 or len(b) != 10:
        raise ValueError("expected 10-digit base-7 words")
    return all((int(x) - int(y)) % 7 in (0, 1, 6) for x, y in zip(a, b))


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


def build_conflict_adjacency(L: list[str], R: list[str]):
    # Compact trie: children[node] is digit->node, terminal[node] is R index.
    children: list[dict[int, int]] = [{}]
    terminal = [-1]
    for j, word in enumerate(R):
        node = 0
        for ch in word:
            d = ord(ch) - 48
            nxt = children[node].get(d)
            if nxt is None:
                nxt = len(children)
                children[node][d] = nxt
                children.append({})
                terminal.append(-1)
            node = nxt
        if terminal[node] != -1:
            raise RuntimeError("duplicate trie terminal")
        terminal[node] = j

    allowed = [[(d - 1) % 7, d, (d + 1) % 7] for d in range(7)]
    adj: list[list[int]] = [[] for _ in L]
    trie_visits = 0
    for i, word in enumerate(L):
        frontier = [0]
        for ch in word:
            digs = allowed[ord(ch) - 48]
            nxt_frontier = []
            for node in frontier:
                c = children[node]
                for d in digs:
                    z = c.get(d)
                    if z is not None:
                        nxt_frontier.append(z)
            trie_visits += len(nxt_frontier)
            frontier = nxt_frontier
            if not frontier:
                break
        if frontier:
            out = []
            for node in frontier:
                j = terminal[node]
                if j != -1:
                    out.append(j)
            out.sort()
            # Defensive replay of every reported edge.
            if any(not conflict(word, R[j]) for j in out):
                raise RuntimeError("trie emitted a non-conflict edge")
            adj[i] = out
    return adj, len(children), trie_visits


def hopcroft_karp(adj: list[list[int]], nr: int):
    nl = len(adj)
    sys.setrecursionlimit(max(10000, 2 * (nl + nr) + 100))
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
    adj, trie_nodes, trie_visits = build_conflict_adjacency(L, R)
    edges = sum(map(len, adj))

    matching, ml, mr = hopcroft_karp(adj, len(R))

    # Alternating reachability from unmatched left vertices: unmatched L->R,
    # matched R->L. Konig cover = (L\ZL) union (R intersect ZR).
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
            if ml[u] == v:
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

    # Exact edge-cover replay without materializing a separate edge list.
    for i, nbrs in enumerate(adj):
        if not zl[i]:
            continue
        for j in nbrs:
            if not zr[j]:
                raise RuntimeError(f"uncovered conflict edge {(i,j)}")

    baseline = max(len(A), len(B))
    st = {
        "method": "exact-bipartite-union-konig-trie",
        "size_a": len(A),
        "size_b": len(B),
        "common": len(common),
        "left_only": len(L),
        "right_only": len(R),
        "cross_conflict_edges": edges,
        "matching_size": matching,
        "min_vertex_cover_size": len(cover_l) + len(cover_r),
        "union_size": len(A | B),
        "recombined_score": len(out),
        "gain_over_best_input": len(out) - baseline,
        "trie_nodes": trie_nodes,
        "trie_visits": trie_visits,
        "left_degree_min": min(map(len, adj), default=0),
        "left_degree_max": max(map(len, adj), default=0),
        "left_degree_sum": edges,
        "unmatched_left": sum(v == -1 for v in ml),
        "unmatched_right": sum(v == -1 for v in mr),
    }
    # For small difference sets, retain exact matching/cover details as evidence.
    if len(L) <= 256 and len(R) <= 256:
        st.update(
            left_degrees=[len(x) for x in adj],
            matching_pairs=[[L[i], R[v]] for i, v in enumerate(ml) if v != -1],
            cover_left=[L[i] for i in cover_l],
            cover_right=[R[j] for j in cover_r],
        )
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    if len(out) > baseline:
        args.candidate.parent.mkdir(parents=True, exist_ok=True)
        args.candidate.write_text(json.dumps({"points": sorted(out)}, separators=(",", ":")) + "\n")
    print(json.dumps(st, sort_keys=True))


if __name__ == "__main__":
    main()
