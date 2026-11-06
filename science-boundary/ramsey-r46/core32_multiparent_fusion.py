#!/usr/bin/env python3
"""Constructive 32-core/four-tail recombination from 37 Exoo R(4,6,35) parents.
Uses Bliss canonical labels to align cores, then exact 64-way tail-edge search.
Requires python-igraph at runtime. Writes only fully recounted 36-vertex seeds.
"""
import argparse
import itertools
import json
import random
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import igraph as ig

SOURCE = "https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6"
FULL = (1 << 32) - 1
PAIRS = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
TRIPLES = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))

def decode(code):
    n = ord(code[0]) - 63
    bits = (ord(c) - 63 >> k & 1 for c in code[1:] for k in (5, 4, 3, 2, 1, 0))
    a = [0] * n
    for j in range(1, n):
        for i in range(j):
            if next(bits):
                a[i] |= 1 << j
                a[j] |= 1 << i
    return a

def complement(a):
    full = (1 << len(a)) - 1
    return [full & ~r & ~(1 << i) for i, r in enumerate(a)]

def cliques(a, cand, k):
    if not k:
        return 1
    result = 0
    while cand.bit_count() >= k:
        bit = cand & -cand
        i = bit.bit_length() - 1
        cand ^= bit
        result += cliques(a, cand & a[i], k - 1)
    return result

def legal35(a):
    return not cliques(a, (1 << 35)-1, 4) and not cliques(complement(a), (1 << 35)-1, 6)

def canon_core(parent, omitted):
    omit = set(omitted)
    keep = [i for i in range(35) if i not in omit]
    edges = [(i, j) for i in range(32) for j in range(i+1, 32)
             if parent[keep[i]] >> keep[j] & 1]
    g = ig.Graph(n=32, edges=edges, directed=False)
    p = list(g.canonical_permutation())
    canon = {tuple(sorted(e)) for e in g.permute_vertices(p).get_edgelist()}
    test = {tuple(sorted((p[i], p[j]))) for i, j in edges}
    if test != canon:
        inv = [0] * 32
        for i, j in enumerate(p):
            inv[j] = i
        p = inv
        assert {tuple(sorted((p[i], p[j]))) for i, j in edges} == canon
    a = [0] * 32
    for i, j in canon:
        a[i] |= 1 << j
        a[j] |= 1 << i
    key = b"".join(row.to_bytes(4, "little") for row in a)
    tails = [sum(1 << p[i] for i, u in enumerate(keep) if parent[t] >> u & 1)
             for t in omitted]
    return key, a, tails

def reconstruct(core, tails, bits):
    a = core[:] + [0] * 4
    for i, mask in enumerate(tails):
        for u in range(32):
            if mask >> u & 1:
                a[u] |= 1 << (32+i)
                a[32+i] |= 1 << u
    for e, (i, j) in enumerate(PAIRS):
        if bits >> e & 1:
            a[32+i] |= 1 << (32+j)
            a[32+j] |= 1 << (32+i)
    return a

def local_best(core, signatures, target):
    comp = complement(core)
    pc = {}
    for x, y in itertools.combinations_with_replacement(set(signatures), 2):
        common = x & y
        edgecount = sum((core[i] & common).bit_count()
                        for i in range(32) if common >> i & 1) // 2
        independent4 = cliques(comp, FULL & ~(x | y), 4)
        pc[x, y] = pc[y, x] = (independent4, edgecount)
    best, result, evaluations = target, None, 0
    for ids in itertools.combinations_with_replacement(range(len(signatures)), 4):
        tails = tuple(signatures[i] for i in ids)
        pairs = [pc[tails[u], tails[v]] for u, v in PAIRS]
        if sum(min(q) for q in pairs) >= best:
            continue
        triple = []
        for u, v, w in TRIPLES:
            x, y, z = tails[u], tails[v], tails[w]
            triple.append((cliques(comp, FULL & ~(x | y | z), 3),
                           (x & y & z).bit_count()))
        allzero = cliques(comp, FULL & ~(tails[0]|tails[1]|tails[2]|tails[3]), 2)
        for bits in range(64):
            score = sum(pairs[i][bits >> i & 1] for i in range(6))
            if score >= best:
                continue
            for ti, tri in enumerate(TRIPLES):
                tri_bits = [bits >> PAIRS.index(tuple(sorted((tri[x], tri[y])))) & 1
                            for x, y in ((0,1), (0,2), (1,2))]
                if tri_bits == [0, 0, 0]:
                    score += triple[ti][0]
                elif tri_bits == [1, 1, 1]:
                    score += triple[ti][1]
            if bits == 0:
                score += allzero
            elif bits == 63:
                score += 1
            evaluations += 1
            if score < best:
                best, result = score, (tails, bits)
    return best, result, evaluations

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--g6", type=Path)
    p.add_argument("--samples-per-parent", type=int, default=2000)
    p.add_argument("--max-signatures", type=int, default=24)
    p.add_argument("--rng", type=int, default=20261106)
    p.add_argument("--outdir", type=Path, required=True)
    args = p.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    raw = args.g6.read_text() if args.g6 else urllib.request.urlopen(SOURCE, timeout=45).read().decode("ascii")
    parents = []
    for code in raw.splitlines():
        a = decode(code)
        assert len(a) == 35
        if not legal35(a):
            a = complement(a)
        assert legal35(a)
        parents.append(a)
    assert len(parents) == 37
    print("loaded 37 valid parents", flush=True)
    rnd = random.Random(args.rng)
    deleted = list(itertools.combinations(range(35), 3))
    classes = {}
    for pi, parent in enumerate(parents):
        for omitted in rnd.sample(deleted, min(args.samples_per_parent, len(deleted))):
            key, core, tails = canon_core(parent, omitted)
            if key not in classes:
                classes[key] = (core, defaultdict(set))
            for tail in tails:
                classes[key][1][tail].add(pi)
        print("indexed", pi+1, "parents; unique core classes", len(classes),
              "seconds", round(time.monotonic()-t0, 1), flush=True)
    order = sorted(classes.values(),
                   key=lambda c: (-len(c[1]), -len({pi for ids in c[1].values() for pi in ids})))
    best = 15
    best_record = None
    stats = Counter()
    for ci, (core, candidates) in enumerate(order):
        family = {pi for ids in candidates.values() for pi in ids}
        if len(family) < 2:
            continue
        stats["cross_parent_classes"] += 1
        sig = sorted(candidates, key=lambda x: (-len(candidates[x]), x))[:args.max_signatures]
        val, proposal, counted = local_best(core, sig, best)
        stats["scored_six_bit_assignments"] += counted
        if val < best:
            best = val
            tails, bits = proposal
            g = reconstruct(core, tails, bits)
            c4 = cliques(g, (1 << 36)-1, 4)
            i6 = cliques(complement(g), (1 << 36)-1, 6)
            assert c4 + i6 == best
            rows = ["".join("1" if g[i] >> j & 1 else "0" for j in range(36))
                    for i in range(36)]
            (args.outdir / "best-36.json").write_text(json.dumps({"adjacency": rows}) + "\n")
            best_record = {"defects": best, "K4": c4, "I6": i6,
                           "edges": sum(r.bit_count() for r in g)//2,
                           "parent_count_for_core": len(family), "core_index": ci}
            print("BEST", json.dumps(best_record), flush=True)
            if best == 0:
                break
        if ci and ci % 1000 == 0:
            print("scanned", ci, "classes; best", best,
                  "seconds", round(time.monotonic()-t0,1), flush=True)
    result = {"campaign": "core32-multiparent-four-tail",
              "source": SOURCE, "parents": 37,
              "samples_per_parent": args.samples_per_parent,
              "unique_core_classes": len(classes),
              "baseline_to_beat": 14, "best_improvement": best_record,
              "stats": dict(stats), "seconds": round(time.monotonic()-t0,2)}
    (args.outdir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print("SUMMARY", json.dumps(result), flush=True)

if __name__ == "__main__":
    main()
