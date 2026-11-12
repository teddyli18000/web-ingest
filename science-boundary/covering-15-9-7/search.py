#!/usr/bin/env python3
"""Randomized exact large-neighborhood repair of a 15,9,7 covering."""
import argparse
import itertools
import json
import random
import time
from pathlib import Path
from ortools.sat.python import cp_model

POINTS = range(15)
SEVENS = list(itertools.combinations(POINTS, 7))
INDEX = {v: i for i, v in enumerate(SEVENS)}
NINES = list(itertools.combinations(POINTS, 9))
NINE_INDEX = {b: i for i, b in enumerate(NINES)}
COVER = [tuple(INDEX[s] for s in itertools.combinations(b, 7)) for b in NINES]
HITS = [[] for _ in SEVENS]
for i, cov in enumerate(COVER):
    for j in cov:
        HITS[j].append(i)

def check(ids):
    assert len(ids) == len(set(ids))
    counts = [0] * len(SEVENS)
    for i in ids:
        for j in COVER[i]:
            counts[j] += 1
    return min(counts), sum(c == 1 for c in counts), counts

def save(ids, path):
    obj = {"blocks": [list(NINES[i]) for i in sorted(ids)]}
    Path(path).write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", default="p015-results")
    p.add_argument("--seed", type=int, default=15)
    p.add_argument("--rounds", type=int, default=18)
    p.add_argument("--seconds", type=float, default=75)
    p.add_argument("--workers", type=int, default=4)
    a = p.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = json.loads(Path(a.input).read_text())["blocks"]
    state = [NINE_INDEX[tuple(sorted(b))] for b in blocks]
    assert check(state)[0] >= 1
    best = state[:]
    save(best, out / "best.json")
    history = []
    started = time.monotonic()

    for iteration in range(a.rounds):
        k = rng.choice([12, 18, 24, 30, 36, 42, 48, 60])
        k = min(k, len(state))
        _, _, cnt = check(state)
        # Prioritize blocks with little exclusive coverage, plus randomization.
        score = [(sum(cnt[j] == 1 for j in COVER[i]) + rng.random() * 18, i) for i in state]
        score.sort()
        pool = [i for _, i in score[:min(len(score), k * 4)]]
        removed = set(rng.sample(pool, k))
        frozen = [i for i in state if i not in removed]
        _, _, remain = check(frozen)
        uncovered = [j for j, c in enumerate(remain) if c == 0]
        allowed = sorted({i for j in uncovered for i in HITS[j]})
        model = cp_model.CpModel()
        x = {i: model.NewBoolVar(f"b{i}") for i in allowed}
        for j in uncovered:
            model.Add(sum(x[i] for i in HITS[j] if i in x) >= 1)
        model.Add(sum(x.values()) <= k)
        # Minimize block count first, and random secondary cost to encourage alternate basins.
        weights = {i: rng.randrange(1, 100) for i in allowed}
        model.Minimize(10000 * sum(x.values()) + sum(weights[i] * x[i] for i in allowed))
        for i in removed:
            if i in x:
                model.AddHint(x[i], 1)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = a.seconds
        solver.parameters.num_search_workers = a.workers
        solver.parameters.random_seed = rng.randrange(2**30)
        status = solver.Solve(model)
        entry = {"iteration": iteration, "removed": k, "uncovered": len(uncovered), "variables": len(allowed),
                 "status": solver.StatusName(status), "seconds": round(solver.WallTime(), 2)}
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            chosen = [i for i in allowed if solver.Value(x[i])]
            candidate = frozen + chosen
            assert check(candidate)[0] >= 1
            entry["score"] = len(candidate)
            entry["changes"] = len(set(candidate) - set(state))
            state = candidate
            if len(state) < len(best):
                best = state[:]
                save(best, out / "best.json")
                print("IMPROVEMENT", len(best), flush=True)
        history.append(entry)
        (out / "history.json").write_text(json.dumps(history, indent=2))
        print(json.dumps(entry), flush=True)
    save(best, out / "certificate.json")
    print(json.dumps({"best":len(best), "verified":check(best)[0]>=1,
                       "elapsed":round(time.monotonic()-started,1)}), flush=True)

if __name__ == "__main__":
    main()
