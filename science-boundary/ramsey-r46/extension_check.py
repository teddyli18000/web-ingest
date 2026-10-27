#!/usr/bin/env python3
"""Exact one-vertex extension test for the 37 published R(4,6,35) graphs.

For a (4,6)-graph G and a new vertex x, let S=N_G'(x) among the old
vertices. G+x is again a (4,6)-graph iff:
  * S contains no triangle of G, and
  * S hits every independent 5-set of G.

The program independently solves this finite feasibility problem two ways:
(1) a small CNF/DPLL solver, and (2) direct hitting-set branching. Agreement is
required. Input graphs are fetched from Exoo's public 2012 collection unless
paths are supplied explicitly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

EXOO_BASE = "https://cs.indstate.edu/ge/RAMSEY/R46/h{index:04d}"
N_PUBLISHED = 37


def parse_matrix(text: str) -> list[int]:
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    n = len(rows)
    if n == 0 or any(len(r) != n or set(r) - {"0", "1"} for r in rows):
        raise ValueError("not a square 0/1 matrix")
    adj = []
    for i, row in enumerate(rows):
        if row[i] != "0":
            raise ValueError(f"loop at {i}")
        mask = 0
        for j, c in enumerate(row):
            if c == "1":
                mask |= 1 << j
        adj.append(mask)
    for i in range(n):
        for j in range(i + 1, n):
            if ((adj[i] >> j) & 1) != ((adj[j] >> i) & 1):
                raise ValueError(f"asymmetry at {i},{j}")
    return adj


def complement(adj: list[int]) -> list[int]:
    n = len(adj)
    full = (1 << n) - 1
    return [full & ~a & ~(1 << i) for i, a in enumerate(adj)]


def has_clique(adj: list[int], k: int) -> bool:
    n = len(adj)

    def rec(cand: int, depth: int) -> bool:
        if depth == k:
            return True
        need = k - depth
        while cand.bit_count() >= need:
            b = cand & -cand
            v = b.bit_length() - 1
            cand ^= b
            if rec(cand & adj[v], depth + 1):
                return True
        return False

    return rec((1 << n) - 1, 0)


def orient_r46(adj: list[int]) -> tuple[list[int], str]:
    """Return orientation with no K4 and no independent 6."""
    candidates = [(adj, "as-published"), (complement(adj), "complemented")]
    good = []
    for g, label in candidates:
        if not has_clique(g, 4) and not has_clique(complement(g), 6):
            good.append((g, label))
    if len(good) != 1:
        raise ValueError(f"expected exactly one R(4,6) orientation, got {len(good)}")
    return good[0]


def triangles(adj: list[int]) -> list[int]:
    out = []
    n = len(adj)
    for a in range(n):
        m = adj[a] & ~((1 << (a + 1)) - 1)
        while m:
            bb = m & -m
            b = bb.bit_length() - 1
            m ^= bb
            common = adj[a] & adj[b] & ~((1 << (b + 1)) - 1)
            while common:
                bc = common & -common
                c = bc.bit_length() - 1
                common ^= bc
                out.append((1 << a) | (1 << b) | (1 << c))
    return out


def independent_sets(adj: list[int], k: int) -> list[int]:
    """Enumerate independent k-sets as bitmasks with a clique recursion in complement."""
    comp = complement(adj)
    n = len(adj)
    out: list[int] = []

    def rec(chosen: int, cand: int, depth: int) -> None:
        if depth == k:
            out.append(chosen)
            return
        need = k - depth
        while cand.bit_count() >= need:
            b = cand & -cand
            v = b.bit_length() - 1
            cand ^= b
            rec(chosen | b, cand & comp[v], depth + 1)

    rec(0, (1 << n) - 1, 0)
    return out


@dataclass(frozen=True)
class Constraints:
    n: int
    tris: tuple[int, ...]
    ind5: tuple[int, ...]


def build_constraints(adj: list[int]) -> Constraints:
    return Constraints(len(adj), tuple(triangles(adj)), tuple(independent_sets(adj, 5)))


def solve_dpll(c: Constraints) -> int | None:
    """Solve clauses: each triangle has >=1 false; each independent-5 has >=1 true."""
    allmask = (1 << c.n) - 1
    clauses = [(m, 0) for m in c.ind5] + [(0, m) for m in c.tris]
    occ = [0] * c.n
    for pos, neg in clauses:
        m = pos | neg
        while m:
            b = m & -m
            occ[b.bit_length() - 1] += 1
            m ^= b

    def rec(true: int, false: int) -> int | None:
        while True:
            changed = False
            assigned = true | false
            for pos, neg in clauses:
                if (pos & true) or (neg & false):
                    continue
                un_pos = pos & ~assigned
                un_neg = neg & ~assigned
                u = un_pos | un_neg
                if not u:
                    return None
                if u & (u - 1) == 0:
                    if un_pos:
                        true |= u
                    else:
                        false |= u
                    changed = True
            if not changed:
                break
        assigned = true | false
        if assigned == allmask:
            return true
        best_v = max(
            (v for v in range(c.n) if not (assigned >> v) & 1),
            key=occ.__getitem__,
        )
        bit = 1 << best_v
        ans = rec(true | bit, false)
        if ans is not None:
            return ans
        return rec(true, false | bit)

    return rec(0, 0)


def solve_hitting(adj: list[int], c: Constraints) -> int | None:
    """Independent exact solver: branch on an uncovered independent 5-set."""
    memo: set[tuple[int, int]] = set()

    def rec(chosen: int, forbidden: int) -> int | None:
        key = (chosen, forbidden)
        if key in memo:
            return None
        memo.add(key)
        target = 0
        best_avail = 99
        for ind in c.ind5:
            if ind & chosen:
                continue
            avail = ind & ~forbidden
            k = avail.bit_count()
            if k == 0:
                return None
            if k < best_avail:
                best_avail = k
                target = avail
                if k == 1:
                    break
        if target == 0:
            return chosen
        opts = []
        m = target
        while m:
            b = m & -m
            v = b.bit_length() - 1
            m ^= b
            score = sum(1 for ind in c.ind5 if not (ind & chosen) and (ind & b))
            opts.append((-score, v, b))
        opts.sort()
        for _, v, b in opts:
            new_forbidden = forbidden
            neigh_selected = adj[v] & chosen
            mm = neigh_selected
            while mm:
                bu = mm & -mm
                u = bu.bit_length() - 1
                mm ^= bu
                new_forbidden |= adj[v] & adj[u]
            if new_forbidden & b:
                continue
            ans = rec(chosen | b, new_forbidden)
            if ans is not None:
                return ans
        return None

    return rec(0, 0)


def verify_extension(adj: list[int], chosen: int) -> bool:
    n = len(adj)
    g = adj[:] + [0]
    for v in range(n):
        if chosen >> v & 1:
            g[v] |= 1 << n
            g[n] |= 1 << v
    return not has_clique(g, 4) and not has_clique(complement(g), 6)


def fetch_graph(index: int, timeout: float) -> tuple[str, str]:
    url = EXOO_BASE.format(index=index)
    req = urllib.request.Request(url, headers={"User-Agent": "science-boundary-r46/1"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
    return raw.decode("ascii"), hashlib.sha256(raw).hexdigest()


def analyze_one(name: str, text: str, sha256: str | None = None) -> dict:
    started = time.monotonic()
    published = parse_matrix(text)
    g, orientation = orient_r46(published)
    c = build_constraints(g)
    dpll = solve_dpll(c)
    hit = solve_hitting(g, c)
    if (dpll is None) != (hit is None):
        raise RuntimeError(f"independent solvers disagree on {name}")
    if dpll is not None:
        if not verify_extension(g, dpll) or not verify_extension(g, hit or 0):
            raise RuntimeError(f"extension solver produced invalid witness on {name}")
    return {
        "name": name,
        "sha256": sha256,
        "orientation": orientation,
        "n": len(g),
        "triangles": len(c.tris),
        "independent5": len(c.ind5),
        "extendable": dpll is not None,
        "neighbor_set": [
            i for i in range(len(g)) if dpll is not None and (dpll >> i) & 1
        ],
        "seconds": round(time.monotonic() - started, 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--fetch-all", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    if not args.paths and not args.fetch_all:
        ap.error("provide matrix paths or --fetch-all")
    results = []
    if args.fetch_all:
        for i in range(1, N_PUBLISHED + 1):
            text, digest = fetch_graph(i, args.timeout)
            result = analyze_one(f"h{i:04d}", text, digest)
            results.append(result)
            print(json.dumps(result, sort_keys=True), flush=True)
    for path in args.paths:
        raw = path.read_bytes()
        result = analyze_one(
            path.name, raw.decode("ascii"), hashlib.sha256(raw).hexdigest()
        )
        results.append(result)
        print(json.dumps(result, sort_keys=True), flush=True)
    summary = {
        "graphs": len(results),
        "extendable": sum(result["extendable"] for result in results),
        "all_solver_agreement": True,
        "source": "Geoffrey Exoo public R(4,6) collection",
        "source_url_template": EXOO_BASE,
        "results": results,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        "SUMMARY "
        + json.dumps(
            {key: value for key, value in summary.items() if key != "results"},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
