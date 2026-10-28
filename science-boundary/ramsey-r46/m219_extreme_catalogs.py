#!/usr/bin/env python3
"""Authenticate and extract the tiny local extreme strata needed at m=219.

Reads the complete McKay R(3,6,11) and R(4,5,24) catalogues and records the
exact e=26 and e=116 strata respectively.  These are the local pair forced at
four of the five degree-11 vertices in every m=219, n11=5 candidate.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path


def decode_graph6(s: str) -> list[int]:
    s = s.strip()
    if s.startswith(">>graph6<<"):
        s = s[len(">>graph6<<"):]
    if not s:
        raise ValueError("empty graph6")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 supported")
    bits = []
    for ch in s[1:]:
        x = ord(ch) - 63
        if not 0 <= x < 64:
            raise ValueError("invalid graph6")
        bits.extend((x >> k) & 1 for k in range(5, -1, -1))
    need = n * (n - 1) // 2
    if len(bits) < need:
        raise ValueError("truncated graph6")
    adj = [0] * n
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
            p += 1
    return adj


def edge_count(adj: list[int]) -> int:
    return sum(x.bit_count() for x in adj) // 2


def degree_sequence(adj: list[int]) -> list[int]:
    return sorted(x.bit_count() for x in adj)


def triangle_count(adj: list[int]) -> int:
    total = 0
    for i in range(len(adj)):
        js = adj[i] & ~((1 << (i + 1)) - 1)
        while js:
            b = js & -js
            j = b.bit_length() - 1
            total += (adj[i] & adj[j] & ~((1 << (j + 1)) - 1)).bit_count()
            js ^= b
    return total


def independent_set_hist(adj: list[int], max_k: int = 6) -> dict[str, int]:
    # n<=24 and only 11 selected graphs: simple subset DP by combinations is OK.
    import itertools
    n = len(adj)
    out = {}
    for k in range(2, max_k + 1):
        c = 0
        for ss in itertools.combinations(range(n), k):
            ok = True
            for a in range(k):
                for b in range(a + 1, k):
                    if (adj[ss[a]] >> ss[b]) & 1:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                c += 1
        out[str(k)] = c
    return out


def iter_g6(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith(">>"):
                continue
            yield s, decode_graph6(s)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def scan(path: Path, n: int, target_edges: int, expected_total: int, expected_hits: int) -> dict:
    total = 0
    hits = []
    edge_hist = Counter()
    for g6, adj in iter_g6(path):
        total += 1
        assert len(adj) == n, (path, len(adj), n)
        e = edge_count(adj)
        edge_hist[e] += 1
        if e == target_edges:
            hits.append({
                "graph6": g6,
                "edges": e,
                "degree_sequence": degree_sequence(adj),
                "triangles": triangle_count(adj),
                "independent_sets": independent_set_hist(adj, 5),
            })
    assert total == expected_total, (path, total, expected_total)
    assert len(hits) == expected_hits, (path, len(hits), expected_hits)
    return {
        "path": str(path),
        "sha256": sha256(path),
        "total_graphs": total,
        "target_edges": target_edges,
        "target_count": len(hits),
        "edge_histogram": {str(k): v for k, v in sorted(edge_hist.items())},
        "target_graphs": hits,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r36-11", type=Path, required=True)
    ap.add_argument("--r45-24", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    out = {
        "source": "Brendan McKay Combinatorial Data Ramsey catalogues",
        "source_urls": {
            "r36_11": "https://users.cecs.anu.edu.au/~bdm/data/r36_11.g6.gz",
            "r45_24": "https://users.cecs.anu.edu.au/~bdm/data/r45_24.g6",
        },
        "A26": scan(args.r36_11, 11, 26, 30395, 2),
        "B116": scan(args.r45_24, 24, 116, 352366, 9),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "A26_count": out["A26"]["target_count"],
        "B116_count": out["B116"]["target_count"],
        "A26_sha256": out["A26"]["sha256"],
        "B116_sha256": out["B116"]["sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
