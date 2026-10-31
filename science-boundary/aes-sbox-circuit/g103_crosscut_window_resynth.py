#!/usr/bin/env python3
"""Jointly resynthesize a G103 window that crosses the old prefix/suffix cut.

The normalized NIST G103 AES S-box has 32 AND and 71 linear gates.  Previous
work often split it after the last AND into a 49-linear nonlinear prefix and a
22-gate pure-linear suffix, then tried to save gates on each side separately.
That cut is only a representation choice.

This driver constructs an equivalent 103-gate circuit in one of the cheap
GL(3,2) cut bases and calls temporal_window_resynth on a window ending at the
final output interval.  The window may therefore contain several late AND
releases, the three cut coordinates, and the entire output network at once.
With delta=3, any hit is directly a <=100-gate complete AES circuit.

This is a heuristic beam search.  A miss excludes nothing outside the explored
beam/restart portfolio; a hit is independently checked on all 256 AES inputs by
temporal_window_resynth and can then be sent to the official Few Shots verifier.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez
import g103_explicit_cut_basis as xp
import g103_suffix_guide_subset as gs
import temporal_window_resynth as tw


def transformed_full(c, rows):
    prec, pmeta = xp.synthesize_at_cut(c, rows)
    if prec is None:
        raise ValueError(("basis has no <=49 explicit prefix", rows, pmeta))
    net, smeta = gs.search(c, rows, 22)
    if net is None:
        raise AssertionError(("all-guide transformed suffix failed to close", rows, smeta))
    full = xp.attach_suffix(c, prec, net)
    ok = ras.independent_check(full)
    if not ok[0]:
        raise AssertionError(("transformed 103 seed failed AES", rows, ok))
    na = sum(g["op"] == "AND" for g in full["gates"])
    nl = len(full["gates"]) - na
    if (na, nl) != (32, 71):
        raise AssertionError(("unexpected transformed seed cost", rows, na, nl))
    return full, pmeta, smeta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--basis-rows", type=ez.parse_rows, default=(1, 2, 4))
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--beam", type=int, default=360)
    ap.add_argument("--max-candidates", type=int, default=56)
    ap.add_argument("--restarts", type=int, default=6)
    ap.add_argument("--delta", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    c = ras.load_circuit("nist-g103")
    assert ras.independent_check(c)[0]
    t0 = time.time()
    full, pmeta, smeta = transformed_full(c, args.basis_rows)
    sched = tw.original_schedule(full)
    n_and = sum(g["op"] == "AND" for g in full["gates"])
    if n_and != 32:
        raise AssertionError(n_and)
    end = n_and
    if not (0 <= args.start <= end):
        raise ValueError((args.start, end))

    result = tw.search_window(
        full, args.start, end,
        args.beam, args.max_candidates, args.restarts, args.delta, args.seed,
    )
    candidate = result.pop("candidate", None)
    summary = {
        "basis_rows": list(args.basis_rows),
        "start": args.start,
        "end": end,
        "delta": args.delta,
        "beam": args.beam,
        "max_candidates": args.max_candidates,
        "restarts": args.restarts,
        "seed": args.seed,
        "schedule": sched,
        "prefix_meta": pmeta,
        "suffix_seed_meta": smeta,
        "result": result,
        "elapsed_s": round(time.time() - t0, 3),
    }
    if candidate is not None:
        ok = ras.independent_check(candidate)
        if not ok[0]:
            raise AssertionError(("cross-cut candidate failed AES", ok))
        (out / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
        summary["candidate_gates"] = len(candidate["gates"])
        summary["verified_all_256"] = True
        summary["gate_counts"] = {
            op: sum(g["op"] == op for g in candidate["gates"])
            for op in ("AND", "XOR", "XNOR")
        }

    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "basis_rows": summary["basis_rows"],
        "start": args.start,
        "delta": args.delta,
        "elapsed_s": summary["elapsed_s"],
        "candidate_gates": summary.get("candidate_gates"),
        **result,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
