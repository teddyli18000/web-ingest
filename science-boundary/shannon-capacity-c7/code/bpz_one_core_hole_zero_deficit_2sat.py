#!/usr/bin/env python3
"""Exact one-BB-hole zero-P-deficit search via incremental 2-SAT.

For the pinned BPZ/Tandon construction, the total peripheral union of the 18
score-134753 terminal optima is P=(X x Q) union (Q x X), with |X|=367 and Q
partitioned into eight conflicting private pairs.  Since alpha(Q)=8, every
maximum 5872-point independent subset of P chooses exactly one endpoint from
each private pair in every X-row and every X-column.  Those choices are exactly
2*367*8=5872 Boolean variables; all remaining Q-Q and left/right conflicts are
binary forbidden choices, hence a 2-CNF instance.

Deleting one BB core point d=(b,c) unlocks T_d=(W_b x W_c)\{d}, where
W_b={z:N[z] intersect B={b}}.  A zero-P-deficit breakthrough needs two
nonconfusable unlocked points compatible with a maximum P set:
128880 + 5872 + 2 = 134754.  Compatibility with one unlocked point becomes
only unit assumptions on the base 2-SAT instance.  The program therefore reuses
one Minisat22 solver and checks every unlocked pair in every assigned core hole.
If any larger unlocked set works with a maximum P set, one of its pairs works,
so this is exact for the entire zero-P-deficit one-hole mechanism.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BB_SIZE = 359 * 359
RECORD_SCORE = 134_753
MAX_P = 5_872
TARGET_SCORE = 134_754
PAIR_COUNT = 8


def choice_lit(var, bit):
    return var if bit else -var


def forbid_choice_lit(var, bit):
    return -choice_lit(var, bit)


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
    from pysat.solvers import Minisat22  # type: ignore

    data_path = root / "data" / "base_c7.json"
    raw = json.loads(data_path.read_text())
    base, _transform, _exchanges, axioms = load_base(data_path)
    if not all(axioms.values()):
        raise RuntimeError({k: v for k, v in axioms.items() if not v})
    ring = base.ring

    I = set(map(int, raw["I0"]))
    X = set(map(int, raw["X"]))
    pairs = [tuple(map(int, p)) for p in raw["private_pairs"]]
    PH = set(map(int, raw["PH"]))
    PV = set(map(int, raw["PV"]))
    Q = PH | PV
    owners = {a for a, _ in pairs}
    alts = {b for _, b in pairs}
    B = I - owners
    if (len(I), len(X), len(B), len(Q), len(pairs)) != (367, 367, 359, 16, 8):
        raise RuntimeError("pinned base size drift")
    if owners | alts != Q or owners & alts:
        raise RuntimeError("private pairs do not partition Q")
    if not all(b in ring.NB[a] for a, b in pairs):
        raise RuntimeError("private pair lost conflict")
    if any((ring.NB[x] & X) - {x} for x in X):
        raise RuntimeError("X is not independent")
    if any((ring.NB[x] & PH) - {x} for x in PH):
        raise RuntimeError("PH independence drift")
    if any((ring.NB[x] & PV) - {x} for x in PV):
        raise RuntimeError("PV independence drift")

    xlist = sorted(X)
    xidx = {x: i for i, x in enumerate(xlist)}
    pair_end = list(pairs)

    def lv(x, p):
        return xidx[x] * PAIR_COUNT + p + 1

    left_vars = len(xlist) * PAIR_COUNT

    def rv(x, p):
        return left_vars + xidx[x] * PAIR_COUNT + p + 1

    nvars = 2 * left_vars
    clauses = []

    # Additional Q conflicts between distinct private pairs.  A Boolean variable
    # itself already enforces exactly one endpoint from its own private pair.
    q_forbids = []
    for i in range(PAIR_COUNT):
        for j in range(i + 1, PAIR_COUNT):
            for si in (0, 1):
                a = pair_end[i][si]
                for sj in (0, 1):
                    b = pair_end[j][sj]
                    if b in ring.NB[a]:
                        q_forbids.append((i, si, j, sj))
    for x in xlist:
        for i, si, j, sj in q_forbids:
            clauses.append([forbid_choice_lit(lv(x, i), si), forbid_choice_lit(lv(x, j), sj)])
            clauses.append([forbid_choice_lit(rv(x, i), si), forbid_choice_lit(rv(x, j), sj)])

    # Left/right cross conflicts.  L=(x,e_i^si) and R=(e_j^sj,y) conflict iff
    # x~e_j^sj and e_i^si~y.  Equality/duplicate physical points are included
    # because closed neighborhoods contain the vertex itself.
    x_near_endpoint = {}
    for p in range(PAIR_COUNT):
        for bit in (0, 1):
            e = pair_end[p][bit]
            x_near_endpoint[(p, bit)] = sorted(X & ring.NB[e])
    cross_clauses = 0
    for i in range(PAIR_COUNT):
        for si in (0, 1):
            ys = x_near_endpoint[(i, si)]
            if not ys:
                continue
            for j in range(PAIR_COUNT):
                for sj in (0, 1):
                    xs = x_near_endpoint[(j, sj)]
                    if not xs:
                        continue
                    for x in xs:
                        a = forbid_choice_lit(lv(x, i), si)
                        for y in ys:
                            clauses.append([a, forbid_choice_lit(rv(y, j), sj)])
                            cross_clauses += 1

    solver = Minisat22(bootstrap_with=clauses)
    if not solver.solve():
        raise RuntimeError("maximum-P 2-SAT base unexpectedly UNSAT")

    # Exact singleton-support classes against B.
    singleton = defaultdict(list)
    safe = set()
    for z in range(ring.n):
        S = ring.NB[z] & B
        if not S:
            safe.add(z)
        elif len(S) == 1:
            singleton[next(iter(S))].append(z)
    if safe != Q or set(singleton) != B:
        raise RuntimeError(("support-class drift", len(safe), len(singleton)))
    for b in B:
        if set(singleton[b]) & B != {b}:
            raise RuntimeError(("singleton/B intersection drift", b))

    assumption_cache = {}

    def assumptions_for(t):
        cached = assumption_cache.get(t, "missing")
        if cached != "missing":
            return cached
        u, v = t
        xu = sorted(X & ring.NB[u])
        xv = sorted(X & ring.NB[v])
        A = set()
        for p in range(PAIR_COUNT):
            for bit in (0, 1):
                e = pair_end[p][bit]
                # t=(u,v) versus left point (x,e).
                if e in ring.NB[v]:
                    for x in xu:
                        A.add(forbid_choice_lit(lv(x, p), bit))
                # t=(u,v) versus right point (e,x).
                if e in ring.NB[u]:
                    for x in xv:
                        A.add(forbid_choice_lit(rv(x, p), bit))
        if any(-lit in A for lit in A):
            assumption_cache[t] = None
            return None
        ans = tuple(sorted(A, key=lambda z: (abs(z), z)))
        assumption_cache[t] = ans
        return ans

    def confusable(a, b):
        return b[0] in ring.NB[a[0]] and b[1] in ring.NB[a[1]]

    def max_p_from_model(model):
        pos = {z for z in model if 1 <= z <= nvars}
        represented = []
        for x in xlist:
            for p in range(PAIR_COUNT):
                bit = 1 if lv(x, p) in pos else 0
                represented.append((x, pair_end[p][bit]))
        for x in xlist:
            for p in range(PAIR_COUNT):
                bit = 1 if rv(x, p) in pos else 0
                represented.append((pair_end[p][bit], x))
        if len(represented) != MAX_P or len(set(represented)) != MAX_P:
            raise RuntimeError(("maximum-P representation overlap", len(represented), len(set(represented))))
        out = set(represented)
        verts = sorted(out)
        by_first_bits = {}
        by_first_id = {}
        for i, (u, v) in enumerate(verts):
            by_first_bits[u] = by_first_bits.get(u, 0) | (1 << v)
            by_first_id.setdefault(u, {})[v] = i
        for i, (u, v) in enumerate(verts):
            nb_v_bits = ring.BITS[v]
            for a in ring.NB[u]:
                bits = by_first_bits.get(a, 0) & nb_v_bits
                if not bits:
                    continue
                for d, j in by_first_id[a].items():
                    if j > i and (bits & (1 << d)):
                        raise RuntimeError(("maximum-P replay conflict", verts[i], verts[j]))
        return out

    holes = []
    for b in sorted(B):
        for c in sorted(B):
            n = len(singleton[b]) * len(singleton[c]) - 1
            if n >= 2:
                holes.append((n, b, c))
    holes.sort(key=lambda z: (-z[0], z[1], z[2]))

    stats = {
        "holes_total": len(holes),
        "holes_shard": 0,
        "unlocked_total": 0,
        "unlocked_individually_viable": 0,
        "pairs_total": 0,
        "pairs_nonconfusable": 0,
        "pairs_direct_assumption_consistent": 0,
        "pair_sat_calls": 0,
    }
    winner = None

    for rank, (expected, b, c) in enumerate(holes):
        if rank % args.shards != args.shard:
            continue
        stats["holes_shard"] += 1
        T = [(u, v) for u in singleton[b] for v in singleton[c] if not (u in B and v in B)]
        if len(T) != expected:
            raise RuntimeError(("T size drift", rank, b, c, len(T), expected))
        stats["unlocked_total"] += len(T)

        viable = []
        for t in T:
            A = assumptions_for(t)
            if A is not None and solver.solve(assumptions=list(A)):
                viable.append((t, A))
        stats["unlocked_individually_viable"] += len(viable)

        for i in range(len(viable)):
            t1, A1 = viable[i]
            for j in range(i + 1, len(viable)):
                stats["pairs_total"] += 1
                t2, A2 = viable[j]
                if confusable(t1, t2):
                    continue
                stats["pairs_nonconfusable"] += 1
                A = set(A1)
                A.update(A2)
                if any(-lit in A for lit in A):
                    continue
                stats["pairs_direct_assumption_consistent"] += 1
                stats["pair_sat_calls"] += 1
                assumptions = sorted(A, key=lambda z: (abs(z), z))
                if not solver.solve(assumptions=assumptions):
                    continue

                Psel = max_p_from_model(solver.get_model())
                core = (b, c)
                for t in (t1, t2):
                    if (ring.NB[t[0]] & B, ring.NB[t[1]] & B) != ({b}, {c}):
                        raise RuntimeError(("wrong core footprint", rank, t, core))
                    for p in Psel:
                        if confusable(t, p):
                            raise RuntimeError(("assumption replay failed", rank, t, p))
                BB = {(u, v) for u in B for v in B}
                BB.remove(core)
                candidate = BB | Psel | {t1, t2}
                if len(candidate) != TARGET_SCORE:
                    raise RuntimeError(("candidate score drift", len(candidate)))
                winner = {
                    "global_hole_rank": rank,
                    "core": [b, c],
                    "unlocked_available": len(T),
                    "t_pair": [list(t1), list(t2)],
                    "assumptions": len(assumptions),
                    "candidate_score": len(candidate),
                }
                args.shot_dir.mkdir(parents=True, exist_ok=True)

                def point(pair):
                    u, v = pair
                    return "".join(str(x) for x in (ring.decode(u) + ring.decode(v)))

                points = sorted(point(p) for p in candidate)
                if len(points) != TARGET_SCORE or len(points) != len(set(points)):
                    raise RuntimeError("certificate conversion drift")
                (args.shot_dir / "certificate.json").write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
                break
            if winner is not None:
                break
        if winner is not None:
            break

    solver.delete()
    status = {
        "method": "exact-one-BB-hole-zero-P-deficit-incremental-2SAT",
        "record_score": RECORD_SCORE,
        "target_score": TARGET_SCORE,
        "max_P": MAX_P,
        "boolean_variables": nvars,
        "base_2cnf_clauses": len(clauses),
        "q_internal_forbidden_endpoint_pairs": len(q_forbids),
        "cross_2cnf_clauses": cross_clauses,
        "shard": args.shard,
        "shards": args.shards,
        **stats,
        "breakthrough": winner is not None,
        "winner": winner,
        "scope_note": "exact for every one-core-hole breakthrough retaining a maximum 5872-point independent set from P; any compatible unlocked set of size >=2 contains a tested pair",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    if winner is not None:
        (args.shot_dir / "metadata.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
