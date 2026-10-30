#!/usr/bin/env python3
"""Jointly resynthesize linear helpers across several fixed AND releases.

The current 101-gate AES circuit has 33 AND gates and 68 XOR/XNOR gates. Root-wise
ODC and one-shared-helper searches can miss a saving that requires changing several
linear helpers together and moving them across an AND boundary. This script selects
a temporal window of the existing circuit, keeps every AND in that window fixed, and
beam-searches a new XOR/XNOR helper network for all internal AND operands plus every
wire that must remain live at the right boundary.

A successful budget of one fewer linear gate yields a complete <=100-gate circuit.
Failure is evidence only about the searched windows/beam, not a lower bound.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import random
from dataclasses import dataclass

import released_and_skeleton as ras


def original_schedule(c):
    n = sum(g["op"] == "AND" for g in c["gates"])
    counts = [0] * (n + 1)
    ai = 0
    for g in c["gates"]:
        if g["op"] == "AND":
            ai += 1
        else:
            counts[ai] += 1
    return counts


def vectorize(c):
    n_and = sum(g["op"] == "AND" for g in c["gates"])
    const_bit = 8 + n_and
    C = 1 << const_bit
    vals = {f"x{i}": 1 << i for i in range(8)}
    out_vec = []
    and_no = 0
    for g in c["gates"]:
        a, b = vals[g["a"]], vals[g["b"]]
        if g["op"] == "XOR":
            v = a ^ b
        elif g["op"] == "XNOR":
            v = a ^ b ^ C
        elif g["op"] == "AND":
            v = 1 << (8 + and_no)
            and_no += 1
        else:
            raise ValueError(g["op"])
        vals[g["out"]] = v
        out_vec.append(v)
    return vals, out_vec, const_bit


def interval_boundaries(c):
    n_and = sum(g["op"] == "AND" for g in c["gates"])
    starts = [None] * (n_and + 1)
    ai = 0
    starts[0] = 0
    for i, g in enumerate(c["gates"]):
        if g["op"] == "AND":
            ai += 1
            starts[ai] = i + 1
    assert all(x is not None for x in starts)
    return starts


def window_positions(c, start_interval, end_interval):
    """Intervals [start,end] inclusive; internal ANDs are start..end-1."""
    starts = interval_boundaries(c)
    n = len(starts) - 1
    if not (0 <= start_interval <= end_interval <= n):
        raise ValueError((start_interval, end_interval, n))
    lo = starts[start_interval]
    hi = len(c["gates"]) if end_interval == n else starts[end_interval + 1] - 1
    return lo, hi


def atom_dependency(v, n_and, const_bit):
    mask = (v >> 8) & ((1 << n_and) - 1)
    return mask.bit_length() - 1


def state_hash(stage, helpers):
    h = hashlib.blake2b(digest_size=16)
    h.update(stage.to_bytes(2, "little"))
    for x in sorted(x[4] for x in helpers):
        h.update(int(x).to_bytes(8, "little", signed=False))
    return h.digest()


@dataclass
class State:
    stage: int
    helpers: tuple  # (stage, op, a_vec, b_vec, out_vec)
    avail: frozenset
    score: float = 0.0


def normalize_stage(state, and_targets, and_atoms):
    stage = state.stage
    avail = set(state.avail)
    while stage < len(and_targets):
        a, b = and_targets[stage]
        if a not in avail or b not in avail:
            break
        avail.add(and_atoms[stage])
        stage += 1
    if stage == state.stage and len(avail) == len(state.avail):
        return state
    return State(stage, state.helpers, frozenset(avail), state.score)


def goal(state, live_targets, and_targets, and_atoms):
    state = normalize_stage(state, and_targets, and_atoms)
    return state.stage == len(and_targets) and all(t in state.avail for t in live_targets)


def active_targets(state, future_targets, global_released, n_and, const_bit):
    out = []
    for t, deadline, weight in future_targets:
        if t in state.avail:
            continue
        if atom_dependency(t, n_and, const_bit) >= global_released:
            continue
        out.append((t, deadline, weight))
    return out


def pair_map(avail, C):
    xs = sorted(avail)
    out = {}
    for i, a in enumerate(xs):
        for b in xs[i + 1:]:
            v = a ^ b
            if v not in avail and v not in out:
                out[v] = ("XOR", a, b)
            vn = v ^ C
            if vn not in avail and vn not in out:
                out[vn] = ("XNOR", a, b)
    return out


def candidate_moves(state, future_targets, guide_vecs, start_interval, n_and, const_bit,
                    max_candidates, rng):
    C = 1 << const_bit
    avail = state.avail
    pm = pair_map(avail, C)
    if not pm:
        return []
    released = start_interval + state.stage
    active = active_targets(state, future_targets, released, n_and, const_bit)
    scores = collections.defaultdict(float)
    for t, deadline, base_weight in active:
        d = max(0, deadline - state.stage)
        w = base_weight / (1.0 + d)
        if t in pm:
            scores[t] += 1500.0 * w
        for a in avail:
            h = t ^ a
            if h in pm:
                scores[h] += 120.0 * w
            hn = h ^ C
            if hn in pm:
                scores[hn] += 120.0 * w
    for v in guide_vecs:
        if v in pm:
            scores[v] += 20.0
    keys = list(pm)
    if keys:
        rng.shuffle(keys)
        for v in keys[: min(24, len(keys))]:
            scores[v] += 0.05
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:max_candidates]
    return [(s, v, *pm[v]) for v, s in ranked]


def state_quality(state, future_targets, live_targets, start_interval, n_and, const_bit):
    C = 1 << const_bit
    released = start_interval + state.stage
    active = active_targets(state, future_targets, released, n_and, const_bit)
    q = 100000.0 * state.stage
    q += 3000.0 * sum(t in state.avail for t in live_targets)
    av = state.avail
    for t, deadline, w in active:
        one = False
        for a in av:
            if (t ^ a) in av or (t ^ a ^ C) in av:
                one = True
                break
        if one:
            q += 80.0 * w / (1.0 + max(0, deadline - state.stage))
    return q


def search_window(c, start_interval, end_interval, beam, max_candidates, restarts, delta, seed):
    vals, _out_vec, const_bit = vectorize(c)
    n_and = sum(g["op"] == "AND" for g in c["gates"])
    sched = original_schedule(c)
    lo, hi = window_positions(c, start_interval, end_interval)
    window = c["gates"][lo:hi]
    orig_linear = sum(g["op"] != "AND" for g in window)
    assert orig_linear == sum(sched[start_interval:end_interval + 1])
    budget = orig_linear - delta
    if budget < 0:
        return {"status": "skipped_budget", "start": start_interval, "end": end_interval,
                "orig_linear": orig_linear, "budget": budget}

    prefix = c["gates"][:lo]
    suffix = c["gates"][hi:]
    prefix_names = [f"x{i}" for i in range(8)] + [g["out"] for g in prefix]
    base_avail = {vals[w] for w in prefix_names}

    and_targets = []
    and_atoms = []
    guide_vecs = []
    global_ai = start_interval
    for g in window:
        if g["op"] == "AND":
            and_targets.append((vals[g["a"]], vals[g["b"]]))
            and_atoms.append(1 << (8 + global_ai))
            global_ai += 1
        else:
            guide_vecs.append(vals[g["out"]])
    assert len(and_targets) == end_interval - start_interval

    win_outputs = {g["out"] for g in window}
    live_names = set()
    for g in suffix:
        for k in ("a", "b"):
            if g[k] in win_outputs:
                live_names.add(g[k])
    for o in c["outputs"]:
        if o in win_outputs:
            live_names.add(o)
    live_targets = sorted({vals[w] for w in live_names})

    ft = {}
    for j, (a, b) in enumerate(and_targets):
        for t in (a, b):
            ft[(t, j)] = max(ft.get((t, j), 0.0), 8.0)
    m = len(and_targets)
    for t in live_targets:
        ft[(t, m)] = max(ft.get((t, m), 0.0), 3.0)
    future_targets = [(t, d, w) for (t, d), w in ft.items()]

    best_state = None
    stats = {"expanded": 0, "generated": 0, "dedup": 0}
    for rr in range(restarts):
        rng = random.Random(seed + 1000003 * rr + 1009 * start_interval + 9176 * end_interval)
        init = normalize_stage(State(0, tuple(), frozenset(base_avail)), and_targets, and_atoms)
        if goal(init, live_targets, and_targets, and_atoms):
            best_state = init
            break
        layer = [init]
        seen = {state_hash(init.stage, init.helpers)}
        for _cost in range(budget):
            nxt = []
            for st in layer:
                stats["expanded"] += 1
                moves = candidate_moves(st, future_targets, guide_vecs, start_interval, n_and,
                                        const_bit, max_candidates, rng)
                for _, cv, op, a, b in moves:
                    helpers = st.helpers + ((st.stage, op, a, b, cv),)
                    ns = State(st.stage, helpers, frozenset(set(st.avail) | {cv}))
                    ns = normalize_stage(ns, and_targets, and_atoms)
                    stats["generated"] += 1
                    key = state_hash(ns.stage, ns.helpers)
                    if key in seen:
                        stats["dedup"] += 1
                        continue
                    seen.add(key)
                    if goal(ns, live_targets, and_targets, and_atoms):
                        best_state = ns
                        break
                    ns.score = state_quality(ns, future_targets, live_targets, start_interval,
                                             n_and, const_bit) + rng.random() * 1e-3
                    nxt.append(ns)
                if best_state is not None:
                    break
            if best_state is not None:
                break
            if not nxt:
                break
            nxt.sort(key=lambda s: s.score, reverse=True)
            layer = nxt[:beam]
        if best_state is not None:
            break

    result = {
        "status": "found" if best_state is not None else "not_found",
        "start": start_interval, "end": end_interval,
        "gate_lo": lo, "gate_hi": hi,
        "internal_ands": len(and_targets), "orig_linear": orig_linear, "budget": budget,
        "live_outs": len(live_targets), "beam": beam, "max_candidates": max_candidates,
        "restarts": restarts, **stats,
    }
    if best_state is None:
        return result

    vec_name = {}
    for w in prefix_names:
        vec_name.setdefault(vals[w], w)
    newg = []
    helpers_by_stage = collections.defaultdict(list)
    for rec in best_state.helpers:
        helpers_by_stage[rec[0]].append(rec)
    internal_ands = [g for g in window if g["op"] == "AND"]
    helper_no = 0
    for stage in range(len(internal_ands) + 1):
        for _, op, a, b, cv in helpers_by_stage.get(stage, []):
            if cv in vec_name:
                continue
            name = f"__tw_{start_interval}_{end_interval}_{helper_no}"
            helper_no += 1
            newg.append({"op": op, "a": vec_name[a], "b": vec_name[b], "out": name})
            vec_name[cv] = name
        if stage < len(internal_ands):
            g = internal_ands[stage]
            av, bv = and_targets[stage]
            if av not in vec_name or bv not in vec_name:
                raise AssertionError(("missing AND operand", stage, av in vec_name, bv in vec_name))
            newg.append({"op": "AND", "a": vec_name[av], "b": vec_name[bv], "out": g["out"]})
            vec_name[and_atoms[stage]] = g["out"]

    live_map = {}
    for w in live_names:
        v = vals[w]
        if v not in vec_name:
            raise AssertionError(("missing liveout", w))
        live_map[w] = vec_name[v]

    suff = []
    for g in suffix:
        ng = dict(g)
        ng["a"] = live_map.get(ng["a"], ng["a"])
        ng["b"] = live_map.get(ng["b"], ng["b"])
        suff.append(ng)
    outs = [live_map.get(o, o) for o in c["outputs"]]
    candidate = ras.prune({"gates": [dict(g) for g in prefix] + newg + suff, "outputs": outs})
    ok = ras.independent_check(candidate)
    if not ok[0]:
        raise AssertionError(("candidate failed AES check", ok))
    result.update({"candidate_gates": len(candidate["gates"]),
                   "helpers_used": len(best_state.helpers),
                   "verified_all_256": True,
                   "candidate": candidate})
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(ras.SOURCES), default="fs-101")
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--beam", type=int, default=240)
    ap.add_argument("--max-candidates", type=int, default=40)
    ap.add_argument("--restarts", type=int, default=4)
    ap.add_argument("--delta", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    c = ras.load_circuit(args.family)
    assert ras.independent_check(c)[0]
    res = search_window(c, args.start, args.end, args.beam, args.max_candidates,
                        args.restarts, args.delta, args.seed)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    candidate = res.pop("candidate", None)
    if candidate is not None:
        (out / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n")
    print(json.dumps(res, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
