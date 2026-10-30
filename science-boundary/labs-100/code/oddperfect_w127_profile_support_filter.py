#!/usr/bin/env python3
"""Filter order-10 W127 NGP survivors by exact +25-pair support compatibility.

Input lines are pairs of base-6 encoded length-10 residue-sum profiles written by
oddperfect_h20_w127_ngp10.cpp.  For a length-50 binary sequence X, positions
j+10q (q=0..4) form one mod-10 column.  Pairing positions distance 25 connects
column r to column r+5 inside each residue r mod 5 (up to a cyclic permutation
of the five entries).

If two 5-sign columns have sums s,t and plus counts a=(5+s)/2,b=(5+t)/2,
the number e of equal +25 pairs is
    e = 5-a-b+2x,
where max(0,a+b-5) <= x <= min(a,b).
Thus each order-10 profile determines exactly the possible support sizes of the
ternary half-fold p_i=(X_i+X_{i+25})/2.

For W=127 in the normalized (20,0) class, the A/B half-fold supports must obey
ka+kc=26 with ka in {10,12,...,24}.  This program applies that condition to
every exact order-10 cross+NGP survivor and reports the surviving ka layers.
"""

import argparse
from collections import Counter


def decode(code: int):
    out = []
    for _ in range(10):
        out.append(-5 + 2 * (code % 6))
        code //= 6
    return out


def equal_pair_options(s: int, t: int):
    a = (5 + s) // 2
    b = (5 + t) // 2
    lo = max(0, a + b - 5)
    hi = min(a, b)
    return {5 - a - b + 2 * x for x in range(lo, hi + 1)}


def support_options(code: int):
    s = decode(code)
    poss = {0}
    for r in range(5):
        nxt = set()
        for total in poss:
            for e in equal_pair_options(s[r], s[r + 5]):
                nxt.add(total + e)
        poss = nxt
    return poss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("survivors", help="<prefix>_ngp10_survivors.txt")
    args = ap.parse_args()

    rows = []
    with open(args.survivors) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            a, b = map(int, line.split())
            rows.append((a, b))

    cache = {}
    by_ka = Counter()
    compatible_pairs = 0
    layer_sets = Counter()
    for ca, cb in rows:
        ma = cache.setdefault(("a", ca), support_options(ca))
        mb = cache.setdefault(("b", cb), support_options(cb))
        layers = tuple(k for k in range(10, 25, 2) if k in ma and (26 - k) in mb)
        if layers:
            compatible_pairs += 1
            layer_sets[layers] += 1
            for k in layers:
                by_ka[k] += 1

    print(f"input_ngp10_survivors={len(rows)}")
    print(f"support_compatible_profile_pairs={compatible_pairs}")
    for k in range(10, 25, 2):
        print(f"ka={k} compatible_profiles={by_ka[k]}")
    print("layer_sets:")
    for layers, n in sorted(layer_sets.items()):
        print(f"  {','.join(map(str, layers))}: {n}")

    # Internal consistency: sums of the original length-50 halves are fixed.
    # Therefore A supports must be even >=10, B supports even, and ka+kc=26.
    for ca, cb in rows[:100]:
        assert all(k % 2 == 0 and 10 <= k <= 25 for k in support_options(ca))
        assert all(k % 2 == 0 for k in support_options(cb))


if __name__ == "__main__":
    main()
