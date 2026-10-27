#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Minisat22

BASE = 7
D = 5
U = BASE ** D
R_SIZE = 367
BASELINE_SCORE = 134_753
TARGET_SCORE = 134_770

OLD_DELETED = (
    (1, 3, 4, 4, 6),
    (3, 4, 0, 3, 5),
    (5, 3, 1, 3, 4),
    (4, 4, 6, 1, 6),
    (6, 0, 6, 4, 5),
    (0, 3, 5, 6, 5),
    (6, 4, 3, 4, 0),
    (6, 4, 5, 3, 2),
)


def enc5(word):
    v = 0
    for x in word:
        v = v * BASE + x
    return v


def dec5(v):
    out = [0] * D
    for i in range(D - 1, -1, -1):
        out[i] = v % BASE
        v //= BASE
    return tuple(out)


def dec10(v):
    out = ["0"] * (2 * D)
    for i in range(2 * D - 1, -1, -1):
        out[i] = str(v % BASE)
        v //= BASE
    return "".join(out)


def conflict(a, b, digits):
    da = digits[a]
    db = digits[b]
    for x, y in zip(da, db):
        delta = (x - y) % BASE
        if delta not in (0, 1, BASE - 1):
            return False
    return True


def load_r(path):
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            w = tuple(map(int, line.split()))
            if len(w) != D:
                raise ValueError("bad R367 line")
            words.append(enc5(w))
    if len(words) != R_SIZE or len(set(words)) != R_SIZE:
        raise ValueError("R367 size/uniqueness mismatch")
    return words


def make_x(r, digits):
    out = []
    for rid in r:
        w = digits[rid]
        out.append(enc5(((2 - w[1]) % 7, w[3], w[0], (2 - w[2]) % 7, w[4])))
    out[267] = enc5((1, 5, 6, 3, 5))
    if len(set(out)) != R_SIZE:
        raise ValueError("X has duplicates")
    for i, j in combinations(range(R_SIZE), 2):
        if conflict(out[i], out[j], digits):
            raise ValueError("X is not independent")
    return out


def support_masks(r, digits):
    masks = [0] * U
    sizes = [0] * U
    for v in range(U):
        mask = 0
        count = 0
        for i, rv in enumerate(r):
            if conflict(v, rv, digits):
                mask |= 1 << i
                count += 1
        masks[v] = mask
        sizes[v] = count
    return masks, sizes


def safe_vertices(kmask, supports):
    outside = ~kmask
    return [v for v, sm in enumerate(supports) if sm & outside == 0]


def var_h(pool, xi, ei):
    return pool.id(("h", xi, ei))


def var_v(pool, xi, ei):
    return pool.id(("v", xi, ei))


def solve_structure(k_indices, choose, r, xset, digits, supports, *, want_model):
    kmask = sum(1 << i for i in k_indices)
    safe = safe_vertices(kmask, supports)
    if len(safe) < choose:
        return None, {"safe": len(safe), "active_x": 0, "clauses": 0, "vars": 0}

    endpoint_conflicts = []
    for a in range(len(safe)):
        for b in range(a + 1, len(safe)):
            if conflict(safe[a], safe[b], digits):
                endpoint_conflicts.append((a, b))

    rel = []
    active = []
    for xi, xv in enumerate(xset):
        rr = [ei for ei, e in enumerate(safe) if conflict(e, xv, digits)]
        rel.append(rr)
        if rr:
            active.append(xi)

    pool = IDPool()
    cnf = CNF()

    for xi in range(R_SIZE):
        hlits = [var_h(pool, xi, ei) for ei in range(len(safe))]
        vlits = [var_v(pool, xi, ei) for ei in range(len(safe))]
        hcard = CardEnc.equals(hlits, bound=choose, vpool=pool, encoding=EncType.seqcounter)
        vcard = CardEnc.equals(vlits, bound=choose, vpool=pool, encoding=EncType.seqcounter)
        cnf.extend(hcard.clauses)
        cnf.extend(vcard.clauses)
        for a, b in endpoint_conflicts:
            cnf.append([-var_h(pool, xi, a), -var_h(pool, xi, b)])
            cnf.append([-var_v(pool, xi, a), -var_v(pool, xi, b)])

    for i in active:
        ri = rel[i]
        for j in active:
            rj = rel[j]
            for e in rj:
                he = var_h(pool, i, e)
                for f in ri:
                    cnf.append([-he, -var_v(pool, j, f)])

    stats = {
        "safe": len(safe),
        "active_x": len(active),
        "endpoint_conflict_edges": len(endpoint_conflicts),
        "clauses": len(cnf.clauses),
        "vars": pool.top,
    }

    with Minisat22(bootstrap_with=cnf.clauses) as solver:
        if not solver.solve():
            return None, stats
        if not want_model:
            return True, stats
        positive = set(l for l in solver.get_model() if l > 0)

    hsel = []
    vsel = []
    for xi in range(R_SIZE):
        hs = [safe[ei] for ei in range(len(safe)) if var_h(pool, xi, ei) in positive]
        vs = [safe[ei] for ei in range(len(safe)) if var_v(pool, xi, ei) in positive]
        if len(hs) != choose or len(vs) != choose:
            raise RuntimeError("SAT model violates cardinality")
        hsel.append(hs)
        vsel.append(vs)
    return (safe, hsel, vsel), stats


def build_candidate(k_indices, model, r, xset, digits):
    safe, hsel, vsel = model
    del safe
    kset = set(k_indices)
    b = [rv for i, rv in enumerate(r) if i not in kset]
    choose = len(k_indices)
    expected = len(b) ** 2 + 2 * choose * len(xset)

    candidate = set()
    for a in b:
        for c in b:
            candidate.add(a * U + c)
    for xi, xv in enumerate(xset):
        for e in hsel[xi]:
            candidate.add(e * U + xv)
        for e in vsel[xi]:
            candidate.add(xv * U + e)

    if len(candidate) != expected:
        raise RuntimeError(f"candidate has duplicates: {len(candidate)} != {expected}")

    for xi in range(R_SIZE):
        hs = hsel[xi]
        vs = vsel[xi]
        for a, c in combinations(hs, 2):
            if conflict(a, c, digits):
                raise RuntimeError("H same-X independence replay failed")
        for a, c in combinations(vs, 2):
            if conflict(a, c, digits):
                raise RuntimeError("V same-X independence replay failed")

    for i in range(R_SIZE):
        for j in range(R_SIZE):
            if any(conflict(e, xset[j], digits) for e in hsel[i]) and any(
                conflict(xset[i], f, digits) for f in vsel[j]
            ):
                raise RuntimeError("H/V cross-independence replay failed")

    return candidate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline_certificate", type=Path)
    ap.add_argument("output_certificate", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    digits = tuple(dec5(v) for v in range(U))
    r = load_r(args.r367)
    xset = make_x(r, digits)
    r_index = {v: i for i, v in enumerate(r)}
    old_k = tuple(r_index[enc5(w)] for w in OLD_DELETED)
    if len(set(old_k)) != 8:
        raise RuntimeError("old deleted indices are not distinct")

    supports, support_sizes = support_masks(r, digits)
    support_hist = {}
    for s in support_sizes:
        support_hist[s] = support_hist.get(s, 0) + 1

    audit, audit_stats = solve_structure(old_k, 8, r, xset, digits, supports, want_model=True)
    if audit is None:
        raise RuntimeError(f"generalized SAT model rejects known k=8 structure: {audit_stats}")
    audit_candidate = build_candidate(old_k, audit, r, xset, digits)
    if len(audit_candidate) != BASELINE_SCORE:
        raise RuntimeError("k=8 audit candidate has wrong score")
    print("audit8", json.dumps(audit_stats, sort_keys=True), flush=True)

    old_k_set = set(old_k)
    remaining = [i for i in range(R_SIZE) if i not in old_k_set]

    ranked = []
    old_mask = sum(1 << i for i in old_k)
    for extra in remaining:
        kmask = old_mask | (1 << extra)
        safe_count = sum(1 for sm in supports if sm & ~kmask == 0)
        ranked.append((safe_count, extra))
    ranked.sort(reverse=True)

    tested = 0
    sat_prefilter = 0
    best_safe = ranked[0][0] if ranked else 0
    best_active = None
    for safe_count, extra in ranked:
        k9 = tuple(sorted((*old_k, extra)))
        tested += 1
        model, stats = solve_structure(k9, 9, r, xset, digits, supports, want_model=True)
        if best_active is None or stats["active_x"] < best_active:
            best_active = stats["active_x"]
        if model is None:
            continue
        sat_prefilter += 1
        candidate = build_candidate(k9, model, r, xset, digits)
        if len(candidate) != TARGET_SCORE:
            raise RuntimeError("k=9 candidate has wrong score")

        baseline = json.loads(args.baseline_certificate.read_text(encoding="utf-8"))["points"]
        baseline_ids = {int(p, 7) for p in baseline}
        removed = len(baseline_ids - candidate)
        added = len(candidate - baseline_ids)

        args.output_certificate.parent.mkdir(parents=True, exist_ok=True)
        args.output_certificate.write_text(
            json.dumps({"points": [dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        status = {
            "candidate": True,
            "score": len(candidate),
            "method": "generalized-safe-endpoint-sat",
            "tested_k9": tested,
            "safe_endpoints": stats["safe"],
            "active_x": stats["active_x"],
            "vars": stats["vars"],
            "clauses": stats["clauses"],
            "deleted_r_indices": list(k9),
            "deleted_r_words": ["".join(map(str, digits[r[i]])) for i in k9],
            "removed_vs_baseline": removed,
            "added_vs_baseline": added,
            "support_histogram": support_hist,
            "audit8": audit_stats,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
        return

    status = {
        "candidate": False,
        "score": BASELINE_SCORE,
        "method": "generalized-safe-endpoint-sat",
        "tested_k9": tested,
        "sat_k9": sat_prefilter,
        "best_safe_endpoints": best_safe,
        "min_active_x": best_active,
        "support_histogram": support_hist,
        "audit8": audit_stats,
    }
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("NONE", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
