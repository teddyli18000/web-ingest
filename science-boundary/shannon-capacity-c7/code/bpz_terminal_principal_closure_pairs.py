#!/usr/bin/env python3
"""Recombine principal arbitrary-radius tight Hall closures from two BPZ blocks.

This is a stronger successor to the terminal-SCC pair slice.  For a Hall-
saturated omitted product block, fix a left-saturating matching M and form the
matching-closure digraph on candidates: x -> M^{-1}(b) for every matched
blocker b adjacent to x, with a sink edge for every unmatched blocker.

After SCC condensation, a component is usable iff it cannot reach a sink.  For
such a component S, its full forward closure Desc(S) is an exact tight Hall set:
its candidate count equals its blocker-neighborhood count.  This script pairs
principal closures arising from baseline blockers matched in two distinct
omitted blocks.  It handles overlapping actual candidate vertices exactly:
for two neutral pieces A1,A2, the net gain is

    |N(A1) intersect N(A2)| - |A1 intersect A2|.

A positive-gain, cross-independent pair gives a valid improvement.  This is an
exact search over the principal-closure-pair slice, but it is not a proof over
all unions of several principal closures or individually negative Hall pieces.
"""

import argparse
import json
import sys
from collections import deque
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


def condensation(adj, pair_l, pair_r):
    """Return SCC condensation and which components can reach an unmatched blocker."""
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
            u, k = stack[-1]
            if k < len(d_adj[u]):
                v = d_adj[u][k]
                stack[-1] = (u, k + 1)
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
        stack = [root]
        while stack:
            u = stack.pop()
            cur.append(u)
            for v in rev[u]:
                if comp[v] < 0:
                    comp[v] = cid
                    stack.append(v)
        members.append(cur)

    m = len(members)
    dag = [set() for _ in range(m)]
    rdag = [set() for _ in range(m)]
    direct_sink = [False] * m
    for u in range(n):
        cu = comp[u]
        if sink_edge[u]:
            direct_sink[cu] = True
        for v in d_adj[u]:
            cv = comp[v]
            if cu != cv:
                dag[cu].add(cv)
                rdag[cv].add(cu)

    bad = direct_sink[:]
    q = deque(i for i, x in enumerate(bad) if x)
    while q:
        c = q.popleft()
        for p in rdag[c]:
            if not bad[p]:
                bad[p] = True
                q.append(p)
    return comp, members, dag, bad


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

    blocks = []
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
                block_summary.append({"word":"".join(w), "candidates":len(candidates),
                                      "deficiency":deficiency})
                continue
            comp, members, dag, bad = condensation(adj, pair_l, pair_r)
            source = {}
            for b, left in enumerate(pair_r):
                if left >= 0:
                    c = comp[left]
                    if not bad[c]:
                        source[b] = c
            blocks.append({
                "word": "".join(w), "candidates": candidates, "adj": adj,
                "pair_l": pair_l, "pair_r": pair_r, "comp": comp,
                "members": members, "dag": dag, "bad": bad,
                "source": source, "closure_cache": {},
            })
            block_summary.append({
                "word":"".join(w), "candidates":len(candidates), "deficiency":0,
                "sccs":len(members), "sinkfree_sccs":sum(not x for x in bad),
                "matched_blockers_with_tight_principal":len(source),
            })
            print(json.dumps(block_summary[-1], sort_keys=True), flush=True)

    def closure(block, cid):
        cache = block["closure_cache"]
        if cid in cache:
            return cache[cid]
        if block["bad"][cid]:
            raise RuntimeError(("requested sink-reaching closure", block["word"], cid))
        seen = {cid}
        stack = [cid]
        while stack:
            c = stack.pop()
            for d in block["dag"][c]:
                if block["bad"][d]:
                    raise RuntimeError(("sinkfree component reaches bad", block["word"], cid, d))
                if d not in seen:
                    seen.add(d)
                    stack.append(d)
        idx = []
        for c in seen:
            idx.extend(block["members"][c])
        selected = frozenset(block["candidates"][i] for i in idx)
        blockers_set = frozenset(block["pair_l"][i] for i in idx)
        if -1 in blockers_set or len(selected) != len(idx) or len(blockers_set) != len(idx):
            raise RuntimeError(("principal closure cardinality mismatch", block["word"], cid,
                                len(idx), len(selected), len(blockers_set)))
        neigh = set()
        for i in idx:
            neigh.update(block["adj"][i])
        if neigh != set(blockers_set):
            raise RuntimeError(("principal closure not tight", block["word"], cid,
                                len(idx), len(neigh), len(blockers_set)))
        rec = (selected, blockers_set, len(seen))
        cache[cid] = rec
        return rec

    def cross_conflict_distinct(P, Q):
        by_first = {}
        for a, b in Q:
            by_first[a] = by_first.get(a, 0) | (1 << b)
        for a, b in P:
            for c in ring.NB[a]:
                bits = by_first.get(c, 0) & ring.BITS[b]
                if c == a and (a, b) in Q:
                    bits &= ~(1 << b)
                if bits:
                    return True
        return False

    best = None
    block_pairs = 0
    common_blockers = 0
    source_pairs = 0
    positive_overlap_pairs = 0
    cross_conflict_pairs = 0
    for bi in range(len(blocks)):
        P = blocks[bi]
        for bj in range(bi + 1, len(blocks)):
            Q = blocks[bj]
            block_pairs += 1
            if len(P["source"]) <= len(Q["source"]):
                shared = [b for b in P["source"] if b in Q["source"]]
            else:
                shared = [b for b in Q["source"] if b in P["source"]]
            common_blockers += len(shared)
            pairs = {(P["source"][b], Q["source"][b]) for b in shared}
            source_pairs += len(pairs)
            for c1, c2 in pairs:
                s1, b1, cc1 = closure(P, c1)
                s2, b2, cc2 = closure(Q, c2)
                blocker_overlap = b1 & b2
                if not blocker_overlap:
                    raise RuntimeError(("source pair lost common blocker", P["word"], Q["word"], c1, c2))
                candidate_overlap = s1 & s2
                gain = len(blocker_overlap) - len(candidate_overlap)
                if gain <= 0:
                    continue
                positive_overlap_pairs += 1
                if len(s1) <= len(s2):
                    bad = cross_conflict_distinct(s1, s2)
                else:
                    bad = cross_conflict_distinct(s2, s1)
                if bad:
                    cross_conflict_pairs += 1
                    continue
                deleted_ids = b1 | b2
                added = s1 | s2
                if len(added) - len(deleted_ids) != gain:
                    raise RuntimeError(("gain identity failed", P["word"], Q["word"], c1, c2))
                candidate_set = (baseline - {owner_pair[b] for b in deleted_ids}) | set(added)
                if len(candidate_set) != EXPECTED_SCORE + gain:
                    raise RuntimeError(("candidate size mismatch", len(candidate_set), gain))
                rec = {
                    "word1":P["word"], "word2":Q["word"],
                    "source_scc1":c1, "source_scc2":c2,
                    "closure_sccs1":cc1, "closure_sccs2":cc2,
                    "size1":len(s1), "size2":len(s2),
                    "shared_blockers":len(blocker_overlap),
                    "shared_candidates":len(candidate_overlap),
                    "deleted":len(deleted_ids), "added":len(added),
                    "gain":gain, "candidate_score":len(candidate_set),
                }
                if best is None or (gain, -len(deleted_ids)) > (best[0], -best[1]):
                    best = (gain, len(deleted_ids), rec, candidate_set)

    status = {
        "method":"exact-bpz-neutral-principal-closure-pair-recombination",
        "record_score":EXPECTED_SCORE,
        "family_sizes":sizes,
        "single_block_deficient":direct_deficient,
        "blocks":block_summary,
        "hall_saturated_blocks":len(blocks),
        "block_pairs":block_pairs,
        "common_matched_blockers_with_tight_principals":common_blockers,
        "distinct_principal_source_pairs":source_pairs,
        "positive_overlap_source_pairs":positive_overlap_pairs,
        "cross_conflict_positive_pairs":cross_conflict_pairs,
        "cached_principal_closures":sum(len(b["closure_cache"]) for b in blocks),
        "breakthrough":best is not None,
        "best":None if best is None else best[2],
        "scope_note":"exact for pairs of principal sink-free forward closures; not all unions of closures",
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
            json.dumps({"points":points}, separators=(",", ":")) + "\n")
        (args.shot_dir / "metadata.json").write_text(
            json.dumps({"method":status["method"], **rec}, indent=2, sort_keys=True) + "\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:v for k,v in status.items() if k != "blocks"}, sort_keys=True))


if __name__ == "__main__":
    main()
