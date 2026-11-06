#!/usr/bin/env python3
"""Construct Ramsey(4,6) graph on 36 vertices by six-tail fusion over valid 30-core.

Enumerates every individually legal tail neighborhood and searches a pool of
joint six-tail assignments. All 15 tail-tail edges are optimized exactly each
step, accounting for every K4/I6 intersection motif. Check candidate by an
independent full bitset recount before saving.
"""
import argparse
import functools
import itertools
import json
import math
import random
import time
import urllib.request
from pathlib import Path
import numpy as np

URL = 'https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6'
OMIT = (1, 12, 16, 24, 29)
P = list(itertools.combinations(range(6), 2))
PI = {e: i for i, e in enumerate(P)}
TRI = list(itertools.combinations(range(6), 3))
QUAD = list(itertools.combinations(range(6), 4))
FIVE = list(itertools.combinations(range(6), 5))
N = 30
FULL = (1 << N) - 1

def decode(code):
    n = ord(code[0]) - 63
    bits = (ord(c) - 63 >> s & 1 for c in code[1:]
            for s in (5, 4, 3, 2, 1, 0))
    a = [0] * n
    for j in range(1, n):
        for i in range(j):
            if next(bits):
                a[i] |= 1 << j
                a[j] |= 1 << i
    return a

def comp(a):
    mask = (1 << len(a)) - 1
    return [mask & ~row & ~(1 << i) for i, row in enumerate(a)]

def count(a, candidates, k):
    if k == 0:
        return 1
    total = 0
    while candidates.bit_count() >= k:
        bit = candidates & -candidates
        i = bit.bit_length() - 1
        candidates ^= bit
        total += count(a, candidates & a[i], k - 1)
    return total

def clique_masks(a, k):
    out = []
    def rec(candidates, chosen, left):
        if not left:
            out.append(chosen)
            return
        while candidates.bit_count() >= left:
            bit = candidates & -candidates
            i = bit.bit_length() - 1
            candidates ^= bit
            rec(candidates & a[i], chosen | bit, left - 1)
    rec((1 << len(a)) - 1, 0, k)
    return out

def legal_domains(core):
    triangles = clique_masks(core, 3)
    i5 = clique_masks(comp(core), 5)
    occ = [0] * N
    for m in triangles + i5:
        while m:
            v = (m & -m).bit_length() - 1
            m &= m - 1
            occ[v] += 1
    result = []
    def propagate(one, zero):
        while True:
            if one & zero:
                return None
            used = one.bit_count()
            free = FULL & ~(one | zero)
            if used > 17 or used + free.bit_count() < 6:
                return None
            changed = False
            if used == 17 and free:
                zero |= free
                changed = True
            if used + free.bit_count() == 6 and free:
                one |= free
                changed = True
            for mask in triangles:
                k = (one & mask).bit_count()
                if k == 3:
                    return None
                if k == 2:
                    u = mask & ~(one | zero)
                    if u.bit_count() == 1:
                        zero |= u
                        changed = True
            for mask in i5:
                k = (zero & mask).bit_count()
                if k == 5:
                    return None
                if k == 4:
                    u = mask & ~(one | zero)
                    if u.bit_count() == 1:
                        one |= u
                        changed = True
            if not changed:
                return one, zero
    def dfs(one, zero):
        p = propagate(one, zero)
        if p is None:
            return
        one, zero = p
        free = FULL & ~(one | zero)
        if not free:
            result.append(one)
            return
        v = max((i for i in range(N) if free >> i & 1),
                key=lambda i: occ[i])
        bit = 1 << v
        dfs(one | bit, zero)
        dfs(one, zero | bit)
    dfs(0, 0)
    return result

def features():
    x = np.arange(32768, dtype=np.int32)
    out = [((x >> i) & 1).astype(np.int16) for i in range(15)]
    def edge_mask(vertices):
        return sum(1 << PI[a, b]
                   for a, b in itertools.combinations(vertices, 2))
    for collection in (TRI, QUAD):
        for vertices in collection:
            mask = edge_mask(vertices)
            out.extend([((x & mask) == mask).astype(np.int16),
                        ((x & mask) == 0).astype(np.int16)])
    for vertices in FIVE:
        out.append(((x & edge_mask(vertices)) == 0).astype(np.int16))
    out.append((x == 0).astype(np.int16))
    return np.stack(out, axis=1)

def construct(core, domain, ids, bits):
    graph = core[:] + [0] * 6
    for t, index in enumerate(ids):
        mask = domain[index]
        for v in range(N):
            if mask >> v & 1:
                graph[v] |= 1 << (N + t)
                graph[N + t] |= 1 << v
    for j, (u, v) in enumerate(P):
        if bits >> j & 1:
            graph[N + u] |= 1 << (N + v)
            graph[N + v] |= 1 << (N + u)
    return graph

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--g6', type=Path)
    parser.add_argument('--rng', type=int, default=42)
    parser.add_argument('--steps', type=int, default=10000)
    parser.add_argument('--outdir', type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    if args.g6:
        src = args.g6.read_text()
    else:
        src = urllib.request.urlopen(URL, timeout=45).read().decode('ascii')
    parent = decode(src.splitlines()[0])
    assert len(parent) == 35
    valid = lambda graph: (count(graph, (1 << len(graph)) - 1, 4) == 0 and
                          count(comp(graph), (1 << len(graph)) - 1, 6) == 0)
    assert valid(parent)
    keep = [i for i in range(35) if i not in OMIT]
    core = [sum(1 << j for j, v in enumerate(keep)
                if parent[u] >> v & 1) for u in keep]
    assert valid(core)
    domain = legal_domains(core)
    known = [sum(1 << j for j, v in enumerate(keep)
                 if parent[u] >> v & 1) for u in OMIT]
    assert all(mask in domain for mask in known)
    print('legal domain', len(domain), 'K3', len(clique_masks(core, 3)),
          'I5', len(clique_masks(comp(core), 5)), flush=True)
    assert len(domain) == 1239
    feature_matrix = features()
    complement = comp(core)
    rng = random.Random(args.rng)
    nearest = []
    for i, x in enumerate(domain):
        distances = sorted(((x ^ y).bit_count(), j)
                           for j, y in enumerate(domain) if i != j)
        nearest.append([j for _, j in distances[:20]])

    @functools.lru_cache(maxsize=100000)
    def pair(x, y):
        common = x & y
        k4 = sum((core[i] & common).bit_count()
                 for i in range(N) if common >> i & 1) // 2
        return count(complement, FULL & ~(x | y), 4), k4

    @functools.lru_cache(maxsize=250000)
    def triple(x, y, z):
        return (x & y & z).bit_count(), count(
            complement, FULL & ~(x | y | z), 3)

    @functools.lru_cache(maxsize=150000)
    def quad(x, y, z, w):
        return count(complement, FULL & ~(x | y | z | w), 2)

    def evaluate(ids):
        masks = [domain[i] for i in ids]
        pcs = [pair(*sorted((masks[u], masks[v]))) for u, v in P]
        base = sum(a for a, b in pcs)
        weights = [b - a for a, b in pcs]
        for subset in TRI:
            x, y, z = sorted(masks[i] for i in subset)
            a, b = triple(x, y, z)
            weights.extend((a, b))
        for subset in QUAD:
            x = sorted(masks[i] for i in subset)
            weights.extend((1, quad(*x)))
        for subset in FIVE:
            anti = FULL
            for t in subset:
                anti &= ~masks[t]
            weights.append(anti.bit_count())
        weights.append(1)
        score = base + feature_matrix @ np.asarray(weights, dtype=np.int16)
        best_bits = int(score.argmin())
        return int(score[best_bits]), best_bits

    def verify(ids, bits, score):
        graph = construct(core, domain, ids, bits)
        full = (1 << 36) - 1
        k4, i6 = count(graph, full, 4), count(comp(graph), full, 6)
        assert k4 + i6 == score, (k4, i6, score)
        return graph, k4, i6

    seed_ids = tuple(sorted(domain.index(mask) for mask in known))
    start = time.time()
    steps = 0
    best = 10 ** 9
    pool = []
    visited = set()
    best_meta = {}
    while steps < args.steps:
        if len(pool) >= 2 and rng.random() < 0.25:
            first, second = rng.sample(pool[:min(15, len(pool))], 2)
            ids = [rng.choice([first[1][j], second[1][j]]) for j in range(6)]
        elif pool and rng.random() < 0.7:
            ids = list(rng.choice(pool[:min(12, len(pool))])[1])
            for _ in range(rng.randint(2, 4)):
                j = rng.randrange(6)
                ids[j] = rng.choice(nearest[ids[j]])
        else:
            ids = list(seed_ids) + [rng.choice(nearest[rng.choice(seed_ids)])]
        ids = tuple(sorted(ids))
        val, bits = evaluate(ids)
        temp = 7.0 + rng.randrange(14)
        for _ in range(min(350, args.steps - steps)):
            steps += 1
            if ids not in visited:
                visited.add(ids)
                if val < best:
                    best = val
                    graph, k4, i6 = verify(ids, bits, val)
                    rows = [''.join('1' if graph[i] >> j & 1 else '0'
                                    for j in range(36)) for i in range(36)]
                    (args.outdir / 'best-36.json').write_text(
                        json.dumps({'adjacency': rows}) + '\n')
                    best_meta = {
                        'defects': val, 'K4': k4, 'I6': i6,
                        'edges': sum(r.bit_count() for r in graph) // 2,
                        'steps': steps}
                    print('BEST', best_meta, flush=True)
                    if val == 0:
                        break
                pool.append((val, ids))
                pool.sort(key=lambda p: p[0])
                pool = pool[:20]
            proposal = list(ids)
            j = rng.randrange(6)
            proposal[j] = (rng.choice(nearest[proposal[j]])
                           if rng.random() < .85
                           else rng.randrange(len(domain)))
            if rng.random() < .13:
                k = rng.randrange(6)
                proposal[k] = rng.choice(nearest[proposal[k]])
            proposal = tuple(sorted(proposal))
            score, new_bits = evaluate(proposal)
            if score <= val or rng.random() < math.exp((val - score) / temp):
                ids, val, bits = proposal, score, new_bits
            temp *= .98
        if best == 0:
            break
    result = {
        'campaign': 'core30-six-tail-catalogue-coordinated-repair',
        'parent_index': 0, 'omitted': OMIT,
        'legal_tail_masks': len(domain),
        'steps': steps, 'seed': args.rng,
        'best': best_meta,
        'elapsed_seconds': round(time.time() - start, 2)}
    (args.outdir / 'summary.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print('SUMMARY', json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
