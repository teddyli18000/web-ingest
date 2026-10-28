#!/usr/bin/env python3
"""Read-only statistics for public graph6 Ramsey catalogues.

No archive member is extracted or executed.  The r45 extreme tarball is read
member-by-member in memory; only regular-file bytes that parse as graph6 lines
contribute.  This is used to derive exact edge-count support for structural
R(4,6,36) endpoint arguments.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import tarfile
from collections import Counter, defaultdict
from pathlib import Path


def graph6_n_edges(raw: bytes) -> tuple[int, int]:
    s = raw.strip()
    if s.startswith(b">>graph6<<"):
        s = s[len(b">>graph6<<"):]
    if not s:
        raise ValueError("empty graph6")
    x = s[0] - 63
    if not 0 <= x <= 62:
        raise ValueError("only graph6 n<=62 is expected")
    n = x
    need = n * (n - 1) // 2
    ones = 0
    seen = 0
    for ch in s[1:]:
        v = ch - 63
        if not 0 <= v < 64:
            raise ValueError("bad graph6 byte")
        for bit in range(5, -1, -1):
            if seen >= need:
                break
            ones += (v >> bit) & 1
            seen += 1
    if seen != need:
        raise ValueError("truncated graph6")
    return n, ones


def add_lines(data: bytes, hist: dict[int, Counter], counts: Counter) -> None:
    for raw in data.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith(b">>"):
            continue
        n, e = graph6_n_edges(raw)
        hist[n][e] += 1
        counts[n] += 1


def summarize(hist: dict[int, Counter], counts: Counter) -> dict:
    out = {}
    for n in sorted(hist):
        keys = sorted(hist[n])
        out[str(n)] = {
            "graphs_read": counts[n],
            "min_edges": keys[0],
            "max_edges": keys[-1],
            "edge_hist": {str(e): hist[n][e] for e in keys},
        }
    return out


def tar45(path: Path) -> dict:
    hist: dict[int, Counter] = defaultdict(Counter); counts = Counter(); members = []
    with tarfile.open(path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            f = tf.extractfile(m)
            if f is None:
                continue
            data = f.read()
            before = sum(counts.values())
            try:
                add_lines(data, hist, counts)
            except ValueError:
                continue
            after = sum(counts.values())
            if after > before:
                members.append({"name": m.name, "bytes": len(data), "graphs": after - before})
    return {"kind": "r45extreme", "members_used": members, "by_n": summarize(hist, counts)}


def read_g6_path(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            return f.read()
    return path.read_bytes()


def r36(paths: list[Path]) -> dict:
    hist: dict[int, Counter] = defaultdict(Counter); counts = Counter(); files = []
    for p in paths:
        data = read_g6_path(p)
        before = sum(counts.values()); add_lines(data, hist, counts); after = sum(counts.values())
        files.append({"name": p.name, "bytes_uncompressed": len(data), "graphs": after - before})
    return {"kind": "complete-r36-catalogues", "files": files, "by_n": summarize(hist, counts)}


def self_test() -> None:
    # n=4, no edges and K4 are graph6 strings C? and C~ respectively.
    assert graph6_n_edges(b"C?") == (4, 0)
    assert graph6_n_edges(b"C~") == (4, 6)
    print("ramsey-catalog-extremes self-test ok")


def main() -> None:
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tar45"); t.add_argument("archive", type=Path); t.add_argument("--output", type=Path, required=True)
    r = sub.add_parser("r36"); r.add_argument("paths", type=Path, nargs="+"); r.add_argument("--output", type=Path, required=True)
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return
    result = tar45(a.archive) if a.cmd == "tar45" else r36(a.paths)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"kind": result["kind"], "n": sorted(result["by_n"])}, sort_keys=True))


if __name__ == "__main__": main()
