#!/usr/bin/env python3
"""Joint CP-SAT recombination of relabeled valid C(15,9,7) covers."""
import argparse
import itertools
import json
import random
from pathlib import Path
from ortools.sat.python import cp_model

P = range(15)
SEVENS = list(itertools.combinations(P, 7))
INDEX = {s: i for i, s in enumerate(SEVENS)}

def verify(blocks):
    covered = bytearray(len(SEVENS))
    for block in blocks:
        assert len(block) == len(set(block)) == 9
        for s in itertools.combinations(sorted(block), 7):
            covered[INDEX[s]] = 1
    return 0 not in covered

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=15)
    p.add_argument("--rounds", type=int, default=8)
    p.add_argument("--parents", type=int, default=2)
    p.add_argument("--seconds", type=int, default=90)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--diversity", type=int, default=6)
    p.add_argument("--near", action="store_true")
    args = p.parse_args()
    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = {tuple(sorted(b)) for b in json.loads(Path(args.input).read_text())["blocks"]}
    assert len(base) == 270 and verify(base)
    parent = list(base)
    best = 270
    history = []
    for iteration in range(args.rounds):
        sources = [base]
        for k in range(args.parents - 1):
            permutation = list(P)
            rng.shuffle(permutation)
            if args.near and k == 0:
                permutation = list(P)
                for _ in range(rng.randint(1, 5)):
                    i, j = rng.sample(list(P), 2)
                    permutation[i], permutation[j] = permutation[j], permutation[i]
            src = parent if k == 0 else base
            relabeled = {tuple(sorted(permutation[q] for q in block)) for block in src}
            assert verify(relabeled)
            sources.append(relabeled)
        options = sorted(set.union(*sources))
        index = {block: i for i, block in enumerate(options)}
        hits = [[] for _ in SEVENS]
        for i, block in enumerate(options):
            for subset in itertools.combinations(block, 7):
                hits[INDEX[subset]].append(i)
        model = cp_model.CpModel()
        x = [model.NewBoolVar(f"x{i}") for i in range(len(options))]
        for candidates in hits:
            model.Add(sum(x[i] for i in candidates) >= 1)
        model.Add(sum(x) <= 270)
        for source in sources:
            model.Add(sum(x[index[block]] for block in options if block not in source) >= args.diversity)
        weights = [rng.randrange(1, 51) for _ in options]
        model.Minimize(100000 * sum(x) + sum(weights[i] * x[i] for i in range(len(options))))
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = args.seconds
        solver.parameters.num_search_workers = args.workers
        solver.parameters.random_seed = rng.randrange(2**30)
        status = solver.Solve(model)
        entry = {"iteration": iteration, "status": solver.StatusName(status),
                 "candidates": len(options), "elapsed": round(solver.WallTime(), 1)}
        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            candidate = [block for i, block in enumerate(options) if solver.Value(x[i])]
            assert verify(candidate)
            entry["score"] = len(candidate)
            entry["distance_baseline"] = len(set(candidate) - base)
            if len(candidate) < best:
                best = len(candidate)
                (out / "certificate.json").write_text(
                    json.dumps({"blocks": candidate}, separators=(",", ":")))
                print("IMPROVEMENT", best, flush=True)
            if len(candidate) == 270 and entry["distance_baseline"] >= args.diversity:
                parent = candidate
                (out / "novel-parent.json").write_text(
                    json.dumps({"blocks": candidate}, separators=(",", ":")))
        history.append(entry)
        (out / "history.json").write_text(json.dumps(history, indent=2))
        print(json.dumps(entry), flush=True)
        if best <= 269:
            break
    if not (out / "certificate.json").exists():
        (out / "certificate.json").write_text(
            json.dumps({"blocks": sorted(base)}, separators=(",", ":")))

if __name__ == "__main__":
    main()
