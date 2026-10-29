#!/usr/bin/env python3
"""Exact global one-BB-hole + terminal-periphery SAT for C7^10.

The 18 pinned BPZ/Tandon score-134753 terminal optima share
BB=B x B with |B|=359 and their total peripheral union is
P=(X x Q) union (Q x X), where Q is the 16-point set compatible with B.

This program searches *all* one-core-hole choices assigned to one shard in a
single SAT instance.  For z in C7^5 put S(z)=N[z] intersect B.  Every point
(u,v) with |S(u)|=|S(v)|=1 has a unique BB blocker
(owner(u),owner(v)); deleting that one core point is exactly what makes the
point compatible with the retained BB core.  A selector variable h_d is made
for every core hole d in this shard, and each unlocked point x implies its
unique selector.  At most one selector may be chosen and at least one is chosen.

The real C7^10 conflict graph is enforced on P plus all singleton-footprint
points belonging to this shard.  The target is >=5874 peripheral points:
128881 - 1 retained core points + 5874 = 134754.

Using --shard s --shards k partitions the 359^2 core holes by sorted rank modulo
k.  Running all k shards is therefore an exact search of the entire one-hole
family over P plus every point whose complete BB footprint is that one hole.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BB_SIDE = 359
BB_SIZE = BB_SIDE * BB_SIDE
RECORD_SCORE = 134_753
KNOWN_PERIPH = RECORD_SCORE - BB_SIZE  # 5872
TARGET_PERIPH = KNOWN_PERIPH + 2       # one core deletion => need 5874


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("shot_dir", type=Path)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    args = ap.parse_args()
    if args.shards <= 0 or not (0 <= args.shard < args.shards):
        raise SystemExit("bad shard")

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore
    from pysat.solvers import Minicard  # type: ignore

    data_path = root / "data" / "base_c7.json"
    raw = json.loads(data_path.read_text())
    base, _transform, _exchanges, axioms = load_base(data_path)
    if not all(axioms.values()):
        raise RuntimeError({k: v for k, v in axioms.items() if not v})
    ring = base.ring

    I = set(map(int, raw["I0"]))
    X = set(map(int, raw["X"]))
    pairs = [tuple(map(int, p)) for p in raw["private_pairs"]]
    owners = {a for a, _ in pairs}
    B = I - owners
    PH = set(map(int, raw["PH"]))
    PV = set(map(int, raw["PV"]))
    Q = PH | PV
    if (len(I), len(X), len(B), len(PH), len(PV), len(Q), len(pairs)) != (367, 367, 359, 8, 8, 16, 8):
        raise RuntimeError("pinned base size drift")
    if B != set(base.B.elements) or X != set(base.X.elements):
        raise RuntimeError("raw/load_base mismatch")

    # Exact support classes against B.  The classes with support size one are
    # disjoint and each contains its unique B owner.
    singleton = defaultdict(list)
    safe = set()
    for z in range(ring.n):
        S = ring.NB[z] & B
        if not S:
            safe.add(z)
        elif len(S) == 1:
            singleton[next(iter(S))].append(z)
    if safe != Q:
        raise RuntimeError(("safe set != Q", len(safe), len(Q), sorted(safe ^ Q)))
    if set(singleton) != B:
        raise RuntimeError(("singleton owner coverage", len(singleton), len(B)))
    for b in B:
        if set(singleton[b]) & B != {b}:
            raise RuntimeError(("singleton/B intersection drift", b))

    # P is the exact union of all 18 terminal-optimal peripheries.
    P = {(x, q) for x in X for q in Q} | {(q, x) for q in Q for x in X}
    fam = {
        "B": B,
        "N": set(base.X0.elements),
        "A": set(base.XV.elements),
        "D": set(base.XH.elements),
        "O": set(base.R.elements),
        "H": PH,
        "V": PV,
    }
    explicit = set()
    known_peripheries = []
    for q in ("O", "H", "V"):
        for r in ("O", "H", "V"):
            for orient in (0, 1):
                words = (
                    (("N", q), ("A", "H"), ("D", "V"), (r, "N"), ("H", "D"), ("V", "A"))
                    if orient == 0 else
                    (("N", q), ("A", "V"), ("D", "H"), (r, "N"), ("H", "A"), ("V", "D"))
                )
                S = set()
                for a, b in words:
                    S.update((u, v) for u in fam[a] for v in fam[b])
                if len(S) != KNOWN_PERIPH:
                    raise RuntimeError(("periphery size drift", q, r, orient, len(S)))
                explicit |= S
                known_peripheries.append(S)
    if explicit != P:
        raise RuntimeError(("18-basin union != XQ|QX", len(explicit), len(P), len(explicit ^ P)))
    if any(u in B and v in B for u, v in P):
        raise RuntimeError("P overlaps BB")

    # Deterministic partition of all 359^2 holes, including holes that unlock no
    # new point.  Keeping zero-unlock holes makes this exact without assuming a
    # prior upper bound on alpha(P).
    all_holes = []
    for b in sorted(B):
        sb = len(singleton[b])
        for c in sorted(B):
            sc = len(singleton[c])
            all_holes.append((sb * sc - 1, b, c))
    all_holes.sort(key=lambda x: (-x[0], x[1], x[2]))
    holes = [(rank, n, b, c) for rank, (n, b, c) in enumerate(all_holes) if rank % args.shards == args.shard]
    if not holes:
        raise RuntimeError("empty shard")

    pverts = sorted(P)
    np = len(pverts)
    pid = {p: i for i, p in enumerate(pverts)}
    p_by_first_bits = {}
    p_by_first_id = {}
    for i, (u, v) in enumerate(pverts):
        p_by_first_bits[u] = p_by_first_bits.get(u, 0) | (1 << v)
        p_by_first_id.setdefault(u, {})[v] = i

    # Materialize this shard's unlocked vertices.  Hole classes are disjoint
    # because each 5D singleton-support point has a unique owner.
    tverts = []
    t_hole = []
    hole_ranges = []
    for local_h, (rank, expected, b, c) in enumerate(holes):
        lo = len(tverts)
        for u in singleton[b]:
            for v in singleton[c]:
                if u in B and v in B:
                    continue
                tverts.append((u, v))
                t_hole.append(local_h)
        hi = len(tverts)
        if hi - lo != expected:
            raise RuntimeError(("unlocked count drift", rank, b, c, hi - lo, expected))
        hole_ranges.append((lo, hi))
    if len(set(tverts)) != len(tverts):
        raise RuntimeError("unlocked vertices overlap across holes")
    if set(tverts) & P:
        raise RuntimeError("unlocked set overlaps P")

    nt = len(tverts)
    nh = len(holes)
    t0 = np
    h0 = np + nt
    nsel = np + nt

    solver = Minicard()
    pp_edges = 0
    pt_edges = 0
    tt_edges = 0

    # Exact P-P conflict graph.
    for i, (u, v) in enumerate(pverts):
        nb_v_bits = ring.BITS[v]
        for a in ring.NB[u]:
            bits = p_by_first_bits.get(a, 0) & nb_v_bits
            if not bits:
                continue
            ids = p_by_first_id[a]
            while bits:
                lsb = bits & -bits
                d = lsb.bit_length() - 1
                bits -= lsb
                j = ids[d]
                if j > i:
                    solver.add_clause([-(i + 1), -(j + 1)])
                    pp_edges += 1

    # Verify known record peripheries against the graph relation before solving.
    for k, S in enumerate(known_peripheries):
        ids = {pid[p] for p in S}
        if len(ids) != KNOWN_PERIPH:
            raise RuntimeError(("known periphery id drift", k, len(ids)))
        for i in ids:
            u, v = pverts[i]
            nb_v_bits = ring.BITS[v]
            for a in ring.NB[u]:
                bits = p_by_first_bits.get(a, 0) & nb_v_bits
                if not bits:
                    continue
                for d, j in p_by_first_id[a].items():
                    if j > i and j in ids and (bits & (1 << d)):
                        raise RuntimeError(("known periphery conflict", k, i, j))

    # T -> unique hole selector, plus exact P-T conflicts.
    for j, (u, v) in enumerate(tverts):
        xv = t0 + j + 1
        hv = h0 + t_hole[j] + 1
        solver.add_clause([-xv, hv])
        nb_v_bits = ring.BITS[v]
        for a in ring.NB[u]:
            bits = p_by_first_bits.get(a, 0) & nb_v_bits
            if not bits:
                continue
            for d, i in p_by_first_id[a].items():
                if bits & (1 << d):
                    solver.add_clause([-xv, -(i + 1)])
                    pt_edges += 1

    # Only intra-hole T-T conflicts are needed: selecting T from two distinct
    # holes would force two selectors, forbidden below.
    for local_h, (lo, hi) in enumerate(hole_ranges):
        if hi - lo < 2:
            continue
        by_first_bits = {}
        by_first_id = {}
        for j in range(lo, hi):
            u, v = tverts[j]
            by_first_bits[u] = by_first_bits.get(u, 0) | (1 << v)
            by_first_id.setdefault(u, {})[v] = j
        for j in range(lo, hi):
            u, v = tverts[j]
            nb_v_bits = ring.BITS[v]
            for a in ring.NB[u]:
                bits = by_first_bits.get(a, 0) & nb_v_bits
                if not bits:
                    continue
                ids = by_first_id[a]
                while bits:
                    lsb = bits & -bits
                    d = lsb.bit_length() - 1
                    bits -= lsb
                    k = ids[d]
                    if k > j:
                        solver.add_clause([-(t0 + j + 1), -(t0 + k + 1)])
                        tt_edges += 1

    hvars = [h0 + i + 1 for i in range(nh)]
    solver.add_atmost(hvars, 1)
    solver.add_clause(hvars)  # exactly one core hole in this shard

    # At least TARGET_PERIPH selected P/T vertices.
    solver.add_atmost([-(i + 1) for i in range(nsel)], nsel - TARGET_PERIPH)

    # Phase near a known record basin and the largest local hole.
    seed = {pid[p] for p in known_peripheries[0]}
    phases = [(i + 1 if i in seed else -(i + 1)) for i in range(np)]
    if nh:
        seed_h = 0
        slo, shi = hole_ranges[seed_h]
        phases.extend(t0 + j + 1 if slo <= j < shi else -(t0 + j + 1) for j in range(nt))
        phases.extend(h0 + i + 1 if i == seed_h else -(h0 + i + 1) for i in range(nh))
    try:
        solver.set_phases(phases)
    except Exception:
        pass

    print(json.dumps({
        "stage": "built",
        "shard": args.shard,
        "shards": args.shards,
        "holes": nh,
        "p_vertices": np,
        "t_vertices": nt,
        "pp_edges": pp_edges,
        "pt_edges": pt_edges,
        "tt_edges": tt_edges,
        "target_periphery": TARGET_PERIPH,
    }, sort_keys=True), flush=True)

    sat = solver.solve()
    model = solver.get_model() if sat else None
    solver.delete()

    status = {
        "method": "exact-global-selector-one-BB-hole-plus-18-basin-periphery-sat",
        "record_score": RECORD_SCORE,
        "bb_size": BB_SIZE,
        "known_periphery": KNOWN_PERIPH,
        "target_periphery": TARGET_PERIPH,
        "shard": args.shard,
        "shards": args.shards,
        "all_core_holes": len(all_holes),
        "shard_core_holes": nh,
        "periphery_union_vertices": np,
        "unlocked_vertices": nt,
        "pp_edges": pp_edges,
        "pt_edges": pt_edges,
        "tt_edges": tt_edges,
        "sat_target": bool(sat),
        "breakthrough": bool(sat),
        "winner": None,
        "scope_note": "exact for all one-BB-hole choices assigned to this shard over P=(union of 18 terminal-optimal peripheries) plus every vertex whose complete BB footprint is the selected singleton-support core hole",
    }

    if sat:
        positive = {z for z in model if z > 0}
        chosen_h = [i for i, hv in enumerate(hvars) if hv in positive]
        if len(chosen_h) != 1:
            raise RuntimeError(("selector model drift", chosen_h))
        local_h = chosen_h[0]
        rank, unlocked_expected, b, c = holes[local_h]
        chosenP = {pverts[i] for i in range(np) if (i + 1) in positive}
        chosenT = {tverts[j] for j in range(nt) if (t0 + j + 1) in positive}
        if any(t_hole[j] != local_h for j in range(nt) if (t0 + j + 1) in positive):
            raise RuntimeError("model selected T from wrong hole")
        chosen = chosenP | chosenT
        if len(chosen) < TARGET_PERIPH:
            raise RuntimeError(("SAT model below target", len(chosen)))

        # Independent replay on selected peripheral points only.
        selected = sorted(chosen)
        selected_by_first_bits = {}
        selected_by_first_id = {}
        for i, (u, v) in enumerate(selected):
            selected_by_first_bits[u] = selected_by_first_bits.get(u, 0) | (1 << v)
            selected_by_first_id.setdefault(u, {})[v] = i
        for i, (u, v) in enumerate(selected):
            nb_v_bits = ring.BITS[v]
            for a in ring.NB[u]:
                bits = selected_by_first_bits.get(a, 0) & nb_v_bits
                if not bits:
                    continue
                for d, j in selected_by_first_id[a].items():
                    if j > i and (bits & (1 << d)):
                        raise RuntimeError(("SAT replay conflict", selected[i], selected[j]))

        # Every selected T point must have exactly the chosen core point as BB
        # footprint; P is compatible with all of BB by construction.
        for u, v in chosenT:
            if (ring.NB[u] & B, ring.NB[v] & B) != ({b}, {c}):
                raise RuntimeError(("wrong BB footprint", (u, v), (b, c)))

        BB = {(u, v) for u in B for v in B}
        core = (b, c)
        if core not in BB:
            raise RuntimeError("chosen hole not in BB")
        BB.remove(core)
        candidate = BB | chosen
        if len(candidate) < 134_754:
            raise RuntimeError(("candidate below target", len(candidate)))

        status["winner"] = {
            "global_rank": rank,
            "core": [b, c],
            "unlocked_available": unlocked_expected,
            "selected_P": len(chosenP),
            "selected_unlocked": len(chosenT),
            "selected_periphery": len(chosen),
            "candidate_score": len(candidate),
        }
        args.shot_dir.mkdir(parents=True, exist_ok=True)

        def point(pair):
            u, v = pair
            return "".join(str(x) for x in (ring.decode(u) + ring.decode(v)))

        points = sorted(point(p) for p in candidate)
        if len(points) != len(candidate) or len(points) != len(set(points)):
            raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir / "certificate.json").write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
        (args.shot_dir / "metadata.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
