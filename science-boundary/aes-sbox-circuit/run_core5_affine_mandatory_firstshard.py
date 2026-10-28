#!/usr/bin/env python3
"""Exact first-AND sharding wrapper for search_core5_affine_mandatory.py.

The underlying exact search branches on the nonlinear class of the first AND.
There are exactly 35 possible nonzero classes from affine functions of the four
core inputs.  Distinct first classes never merge at depth zero, so filtering them
into disjoint shards partitions the complete search with no loss.

This wrapper monkey-patches only the depth-zero candidate list and then delegates
all physical phase, mandatory-form, dominance, fifth-AND and target accounting to
the underlying exact implementation unchanged.
"""
from __future__ import annotations

import argparse
import sys

import search_core5_affine_mandatory as exact


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int, required=True, choices=range(16))
    ap.add_argument("--first-shard", type=int, required=True)
    ap.add_argument("--first-shards", type=int, required=True)
    ap.add_argument("--fifth-shard", type=int, default=0)
    ap.add_argument("--fifth-shards", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not 0 <= args.first_shard < args.first_shards:
        raise SystemExit("bad first shard")

    _pattern, _targets, target_basis = exact.rank4_cases()[args.case]
    original = exact.candidate_pairs
    depth0 = original((), target_basis, {})
    residues = sorted({pair[4][0] for pair in depth0})
    assert len(residues) == 35, len(residues)
    allowed = {
        residue for i, residue in enumerate(residues)
        if (i % args.first_shards) == args.first_shard
    }
    assert allowed

    def sharded_pairs(nonlinear_basis, target_basis_arg, cache):
        pairs = original(nonlinear_basis, target_basis_arg, cache)
        if nonlinear_basis:
            return pairs
        return tuple(pair for pair in pairs if pair[4][0] in allowed)

    exact.candidate_pairs = sharded_pairs
    sys.argv = [
        "search_core5_affine_mandatory.py",
        "--case", str(args.case),
        "--shard", str(args.fifth_shard),
        "--shards", str(args.fifth_shards),
        "--out", args.out,
    ]
    exact.main()


if __name__ == "__main__":
    main()
