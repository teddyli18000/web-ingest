#!/usr/bin/env python3
"""Emit a compact numeric instance for the generic joint-decoupled C++ frontier.

The three output lines are, respectively, the 18 input-plane masks, the 18 output
plane masks, and the nine transported base-correction masks for P(x)=c*x^(2^k).
"""
from __future__ import annotations

import argparse
import pathlib

import search_semilinear_outer as outer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--k", type=int, choices=range(8), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    planes, outpairs, corrections = outer.transported_data(args.c, args.k)
    path = pathlib.Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(" ".join(str(v) for pair in planes for v in pair) + "\n")
        f.write(" ".join(str(v) for pair in outpairs for v in pair) + "\n")
        f.write(" ".join(str(v) for v in corrections) + "\n")


if __name__ == "__main__":
    main()
