#!/usr/bin/env python3
"""RNBP-inspired whole-circuit linear synthesis over a fixed AND skeleton.

This adapts the global target-distance idea from the Extended-BP S-box framework
to the exact Few Shots {AND,XOR,XNOR} model and our released-AND representation.
Every helper is synthesized only from signals already available at its temporal
stage.  An AND atom is released only when both of its exact affine operands have
been synthesized.  Thus no helper may depend on a future nonlinear atom.

The algorithm is heuristic.  A found circuit is independently checked on all
256 AES inputs; failure to find <=100 is not a lower bound.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import random

import released_and_skeleton as ras


def max_atom_dep(v, n_and, const_bit):
    mask = (v >> 8) & ((1 << n_and) - 1)
    return mask.bit_length() - 1


def affine_weight(v, const_bit):
    return (v & ((1 << const_bit) - 1)).bit_count()


def pair_map(S, C):
    """All one-gate XOR/XNOR outputs, with one witness per exact affine vector."""
    xs = list(S)
    out = {}
    for i, a in enumerate(xs):
        for b in xs[i + 1:]:
            v = a ^ b
            if v not in S:
                out.setdefault(v, ("XOR", a, b))
            vn = v ^ C
            if vn not in S:
                out.setdefault(vn, ("XNOR", a, b))
    return out


def dist2(t, S, P, C):
    """Exact distance through two additional gates; 3 means farther/unknown."""
    if t in S:
        return 0
    if t in P:
        return 1
    for s in S:
        if (t ^ s) in P or (t ^ s ^ C) in P:
            return 2
    return 3


def original_linear_vectors(c, sk):
    C = 1 << sk["const_bit"]
    vals = {f"x{i}": 1 << i for i in range(8)}
    out = set()
    ai = 0
    for g in c["gates"]:
        a, b = vals[g["a"]], vals[g["b"]]
        if g["op"] == "XOR":
            v = a ^ b
            out.add(v)
        elif g["op"] == "XNOR":
            v = a ^ b ^ C
            out.add(v)
        elif g["op"] == "AND":
            v = 1 << (8 + ai)
            ai += 1
        else:
            raise ValueError(g["op"])
        vals[g["out"]] = v
    return out


def target_rows(sk):
    rows = []
    for i, ab in enumerate(sk["ands"]):
        rows.append((ab["a"], i, 12.0, f"a{i}"))
        rows.append((ab["b"], i, 12.0, f"b{i}"))
    for i, v in enumerate(sk["outputs"]):
        rows.append((v, sk["n_and"], 6.0, f"y{i}"))
    return rows


def active_targets(sk, S, stage, rows):
    active = []
    for t, deadline, wt, label in rows:
        if t in S:
            continue
        # A target is legal only after every AND atom in its affine support exists.
        if max_atom_dep(t, sk["n_and"], sk["const_bit"]) >= stage:
            continue
        active.append((t, deadline, wt, label))
    return active


def release_ready(sk, S, stage, gates, names):
    while stage < sk["n_and"]:
        ab = sk["ands"][stage]
        if ab["a"] not in S or ab["b"] not in S:
            break
        out = f"w{len(gates)}"
        gates.append({"op": "AND", "a": names[ab["a"]], "b": names[ab["b"]], "out": out})
        atom = 1 << (8 + stage)
        S.add(atom)
        names[atom] = out
        stage += 1
    return stage


def residual_closeness(t, w, S, P, C):
    """How many gates remain to t after w is introduced (cheap lookahead)."""
    if w == t:
        return 0
    r = t ^ w
    if r in S or (r ^ C) in S:
        return 1
    if r in P or (r ^ C) in P:
        return 2
    return 3


def choose_move(sk, S, stage, rows, guide, rng, topk):
    C = 1 << sk["const_bit"]
    P = pair_map(S, C)
    if not P:
        return None, {}
    active = active_targets(sk, S, stage, rows)
    if not active:
        return None, {"active": 0, "pairs": len(P)}

    # If the next required operand is one gate away, finish it immediately.
    if stage < sk["n_and"]:
        need = sk["ands"][stage]
        for t in (need["a"], need["b"]):
            if t not in S and t in P:
                return (t, *P[t]), {"active": len(active), "pairs": len(P), "preemptive": True}
    elif stage == sk["n_and"]:
        for t in sk["outputs"]:
            if t not in S and t in P:
                return (t, *P[t]), {"active": len(active), "pairs": len(P), "preemptive": True}

    curd = {t: dist2(t, S, P, C) for t, _, _, _ in active}
    scored = []
    for w, witness in P.items():
        score = 0.0
        changed = 0
        for t, deadline, wt, _ in active:
            horizon = max(0, deadline - stage)
            weight = wt / (1.0 + 0.35 * horizon)
            rem = residual_closeness(t, w, S, P, C)
            nd = min(curd[t], 1 + rem)
            if nd < curd[t]:
                score += (curd[t] - nd) * 300.0 * weight
                changed += 1
            # Even if the coarse distance class does not change, favor a helper
            # that cancels affine support against several near-future targets.
            before = affine_weight(t, sk["const_bit"])
            after = min(affine_weight(t ^ w, sk["const_bit"]),
                        affine_weight(t ^ w ^ C, sk["const_bit"]))
            if after < before:
                score += (before - after) * 1.5 * weight
        if w in guide:
            score += 18.0
        if changed:
            score += 2.0 * changed * changed
        scored.append((score, changed, w, witness))

    scored.sort(key=lambda z: (-z[0], -z[1], z[2]))
    elite = scored[: max(1, min(topk, len(scored)))]
    # Randomized elite choice is the RNBP diversification analogue.  Rank weight
    # avoids overcommitting to tiny numerical differences in the distance proxy.
    weights = [1.0 / math.sqrt(i + 1.0) for i in range(len(elite))]
    choice = rng.choices(elite, weights=weights, k=1)[0]
    _, _, w, witness = choice
    return (w, *witness), {"active": len(active), "pairs": len(P),
                            "elite_best": elite[0][0], "elite_chosen": choice[0]}


def synthesize(base, rng_seed=1, max_linear=80, topk=8):
    sk = ras.extract_skeleton(base)
    C = 1 << sk["const_bit"]
    rows = target_rows(sk)
    guide = original_linear_vectors(base, sk)
    rng = random.Random(rng_seed)

    S = {1 << i for i in range(8)}
    names = {1 << i: f"x{i}" for i in range(8)}
    gates = []
    stage = 0
    linear = 0
    trace = []
    stage = release_ready(sk, S, stage, gates, names)

    while linear < max_linear:
        if stage == sk["n_and"] and all(v in S for v in sk["outputs"]):
            break
        move, info = choose_move(sk, S, stage, rows, guide, rng, topk)
        if move is None:
            return None, {"status": "stuck", "seed": rng_seed, "linear": linear,
                          "released_ands": stage, "trace_tail": trace[-20:], **info}
        w, op, a, b = move
        if w in S:
            raise AssertionError(("duplicate helper", w))
        out = f"w{len(gates)}"
        gates.append({"op": op, "a": names[a], "b": names[b], "out": out})
        S.add(w)
        names[w] = out
        linear += 1
        old_stage = stage
        stage = release_ready(sk, S, stage, gates, names)
        trace.append({"linear": linear, "stage_before": old_stage, "stage_after": stage,
                      "op": op, "guide": w in guide, **info})

    if not (stage == sk["n_and"] and all(v in S for v in sk["outputs"])):
        return None, {"status": "budget_exhausted", "seed": rng_seed, "linear": linear,
                      "released_ands": stage, "trace_tail": trace[-20:]}

    circuit = ras.prune({"gates": gates, "outputs": [names[v] for v in sk["outputs"]]})
    ok = ras.independent_check(circuit)
    if not ok[0]:
        raise AssertionError(("AES verification failed", ok))
    stats = collections.Counter(g["op"] for g in circuit["gates"])
    summary = {"status": "found", "seed": rng_seed, "raw_linear": linear,
               "raw_ands": sk["n_and"], "candidate_gates": len(circuit["gates"]),
               "candidate_stats": dict(stats), "released_ands": stage,
               "verified_all_256": True, "trace_tail": trace[-20:]}
    return circuit, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(ras.SOURCES), default="fs-101")
    ap.add_argument("--rng-seed", type=int, required=True)
    ap.add_argument("--max-linear", type=int, default=80)
    ap.add_argument("--topk", type=int, default=8)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    base = ras.load_circuit(args.family)
    assert ras.independent_check(base)[0]
    circuit, summary = synthesize(base, args.rng_seed, args.max_linear, args.topk)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if circuit is not None:
        (out / "candidate.json").write_text(json.dumps(circuit, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
