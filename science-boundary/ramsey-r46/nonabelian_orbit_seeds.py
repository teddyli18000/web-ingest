#!/usr/bin/env python3
"""Reconstruct and independently recount nonabelian 36-vertex near-misses.

Vertex set S3 x S3, with either full left-regular Cayley symmetry,
a subgroup C3 x C3, or a subgroup C3. These are NOT Ramsey witnesses.
"""
import argparse
import itertools
import json
from pathlib import Path

PERMS = list(itertools.permutations(range(3)))
GROUP = list(itertools.product(PERMS, PERMS))
IDENTITY = (0, 1, 2)
INDEX = {v: i for i, v in enumerate(GROUP)}
CYCLE = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]
MASKS = {
    "cayley": [1362268],
    "h9": [2167832364490870542, 46],
    "h3": [6632679916337208862, 9658604789484290829, 14244007044121113879, 182058],
}
EXPECT = {"cayley": (45, 0), "h9": (36, 0), "h3": (33, 0)}

def compose(p, q):
    return tuple(p[q[k]] for k in range(3))

def product(a, b):
    return INDEX[compose(GROUP[a][0], GROUP[b][0]), compose(GROUP[a][1], GROUP[b][1])]

def inverse(a):
    p, q = GROUP[a]
    return INDEX[tuple(p.index(k) for k in range(3)), tuple(q.index(k) for k in range(3))]

def group_orbits(level):
    if level == "cayley":
        orbits = []
        done = set()
        for a in range(1, 36):
            if a not in done:
                o = {a, inverse(a)}
                orbits.append(sorted(o))
                done.update(o)
        assert len(orbits) == 25
        return [[(u, v) for u in range(36) for v in range(u + 1, 36)
                 if product(inverse(u), v) in o] for o in orbits]
    if level == "h9":
        subgroup = [INDEX[p, q] for p, q in itertools.product(CYCLE, CYCLE)]
    elif level == "h3":
        subgroup = [INDEX[p, IDENTITY] for p in CYCLE]
    else:
        raise ValueError(level)
    done = set()
    orbits = []
    for edge in itertools.combinations(range(36), 2):
        if edge in done:
            continue
        orb = {tuple(sorted((product(h, edge[0]), product(h, edge[1])))) for h in subgroup}
        done.update(orb)
        orbits.append(sorted(orb))
    assert len(orbits) == 630 // len(subgroup)
    return orbits

def graph(level):
    orbits = group_orbits(level)
    mask = MASKS[level]
    rows = [[0] * 36 for _ in range(36)]
    for i, o in enumerate(orbits):
        if mask[i // 64] >> (i % 64) & 1:
            for u, v in o:
                rows[u][v] = rows[v][u] = 1
    return ["".join(map(str, row)) for row in rows]

def count_cliques(rows, k, complement=False):
    n = len(rows)
    full = (1 << n) - 1
    adj = [sum(1 << j for j in range(n) if j != i and
               (rows[i][j] == "0" if complement else rows[i][j] == "1"))
           for i in range(n)]
    def rec(cand, size):
        if size == 0:
            return 1
        total = 0
        while cand.bit_count() >= size:
            bit = cand & -cand
            u = bit.bit_length() - 1
            cand ^= bit
            total += rec(cand & adj[u], size - 1)
        return total
    return rec(full, k)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", choices=MASKS.keys(), default="h3")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = graph(args.level)
    assert all(rows[i][j] == rows[j][i] for i in range(36) for j in range(36))
    assert all(rows[i][i] == "0" for i in range(36))
    k4, i6 = count_cliques(rows, 4), count_cliques(rows, 6, True)
    assert (k4, i6) == EXPECT[args.level]
    degrees = [row.count("1") for row in rows]
    result = {"group": "S3 x S3", "symmetry": args.level,
              "vertices": 36, "edges": sum(degrees) // 2,
              "degrees": sorted(set(degrees)), "K4": k4, "I6": i6,
              "defects": k4 + i6, "orbit_mask_words": MASKS[args.level]}
    print(json.dumps(result, sort_keys=True))
    if args.out:
        args.out.write_text(json.dumps({"adjacency": rows}) + "\n")

if __name__ == "__main__":
    main()
