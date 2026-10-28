#!/usr/bin/env python3
"""Generate deterministic randomized 15-regular graphs on 36 vertices.

Start from a 15-regular circulant (distances 1..7 and 18) and apply many
random valid 2-switches.  Every switch preserves simplicity and every vertex
degree exactly.  These graphs are deliberately only search seeds: they are
not claimed Ramsey graphs.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

N = 36
D = 15


def initial_graph() -> list[set[int]]:
    adj = [set() for _ in range(N)]
    for i in range(N):
        for d in range(1, 8):
            j = (i + d) % N
            adj[i].add(j)
            adj[j].add(i)
        j = (i + N // 2) % N
        adj[i].add(j)
        adj[j].add(i)
    assert all(len(a) == D for a in adj)
    return adj


def edges(adj: list[set[int]]) -> list[tuple[int, int]]:
    return [(u, v) for u in range(N) for v in adj[u] if u < v]


def randomize(seed: int, switches: int) -> tuple[list[set[int]], int]:
    rng = random.Random(seed)
    adj = initial_graph()
    accepted = 0
    attempts = 0
    while accepted < switches:
        attempts += 1
        es = edges(adj)
        a, b = es[rng.randrange(len(es))]
        c, d = es[rng.randrange(len(es))]
        if len({a, b, c, d}) != 4:
            continue
        if rng.randrange(2):
            c, d = d, c
        # Replace ab, cd by ac, bd when both new edges are absent.
        if c in adj[a] or d in adj[b] or a == c or b == d:
            continue
        adj[a].remove(b)
        adj[b].remove(a)
        adj[c].remove(d)
        adj[d].remove(c)
        adj[a].add(c)
        adj[c].add(a)
        adj[b].add(d)
        adj[d].add(b)
        accepted += 1
    assert all(len(a) == D for a in adj)
    assert len(edges(adj)) == N * D // 2
    return adj, attempts


def rows(adj: list[set[int]]) -> list[str]:
    out = ["".join("1" if j in adj[i] else "0" for j in range(N)) for i in range(N)]
    for i in range(N):
        assert out[i][i] == "0"
        for j in range(N):
            assert out[i][j] == out[j][i]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--switches", type=int, default=20_000)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.switches < 0:
        ap.error("--switches must be nonnegative")
    adj, attempts = randomize(args.seed, args.switches)
    cert = {"adjacency": rows(adj)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cert, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "seed": args.seed,
        "switches": args.switches,
        "attempts": attempts,
        "vertices": N,
        "degree": D,
        "edges": N * D // 2,
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
