#!/usr/bin/env python3
"""Aggregate p008 semilinear-search summary.json artifacts.

Recursively finds summary.json files under one or more directories and reports
coverage plus the total number of 101 candidates / saved witnesses.  This keeps
workflow-success status separate from scientific negative evidence: a successful
search job is only a zero-candidate result when its summary says so.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    rows = []
    seen_paths = set()
    for root in args.roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("summary.json")):
            resolved = path.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            data = json.loads(path.read_text())
            counts = data.get("counts", {}) or {}
            row = {
                "path": str(path),
                "c": data.get("c"),
                "k": data.get("k"),
                "prefix": data.get("prefix"),
                "proof_scope": data.get("proof_scope"),
                "orientations": counts.get("orientations"),
                "candidates_101": counts.get("candidates_101", data.get("candidates_101", 0)),
                "best_witnesses_saved": data.get("best_witnesses_saved", 0),
                "best_total_gate_upper_bound": data.get("best_total_gate_upper_bound"),
                "elapsed_seconds": data.get("elapsed_seconds"),
            }
            rows.append(row)

    summary = {
        "summary_files": len(rows),
        "total_orientations": sum(int(r["orientations"] or 0) for r in rows),
        "total_candidates_101": sum(int(r["candidates_101"] or 0) for r in rows),
        "total_best_witnesses_saved": sum(int(r["best_witnesses_saved"] or 0) for r in rows),
        "nonzero_candidate_rows": [r for r in rows if int(r["candidates_101"] or 0) != 0],
        "nonzero_witness_rows": [r for r in rows if int(r["best_witnesses_saved"] or 0) != 0],
        "rows": rows,
    }
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
