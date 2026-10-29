#!/usr/bin/env python3
"""Exact arbitrary-radius exchange test for each omitted BPZ terminal block.

For the BPZ 5D gadget, the public 10D record is the disjoint union of seven
Cartesian product blocks

    BB, NO, AH, DV, ON, HD, VA.

Consider one other label word uv.  If F_u and F_v are independent, then the
entire product F_u x F_v is independent.  After removing points already in the
record, let C be the external candidates in this block and connect each c in C
to every record vertex that conflicts with c.  For any A subset C, replacing
N(A) by A changes the score by |A|-|N(A)|.  Hall's theorem therefore gives an
arbitrary-radius exact test:

    a net-positive exchange exists in this whole block
    iff the blocker bipartite graph has no matching saturating C.

Thus one maximum matching closes *all radii* for a terminal block at once.  If
a Hall-deficient block is found, the alternating-reachability witness is
materialized as a Few Shots p004 certificate for authoritative verification.
"""

import argparse
import json
import sys
from collections import deque
from pathlib import Path

LABELS = ("B", "N", "A", "D", "O", "H", "V")
RECORD_CODE = (
    ("B", "B"),
    ("N", "O"),
    ("A", "H"),
    ("D", "V"),
    ("O", "N"),
    ("H", "D"),
    ("V", "A"),
)
EXPECTED_SCORE = 134_753


def hopcroft_karp(adj, n_right):
    n_left = len(adj)
    pair_l = [-1] * n_left
    pair_r = [-1] * n_right
    dist = [-1] * n_left
    sys.setrecursionlimit(max(1_000_000, n_left * 2 + 1000))

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
            du = dist[u]
            for v in adj[u]:
                w = pair_r[v]
                if w < 0:
                    found = True
                elif dist[w] < 0:
                    dist[w] = du + 1
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


def hall_witness(adj, pair_l, pair_r):
    """Return alternating-reachable Z_L,Z_R from all unmatched left vertices."""
    zl = set(u for u, v in enumerate(pair_l) if v < 0)
    zr = set()
    q = deque(zl)
    while q:
        u = q.popleft()
        matched_v = pair_l[u]
        for v in adj[u]:
            # L->R uses only unmatched edges.
            if v == matched_v:
                continue
            if v in zr:
                continue
            zr.add(v)
            w = pair_r[v]
            if w >= 0 and w not in zl:
                zl.add(w)
                q.append(w)
    # Exact neighborhood check: every neighbor of Z_L must be in Z_R, and vice versa.
    neigh = set()
    for u in zl:
        neigh.update(adj[u])
    if neigh != zr:
        raise RuntimeError(("alternating Hall witness mismatch", len(zl), len(zr),
                            len(neigh), len(neigh - zr), len(zr - neigh)))
    return sorted(zl), sorted(zr)


def main() -> None:
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
        "B": set(base.B.elements),
        "N": set(base.X0.elements),
        "A": set(base.XV.elements),
        "D": set(base.XH.elements),
        "O": set(base.R.elements),
        "H": set(base.PH.elements),
        "V": set(base.PV.elements),
    }
    sizes = {k: len(v) for k, v in fam.items()}
    expected_sizes = {"B": 359, "N": 322, "A": 19, "D": 26,
                      "O": 8, "H": 8, "V": 8}
    if sizes != expected_sizes:
        raise RuntimeError(("family-size drift", sizes))

    # Every label family must itself be independent for the product-block Hall
    # argument.  Check from explicit data, do not rely on the abstract rules.
    family_independent = {}
    for lab, F in fam.items():
        bad = []
        for x in F:
            z = (ring.NB[x] & F) - {x}
            if z:
                bad.append((x, min(z)))
                break
        family_independent[lab] = not bad
        if bad:
            raise RuntimeError(("label family not independent", lab, bad[0]))

    # Materialize the record blocks and give every record pair a stable owner id.
    owner_pair = []
    owner = {}
    block_sizes = {}
    for w in RECORD_CODE:
        count = 0
        for a in fam[w[0]]:
            for b in fam[w[1]]:
                p = (a, b)
                if p in owner:
                    raise RuntimeError(("record blocks overlap", w, p))
                owner[p] = len(owner_pair)
                owner_pair.append(p)
                count += 1
        block_sizes["".join(w)] = count
    if len(owner_pair) != EXPECTED_SCORE:
        raise RuntimeError(("record score drift", len(owner_pair), block_sizes))
    baseline = set(owner)

    # Precompute exact 5D closed-neighborhood intersections with each family.
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
        # Record blocks are disjoint, so duplicates would indicate a bug.
        if len(out) != len(set(out)):
            raise RuntimeError(("duplicate blocker owner", a, b))
        return out

    results = []
    best = None
    total_candidates = 0
    total_edges = 0

    for u in LABELS:
        for v in LABELS:
            w = (u, v)
            if w in RECORD_CODE:
                continue
            candidates = []
            adj = []
            baseline_overlap = 0
            for a in sorted(fam[u]):
                for b in sorted(fam[v]):
                    if (a, b) in baseline:
                        baseline_overlap += 1
                        continue
                    candidates.append((a, b))
                    adj.append(blockers(a, b))
            n = len(candidates)
            e = sum(map(len, adj))
            total_candidates += n
            total_edges += e
            matching, pair_l, pair_r = hopcroft_karp(adj, len(owner_pair))
            deficiency = n - matching
            rec = {
                "word": "".join(w),
                "cartesian_size": len(fam[u]) * len(fam[v]),
                "baseline_overlap": baseline_overlap,
                "external_candidates": n,
                "blocker_edges": e,
                "matching": matching,
                "deficiency": deficiency,
                "saturates_candidates": deficiency == 0,
            }
            if deficiency > 0:
                zl, zr = hall_witness(adj, pair_l, pair_r)
                if len(zl) - len(zr) != deficiency:
                    raise RuntimeError(("Hall deficiency mismatch", w, deficiency,
                                        len(zl), len(zr)))
                selected = [candidates[i] for i in zl]
                deleted = [owner_pair[j] for j in zr]
                candidate_set = (baseline - set(deleted)) | set(selected)
                expected = EXPECTED_SCORE + deficiency
                if len(candidate_set) != expected:
                    raise RuntimeError(("candidate size mismatch", w, len(candidate_set), expected))
                # The product block is independent because both factor families were
                # explicitly checked independent.  Every selected-to-baseline conflict
                # is exactly in zr by construction.  Recheck the latter exhaustively.
                deleted_ids = set(zr)
                for i in zl:
                    if not set(adj[i]) <= deleted_ids:
                        raise RuntimeError(("retained blocker", w, i))
                rec.update({
                    "hall_left": len(zl),
                    "hall_right": len(zr),
                    "candidate_score": expected,
                })
                if best is None or deficiency > best[0]:
                    best = (deficiency, w, candidate_set, rec)
            results.append(rec)
            print(json.dumps(rec, sort_keys=True), flush=True)

    status = {
        "method": "exact-bpz-single-omitted-block-hall",
        "record_score": EXPECTED_SCORE,
        "record_code": ["".join(w) for w in RECORD_CODE],
        "family_sizes": sizes,
        "family_independent": family_independent,
        "blocks_checked": len(results),
        "total_external_candidates_with_multiplicity": total_candidates,
        "total_blocker_edges_with_multiplicity": total_edges,
        "max_deficiency": max((r["deficiency"] for r in results), default=0),
        "breakthrough": best is not None,
        "best": None if best is None else best[3],
        "results": results,
    }

    if best is not None:
        deficiency, w, candidate_set, rec = best
        args.shot_dir.mkdir(parents=True, exist_ok=True)
        def point(pair):
            a, b = pair
            return "".join(str(x) for x in (ring.decode(a) + ring.decode(b)))
        points = sorted(point(p) for p in candidate_set)
        if len(points) != EXPECTED_SCORE + deficiency or len(points) != len(set(points)):
            raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir / "certificate.json").write_text(
            json.dumps({"points": points}, separators=(",", ":")) + "\n")
        (args.shot_dir / "metadata.json").write_text(json.dumps({
            "method": status["method"],
            "word": "".join(w),
            "score": len(points),
            "deficiency": deficiency,
        }, indent=2, sort_keys=True) + "\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in status.items() if k != "results"}, sort_keys=True))


if __name__ == "__main__":
    main()
