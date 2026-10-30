#!/usr/bin/env python3
"""Exact amplification search for the known BPZ row-support +1 defects.

The core of each terminal 134753 construction is B x B, |B|=359.  Existing
exact 5D support searches found one k=5 replacement C->Y with |Y|=6 and four
k=6 replacements with |Y|=7.  For any row set A subset B we may therefore
replace

    A x C  by  A x Y

inside the 10D construction.  The raw gain is |A|.  The only remaining issue is
which points of a chosen 5872-point terminal periphery conflict with A x Y.

For a fixed defect, orientation, and one of the 18 terminal optima, let L_a be
the set of periphery points conflicting with row a's new points.  The exact net
score increment after keeping every nonconflicting old point is

    |A| - | union_{a in A} L_a |.

Maximizing this over all 2^359 row subsets is a maximum-weight closure problem:
row nodes have profit +1, periphery-loss nodes have cost -1, and each row has an
infinite-capacity implication edge to every loss it forces.  We solve the
closure exactly by one s-t min cut (Dinic) per scenario.

We scan all five known raw +1 defects, all 18 terminal optima, and both row/column
orientations.  Any positive optimum is materialized as a full 10D Few Shots
certificate; the upstream verifier is still the authoritative final check.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

PINNED_DEFECTS = [
    {
        "name": "k5-unique",
        "owners": [1644, 13347, 13600, 13692, 14040],
        "additions": [3709, 13684, 14335, 15959, 16045, 16050],
    },
    {
        "name": "k6-0",
        "owners": [8888, 10960, 13347, 13600, 13692, 14040],
        "additions": [6494, 10659, 13649, 13684, 14335, 15959, 16045],
    },
    {
        "name": "k6-1",
        "owners": [1644, 11305, 13347, 13600, 13692, 14040],
        "additions": [3709, 11298, 13684, 14335, 15959, 16045, 16050],
    },
    {
        "name": "k6-2",
        "owners": [1644, 13248, 13347, 13600, 13692, 14040],
        "additions": [3709, 13297, 13684, 14335, 15959, 16045, 16050],
    },
    {
        "name": "k6-3",
        "owners": [1644, 1741, 13347, 13600, 13692, 14040],
        "additions": [3709, 13684, 14335, 15959, 16045, 16050, 16147],
    },
]


class Dinic:
    def __init__(self, n: int):
        self.g: list[list[list[int]]] = [[] for _ in range(n)]

    def add(self, u: int, v: int, c: int) -> None:
        a = [v, c, len(self.g[v])]
        b = [u, 0, len(self.g[u])]
        self.g[u].append(a)
        self.g[v].append(b)

    def flow(self, s: int, t: int) -> int:
        total = 0
        n = len(self.g)
        while True:
            level = [-1] * n
            level[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for v, c, _r in self.g[u]:
                    if c and level[v] < 0:
                        level[v] = level[u] + 1
                        q.append(v)
            if level[t] < 0:
                break
            it = [0] * n

            def dfs(u: int, f: int) -> int:
                if u == t:
                    return f
                while it[u] < len(self.g[u]):
                    e = self.g[u][it[u]]
                    v, c, r = e
                    if c and level[v] == level[u] + 1:
                        z = dfs(v, min(f, c))
                        if z:
                            e[1] -= z
                            self.g[v][r][1] += z
                            return z
                    it[u] += 1
                return 0

            while True:
                z = dfs(s, 10**9)
                if not z:
                    break
                total += z
        return total

    def source_side(self, s: int) -> set[int]:
        seen = {s}
        q = deque([s])
        while q:
            u = q.popleft()
            for v, c, _r in self.g[u]:
                if c and v not in seen:
                    seen.add(v)
                    q.append(v)
        return seen


def max_closure(loss_masks: list[int], loss_count: int) -> tuple[int, list[int], int]:
    """Return (profit, selected-row-indices, union-loss-mask)."""
    nr = len(loss_masks)
    s = nr + loss_count
    t = s + 1
    din = Dinic(t + 1)
    inf = nr + loss_count + 10
    for i, mask in enumerate(loss_masks):
        din.add(s, i, 1)
        m = mask
        while m:
            b = (m & -m).bit_length() - 1
            din.add(i, nr + b, inf)
            m &= m - 1
    for j in range(loss_count):
        din.add(nr + j, t, 1)
    cut = din.flow(s, t)
    side = din.source_side(s)
    rows = [i for i in range(nr) if i in side]
    union = 0
    for i in rows:
        union |= loss_masks[i]
    profit = len(rows) - union.bit_count()
    if profit != nr - cut:
        raise RuntimeError(("closure/mincut mismatch", profit, nr - cut))
    return profit, rows, union


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore

    data_path = root / "data" / "base_c7.json"
    raw = json.loads(data_path.read_text())
    base, _transform, _exchanges, axioms = load_base(data_path)
    if not all(axioms.values()):
        raise RuntimeError({k: v for k, v in axioms.items() if not v})
    ring = base.ring

    I = set(map(int, raw["I0"]))
    pairs = [tuple(map(int, p)) for p in raw["private_pairs"]]
    owners = {p[0] for p in pairs}
    B = I - owners
    PH = set(map(int, raw["PH"]))
    PV = set(map(int, raw["PV"]))
    Q = PH | PV
    X = set(map(int, raw["X"]))
    if (len(B), len(PH), len(PV), len(Q), len(X)) != (359, 8, 8, 16, 367):
        raise RuntimeError("pinned base size drift")

    # Terminal families used by the public BPZ/Tan construction.
    fam = {
        "B": B,
        "N": set(base.X0.elements),
        "A": set(base.XV.elements),
        "D": set(base.XH.elements),
        "O": set(base.R.elements),
        "H": PH,
        "V": PV,
    }
    terminals: list[tuple[str, set[tuple[int, int]]]] = []
    for q in ("O", "H", "V"):
        for r in ("O", "H", "V"):
            for orient in (0, 1):
                if orient == 0:
                    words = (("N", q), ("A", "H"), ("D", "V"),
                             (r, "N"), ("H", "D"), ("V", "A"))
                else:
                    words = (("N", q), ("A", "V"), ("D", "H"),
                             (r, "N"), ("H", "A"), ("V", "D"))
                P: set[tuple[int, int]] = set()
                for u, v in words:
                    P.update((a, b) for a in fam[u] for b in fam[v])
                if len(P) != 5872:
                    raise RuntimeError(("terminal periphery size drift", q, r, orient, len(P)))
                if any(a in B and b in B for a, b in P):
                    raise RuntimeError("terminal periphery overlaps BB")
                terminals.append((f"q={q},r={r},o={orient}", P))
    if len(terminals) != 18:
        raise RuntimeError("terminal count drift")

    def conflict5(a: int, b: int) -> bool:
        return b in ring.NB[a]

    def conflict10(p: tuple[int, int], q: tuple[int, int]) -> bool:
        return conflict5(p[0], q[0]) and conflict5(p[1], q[1])

    # Validate the frozen 5D witnesses against the pinned B and record killers.
    defects = []
    for d in PINNED_DEFECTS:
        C = set(d["owners"])
        Y = list(d["additions"])
        if not C <= B or len(C) + 1 != len(Y):
            raise RuntimeError(("defect shape drift", d))
        if any(y in B for y in Y):
            raise RuntimeError(("defect addition unexpectedly in B", d["name"]))
        for y in Y:
            S = ring.NB[y] & B
            if not S or not S <= C:
                raise RuntimeError(("defect support drift", d["name"], y, sorted(S), sorted(C)))
        for i, y in enumerate(Y):
            for z in Y[i + 1:]:
                if conflict5(y, z):
                    raise RuntimeError(("defect additions not independent", d["name"], y, z))
        killers = {}
        for y in Y:
            ks = [i for i, (a, b) in enumerate(pairs)
                  if a in ring.NB[y] and b in ring.NB[y]]
            if len(ks) > 1:
                raise RuntimeError(("multi-killer drift", y, ks))
            if ks:
                killers[y] = ks[0]
        defects.append({**d, "killer_colors": killers})

    Bv = sorted(B)
    results = []
    best = None

    for ti, (tname, P) in enumerate(terminals):
        pv = sorted(P)
        pindex = {p: i for i, p in enumerate(pv)}
        by_first: dict[int, list[tuple[int, int]]] = {}
        for i, (x, z) in enumerate(pv):
            by_first.setdefault(x, []).append((z, i))
        first_keys = set(by_first)

        def blockers_for(n: tuple[int, int]) -> int:
            a, y = n
            mask = 0
            for x in (ring.NB[a] & first_keys):
                for z, idx in by_first[x]:
                    if z in ring.NB[y]:
                        mask |= 1 << idx
            return mask

        for d in defects:
            C = set(d["owners"])
            Y = list(d["additions"])
            k = len(C)
            for orientation in ("row", "col"):
                loss_masks = []
                for a in Bv:
                    row_new = [(a, y) for y in Y] if orientation == "row" else [(y, a) for y in Y]
                    if any(n in P for n in row_new):
                        raise RuntimeError(("new point overlaps periphery", tname, d["name"], orientation, a))
                    m = 0
                    for n in row_new:
                        m |= blockers_for(n)
                    loss_masks.append(m)
                delta, row_idx, loss_union = max_closure(loss_masks, len(pv))
                chosen = [Bv[i] for i in row_idx]
                entry = {
                    "terminal": tname,
                    "terminal_index": ti,
                    "defect": d["name"],
                    "k": k,
                    "orientation": orientation,
                    "killer_color_count": len(set(d["killer_colors"].values())),
                    "killer_colors": sorted(set(d["killer_colors"].values())),
                    "selected_rows": len(chosen),
                    "periphery_losses": loss_union.bit_count(),
                    "delta": delta,
                    "score": 134753 + delta,
                    "rows": chosen,
                }
                results.append(entry)
                if best is None or (entry["delta"], -entry["periphery_losses"], entry["selected_rows"]) > (
                    best["delta"], -best["periphery_losses"], best["selected_rows"]
                ):
                    best = {**entry, "loss_mask": loss_union}

    assert best is not None
    # Reconstruct the exact best scenario and, if positive, materialize it.
    tname, P = terminals[best["terminal_index"]]
    d = next(x for x in defects if x["name"] == best["defect"])
    C = set(d["owners"])
    Y = list(d["additions"])
    A = set(best["rows"])
    pv = sorted(P)
    loss = {pv[i] for i in range(len(pv)) if (best["loss_mask"] >> i) & 1}
    removed = ({(a, c) for a in A for c in C} if best["orientation"] == "row"
               else {(c, a) for a in A for c in C})
    new = ({(a, y) for a in A for y in Y} if best["orientation"] == "row"
           else {(y, a) for a in A for y in Y})
    core = {(a, b) for a in B for b in B}
    if not removed <= core or new & core or new & P:
        raise RuntimeError("candidate set partition drift")
    kept_p = P - loss

    # Exact structural cross-checks for the only newly introduced points.
    for n in new:
        sb0 = ring.NB[n[0]] & B
        sb1 = ring.NB[n[1]] & B
        if any((x, y) not in removed for x in sb0 for y in sb1):
            raise RuntimeError(("new point hits retained core", n, sorted(sb0), sorted(sb1)))
        if any(conflict10(n, p) for p in kept_p):
            raise RuntimeError(("new point hits retained periphery", n))
    nv = list(new)
    for i, n in enumerate(nv):
        for m in nv[i + 1:]:
            if conflict10(n, m):
                raise RuntimeError(("new points conflict", n, m))

    candidate = (core - removed) | kept_p | new
    expected = 134753 + best["delta"]
    if len(candidate) != expected:
        raise RuntimeError(("candidate score mismatch", len(candidate), expected))

    top = sorted(results, key=lambda r: (r["delta"], -r["periphery_losses"], r["selected_rows"]), reverse=True)
    status = {
        "method": "exact-row-defect-amplification-by-maximum-closure",
        "source": "pinned Tandon/BPZ base_c7.json",
        "terminal_count": len(terminals),
        "defect_count": len(defects),
        "scenario_count": len(results),
        "best": {k: v for k, v in best.items() if k != "loss_mask"},
        "top20": top[:20],
        "defects": [{
            "name": x["name"],
            "owners": x["owners"],
            "additions": x["additions"],
            "killer_colors_by_addition": {str(k): v for k, v in x["killer_colors"].items()},
            "killer_color_count": len(set(x["killer_colors"].values())),
        } for x in defects],
        "candidate_materialized": best["delta"] > 0,
        "candidate_score": len(candidate) if best["delta"] > 0 else None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))

    if best["delta"] > 0:
        def point(p: tuple[int, int]) -> str:
            digs = ring.decode(p[0]) + ring.decode(p[1])
            return "".join(str(x) for x in digs)
        points = sorted(point(p) for p in candidate)
        if len(points) != len(set(points)):
            raise RuntimeError("duplicate encoded candidate")
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
