#!/usr/bin/env python3
"""Recombine arbitrary-radius neutral Hall pieces from two omitted BPZ blocks.

For one omitted terminal product block C, the candidate-to-baseline blocker graph
is bipartite.  If a maximum matching saturates C, every subset A satisfies
|A|<=|N(A)|.  Equal-score subsets (tight Hall sets) can nevertheless be useful
when two blocks share deleted blockers.

Fix a left-saturating matching M.  Direct each candidate x to M^{-1}(b) for
every matched blocker b adjacent to x; an adjacency to an unmatched blocker is
a sink edge.  A terminal SCC with no sink edge is forward-closed, hence its
blocker neighborhood is exactly its matched blockers and it is a neutral
r-for-r exchange.

This script computes those minimal neutral pieces for every Hall-saturated
omitted BPZ terminal word, indexes them by baseline blocker, and tests every
pair of pieces from distinct words that shares a blocker.  If their selected
vertices are disjoint and cross-independent, their combined gain is exactly

    |N(A1) intersect N(A2)| >= 1.

Any winner is materialized as a Few Shots p004 certificate.  A negative result
is exact only for the *terminal-SCC-pair slice*; larger tight closures and
individually negative pieces are separate search spaces.
"""

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

LABELS = ("B", "N", "A", "D", "O", "H", "V")
RECORD_CODE = (
    ("B", "B"), ("N", "O"), ("A", "H"), ("D", "V"),
    ("O", "N"), ("H", "D"), ("V", "A"),
)
EXPECTED_SCORE = 134_753


def hopcroft_karp(adj, n_right):
    n_left = len(adj)
    pair_l = [-1] * n_left
    pair_r = [-1] * n_right
    dist = [-1] * n_left
    sys.setrecursionlimit(max(1_000_000, 2 * n_left + 1000))

    def bfs():
        q = deque()
        found = False
        for u in range(n_left):
            if pair_l[u] < 0:
                dist[u] = 0
                q.append(u)
            else:
                dist[u] = -1
        while q:
            u = q.popleft()
            for v in adj[u]:
                w = pair_r[v]
                if w < 0:
                    found = True
                elif dist[w] < 0:
                    dist[w] = dist[u] + 1
                    q.append(w)
        return found

    def dfs(u):
        for v in adj[u]:
            w = pair_r[v]
            if w < 0 or (dist[w] == dist[u] + 1 and dfs(w)):
                pair_l[u] = v
                pair_r[v] = u
                return True
        dist[u] = -1
        return False

    matching = 0
    while bfs():
        for u in range(n_left):
            if pair_l[u] < 0 and dfs(u):
                matching += 1
    return matching, pair_l, pair_r


def terminal_sccs(adj, pair_l, pair_r):
    """Return terminal sink-free SCCs of the matching-closure digraph.

    Each returned list contains left-vertex indices and is an exact tight Hall
    set.  Uses iterative Kosaraju to avoid Python recursion depth issues.
    """
    n = len(adj)
    d_adj = [[] for _ in range(n)]
    rev = [[] for _ in range(n)]
    sink_edge = [False] * n
    for u, bs in enumerate(adj):
        out = set()
        for b in bs:
            w = pair_r[b]
            if w < 0:
                sink_edge[u] = True
            else:
                out.add(w)
        row = sorted(out)
        d_adj[u] = row
        for w in row:
            rev[w].append(u)

    seen = bytearray(n)
    order = []
    for root in range(n):
        if seen[root]:
            continue
        seen[root] = 1
        stack = [(root, 0)]
        while stack:
            u, i = stack[-1]
            if i < len(d_adj[u]):
                v = d_adj[u][i]
                stack[-1] = (u, i + 1)
                if not seen[v]:
                    seen[v] = 1
                    stack.append((v, 0))
            else:
                order.append(u)
                stack.pop()

    comp = [-1] * n
    members = []
    for root in reversed(order):
        if comp[root] >= 0:
            continue
        cid = len(members)
        comp[root] = cid
        cur = []
        q = [root]
        while q:
            u = q.pop()
            cur.append(u)
            for v in rev[u]:
                if comp[v] < 0:
                    comp[v] = cid
                    q.append(v)
        members.append(cur)

    terminal = [True] * len(members)
    for u in range(n):
        cu = comp[u]
        if sink_edge[u]:
            terminal[cu] = False
        if terminal[cu]:
            for v in d_adj[u]:
                if comp[v] != cu:
                    terminal[cu] = False
                    break

    out = []
    for cid, ok in enumerate(terminal):
        if not ok:
            continue
        S = sorted(members[cid])
        blockers = {pair_l[u] for u in S}
        if -1 in blockers or len(blockers) != len(S):
            raise RuntimeError(("terminal SCC matching mismatch", cid, len(S), len(blockers)))
        neigh = set()
        for u in S:
            neigh.update(adj[u])
        if neigh != blockers:
            raise RuntimeError(("terminal SCC not tight", cid, len(S), len(neigh), len(blockers)))
        out.append((S, sorted(blockers)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("shot_dir", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore

    base, _transform, _exchanges, axioms = load_base(root / "data" / "base_c7.json")
    if not all(axioms.values()):
        raise RuntimeError({k: v for k, v in axioms.items() if not v})
    ring = base.ring
    fam = {
        "B": set(base.B.elements), "N": set(base.X0.elements),
        "A": set(base.XV.elements), "D": set(base.XH.elements),
        "O": set(base.R.elements), "H": set(base.PH.elements),
        "V": set(base.PV.elements),
    }
    sizes = {k: len(v) for k, v in fam.items()}
    if sizes != {"B":359,"N":322,"A":19,"D":26,"O":8,"H":8,"V":8}:
        raise RuntimeError(("family-size drift", sizes))
    for lab, F in fam.items():
        for x in F:
            if (ring.NB[x] & F) - {x}:
                raise RuntimeError(("family not independent", lab, x))

    owner_pair = []
    owner = {}
    for w in RECORD_CODE:
        for a in sorted(fam[w[0]]):
            for b in sorted(fam[w[1]]):
                p = (a, b)
                if p in owner:
                    raise RuntimeError(("record overlap", w, p))
                owner[p] = len(owner_pair)
                owner_pair.append(p)
    if len(owner_pair) != EXPECTED_SCORE:
        raise RuntimeError(("record score drift", len(owner_pair)))
    baseline = set(owner)

    nb_members = {lab: [None] * ring.n for lab in LABELS}
    for lab in LABELS:
        F = fam[lab]
        for x in range(ring.n):
            nb_members[lab][x] = tuple(y for y in ring.NB[x] if y in F)

    def blockers(a, b):
        out = []
        for c, d in RECORD_CODE:
            for x in nb_members[c][a]:
                for y in nb_members[d][b]:
                    out.append(owner[(x, y)])
        if len(out) != len(set(out)):
            raise RuntimeError(("duplicate blocker", a, b))
        return out

    pieces = []
    block_summary = []
    direct_deficient = []
    for u in LABELS:
        for v in LABELS:
            w = (u, v)
            if w in RECORD_CODE:
                continue
            candidates = []
            adj = []
            for a in sorted(fam[u]):
                for b in sorted(fam[v]):
                    if (a, b) in baseline:
                        continue
                    candidates.append((a, b))
                    adj.append(blockers(a, b))
            matching, pair_l, pair_r = hopcroft_karp(adj, len(owner_pair))
            deficiency = len(candidates) - matching
            if deficiency:
                direct_deficient.append({"word":"".join(w), "deficiency":deficiency})
                # The single-block Hall sweep is responsible for materializing this
                # stronger case; do not mix it with the neutral-pair proof below.
                block_summary.append({"word":"".join(w), "candidates":len(candidates),
                                      "deficiency":deficiency, "terminal_sccs":None})
                continue
            ts = terminal_sccs(adj, pair_l, pair_r)
            for S, B in ts:
                cid = len(pieces)
                pieces.append({
                    "id": cid,
                    "word": "".join(w),
                    "word_tuple": w,
                    "selected": [candidates[i] for i in S],
                    "blockers": B,
                })
            block_summary.append({"word":"".join(w), "candidates":len(candidates),
                                  "deficiency":0, "terminal_sccs":len(ts),
                                  "terminal_vertices":sum(len(S) for S,_ in ts),
                                  "max_terminal_scc":max((len(S) for S,_ in ts), default=0)})
            print(json.dumps(block_summary[-1], sort_keys=True), flush=True)

    by_blocker = defaultdict(list)
    for p in pieces:
        for b in p["blockers"]:
            by_blocker[b].append(p["id"])

    candidate_pairs = set()
    for ids in by_blocker.values():
        ids = sorted(set(ids))
        for i in range(len(ids)):
            p = pieces[ids[i]]
            for j in range(i + 1, len(ids)):
                q = pieces[ids[j]]
                if p["word"] == q["word"]:
                    continue
                candidate_pairs.add((ids[i], ids[j]))

    def cross_conflict(P, Q):
        # Build sparse first-coordinate -> bitset(second coordinates) for Q.
        by_first = {}
        for a, b in Q:
            by_first[a] = by_first.get(a, 0) | (1 << b)
        cache = {}
        for a, b in P:
            m = cache.get(a)
            if m is None:
                m = 0
                for c in ring.NB[a]:
                    m |= by_first.get(c, 0)
                cache[a] = m
            if m & ring.BITS[b]:
                return True
        return False

    best = None
    tested = 0
    duplicate_skips = 0
    conflict_skips = 0
    for i, j in sorted(candidate_pairs,
                       key=lambda ij:(len(pieces[ij[0]]["selected"])+len(pieces[ij[1]]["selected"]), ij)):
        p, q = pieces[i], pieces[j]
        sp, sq = set(p["selected"]), set(q["selected"])
        if sp & sq:
            duplicate_skips += 1
            continue
        tested += 1
        # Test smaller side as probes for the factorized bitset check.
        if len(sp) <= len(sq):
            bad = cross_conflict(sp, sq)
        else:
            bad = cross_conflict(sq, sp)
        if bad:
            conflict_skips += 1
            continue
        bp, bq = set(p["blockers"]), set(q["blockers"])
        overlap = bp & bq
        if not overlap:
            raise RuntimeError(("indexed pair lost shared blocker", i, j))
        deleted_ids = bp | bq
        added = sp | sq
        gain = len(added) - len(deleted_ids)
        if gain != len(overlap) or gain <= 0:
            raise RuntimeError(("gain identity failed", i, j, gain, len(overlap)))
        candidate_set = (baseline - {owner_pair[b] for b in deleted_ids}) | added
        if len(candidate_set) != EXPECTED_SCORE + gain:
            raise RuntimeError(("candidate size mismatch", len(candidate_set), gain))
        rec = {
            "piece1": i, "piece2": j, "word1": p["word"], "word2": q["word"],
            "size1": len(sp), "size2": len(sq),
            "shared_blockers": len(overlap), "deleted": len(deleted_ids),
            "added": len(added), "gain": gain, "candidate_score": len(candidate_set),
        }
        if best is None or (gain, -len(deleted_ids)) > (best[0], -best[1]):
            best = (gain, len(deleted_ids), rec, candidate_set)
            # One verified +1 is enough scientifically, but continue the exact SCC-pair
            # slice so the result also records its best gain.

    status = {
        "method": "exact-bpz-neutral-terminal-scc-pair-recombination",
        "record_score": EXPECTED_SCORE,
        "family_sizes": sizes,
        "single_block_deficient": direct_deficient,
        "blocks": block_summary,
        "terminal_pieces": len(pieces),
        "shared_blocker_piece_pairs": len(candidate_pairs),
        "tested_disjoint_piece_pairs": tested,
        "duplicate_candidate_skips": duplicate_skips,
        "cross_conflict_skips": conflict_skips,
        "breakthrough": best is not None,
        "best": None if best is None else best[2],
    }

    if best is not None:
        gain, _radius, rec, candidate_set = best
        args.shot_dir.mkdir(parents=True, exist_ok=True)
        def point(pair):
            a, b = pair
            return "".join(str(x) for x in (ring.decode(a) + ring.decode(b)))
        points = sorted(point(p) for p in candidate_set)
        if len(points) != EXPECTED_SCORE + gain or len(points) != len(set(points)):
            raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir / "certificate.json").write_text(
            json.dumps({"points": points}, separators=(",", ":")) + "\n")
        (args.shot_dir / "metadata.json").write_text(
            json.dumps({"method": status["method"], **rec}, indent=2, sort_keys=True) + "\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:v for k,v in status.items() if k != "blocks"}, sort_keys=True))


if __name__ == "__main__":
    main()
