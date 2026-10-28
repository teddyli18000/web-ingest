#!/usr/bin/env python3
"""Independent CaDiCaL195 rerun of the 118 lucky-d12 orbit branches.

Each branch is regenerated with residual generator lex-leaders, then solved in
an isolated child process so a per-branch wall-clock timeout can be enforced.
The generator set is checked by d12_fixed_ab_sym_sat.greedy_generators to close
to the full residual stabilizer.  A SAT model is decoded and fully checked by
the existing fixed-pair decoder before being written as a candidate.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from pysat.formula import CNF
from pysat.solvers import Solver

import d12_anchor_orbit_dimacs as orbit

HERE = Path(__file__).resolve().parent
DEFAULT_A = HERE / "data" / "r36_12_e29.g6"
DEFAULT_B = HERE / "data" / "r45extreme_n23_e101_unique.g6"


def _solve_child(cnf_path: str, solver_name: str, q: mp.Queue) -> None:
    try:
        cnf = CNF(from_file=cnf_path)
        with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
            sat = solver.solve()
            model = solver.get_model() if sat else None
        q.put({"status": "SAT" if sat else "UNSAT", "model": model})
    except BaseException as exc:  # child must report rather than silently die
        q.put({"status": "ERROR", "error": repr(exc)})


def solve_with_timeout(cnf_path: Path, solver_name: str, timeout_s: float) -> dict:
    q: mp.Queue = mp.Queue(maxsize=1)
    p = mp.Process(target=_solve_child, args=(str(cnf_path), solver_name, q))
    started = time.monotonic()
    p.start()
    p.join(timeout_s)
    elapsed = time.monotonic() - started
    if p.is_alive():
        p.terminate()
        p.join(10)
        if p.is_alive():
            p.kill()
            p.join()
        return {"status": "TIMEOUT", "seconds": round(elapsed, 6)}
    if q.empty():
        return {
            "status": "ERROR",
            "seconds": round(elapsed, 6),
            "error": f"solver child exited {p.exitcode} without a result",
        }
    result = q.get()
    result["seconds"] = round(elapsed, 6)
    result["exitcode"] = p.exitcode
    return result


def write_model_log(path: Path, model: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii") as f:
        f.write("s SATISFIABLE\n")
        width = 20
        for i in range(0, len(model), width):
            f.write("v " + " ".join(map(str, model[i : i + width])) + " 0\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a-catalog", type=Path, default=DEFAULT_A)
    ap.add_argument("--b-catalog", type=Path, default=DEFAULT_B)
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--candidate-dir", type=Path)
    args = ap.parse_args()

    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError((args.shard_index, args.shard_count))

    manifest = orbit.manifest(args.a_catalog, args.b_catalog)
    assert manifest["allowed_labelled_masks"] == 2873
    assert manifest["orbit_count"] == 118
    ordinals = [i for i in range(118) if i % args.shard_count == args.shard_index]

    rows: list[dict] = []
    candidate_dir = args.candidate_dir or args.output.parent / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    for ordinal in ordinals:
        with TemporaryDirectory(prefix=f"d12-cadical-{ordinal:03d}-") as td:
            td_path = Path(td)
            cnf_path = td_path / "branch.cnf"
            meta_path = td_path / "meta.json"
            meta = orbit.generate(
                args.a_catalog,
                args.b_catalog,
                ordinal,
                cnf_path,
                meta_path,
                "generators",
            )
            result = solve_with_timeout(cnf_path, args.solver, args.timeout)
            row = {
                "ordinal": ordinal,
                "anchor_mask": meta["anchor_mask"],
                "anchor_orbit_size": meta["anchor_orbit_size"],
                "stabilizer_A_order": meta["stabilizer_A_order"],
                "stabilizer_A_generators": meta["stabilizer_A_generators"],
                "used_A_permutations": meta["used_A_permutations"],
                "used_B_permutations": meta["used_B_permutations"],
                "variables": meta["variables"],
                "clauses": meta["clauses"],
                "solver": args.solver,
                "residual_mode": "generators",
                "status": result["status"],
                "seconds": result["seconds"],
            }
            if result["status"] == "ERROR":
                row["error"] = result.get("error")
            if result["status"] == "SAT":
                model = result.get("model")
                if not model:
                    raise AssertionError(f"SAT branch {ordinal} returned no model")
                log_path = candidate_dir / f"ordinal-{ordinal:03d}.solver.log"
                candidate_path = candidate_dir / f"ordinal-{ordinal:03d}.json"
                write_model_log(log_path, model)
                # Decoder reconstructs the 36-vertex graph and calls the exact
                # full K4/I6/degree checker before writing the candidate.
                orbit.decode_model(args.a_catalog, args.b_catalog, log_path, candidate_path)
                row["candidate"] = str(candidate_path)
                row["solver_log"] = str(log_path)
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)

    counts = {name: sum(r["status"] == name for r in rows) for name in ("UNSAT", "SAT", "TIMEOUT", "ERROR")}
    report = {
        "campaign": "lucky-d12-cadical195-residual-generators-crosscheck",
        "solver": args.solver,
        "residual_mode": "generators",
        "timeout_s": args.timeout,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "branch_count_total": 118,
        "attempted_ordinals": ordinals,
        "complete_shard": len(rows) == len(ordinals) and counts["ERROR"] == 0,
        "counts": counts,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("campaign", "shard_index", "shard_count", "complete_shard", "counts")}, sort_keys=True))
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
