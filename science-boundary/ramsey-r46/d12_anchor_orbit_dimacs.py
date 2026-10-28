#!/usr/bin/env python3
"""Exact orbit decomposition of the unique lucky-d12 A29/B101 gluing.

The unique B101 graph has exactly one vertex of internal degree 10.  In any
36-vertex Ramsey(4,6) extension, its 12-bit cross-neighbourhood X in A29 must
satisfy the full-degree bound and must hit every independent 5-set of A.
There are 2,873 such labelled masks, but Aut(A29) has order 576.  Taking the
least integer mask in each Aut(A)-orbit leaves 118 representatives.

For every full solution, an automorphism of fixed A maps the distinguished
B column to one of those representatives.  Therefore the disjunction of the
118 branch CNFs is EXACTLY complete for the original fixed-pair problem up to
A relabelling.  Each branch otherwise contains the same complete mixed
K4/I6 and degree 11..17 encoding as d12_fixed_ab_sat.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pysat.formula import IDPool

import d12_fixed_ab_sat as base
import d12_fixed_ab_sym_sat as sym
from d12_fixed_ab_sym_dimacs import ClauseSink, decode as decode_model

NA, NB = 12, 23


def image_mask(mask: int, p: tuple[int, ...]) -> int:
    out = 0
    for a in range(NA):
        if (mask >> a) & 1:
            out |= 1 << p[a]
    return out


def orbit_data(A: list[int], B: list[int]) -> dict:
    autos = sym.automorphisms(A)
    if len(autos) != 576:
        raise AssertionError(f"expected |Aut(A29)|=576, got {len(autos)}")
    db = base.degrees(B)
    anchors = [b for b, d in enumerate(db) if d == 10]
    if len(anchors) != 1:
        raise AssertionError(f"expected unique B degree-10 vertex, got {anchors}")
    anchor = anchors[0]
    bounds = base.cross_bounds(db[anchor], NA, 11, 17)
    if bounds is None:
        raise AssertionError("anchor has impossible full-degree bounds")
    lo, hi = bounds
    i5 = base.subsets(A, 5, False)
    i5_masks = [sum(1 << a for a in vs) for vs in i5]
    allowed = [
        mask for mask in range(1 << NA)
        if lo <= mask.bit_count() <= hi and all(mask & p for p in i5_masks)
    ]
    canonical: dict[int, list[int]] = {}
    for mask in allowed:
        rep = min(image_mask(mask, p) for p in autos)
        canonical.setdefault(rep, []).append(mask)
    reps = sorted(canonical)
    # Exact orbit-cover authentication on the finite allowed set.
    for mask in allowed:
        rep = min(image_mask(mask, p) for p in autos)
        if rep not in canonical:
            raise AssertionError("lost orbit representative")
        if min(image_mask(rep, p) for p in autos) != rep:
            raise AssertionError("representative is not canonical")
    return {
        "anchor_b": anchor,
        "anchor_internal_degree": db[anchor],
        "cross_size_min": lo,
        "cross_size_max": hi,
        "independent5_count_A": len(i5_masks),
        "aut_A_order": len(autos),
        "allowed_labelled_masks": len(allowed),
        "orbit_count": len(reps),
        "representatives": reps,
        "orbit_sizes": [len(canonical[r]) for r in reps],
        "representative_sizes": [r.bit_count() for r in reps],
    }


def load_pair(a_catalog: Path, b_catalog: Path):
    ag6, A, ae = base.select_record(a_catalog, 0, NA)
    bg6, B, be = base.select_record(b_catalog, 0, NB)
    base.validate_A(A); base.validate_B(B)
    if (ae, be) != (29, 101):
        raise ValueError((ae, be))
    return ag6, A, bg6, B


def manifest(a_catalog: Path, b_catalog: Path, out: Path | None = None) -> dict:
    ag6, A, bg6, B = load_pair(a_catalog, b_catalog)
    data = orbit_data(A, B)
    data.update(a_graph6=ag6, b_graph6=bg6)
    if data["allowed_labelled_masks"] != 2873 or data["orbit_count"] != 118:
        raise AssertionError((data["allowed_labelled_masks"], data["orbit_count"]))
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k not in {"representatives", "orbit_sizes", "representative_sizes", "a_graph6", "b_graph6"}}, sort_keys=True))
    return data


def generate(a_catalog: Path, b_catalog: Path, ordinal: int, out: Path, meta: Path) -> dict:
    ag6, A, bg6, B = load_pair(a_catalog, b_catalog)
    od = orbit_data(A, B)
    reps = od["representatives"]
    if not 0 <= ordinal < len(reps):
        raise IndexError((ordinal, len(reps)))
    mask = reps[ordinal]
    anchor = od["anchor_b"]

    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    sink = ClauseSink()
    ramsey_counts = sym.add_all_constraints(sink, pool, x, A, B, 11, 17)
    for a in range(NA):
        sink.add_clause([x[a][anchor] if ((mask >> a) & 1) else -x[a][anchor]])

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="ascii", buffering=1024 * 1024) as f:
        f.write(f"p cnf {pool.top} {len(sink.clauses)}\n")
        for clause in sink.clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")
    result = {
        "encoding": "exact fixed A29/B101 branch with canonical unique-degree10-B anchor mask",
        "branch_ordinal": ordinal,
        "branch_count": len(reps),
        "anchor_b": anchor,
        "anchor_mask": mask,
        "anchor_mask_bits": [a for a in range(NA) if (mask >> a) & 1],
        "anchor_cross_degree": mask.bit_count(),
        "anchor_orbit_size": od["orbit_sizes"][ordinal],
        "allowed_labelled_masks": od["allowed_labelled_masks"],
        "aut_A_order": od["aut_A_order"],
        "variables": pool.top,
        "clauses": len(sink.clauses),
        "ramsey_counts": ramsey_counts,
        "a_graph6": ag6,
        "b_graph6": bg6,
        "path": str(out),
    }
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return result


def self_test() -> None:
    # Pure permutation-mask sanity independent of catalogue files.
    p = tuple(reversed(range(NA)))
    for m in (0, 1, 3, 0x555, (1 << NA) - 1):
        assert image_mask(image_mask(m, p), p) == m
        assert image_mask(m, tuple(range(NA))) == m
    print("d12 anchor-orbit DIMACS self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("manifest")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p = sub.add_parser("generate")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--ordinal", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--meta", type=Path, required=True)
    p = sub.add_parser("decode")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--solver-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    if args.cmd == "manifest":
        manifest(args.a_catalog, args.b_catalog, args.output); return 0
    if args.cmd == "generate":
        generate(args.a_catalog, args.b_catalog, args.ordinal, args.output, args.meta); return 0
    decode_model(args.a_catalog, args.b_catalog, args.solver_log, args.output); return 0


if __name__ == "__main__":
    raise SystemExit(main())
