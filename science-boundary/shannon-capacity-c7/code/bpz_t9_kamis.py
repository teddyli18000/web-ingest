#!/usr/bin/env python3
"""Bridge the strongest BPZ t=9 obstruction instance to KaMIS.

`export` writes the exact induced conflict graph C7^5 \ D in weighted METIS
format (unit weights). `materialize` reads KaMIS struction's 0/1 solution
vector, independently replays it in C7^5, and if it has at least 367 vertices
builds the nominal 134770-point C7^10 certificate.
"""

import argparse
import json
import sys
from pathlib import Path

import bpz_t9_obstruction_mis as mis


def reconstruct(root: Path):
    sys.path.insert(0, str(root.resolve()))
    from shannon.certificates import Ring  # type: ignore

    raw = json.loads((root / "data" / "base_c7.json").read_text())
    I = set(map(int, raw["I0"]))
    X = set(map(int, raw["X"]))
    ring = Ring(mis.D)
    digits = tuple(ring.decode(v) for v in range(mis.U))
    for a, b in mis.I_SWAPS:
        if a not in I or b in I:
            raise RuntimeError("I witness swap drift")
        I.remove(a)
        I.add(b)
    pairs = list(mis.PRIVATE_PAIRS)
    PH = [q if s else a for (a, q), s in zip(pairs, mis.ORIENTATION)]
    PV = [a if s else q for (a, q), s in zip(pairs, mis.ORIENTATION)]
    if len(I) != mis.N or not mis.independent(I, digits):
        raise RuntimeError("I witness drift")
    obstruction = ring.nbhd(set(PH)) & ring.nbhd(set(PV))
    hits = sorted(X & obstruction)
    if len(obstruction) != 1098 or hits != [10665]:
        raise RuntimeError(f"obstruction drift size={len(obstruction)} hits={hits}")
    lower = X - obstruction
    if len(lower) != 366 or not mis.independent(lower, digits):
        raise RuntimeError("known 366-set lower bound drift")
    return I, X, pairs, PH, PV, ring, digits, obstruction, lower


def cmd_export(args):
    _, _, _, _, _, ring, _, obstruction, lower = reconstruct(args.tan_root)
    allowed = [v for v in range(mis.U) if v not in obstruction]
    idx = {v: i for i, v in enumerate(allowed)}
    adj = [[] for _ in allowed]
    degree_sum = 0
    for i, v in enumerate(allowed):
        row = []
        for u in ring.NB[v]:
            if u == v or u not in idx:
                continue
            # Independent symmetry check against the public Ring neighborhood.
            if v not in ring.NB[u]:
                raise RuntimeError("asymmetric Ring neighborhood")
            row.append(idx[u] + 1)
        row = sorted(set(row))
        if i + 1 in row:
            raise RuntimeError("self edge in METIS row")
        adj[i] = row
        degree_sum += len(row)
    if degree_sum % 2:
        raise RuntimeError("odd degree sum")
    edges = degree_sum // 2

    args.graph.parent.mkdir(parents=True, exist_ok=True)
    with args.graph.open("w", encoding="ascii") as f:
        # METIS fmt=10 means one vertex weight before every adjacency list.
        f.write(f"{len(allowed)} {edges} 10\n")
        for row in adj:
            f.write("1")
            if row:
                f.write(" " + " ".join(map(str, row)))
            f.write("\n")
    args.mapping.write_text(json.dumps({"allowed": allowed}, separators=(",", ":")) + "\n")
    meta = {
        "ambient_vertices": mis.U,
        "obstruction_size": len(obstruction),
        "allowed_vertices": len(allowed),
        "edges": edges,
        "known_lower_bound": len(lower),
        "target_auxiliary_size": mis.N,
        "target_10d_score": mis.TARGET,
    }
    args.meta.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(json.dumps(meta, sort_keys=True), flush=True)


def parse_timeout(log: Path):
    rows = []
    for line in log.read_text(errors="replace").splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) < 7:
            continue
        try:
            weight = int(p[3])
        except ValueError:
            continue
        t = p[6].lower()
        if t in ("0", "false"):
            timeout = False
        elif t in ("1", "true"):
            timeout = True
        else:
            continue
        rows.append((weight, timeout, line))
    return rows[-1] if rows else (None, None, None)


def cmd_materialize(args):
    I, _, pairs, PH, PV, ring, digits, obstruction, lower = reconstruct(args.tan_root)
    allowed = list(map(int, json.loads(args.mapping.read_text())["allowed"]))
    bits = [int(x.strip()) for x in args.solution.read_text().splitlines() if x.strip()]
    if len(bits) != len(allowed) or any(x not in (0, 1) for x in bits):
        raise RuntimeError(f"unexpected KaMIS solution vector: {len(bits)} entries")
    X = [v for v, take in zip(allowed, bits) if take]
    if set(X) & obstruction or not mis.independent(X, digits):
        raise RuntimeError("KaMIS solution replay failed")
    if len(X) < len(lower):
        raise RuntimeError(f"KaMIS returned {len(X)} < known lower bound {len(lower)}")

    logged_weight, timeout, csv = parse_timeout(args.log)
    if logged_weight is not None and logged_weight != len(X):
        raise RuntimeError(f"KaMIS log/solution mismatch {logged_weight} != {len(X)}")
    status = {
        "method": "bpz-t9-kamis-v3.2-struction",
        "candidate": len(X) >= mis.N,
        "auxiliary_size": len(X),
        "known_lower_bound": len(lower),
        "solver_timeout": timeout,
        "solver_csv": csv,
        "proven_optimal": timeout is False,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if len(X) < mis.N:
        if timeout is False and len(X) == 366:
            status.update({"score": 134753, "conclusion": "exact-alpha=366-for-this-obstruction"})
        else:
            status.update({"score": 134753, "conclusion": "no-breakthrough-within-solver-run"})
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    X = X[: mis.N]
    if not mis.independent(X, digits):
        raise RuntimeError("truncated 367-set replay failed")
    points, xp = mis.build(I, X, pairs, PH, PV, ring)
    if len(points) != mis.TARGET:
        raise RuntimeError(f"10D target drift {len(points)}")
    status.update({
        "candidate": True,
        "score": len(points),
        "auxiliary_size_used": len(X),
        "private_pairs": [list(z) for z in pairs],
        "orientation": list(mis.ORIENTATION),
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("export")
    p.add_argument("tan_root", type=Path)
    p.add_argument("graph", type=Path)
    p.add_argument("mapping", type=Path)
    p.add_argument("meta", type=Path)
    p.set_defaults(func=cmd_export)
    p = sp.add_parser("materialize")
    p.add_argument("tan_root", type=Path)
    p.add_argument("mapping", type=Path)
    p.add_argument("solution", type=Path)
    p.add_argument("log", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("status", type=Path)
    p.set_defaults(func=cmd_materialize)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
