#!/usr/bin/env python3
"""Merge and validate shards from d12_cadical_crosscheck.py."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    paths = sorted(args.input_dir.glob("shard-*.json"))
    if not paths:
        raise FileNotFoundError(f"no shard JSON files under {args.input_dir}")
    shards = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    shard_counts = {int(s["shard_count"]) for s in shards}
    assert len(shard_counts) == 1, shard_counts
    shard_count = next(iter(shard_counts))
    assert len(shards) == shard_count, (len(shards), shard_count)
    assert {int(s["shard_index"]) for s in shards} == set(range(shard_count))
    assert {s["campaign"] for s in shards} == {"lucky-d12-cadical195-residual-generators-crosscheck"}
    assert {s["solver"] for s in shards} == {"cadical195"}
    assert {s["residual_mode"] for s in shards} == {"generators"}

    rows = [row for shard in shards for row in shard["rows"]]
    by_ordinal: dict[int, list[dict]] = {i: [] for i in range(118)}
    for row in rows:
        ordinal = int(row["ordinal"])
        assert ordinal in by_ordinal, ordinal
        by_ordinal[ordinal].append(row)
    duplicates = {k: len(v) for k, v in by_ordinal.items() if len(v) != 1}
    assert not duplicates, duplicates
    rows = [by_ordinal[i][0] for i in range(118)]

    counts = {name: sum(r["status"] == name for r in rows) for name in ("UNSAT", "SAT", "TIMEOUT", "ERROR")}
    complete = counts["ERROR"] == 0 and counts["TIMEOUT"] == 0
    if counts["SAT"]:
        exact_decision = "SAT"
    elif complete and counts["UNSAT"] == 118:
        exact_decision = "UNSAT"
    else:
        exact_decision = "UNKNOWN"

    result = {
        "campaign": "lucky-d12-cadical195-residual-generators-crosscheck",
        "solver": "cadical195",
        "residual_mode": "generators",
        "shard_count": shard_count,
        "branch_count": 118,
        "complete": complete,
        "exact_decision": exact_decision,
        "counts": counts,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("campaign", "complete", "exact_decision", "counts")}, sort_keys=True))
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
