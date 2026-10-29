#!/usr/bin/env python3
"""Exact 5-AND mandatory-form search for the cheapest legal rank-9 multiplier support.

The fixed-102 five-AND exclusion targeted one particular nine-factor set.  The
new multiplier classification proves that rank-9 GF(16) multiplication has only
three right-support semilinear orbits, and the uniquely most promising coordinate
support is

    S* = {1,2,3,4,5,8,10,12,15},

which needs only five XORs from the four standard coordinate bits.

This wrapper reuses `search_core5_exact_mandatory.py` unchanged after replacing
`search_core5_cost`'s target functions by the nine exact functions

    x -> r · inv_GF16(x),  r in S*.

GF(16) uses polynomial x^4+x+1 and inv(0)=0.  Thus a mandatory minimum >=13
would rule out a zero-preserving `5 AND + 12 linear` inverter that directly
exposes this multiplier support.  A <=12 hit is only a necessary-count witness;
it must still pass physical XOR scheduling and then be integrated with one of the
30 exact multiplier schemes having this right support.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import search_core5_cost as base

SUPPORT = (1,2,3,4,5,8,10,12,15)


def gf16mul(a: int, b: int) -> int:
    p = 0
    for i in range(4):
        if (b >> i) & 1:
            p ^= a << i
    for d in range(6, 3, -1):
        if (p >> d) & 1:
            p ^= 1 << d
            p ^= 1 << (d - 3)
            p ^= 1 << (d - 4)
    return p & 0xF


def gf16pow(a: int, n: int) -> int:
    out = 1
    while n:
        if n & 1:
            out = gf16mul(out, a)
        a = gf16mul(a, a)
        n >>= 1
    return out


def inv(a: int) -> int:
    return 0 if a == 0 else gf16pow(a, 14)


def target_truth(mask: int) -> int:
    tt = 0
    for x in range(16):
        if ((mask & inv(x)).bit_count() & 1):
            tt |= 1 << x
    return tt


def install_targets():
    targets = [target_truth(mask) for mask in SUPPORT]
    # Independent functional sanity: the four coordinate targets really encode
    # the GF(16) inverse for all 16 inputs.
    coords = {mask: target_truth(mask) for mask in (1,2,4,8)}
    for x in range(16):
        got = sum((((coords[1 << i] >> x) & 1) << i) for i in range(4))
        assert got == inv(x), (x, got, inv(x))

    base.TARGETS = targets
    base.TARGET_RESIDUES = [base.STRIP[t] for t in targets]
    base.TARGET_BASIS = base.canonical_basis(base.TARGET_RESIDUES)
    assert len(base.TARGET_BASIS) == 4
    assert len(set(targets)) == 9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    install_targets()
    import search_core5_exact_mandatory as exact

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sys.argv = [
        "search_core5_exact_mandatory.py",
        "--shard", str(args.shard),
        "--shards", str(args.shards),
        "--out", str(out),
    ]
    exact.main()


if __name__ == "__main__":
    main()
