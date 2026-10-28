#!/usr/bin/env python3
"""Focused exact search for a 17-gate replacement of the merged 102 core.

Uses a Z3 Array from wire index to exact 16-state truth table. The only free
core interface is the merged 102 basis (q34,q36,q39,q41); all nine factors
consumed by the tail must occur among the 17 produced gate wires. A SAT result
therefore gives a direct 101 route.
"""
import argparse
import json
import pathlib
import time

MASK16 = (1 << 16) - 1


def var(i):
    v = 0
    for x in range(16):
        if (x >> i) & 1:
            v |= 1 << x
    return v


def target_truths():
    a, b, c, d = [var(i) for i in range(4)]
    q42 = a & b
    q43 = q42 ^ c
    q44 = q43 & d
    q45 = b ^ q44
    q46 = q42 & c
    q47 = d ^ q46
    q48 = a & q47
    q49 = q43 ^ q48
    q50 = q48 ^ b
    q51 = q49 & q50
    q52 = q51 ^ a
    q53 = q52 ^ q49
    q54 = q45 & q53
    q55 = q54 ^ q47
    q56 = q55 ^ q49
    q57 = q53 ^ q45
    q58 = q56 ^ q57
    q59 = q55 ^ q45
    names = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]
    vals = [q45, q59, q52, q57, q53, q49, q58, q55, q56]
    return names, vals


def main():
    import z3

    ap = argparse.ArgumentParser()
    ap.add_argument("--ands", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--allow-xnor", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    assert 1 <= args.ands <= 17

    G = 17
    names_t, targets = target_truths()
    inputs = [var(i) for i in range(4)]
    BV = lambda x: z3.BitVecVal(x, 16)

    s = z3.Solver()
    s.set(timeout=args.timeout * 1000, random_seed=args.seed)

    arr = z3.Array("wires0", z3.IntSort(), z3.BitVecSort(16))
    for i, t in enumerate(inputs):
        arr = z3.Store(arr, i, BV(t))

    vals = []
    A, B, OP = [], [], []
    and_terms = []

    for i in range(G):
        n = 4 + i
        a = z3.Int(f"a{i}")
        b = z3.Int(f"b{i}")
        s.add(a >= 0, a < n, b >= 0, b < n, a < b)
        av = z3.Select(arr, a)
        bv = z3.Select(arr, b)

        if args.allow_xnor:
            op = z3.Int(f"op{i}")
            s.add(op >= 0, op <= 2)  # 0 XOR, 1 XNOR, 2 AND
            v = z3.If(op == 0, av ^ bv, z3.If(op == 1, ~(av ^ bv), av & bv))
            and_terms.append(z3.If(op == 2, 1, 0))
        else:
            op = z3.Bool(f"and{i}")
            v = z3.If(op, av & bv, av ^ bv)
            and_terms.append(z3.If(op, 1, 0))

        idx = 4 + i
        arr = z3.Store(arr, idx, v)
        vals.append(v)
        A.append(a)
        B.append(b)
        OP.append(op)

    s.add(z3.Sum(and_terms) == args.ands)

    # A minimal 17-gate solution can be chosen without duplicated functions.
    s.add(z3.Distinct(*(list(map(BV, inputs)) + vals)))

    # All nine required factors must literally be exposed as gate wires.
    for t in targets:
        s.add(z3.Or(*[v == BV(t) for v in vals]))

    # No dead gate: every gate either is a requested factor or feeds a later gate.
    target_bvs = [BV(t) for t in targets]
    for i, v in enumerate(vals):
        idx = 4 + i
        uses = [v == t for t in target_bvs]
        for j in range(i + 1, G):
            uses.extend([A[j] == idx, B[j] == idx])
        s.add(z3.Or(*uses))

    t0 = time.time()
    r = s.check()
    elapsed = time.time() - t0
    summary = {
        "gates": G,
        "ands": args.ands,
        "basis": ["q34", "q36", "q39", "q41"],
        "allow_xnor": args.allow_xnor,
        "seed": args.seed,
        "solver": str(r),
        "seconds": round(elapsed, 3),
        "reason": s.reason_unknown() if r == z3.unknown else None,
    }

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    if r == z3.sat:
        m = s.model()
        wire_names = ["q34", "q36", "q39", "q41"]
        gates = []
        for i in range(G):
            ai = m.eval(A[i]).as_long()
            bi = m.eval(B[i]).as_long()
            if args.allow_xnor:
                oi = m.eval(OP[i]).as_long()
                op = ["XOR", "XNOR", "AND"][oi]
            else:
                op = "AND" if z3.is_true(m.eval(OP[i], model_completion=True)) else "XOR"
            out = f"r{i}"
            gates.append({"op": op, "a": wire_names[ai], "b": wire_names[bi], "out": out})
            wire_names.append(out)

        target_wire = {}
        model_vals = [m.eval(v).as_long() & MASK16 for v in vals]
        for name, t in zip(names_t, targets):
            hits = [i for i, v in enumerate(model_vals) if v == t]
            assert len(hits) == 1, (name, hits)
            target_wire[name] = f"r{hits[0]}"

        # Independent 16-state reconstruction check.
        for x in range(16):
            vv = {
                "q34": (x >> 0) & 1,
                "q36": (x >> 1) & 1,
                "q39": (x >> 2) & 1,
                "q41": (x >> 3) & 1,
            }
            for g in gates:
                p, q = vv[g["a"]], vv[g["b"]]
                if g["op"] == "AND":
                    vv[g["out"]] = p & q
                elif g["op"] == "XOR":
                    vv[g["out"]] = p ^ q
                else:
                    vv[g["out"]] = 1 ^ p ^ q
            for name, t in zip(names_t, targets):
                assert vv[target_wire[name]] == ((t >> x) & 1)

        model = {"gates": gates, "target_wire": target_wire}
        json.dump(model, open(outdir / "core.json", "w"), indent=2)
        summary["target_wire"] = target_wire

    json.dump(summary, open(outdir / "summary.json", "w"), indent=2)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
