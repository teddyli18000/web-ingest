#!/usr/bin/env python3
"""Inventory McKay's public edge-extremal Ramsey(4,5) archive.

The archive is a published external input.  This script does not assume member
names: it streams every regular file, accepts graph6 records (with or without a
header), and records exact counts by (number of vertices, number of edges).
That makes it easy to see exactly which low/high edge strata are present before
using them as a complete finite input to a Ramsey gluing computation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path


def graph6_order_and_edges(raw: bytes) -> tuple[int, int]:
    s = raw.strip()
    if s.startswith(b">>graph6<<"):
        s = s[len(b">>graph6<<") :]
    if not s:
        raise ValueError("empty graph6 record")
    if s[0] == 126:
        raise ValueError("only short graph6 records (n <= 62) are expected")
    n = s[0] - 63
    if not 0 <= n <= 62:
        raise ValueError("invalid short graph6 order")
    need = n * (n - 1) // 2
    got = 0
    edges = 0
    for ch in s[1:]:
        v = ch - 63
        if not 0 <= v < 64:
            raise ValueError("invalid graph6 character")
        take = min(6, need - got)
        if take <= 0:
            break
        for shift in range(5, 5 - take, -1):
            edges += (v >> shift) & 1
        got += take
    if got < need:
        raise ValueError(f"truncated graph6 record for n={n}: {got} < {need}")
    return n, edges


def encode_short_graph6(n: int, edge_bits: list[int]) -> bytes:
    need = n * (n - 1) // 2
    assert len(edge_bits) == need
    bits = edge_bits + [0] * ((-need) % 6)
    out = bytearray([n + 63])
    for i in range(0, len(bits), 6):
        v = 0
        for bit in bits[i : i + 6]:
            v = (v << 1) | bit
        out.append(v + 63)
    return bytes(out)


def self_test() -> None:
    for n in range(1, 10):
        need = n * (n - 1) // 2
        for bits in ([0] * need, [1] * need, [(i * 7 + n) & 1 for i in range(need)]):
            g6 = encode_short_graph6(n, list(bits))
            got_n, got_e = graph6_order_and_edges(g6)
            assert got_n == n
            assert got_e == sum(bits), (n, got_e, sum(bits), g6)
    print("r45-extreme inventory self-test ok")


def inventory(archive: Path) -> dict:
    sha256 = hashlib.sha256(archive.read_bytes()).hexdigest()
    counts: dict[int, Counter[int]] = defaultdict(Counter)
    members = []
    records = 0
    with tarfile.open(archive, "r:gz") as tf:
        for info in tf.getmembers():
            if not info.isfile():
                continue
            member_counts: Counter[tuple[int, int]] = Counter()
            f = tf.extractfile(info)
            if f is None:
                continue
            for line_number, raw in enumerate(f, 1):
                s = raw.strip()
                if not s or s.startswith(b">>") and not s.startswith(b">>graph6<<"):
                    continue
                try:
                    n, e = graph6_order_and_edges(s)
                except ValueError as exc:
                    raise ValueError(f"{info.name}:{line_number}: {exc}") from exc
                counts[n][e] += 1
                member_counts[(n, e)] += 1
                records += 1
            members.append(
                {
                    "name": info.name,
                    "size_bytes": info.size,
                    "records": sum(member_counts.values()),
                    "counts": [
                        {"n": n, "edges": e, "count": c}
                        for (n, e), c in sorted(member_counts.items())
                    ],
                }
            )
    return {
        "source": "https://users.cecs.anu.edu.au/~bdm/data/r45extreme.tar.gz",
        "archive_sha256": sha256,
        "total_records": records,
        "counts": {
            str(n): {str(e): c for e, c in sorted(ec.items())}
            for n, ec in sorted(counts.items())
        },
        "members": members,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("inventory")
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    result = inventory(args.archive)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "members"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
