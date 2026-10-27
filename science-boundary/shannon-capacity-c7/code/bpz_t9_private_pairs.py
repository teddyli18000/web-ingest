#!/usr/bin/env python3
"""Exact Definition-2 search for nine private pairs in the BPZ/Tan C7^5 base.

Fix the published 367-point main set I and 367-point auxiliary set X from
Tandon's reproducibility repository.  Enumerate every q outside I whose closed
C7^5 neighbourhood meets I in exactly one point r.  Each such private pair
(r,q) has two possible transversal orientations.  Two oriented pairs are
compatible exactly when

  * they use different owners r;
  * their H endpoints are nonconfusable;
  * their V endpoints are nonconfusable; and
  * no x in X is confusable with an H endpoint and a V endpoint.

Thus a size-9 clique in this compatibility graph is exactly a Definition-2
9-pair Gao gadget for the fixed (I,X).  With |I|=|X|=367 this immediately gives
an independent set in C7^10 of size 367^2 + 9^2 = 134770.

The SAT result is replayed from first principles before a certificate is emitted.
"""

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

from pysat.solvers import Minicard

Q = 7
D = 5
U = Q ** D
N = 367
TARGET_T = 9
TARGET_SCORE = N * N + TARGET_T * TARGET_T


def conflict(a: int, b: int, digits) -> bool:
    da, db = digits[a], digits[b]
    return all((x - y) % Q in (0, 1, Q - 1) for x, y in zip(da, db))


def independent(vals, digits) -> bool:
    vals = list(vals)
    return all(not conflict(a, b, digits) for a, b in combinations(vals, 2))


def encode10(a: int, b: int, ring) -> str:
    ds = ring.decode(a) + ring.decode(b)
    if len(ds) != 10 or any(not 0 <= z < Q for z in ds):
        raise RuntimeError("bad 10D point")
    return "".join(map(str, ds))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import Ring  # type: ignore

    raw = json.loads((root / "data" / "base_c7.json").read_text())
    I = set(map(int, raw["I0"]))
    X = set(map(int, raw["X"]))
    if len(I) != N or len(X) != N:
        raise RuntimeError(f"base-size drift: |I|={len(I)} |X|={len(X)}")

    ring = Ring(D)
    digits = tuple(ring.decode(v) for v in range(U))
    if not independent(I, digits) or not independent(X, digits):
        raise RuntimeError("published I or X is not independent")

    # Which X-points are hit by each possible endpoint.  Python big integers
    # make the Definition-2 double-neighbour condition a single bitwise AND.
    xindex = {x: i for i, x in enumerate(sorted(X))}
    xmask = [0] * U
    for x, i in xindex.items():
        bit = 1 << i
        for v in ring.NB[x]:
            xmask[v] |= bit

    # Enumerate every private candidate q and its unique owner r in I.
    private = []
    owner_hist = {}
    for q in range(U):
        if q in I:
            continue
        hits = [z for z in ring.NB[q] if z in I]
        if len(hits) == 1:
            r = hits[0]
            private.append((r, q))
            owner_hist[r] = owner_hist.get(r, 0) + 1

    # Each private pair has two orientations unless it already violates the
    # no-X-point-sees-both-transversals condition by itself.
    options = []
    self_invalid = 0
    for r, q in private:
        if xmask[r] & xmask[q]:
            self_invalid += 1
            continue
        options.append((r, q, r, q, 0))  # owner, alt, H, V, orientation
        options.append((r, q, q, r, 1))

    m = len(options)
    if m == 0:
        raise RuntimeError("no valid oriented private pairs")

    # Hard pairwise incompatibilities.  They are exactly the pairwise form of
    # Definition 2 after the fixed-I/fixed-X private-pair condition above.
    solver = Minicard()
    incompatible = 0
    same_owner = 0
    h_conflicts = 0
    v_conflicts = 0
    x_double_hits = 0
    for i in range(m):
        ri, qi, hi, vi, _ = options[i]
        for j in range(i + 1, m):
            rj, qj, hj, vj, _ = options[j]
            bad = False
            if ri == rj:
                bad = True
                same_owner += 1
            if conflict(hi, hj, digits):
                bad = True
                h_conflicts += 1
            if conflict(vi, vj, digits):
                bad = True
                v_conflicts += 1
            if (xmask[hi] & xmask[vj]) or (xmask[hj] & xmask[vi]):
                bad = True
                x_double_hits += 1
            if bad:
                solver.add_clause([-(i + 1), -(j + 1)])
                incompatible += 1

    # Require at least nine selected options using MiniCard's native cardinality.
    solver.add_atmost([-(i + 1) for i in range(m)], m - TARGET_T)
    sat = solver.solve()
    model = solver.get_model() if sat else None
    solver.delete()

    setup = {
        "I_size": len(I),
        "X_size": len(X),
        "private_candidates": len(private),
        "private_owners": len(owner_hist),
        "max_private_alts_per_owner": max(owner_hist.values(), default=0),
        "self_invalid_pairs": self_invalid,
        "oriented_options": m,
        "incompatible_pairs": incompatible,
        "same_owner_hits": same_owner,
        "H_conflict_hits": h_conflicts,
        "V_conflict_hits": v_conflicts,
        "X_double_hit_pairs": x_double_hits,
        "target_t": TARGET_T,
        "target_score": TARGET_SCORE,
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    args.status.parent.mkdir(parents=True, exist_ok=True)
    if not sat:
        # The published gadget supplies t=8, so UNSAT at t=9 proves the fixed
        # (I,X) Definition-2 optimum is exactly eight private pairs.
        status = {
            "candidate": False,
            "sat": False,
            "method": "bpz-fixed-I-X-definition2-t9-exact",
            "fixed_definition2_max_t": 8,
            "score": N * N + 8 * 8,
            "setup": setup,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("UNSAT", json.dumps(status, sort_keys=True), flush=True)
        return

    pos = {z for z in model if z > 0}
    chosen_idx = [i for i in range(m) if i + 1 in pos]
    # MiniCard may return more than the lower bound.  Any nine form a solution
    # because all selected option pairs satisfy the same hard constraints.
    chosen_idx = chosen_idx[:TARGET_T]
    if len(chosen_idx) != TARGET_T:
        raise RuntimeError(f"SAT model selected only {len(chosen_idx)} options")
    chosen = [options[i] for i in chosen_idx]

    owners = [z[0] for z in chosen]
    PH = [z[2] for z in chosen]
    PV = [z[3] for z in chosen]
    if len(set(owners)) != TARGET_T:
        raise RuntimeError("replay: owners are not distinct")
    if not independent(PH, digits) or not independent(PV, digits):
        raise RuntimeError("replay: transversal is not independent")
    if set(PH) & set(PV):
        raise RuntimeError("replay: transversal endpoints overlap")
    if any(xmask[h] & xmask[v] for h in PH for v in PV):
        raise RuntimeError("replay: X hits both transversals")
    for r, q, _, _, _ in chosen:
        if r not in I or q in I:
            raise RuntimeError("replay: malformed private pair")
        hits = {z for z in ring.NB[q] if z in I}
        if hits != {r}:
            raise RuntimeError(f"replay: private pair ({r},{q}) has hits {hits}")

    R = set(owners)
    B = I - R
    NH = set().union(*(ring.NB[h] for h in PH))
    NV = set().union(*(ring.NB[v] for v in PV))
    if X & NH & NV:
        raise RuntimeError("replay: Definition-2 X double-hit condition failed")
    X0 = X - (NH | NV)
    XH = X & NH
    XV = X & NV
    if X0 | XH | XV != X or (X0 & XH) or (X0 & XV) or (XH & XV):
        raise RuntimeError("replay: X partition failed")

    # Gao product, identical to Lemma 1 / the public construction formula.
    pairs10 = set()
    def add_product(A, C):
        for a in A:
            for c in C:
                pairs10.add((a, c))

    add_product(B, B)
    add_product(R, X0)
    add_product(PH, XH)
    add_product(PV, XV)
    add_product(X0, R)
    add_product(XH, PV)
    add_product(XV, PH)

    expected = (N - TARGET_T) ** 2 + 2 * TARGET_T * N
    if expected != TARGET_SCORE or len(pairs10) != expected:
        raise RuntimeError(f"Gao score mismatch: got {len(pairs10)} expected {expected}")

    points = sorted(encode10(a, b, ring) for a, b in pairs10)
    if len(points) != len(set(points)):
        raise RuntimeError("duplicate 10D points")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")

    status = {
        "candidate": True,
        "sat": True,
        "method": "bpz-fixed-I-X-definition2-t9-exact",
        "score": len(points),
        "owners": owners,
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": len(X0), "XH": len(XH), "XV": len(XV)},
        "chosen_pairs": [
            {"owner": r, "alt": q, "orientation": side} for r, q, _, _, side in chosen
        ],
        "setup": setup,
    }
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
