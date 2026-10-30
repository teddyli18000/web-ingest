#!/usr/bin/env python3
"""Exact mixed-mode amplification of the five known BPZ raw +1 row defects.

For each 5D core row a in B, choose at most one of the five exact raw +1
replacements C_m -> Y_m, or choose none. Different rows are automatically
nonconfusable in the first 5 coordinates because B is an independent set.

For one fixed terminal periphery P and one row/column orientation, introduce:
  x[a,m] = choose defect mode m on row a, profit +1;
  z[p]   = delete old periphery point p, cost 1.
Hard constraints:
  * at most one mode per row;
  * x[a,m] -> z[p] for every periphery point p conflicting with a new point.
The weighted MaxSAT objective is exactly

    max  sum x[a,m] - sum z[p].

Thus this strictly contains the fixed-mode maximum-closure search while still
optimizing the true 10D score contribution of this family. We solve all 18
public terminal configurations in both row and column orientations. A positive
optimum is materialized as a full Few Shots certificate and independently
checked by the upstream verifier in the workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

from bpz_amplify_row_defects import PINNED_DEFECTS

PINNED_COMMIT = "c753408492dde92a239708986d16c15dbf6c3235"


def load_geometry(root: Path):
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
    fam = {
        "B": B,
        "N": set(base.X0.elements),
        "A": set(base.XV.elements),
        "D": set(base.XH.elements),
        "O": set(base.R.elements),
        "H": PH,
        "V": PV,
    }
    if len(B) != 359 or len(PH) != 8 or len(PV) != 8:
        raise RuntimeError("pinned BPZ geometry drift")
    return base, ring, B, fam


def terminal_periphery(fam, q: str, r: str, orient: int):
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
    return P


def validate_defects(ring, B: set[int]):
    out = []
    for d in PINNED_DEFECTS:
        C = set(d["owners"])
        Y = list(d["additions"])
        if not C <= B or len(Y) != len(C) + 1:
            raise RuntimeError(("defect shape", d))
        if any(y in B for y in Y):
            raise RuntimeError(("defect addition in B", d["name"]))
        for y in Y:
            S = ring.NB[y] & B
            if not S or not S <= C:
                raise RuntimeError(("defect support", d["name"], y, sorted(S)))
        for i, y in enumerate(Y):
            for z in Y[i + 1:]:
                if z in ring.NB[y]:
                    raise RuntimeError(("defect not independent", d["name"], y, z))
        out.append({"name": d["name"], "C": C, "Y": Y})
    return out


def solve_scenario(args):
    root_s, q, r, torient, axis = args
    root = Path(root_s)
    _base, ring, B, fam = load_geometry(root)
    defects = validate_defects(ring, B)
    P = terminal_periphery(fam, q, r, torient)
    if any(a in B and b in B for a, b in P):
        raise RuntimeError("periphery overlaps core")
    pv = sorted(P)
    Bv = sorted(B)
    M = len(defects)
    nX = len(Bv) * M
    nZ = len(pv)

    # Index periphery by first coordinate so exact blocker sets are cheap.
    by_first: dict[int, list[tuple[int, int]]] = {}
    for i, (u, v) in enumerate(pv):
        by_first.setdefault(u, []).append((v, i))
    first_keys = set(by_first)

    def blockers(n: tuple[int, int]) -> set[int]:
        u, v = n
        hit: set[int] = set()
        for x in ring.NB[u] & first_keys:
            for y, j in by_first[x]:
                if y in ring.NB[v]:
                    hit.add(j)
        return hit

    def xv(i: int, m: int) -> int:
        return 1 + i * M + m

    def zv(j: int) -> int:
        return 1 + nX + j

    w = WCNF()
    # Per-row partition constraint.
    for i in range(len(Bv)):
        for m in range(M):
            for n in range(m + 1, M):
                w.append([-xv(i, m), -xv(i, n)])

    implication_count = 0
    loss_lists: list[list[set[int]]] = [[set() for _ in range(M)] for _ in Bv]
    for i, a in enumerate(Bv):
        for m, d in enumerate(defects):
            newpts = ([(a, y) for y in d["Y"]]
                      if axis == "row" else [(y, a) for y in d["Y"]])
            loss: set[int] = set()
            for n in newpts:
                loss.update(blockers(n))
            loss_lists[i][m] = loss
            x = xv(i, m)
            for j in loss:
                w.append([-x, zv(j)])
                implication_count += 1

    # Constant-offset objective: cost = nX - selected + losses.
    for i in range(len(Bv)):
        for m in range(M):
            w.append([xv(i, m)], weight=1)
    for j in range(nZ):
        w.append([-zv(j)], weight=1)

    with RC2(w, solver="g3", adapt=True, exhaust=True, incr=True, verbose=0) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("RC2 returned no model")
    pos = {z for z in model if z > 0}
    selected: list[tuple[int, int]] = []
    loss_union: set[int] = set()
    for i, a in enumerate(Bv):
        chosen = [m for m in range(M) if xv(i, m) in pos]
        if len(chosen) > 1:
            raise RuntimeError(("partition violation", a, chosen))
        if chosen:
            m = chosen[0]
            selected.append((a, m))
            loss_union.update(loss_lists[i][m])
    zchosen = {j for j in range(nZ) if zv(j) in pos}
    if zchosen != loss_union:
        # Positive-cost z variables can always be set false unless forced.
        raise RuntimeError(("loss model mismatch", len(zchosen), len(loss_union)))
    delta = len(selected) - len(loss_union)
    if delta != nX - cost:
        raise RuntimeError(("objective mismatch", delta, nX - cost))
    return {
        "q": q,
        "r": r,
        "terminal_orientation": torient,
        "axis": axis,
        "delta": delta,
        "selected_count": len(selected),
        "loss_count": len(loss_union),
        "selected": [[a, defects[m]["name"]] for a, m in selected],
        "loss_indices": sorted(loss_union),
        "hard": len(w.hard),
        "soft": len(w.soft),
        "implications": implication_count,
    }


def materialize(root: Path, best, out_cert: Path):
    base, ring, B, fam = load_geometry(root)
    defects0 = validate_defects(ring, B)
    defects = {d["name"]: d for d in defects0}
    P = terminal_periphery(fam, best["q"], best["r"], best["terminal_orientation"])
    pv = sorted(P)
    selected = [(int(a), defects[name]) for a, name in best["selected"]]
    loss = {pv[j] for j in best["loss_indices"]}
    removed: set[tuple[int, int]] = set()
    new: set[tuple[int, int]] = set()
    for a, d in selected:
        if best["axis"] == "row":
            removed.update((a, c) for c in d["C"])
            new.update((a, y) for y in d["Y"])
        else:
            removed.update((c, a) for c in d["C"])
            new.update((y, a) for y in d["Y"])
    core = {(a, b) for a in B for b in B}
    if not removed <= core or new & core or new & P:
        raise RuntimeError("candidate partition drift")
    kept_p = P - loss

    def cf5(a: int, b: int) -> bool:
        return b in ring.NB[a]

    def cf10(x, y) -> bool:
        return cf5(x[0], y[0]) and cf5(x[1], y[1])

    # Independent structural replay of all newly introduced points.
    for n in new:
        sb0 = ring.NB[n[0]] & B
        sb1 = ring.NB[n[1]] & B
        if any((u, v) not in removed for u in sb0 for v in sb1):
            raise RuntimeError(("new hits retained core", n))
        if any(cf10(n, p) for p in kept_p):
            raise RuntimeError(("new hits retained periphery", n))
    nv = list(new)
    for i, x in enumerate(nv):
        for y in nv[i + 1:]:
            if cf10(x, y):
                raise RuntimeError(("new-new conflict", x, y))

    cand = (core - removed) | kept_p | new
    expected = 134753 + int(best["delta"])
    if len(cand) != expected:
        raise RuntimeError(("score mismatch", len(cand), expected))

    def encode(p):
        return "".join(str(z) for z in (ring.decode(p[0]) + ring.decode(p[1])))

    pts = sorted(encode(p) for p in cand)
    if len(pts) != len(set(pts)):
        raise RuntimeError("duplicate certificate points")
    out_cert.parent.mkdir(parents=True, exist_ok=True)
    out_cert.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
    return len(pts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()
    root = args.tan_root.resolve()

    tasks = [(str(root), q, r, o, axis)
             for q in ("O", "H", "V")
             for r in ("O", "H", "V")
             for o in (0, 1)
             for axis in ("row", "col")]
    workers = max(1, min(args.workers, len(tasks), 4))
    results = []
    if workers == 1:
        for t in tasks:
            results.append(solve_scenario(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(solve_scenario, t) for t in tasks]
            for f in as_completed(futs):
                results.append(f.result())
    results.sort(key=lambda x: (x["delta"], x["selected_count"], -x["loss_count"]), reverse=True)
    best = results[0]
    candidate_score = None
    if best["delta"] > 0:
        candidate_score = materialize(root, best, args.certificate)
    status = {
        "method": "exact-mixed-row-defect-weighted-maxsat",
        "source_commit": PINNED_COMMIT,
        "scenario_count": len(results),
        "workers": workers,
        "mode_count": len(PINNED_DEFECTS),
        "best": best,
        "top10": results[:10],
        "candidate_materialized": best["delta"] > 0,
        "candidate_score": candidate_score,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
