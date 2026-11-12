#!/usr/bin/env python3
"""Global 269-block maximum-coverage CP-SAT with a near-cover warm start."""
import argparse
import itertools
import json
from pathlib import Path
from ortools.sat.python import cp_model

P = range(15)
SEVENS = list(itertools.combinations(P, 7))
NINES = list(itertools.combinations(P, 9))
INDEX = {s: i for i, s in enumerate(SEVENS)}
NINE_ID = {b: i for i, b in enumerate(NINES)}
COV = []
HITS = [[] for _ in SEVENS]
for i, block in enumerate(NINES):
    coverage = [INDEX[q] for q in itertools.combinations(block, 7)]
    COV.append(coverage)
    for t in coverage:
        HITS[t].append(i)

def missing(ids):
    covered = bytearray(len(SEVENS))
    for block in ids:
        for t in COV[block]:
            covered[t] = 1
    return [i for i, c in enumerate(covered) if not c]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--drop", type=int, default=0)
    p.add_argument("--seconds", type=int, default=900)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--seed", type=int, default=15)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = json.loads(Path(args.input).read_text())["blocks"]
    original = [NINE_ID[tuple(sorted(b))] for b in blocks]
    assert len(original) == 270 and missing(original) == []
    ownership = [0] * len(SEVENS)
    for a in original:
        for t in COV[a]:
            ownership[t] += 1
    ranked = sorted(original, key=lambda a: sum(ownership[t] == 1 for t in COV[a]))
    removed = ranked[args.drop]
    ids = [a for a in original if a != removed]
    start_miss = missing(ids)
    print("start_missing", len(start_miss), "removed", removed, flush=True)
    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{i}") for i in range(len(NINES))]
    holes = [model.NewBoolVar(f"u{t}") for t in range(len(SEVENS))]
    for t, choices in enumerate(HITS):
        model.AddBoolOr([x[a] for a in choices] + [holes[t]])
    model.Add(sum(x) == 269)
    model.Minimize(sum(holes))
    chosen = set(ids)
    uncovered = set(start_miss)
    for i, var in enumerate(x):
        model.AddHint(var, int(i in chosen))
    for t, var in enumerate(holes):
        model.AddHint(var, int(t in uncovered))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    status = solver.Solve(model)
    meta = {"status": solver.StatusName(status), "initial_missing": len(start_miss),
            "seed": args.seed, "drop": args.drop, "walltime": round(solver.WallTime(), 2)}
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        result = [i for i in range(len(NINES)) if solver.Value(x[i])]
        assert len(result) == 269
        remain = missing(result)
        meta["best_missing"] = len(remain)
        meta["missing_seven_sets"] = [list(SEVENS[i]) for i in remain]
        (out / "near-certificate.json").write_text(
            json.dumps({"blocks": [list(NINES[i]) for i in result]}, separators=(",", ":")))
        if not remain:
            (out / "certificate.json").write_text(
                json.dumps({"blocks": [list(NINES[i]) for i in result]}, separators=(",", ":")))
            print("FOUND FULL 269 COVER", flush=True)
    if not (out / "certificate.json").exists():
        (out / "certificate.json").write_text(json.dumps({"blocks": blocks}, separators=(",", ":")))
    (out / "result.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta), flush=True)

if __name__ == "__main__":
    main()
