#!/usr/bin/env python3
import argparse
import json
from collections import deque
from pathlib import Path

import generalized9 as g
import neutral2_maxsat as nm
import neutral2_sweep as ns

BASELINE = 134_753
STATE_INDEX = 18
K9 = (60, 160, 231, 244, 250, 267, 330, 344, 364)
XZERO = 294
EXPECTED_REMOVE = (267, 294)
EXPECTED_ADD = (15083, 16388)


def load_state(r0, digits):
    supports0, _ = g.support_masks(r0, digits)
    states = ns.enumerate_states(r0, digits, supports0)
    r, rem, add = states[STATE_INDEX - 1]
    if tuple(rem) != EXPECTED_REMOVE or tuple(add) != EXPECTED_ADD:
        raise RuntimeError(f"state-18 drift: rem={rem} add={add}")
    return r


def port_conflict(a, b, xset, digits):
    oa, ia, ea = a
    ob, ib, eb = b
    if oa == "H" and ob == "H":
        return g.conflict(ea, eb, digits) and g.conflict(xset[ia], xset[ib], digits)
    if oa == "V" and ob == "V":
        return g.conflict(xset[ia], xset[ib], digits) and g.conflict(ea, eb, digits)
    if oa == "H":
        return g.conflict(ea, xset[ib], digits) and g.conflict(xset[ia], eb, digits)
    return g.conflict(xset[ib], ea, digits) and g.conflict(eb, xset[ia], digits)


def hopcroft_karp(adj, nr):
    nl = len(adj)
    ml = [-1] * nl
    mr = [-1] * nr
    dist = [-1] * nl

    def bfs():
        q = deque()
        found = False
        for u in range(nl):
            if ml[u] < 0:
                dist[u] = 0
                q.append(u)
            else:
                dist[u] = -1
        while q:
            u = q.popleft()
            for v in adj[u]:
                w = mr[v]
                if w < 0:
                    found = True
                elif dist[w] < 0:
                    dist[w] = dist[u] + 1
                    q.append(w)
        return found

    def dfs(u):
        for v in adj[u]:
            w = mr[v]
            if w < 0 or (dist[w] == dist[u] + 1 and dfs(w)):
                ml[u] = v
                mr[v] = u
                return True
        dist[u] = -1
        return False

    matching = 0
    while bfs():
        for u in range(nl):
            if ml[u] < 0 and dfs(u):
                matching += 1
    return matching, ml, mr


def deficiency_witness(adj, ml, mr):
    zl = [False] * len(adj)
    zr = [False] * len(mr)
    q = deque()
    for u, v in enumerate(ml):
        if v < 0:
            zl[u] = True
            q.append(u)
    while q:
        u = q.popleft()
        for v in adj[u]:
            if ml[u] == v or zr[v]:
                continue
            zr[v] = True
            w = mr[v]
            if w >= 0 and not zl[w]:
                zl[w] = True
                q.append(w)
    left = [i for i, z in enumerate(zl) if z]
    right = [i for i, z in enumerate(zr) if z]
    return left, right


def verify_independent(words, digits):
    if len(words) != 367 or len(set(words)) != 367:
        raise ValueError("external state is not 367 distinct words")
    for i in range(len(words)):
        for j in range(i + 1, len(words)):
            if g.conflict(words[i], words[j], digits):
                raise ValueError(f"external state is not independent: {i},{j}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("family_f_json", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = load_state(r0, digits)
    supports, _ = g.support_masks(r, digits)
    base_model, base_stats = nm.solve_maxsat(K9, r, xset, digits, supports)
    if base_model is None or base_stats["score"] != BASELINE:
        raise RuntimeError(f"expected rank3 tie, got {base_stats}")
    _, hs, vs = base_model

    bidx = [i for i in range(g.R_SIZE) if i not in set(K9)]
    x0 = xset[XZERO]
    if any(g.conflict(x0, r[i], digits) for i in bidx):
        raise RuntimeError("x294 is not zero-conflict to B")

    old = []
    old_set = set()
    for i, arr in enumerate(hs):
        for e in arr:
            p = ("H", i, e)
            old.append(p); old_set.add(p)
    for i, arr in enumerate(vs):
        for e in arr:
            p = ("V", i, e)
            old.append(p); old_set.add(p)
    if len(old) != base_stats["selected"]:
        raise RuntimeError("old port count mismatch")

    states = json.loads(args.family_f_json.read_text(encoding="utf-8"))["states"]
    best = {"gain": 0}
    tested = 0

    for si, words0 in enumerate(states):
        words = [int(v) for v in words0]
        verify_independent(words, digits)
        for ori in ("H", "V"):
            cand = [e for e in words if (ori, XZERO, e) not in old_set]
            # Only old ports actually touched by this family need right-side nodes.
            touched = []
            touched_index = {}
            adj_old = []
            for e in cand:
                hits = []
                p = (ori, XZERO, e)
                for oi, q in enumerate(old):
                    if port_conflict(p, q, xset, digits):
                        if oi not in touched_index:
                            touched_index[oi] = len(touched)
                            touched.append(oi)
                        hits.append(touched_index[oi])
                adj_old.append(hits)
            matching, ml, mr = hopcroft_karp(adj_old, len(touched))
            gain = len(cand) - matching
            tested += 1
            print("SCREEN", json.dumps({"state": si, "orientation": ori, "left": len(cand), "right": len(touched), "matching": matching, "gain": gain}), flush=True)
            if gain <= best["gain"]:
                continue
            left_wit, right_wit = deficiency_witness(adj_old, ml, mr)
            selected_new = [(ori, XZERO, cand[i]) for i in left_wit]
            dropped_old_indices = [touched[i] for i in right_wit]
            actual_gain = len(selected_new) - len(dropped_old_indices)
            if actual_gain != gain:
                raise RuntimeError(f"deficiency witness mismatch {actual_gain} != {gain}")
            best = {
                "gain": gain,
                "state": si,
                "orientation": ori,
                "left": len(cand),
                "right": len(touched),
                "matching": matching,
                "selected_new": selected_new,
                "dropped_old_indices": dropped_old_indices,
            }
            if gain > 0:
                break
        if best["gain"] > 0:
            break

    status = {
        "candidate": best["gain"] > 0,
        "score": BASELINE + best["gain"],
        "method": "x294-family-f-hall-deficiency",
        "external_states": len(states),
        "tested_state_orientations": tested,
        "best": best,
    }

    if best["gain"] > 0:
        drop = set(best["dropped_old_indices"])
        keep = [p for i, p in enumerate(old) if i not in drop]
        add = [tuple(p) for p in best["selected_new"]]
        for p in add:
            if any(port_conflict(p, q, xset, digits) for q in keep):
                raise RuntimeError("new port conflicts retained old port")
        for i in range(len(add)):
            for j in range(i + 1, len(add)):
                if port_conflict(add[i], add[j], xset, digits):
                    raise RuntimeError("new family ports conflict")
        ports = keep + add
        candidate = {r[a] * g.U + r[b] for a in bidx for b in bidx}
        for ori, i, e in ports:
            xv = xset[i]
            candidate.add(e * g.U + xv if ori == "H" else xv * g.U + e)
        expected = len(bidx) ** 2 + len(ports)
        if len(candidate) != expected or len(candidate) != status["score"]:
            raise RuntimeError(f"candidate size mismatch {len(candidate)} != {expected} != {status['score']}")
        baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
        status["removed_vs_baseline"] = len(baseline - candidate)
        status["added_vs_baseline"] = len(candidate - baseline)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n")
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
    else:
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
