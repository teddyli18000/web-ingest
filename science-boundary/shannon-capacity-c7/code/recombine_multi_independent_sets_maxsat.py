#!/usr/bin/env python3
"""Exact maximum independent set in the union of >=2 C7^10 certificates.

For verifier-valid independent sets S_1,...,S_m, every vertex in the universal
intersection I=cap S_i is isolated in the conflict graph on U=union S_i: any
other union vertex belongs to some S_j, while I is contained in S_j, so the two
cannot conflict.  Hence all of I is always retained.

We build the exact conflict graph on D=U\I using a base-7 confusability trie and
solve maximum independent set exactly with weighted MaxSAT (RC2): one hard
binary clause per conflict edge and one unit soft clause of weight 1 per D
vertex.  The final score is |I| + optimum(D).  Any score >=134754 is materialized
for independent Few Shots verification by the calling workflow.
"""
import argparse
import json
import sys
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF


def load(path: Path) -> set[str]:
    obj = json.loads(path.read_text())
    pts = obj.get("points")
    if not isinstance(pts, list):
        raise ValueError(f"bad certificate {path}")
    s = set(pts)
    if len(s) != len(pts):
        raise ValueError(f"duplicate point in {path}")
    if any(len(p) != 10 or any(c not in "0123456" for c in p) for p in s):
        raise ValueError(f"bad point in {path}")
    return s


def conflict(a: str, b: str) -> bool:
    return all((ord(x) - ord(y)) % 7 in (0, 1, 6) for x, y in zip(a, b))


def exact_edges(words: list[str]):
    """Enumerate every unordered conflict edge exactly with a digit trie."""
    children: list[dict[int, int]] = [{}]
    terminal = [-1]
    for j, w in enumerate(words):
        node = 0
        for ch in w:
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
    edges = []
    visits = 0
    degree = [0] * len(words)
    for i, w in enumerate(words):
        frontier = [0]
        for ch in w:
            digs = allowed[ord(ch) - 48]
            nxtf = []
            for node in frontier:
                c = children[node]
                for d in digs:
                    z = c.get(d)
                    if z is not None:
                        nxtf.append(z)
            visits += len(nxtf)
            frontier = nxtf
            if not frontier:
                break
        for node in frontier:
            j = terminal[node]
            if j > i:
                if not conflict(w, words[j]):
                    raise RuntimeError("trie edge replay failed")
                edges.append((i, j))
                degree[i] += 1
                degree[j] += 1
    return edges, degree, len(children), visits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("certificates", nargs="+", type=Path)
    ap.add_argument("--target", type=int, default=134754)
    args = ap.parse_args()
    if len(args.certificates) < 2:
        raise SystemExit("need at least two certificates")

    sets = [load(p) for p in args.certificates]
    intersection = set.intersection(*sets)
    union = set.union(*sets)
    diff = sorted(union - intersection)

    # Defensive proof of isolation of the universal intersection from the union.
    # It follows abstractly from input independence.  We verify the premise that
    # every union vertex belongs to at least one input set and record membership.
    membership = []
    for v in diff:
        mask = 0
        for i, s in enumerate(sets):
            if v in s:
                mask |= 1 << i
        if not mask:
            raise RuntimeError("union membership drift")
        membership.append(mask)

    edges, degree, trie_nodes, trie_visits = exact_edges(diff)
    wcnf = WCNF()
    # Variable i+1 means keep diff[i].
    for i, j in edges:
        wcnf.append([-(i + 1), -(j + 1)])
    for i in range(len(diff)):
        wcnf.append([i + 1], weight=1)

    with RC2(wcnf, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("MaxSAT returned no model")
    pos = {x for x in model if x > 0}
    kept = [diff[i] for i in range(len(diff)) if i + 1 in pos]
    score = len(intersection) + len(kept)
    expected = len(union) - int(cost)
    if score != expected:
        raise RuntimeError(f"score/cost mismatch {score} != {expected}")

    # Exact replay of every selected conflict edge.
    selected = [i + 1 in pos for i in range(len(diff))]
    bad = [(i, j) for i, j in edges if selected[i] and selected[j]]
    if bad:
        raise RuntimeError(f"selected conflict edges: {bad[:8]}")

    st = {
        "method": "exact-multi-union-maxsat",
        "inputs": len(sets),
        "input_sizes": [len(s) for s in sets],
        "universal_intersection": len(intersection),
        "union_size": len(union),
        "difference_vertices": len(diff),
        "conflict_edges": len(edges),
        "degree_min": min(degree, default=0),
        "degree_max": max(degree, default=0),
        "degree_sum": sum(degree),
        "trie_nodes": trie_nodes,
        "trie_visits": trie_visits,
        "rc2_cost": int(cost),
        "selected_difference": len(kept),
        "score": score,
        "gain_over_best_input": score - max(map(len, sets)),
        "target": args.target,
        "membership_histogram": {},
    }
    hist = {}
    for m in membership:
        hist[str(m)] = hist.get(str(m), 0) + 1
    st["membership_histogram"] = hist

    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    if score >= args.target:
        out = intersection | set(kept)
        if len(out) != score:
            raise RuntimeError("output size drift")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"points": sorted(out)}, separators=(",", ":")) + "\n")
    print(json.dumps(st, sort_keys=True))


if __name__ == "__main__":
    main()
