#!/usr/bin/env python3
"""Screen NIST canonical 5-AND topologies against the p008 102-core factors.

This separates multiplicative topology from linear synthesis. For each NIST five-AND
Topology we ask whether choices of zero-preserving four-input linear parts on the ten
AND operands make the nine factor functions of the live 102-gate core lie in the
linear span of x0..x3 and the five AND outputs.

A SAT hit is only a multiplicative-skeleton candidate. A follow-up stage must still
synthesize all required operand/output linear forms in at most 12 XOR/XNOR gates to
produce a 17-gate core and hence a 101-gate AES S-box circuit.
"""
import argparse
import json
import pathlib
import re
import time
import urllib.request

NIST_COMMIT = "fd53322df78ab50cede328a0dc29e09ea4b8a204"
TOPO_URL = (
    "https://raw.githubusercontent.com/usnistgov/Circuits/"
    f"{NIST_COMMIT}/data/topologies/topologies_k5.txt"
)
TARGET_NAMES = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]


def var(i):
    return sum((((x >> i) & 1) << x) for x in range(16))


def source_targets():
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
    return [a, b, c, d], [q45, q59, q52, q57, q53, q49, q58, q55, q56]


def fetch_topologies(cache):
    p = pathlib.Path(cache)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(TOPO_URL, timeout=30) as response:
            p.write_bytes(response.read())
    return [line.strip() for line in p.read_text().splitlines() if line.strip()]


def parse_topology(line):
    parts = re.findall(r"\(A(\d+)\s+([^:]+?)\s*:\s*([^)]+?)\)", line)
    if len(parts) != 5:
        raise ValueError(f"cannot parse topology: {line!r}")
    out = []
    for want, (idx, left, right) in enumerate(parts):
        if int(idx) != want:
            raise ValueError((want, idx, line))

        def deps(text):
            return tuple(int(tok) for tok in text.split() if tok != "L")

        left_deps, right_deps = deps(left), deps(right)
        if any(j >= want for j in left_deps + right_deps):
            raise ValueError((want, left_deps, right_deps, line))
        out.append((left_deps, right_deps))
    return out


def zsel(z3, idx, vals):
    expr = vals[0]
    for k in range(1, len(vals)):
        expr = z3.If(idx == k, vals[k], expr)
    return expr


def xor_many(z3, vals):
    if not vals:
        return z3.BitVecVal(0, 16)
    value = vals[0]
    for item in vals[1:]:
        value = value ^ item
    return value


def solve_topology(z3, topology, targets, timeout_ms, seed):
    prim = [z3.BitVecVal(var(i), 16) for i in range(4)]
    linear = []
    for mask in range(16):
        linear.append(xor_many(z3, [prim[i] for i in range(4) if (mask >> i) & 1]))

    solver = z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=seed)
    ands, left_masks, right_masks = [], [], []
    for i, (left_deps, right_deps) in enumerate(topology):
        left_mask = z3.Int(f"l{i}")
        right_mask = z3.Int(f"r{i}")
        solver.add(left_mask >= 0, left_mask < 16, right_mask >= 0, right_mask < 16)
        left = zsel(z3, left_mask, linear)
        right = zsel(z3, right_mask, linear)
        for j in left_deps:
            left = left ^ ands[j]
        for j in right_deps:
            right = right ^ ands[j]
        solver.add(
            left != right,
            left != z3.BitVecVal(0, 16),
            right != z3.BitVecVal(0, 16),
        )
        if left_deps == right_deps:
            solver.add(left_mask < right_mask)
        ands.append(left & right)
        left_masks.append(left_mask)
        right_masks.append(right_mask)

    basis = prim + ands
    coeffs = []
    for target_i, target in enumerate(targets):
        cs = [z3.Bool(f"c{target_i}_{j}") for j in range(9)]
        terms = [z3.If(c, b, z3.BitVecVal(0, 16)) for c, b in zip(cs, basis)]
        solver.add(xor_many(z3, terms) == z3.BitVecVal(target, 16))
        coeffs.append(cs)

    # A five-AND minimum representation cannot contain a dead AND.
    for i in range(5):
        uses = []
        for j in range(i + 1, 5):
            if i in topology[j][0] or i in topology[j][1]:
                uses.append(z3.BoolVal(True))
        uses.extend(coeffs[t][4 + i] for t in range(len(targets)))
        solver.add(z3.Or(*uses))

    started = time.time()
    result = solver.check()
    row = {"solver": str(result), "seconds": round(time.time() - started, 4)}
    if result == z3.unknown:
        row["reason"] = solver.reason_unknown()
    elif result == z3.sat:
        model = solver.model()
        row["left_masks"] = [model.eval(x).as_long() for x in left_masks]
        row["right_masks"] = [model.eval(x).as_long() for x in right_masks]
        row["target_masks"] = []
        for cs in coeffs:
            mask = 0
            for j, coeff in enumerate(cs):
                if z3.is_true(model.eval(coeff, model_completion=True)):
                    mask |= 1 << j
            row["target_masks"].append(mask)

        # Independent truth-table reconstruction of the returned model.
        inputs = [var(i) for i in range(4)]
        and_truth = []
        for i, (left_deps, right_deps) in enumerate(topology):
            def lin(mask):
                value = 0
                for k in range(4):
                    if (mask >> k) & 1:
                        value ^= inputs[k]
                return value

            left = lin(row["left_masks"][i])
            right = lin(row["right_masks"][i])
            for j in left_deps:
                left ^= and_truth[j]
            for j in right_deps:
                right ^= and_truth[j]
            and_truth.append(left & right)
        basis_truth = inputs + and_truth
        for target, mask in zip(targets, row["target_masks"]):
            value = 0
            for j, item in enumerate(basis_truth):
                if (mask >> j) & 1:
                    value ^= item
            assert value == target, (hex(value), hex(target), mask)
        row["and_truth"] = [f"0x{x:04x}" for x in and_truth]
    return row


def main():
    import z3

    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--timeout-ms", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-topologies", type=int, default=0)
    parser.add_argument("--cache", default="/tmp/topologies_k5.txt")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    assert 0 <= args.shard < args.shards

    lines = fetch_topologies(args.cache)
    _, targets = source_targets()
    indices = [i for i in range(len(lines)) if i % args.shards == args.shard]
    if args.max_topologies:
        indices = indices[: args.max_topologies]

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    counts = {"sat": 0, "unsat": 0, "unknown": 0}
    started = time.time()
    with out.open("w") as handle:
        for number, index in enumerate(indices, 1):
            topology = parse_topology(lines[index])
            row = solve_topology(z3, topology, targets, args.timeout_ms, args.seed + index)
            row.update({"index": index, "topology": lines[index]})
            counts[row["solver"]] = counts.get(row["solver"], 0) + 1
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            if row["solver"] == "sat":
                print(json.dumps(row, sort_keys=True), flush=True)
            if number % 25 == 0:
                print(
                    json.dumps(
                        {
                            "progress": number,
                            "total": len(indices),
                            "counts": counts,
                            "seconds": round(time.time() - started, 2),
                        }
                    ),
                    flush=True,
                )

    summary = {
        "nist_commit": NIST_COMMIT,
        "topologies_total": len(lines),
        "shard": args.shard,
        "shards": args.shards,
        "tested": len(indices),
        "timeout_ms": args.timeout_ms,
        "counts": counts,
        "seconds": round(time.time() - started, 3),
    }
    (out.parent / (out.stem + "-summary.json")).write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
