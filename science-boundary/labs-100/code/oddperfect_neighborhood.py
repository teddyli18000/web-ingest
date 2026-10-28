#!/usr/bin/env python3
"""Enumerate small exact Hamming neighborhoods inside the odd-perfect manifold.

A move is counted iff, after flipping exactly the requested subset of bits, all
50 odd-lag autocorrelations still have magnitude one.  Energies are computed
from the resulting exact integer correlation vector; no floating point is used.

The default scans weights 1 and 2.  Weights 3 and 4 are useful structural
checks but have C(100,r) candidates and are correspondingly slower.
"""
from __future__ import annotations

import argparse
import itertools

N = 100


def parse(seq: str) -> list[int]:
    if len(seq) != N or any(ch not in "+-" for ch in seq):
        raise SystemExit("sequence must contain exactly 100 +/- characters")
    return [1 if ch == "+" else -1 for ch in seq]


def correlations(s: list[int]) -> list[int]:
    c = [0] * N
    for k in range(1, N):
        c[k] = sum(s[i] * s[i + k] for i in range(N - k))
    return c


def energy(c: list[int]) -> int:
    return sum(x * x for x in c[1:])


def changed_correlations(
    s: list[int], c: list[int], subset: tuple[int, ...]
) -> list[int]:
    """Exact C' after flipping subset.

    Summing each flipped endpoint's incident contribution double-counts an edge
    whose two endpoints are both flipped.  Such an edge is unchanged, so remove
    twice its original product before applying the usual -2 factor.
    """
    cp = c.copy()
    chosen = set(subset)
    for k in range(1, N):
        t = 0
        for p in subset:
            if p + k < N:
                t += s[p] * s[p + k]
            if p - k >= 0:
                t += s[p - k] * s[p]
        for p in subset:
            q = p + k
            if q in chosen:
                t -= 2 * s[p] * s[q]
        cp[k] = c[k] - 2 * t
    return cp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence")
    ap.add_argument("--max-weight", type=int, default=2, choices=range(1, 5))
    ap.add_argument("--show", type=int, default=12)
    args = ap.parse_args()

    s = parse(args.sequence)
    c = correlations(s)
    odd = sum(c[k] * c[k] for k in range(1, N, 2))
    if odd != 50:
        raise SystemExit(f"sequence is not odd-perfect: odd_energy={odd}")
    print(f"BASE energy={energy(c)} odd_energy={odd}")

    for r in range(1, args.max_weight + 1):
        count = 0
        best = None
        examples: list[tuple[tuple[int, ...], int]] = []
        for subset in itertools.combinations(range(N), r):
            cp = changed_correlations(s, c, subset)
            if any(abs(cp[k]) != 1 for k in range(1, N, 2)):
                continue
            e = energy(cp)
            count += 1
            if best is None or e < best:
                best = e
            if len(examples) < args.show:
                examples.append((subset, e))
        print(f"WEIGHT weight={r} legal={count} best={best}")
        for subset, e in examples:
            print("MOVE", ",".join(map(str, subset)), f"energy={e}")


if __name__ == "__main__":
    main()
