#!/usr/bin/env python3
"""Exact SAT search for a rank-9 GF(16) bilinear multiplier with <=8 right forms.

There are only 15^3 = 3375 nonzero rank-one tensors l⊗r⊗c over GF(2)^4.
A Boolean variable selects each possible term.  The constraints are:

* exactly nine selected rank-one terms;
* their XOR is the standard GF(16) multiplication tensor (x^4+x+1 basis);
* at most eight distinct right factors r are used.

`prove_gf16_multiplier_right_support.py` independently proves <=7 right factors
impossible for rank nine, so SAT here means an exactly-eight-factor decomposition;
UNSAT raises the distinct-right-factor lower bound for every rank-9 bilinear
GF(16) multiplier from eight to nine.

Any SAT model is independently evaluated on all 256 input pairs before it is saved.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import z3


def gf16mul(a, b):
    p = 0
    for i in range(4):
        if (b >> i) & 1:
            p ^= a << i
    for d in range(6, 3, -1):
        if (p >> d) & 1:
            p ^= 1 << d
            # x^4 = x + 1 modulo x^4+x+1.
            p ^= 1 << (d - 3)
            p ^= 1 << (d - 4)
    return p & 0xF


def dot(a, b):
    return (a & b).bit_count() & 1


def evaluate(terms, a, b):
    out = 0
    for l, r, c in terms:
        if dot(l, a) & dot(r, b):
            out ^= c
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=1800, help="solver timeout seconds")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    candidates = [(l, r, c) for l in range(1, 16) for r in range(1, 16) for c in range(1, 16)]
    chosen = [z3.Bool(f"t_{l}_{r}_{c}") for l, r, c in candidates]
    index = {term: i for i, term in enumerate(candidates)}
    used_r = {r: z3.Bool(f"use_r_{r}") for r in range(1, 16)}

    solver = z3.Solver()
    solver.set(timeout=args.timeout * 1000)
    solver.set(random_seed=args.seed)

    solver.add(z3.PbEq([(v, 1) for v in chosen], 9))
    for r in range(1, 16):
        group = [chosen[index[(l, r, c)]] for l in range(1, 16) for c in range(1, 16)]
        solver.add(used_r[r] == z3.Or(group))
    solver.add(z3.PbLe([(used_r[r], 1) for r in range(1, 16)], 8))

    # 4x4x4 tensor entries.  The coefficient of a_i b_j in output bit k is
    # output bit k of (basis element 2^i)*(basis element 2^j).
    parity_sizes = []
    for i in range(4):
        for j in range(4):
            product = gf16mul(1 << i, 1 << j)
            for k in range(4):
                xs = []
                for n, (l, r, c) in enumerate(candidates):
                    if ((l >> i) & 1) and ((r >> j) & 1) and ((c >> k) & 1):
                        xs.append(chosen[n])
                parity_sizes.append(len(xs))
                parity = z3.Xor(*xs)
                solver.add(parity if ((product >> k) & 1) else z3.Not(parity))

    started = time.time()
    verdict = solver.check()
    elapsed = time.time() - started
    summary = {
        "verdict": str(verdict),
        "seed": args.seed,
        "timeout_seconds": args.timeout,
        "elapsed_seconds": round(elapsed, 3),
        "candidate_rank_one_terms": len(candidates),
        "selected_terms_required": 9,
        "right_forms_allowed": 8,
        "parity_clause_sizes": {
            "min": min(parity_sizes),
            "max": max(parity_sizes),
            "distinct": sorted(set(parity_sizes)),
        },
        "z3_version": z3.get_version_string(),
    }

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    terms = []
    if verdict == z3.sat:
        model = solver.model()
        terms = [term for term, v in zip(candidates, chosen) if z3.is_true(model.eval(v, model_completion=True))]
        assert len(terms) == 9
        assert len({r for _, r, _ in terms}) <= 8
        for a in range(16):
            for b in range(16):
                assert evaluate(terms, a, b) == gf16mul(a, b), (a, b)
        summary["distinct_right_forms"] = len({r for _, r, _ in terms})
        summary["independent_256_pair_check"] = True
        (out / "terms.json").write_text(json.dumps([{"l": l, "r": r, "c": c} for l, r, c in terms], indent=2) + "\n")
    elif verdict == z3.unsat:
        summary["implication_with_solver_free_le7_proof"] = (
            "every rank-9 GF(16) bilinear decomposition uses nine distinct right forms"
        )
    else:
        summary["reason_unknown"] = solver.reason_unknown()

    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)
    if terms:
        print(json.dumps({"TERMS": terms}), flush=True)


if __name__ == "__main__":
    main()
