#!/usr/bin/env python3
"""Necessary autocorrelation arithmetic profiles for exact LABS-100 E=574.

This does not search sequences. It combines exact identities/congruences on
aperiodic autocorrelations to enumerate parity-half-sum classes that an exact
E=574 sequence could occupy. The output is necessary, not sufficient.
"""
from __future__ import annotations
from collections import defaultdict

N = 100
TARGET = 574
MAX_T = (TARGET - 50) // 8


def odd_reachable():
    """Reachable (t,R), where O=50+8t and R=ab/4, over odd-lag pairs."""
    dp = {(0, 0)}
    for k in range(1, 50, 2):
        opts = set()
        # x=C_k has length 100-k, y=C_{100-k} has length k; both are odd.
        for x in range(-(100 - k), 100 - k + 1, 2):
            for y in range(-k, k + 1, 2):
                if (x + y) % 4:
                    continue
                excess = x * x + y * y - 2
                if excess < 0 or excess % 8:
                    continue
                w = excess // 8
                if w <= MAX_T:
                    opts.add((w, (x + y) // 4))
        nd = set()
        for t0, r0 in dp:
            for w, q in opts:
                if t0 + w <= MAX_T:
                    nd.add((t0 + w, r0 + q))
        dp = nd
    return dp


def even_reachable():
    """Reachable (Q,S,T) for d_r=C_{2r}/2, r=1..49.

    Q=sum d_r^2, S=sum d_r, T=sum (-1)^r d_r. Opposite even lags imply
    d_r and d_{50-r} have the same parity. Exact E=574 has global product
    +1, so d_25=C_50/2 is odd.
    """
    dp = {(0, 0, 0)}
    for r in range(1, 25):
        opts = set()
        # Q<=131 globally, hence |d|<=11 regardless of raw lag bound.
        b1 = min(50 - r, 11)
        b2 = min(r, 11)
        sign = 1 if r % 2 == 0 else -1
        for d1 in range(-b1, b1 + 1):
            for d2 in range(-b2, b2 + 1):
                if (d1 - d2) % 2:
                    continue
                q = d1 * d1 + d2 * d2
                if q <= 131:
                    sm = d1 + d2
                    opts.add((q, sm, sign * sm))
        nd = set()
        for q0, s0, t0 in dp:
            for q, ss, tt in opts:
                if q0 + q <= 131:
                    nd.add((q0 + q, s0 + ss, t0 + tt))
        dp = nd

    out = set()
    # r=25 is unpaired. Product +1 forces C_50 == 2 (mod 4), so d_25 odd.
    for q0, s0, t0 in dp:
        for d in range(-11, 12, 2):
            if d % 2 == 0:
                continue
            q = q0 + d * d
            if q <= 131:
                out.add((q, s0 + d, t0 - d))  # (-1)^25=-1
    return out


def fourier_t_values():
    """Possible T from four residue-class sums q_j, each a sum of 25 signs."""
    vals = range(-25, 26, 2)
    out = defaultdict(set)
    for q0 in vals:
        for q2 in vals:
            a = q0 + q2
            u = q0 - q2
            for q1 in vals:
                for q3 in vals:
                    b = q1 + q3
                    v = q1 - q3
                    z = u * u + v * v
                    assert (z - 100) % 4 == 0
                    out[(a, b)].add((z - 100) // 4)
    return out


def canonical_classes():
    odd = odd_reachable()
    even = even_reachable()
    tvals = fourier_t_values()
    result = {}
    for t in range(MAX_T + 1):
        qbudget = 131 - 2 * t  # even energy = 4*qbudget
        if qbudget < 0:
            continue

        # Exact E=574 has global product +1, hence equal half-products.
        # O=50+8t mod16: even t => both half-products -1 => sums 0 mod4;
        # odd t => both +1 => sums 2 mod4.
        residue = 0 if t % 2 == 0 else 2
        classes = set()
        for a in range(-50, 51, 2):
            if a % 4 != residue:
                continue
            for b in range(-50, 51, 2):
                if b % 4 != residue:
                    continue
                if (t, (a * b) // 4) not in odd:
                    continue
                num = a * a + b * b - 100
                if num % 4:
                    continue
                ssum = num // 4
                if any((qbudget, ssum, tt) in even for tt in tvals[(a, b)]):
                    classes.add(tuple(sorted((abs(a), abs(b)), reverse=True)))
        result[t] = sorted(classes)
    return result


def main():
    result = canonical_classes()
    # Regression checks against independently derived low-layer structure.
    assert result[0] == [(0, 0), (4, 0), (8, 0), (12, 0), (16, 0), (20, 0)]
    assert result[1] == [(2, 2)]
    assert result[2] == [(0, 0), (4, 0), (8, 0), (12, 0), (16, 0), (20, 0)]

    print("t,odd_energy,even_square_budget,canonical_abs_half_sums")
    for t in range(MAX_T + 1):
        print(f"{t},{50 + 8*t},{131 - 2*t},{result[t]}")
    print("MISSING_T", [t for t in range(MAX_T + 1) if not result[t]])


if __name__ == "__main__":
    main()
