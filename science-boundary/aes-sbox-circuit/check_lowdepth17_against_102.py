#!/usr/bin/env python3
"""Exhaust the known 17-gate low-depth GF(16) inverter against 102 factors.

Boyar-Find-Peralta's low-depth work gives a 15-gate NAND/AND/XOR GF(16)
inverter (Fig. 6 of "Small Low-Depth Circuits for Cryptographic Applications").
Eliminating each NAND inside its downstream product gives the corresponding
AND/XOR realization with 7 AND + 10 XOR = 17 gates described in the paper.

We enumerate every GL(4,2) input basis. Among the 60 maps whose four inverter
outputs span the merged-102 inverse-output space, at most four of the nine
specific tail factors occur as existing gate wires. Thus this known 17-gate
inverter is not a direct drop-in replacement for q42..q59 with the tail fixed.
"""
import itertools


def var(i):
    v = 0
    for x in range(16):
        if (x >> i) & 1:
            v |= 1 << x
    return v


A, B, C, D = [var(i) for i in range(4)]
VARS = [A, B, C, D]


def lf(mask):
    v = 0
    for i, t in enumerate(VARS):
        if (mask >> i) & 1:
            v ^= t
    return v


def rank_masks(ms):
    piv = []
    for x in ms:
        y = x
        for p in piv:
            y = min(y, y ^ p)
        if y:
            piv.append(y)
            piv.sort(reverse=True)
    return len(piv)


def span(bs):
    out = set()
    for m in range(1 << len(bs)):
        v = 0
        for i, b in enumerate(bs):
            if (m >> i) & 1:
                v ^= b
        out.add(v)
    return out


def targets():
    a, b, c, d = A, B, C, D
    q42 = a & b
    q43 = q42 ^ c
    q44 = q43 & d
    q45 = b ^ q44
    q46 = q42 & c
    q47 = d ^ q46
    q48 = a & q47
    q49 = q43 ^ q48
    q50 = q48 ^ b
    q51 = q49 & q50
    q52 = q51 ^ a
    q53 = q52 ^ q49
    q54 = q45 & q53
    q55 = q54 ^ q47
    q56 = q55 ^ q49
    q57 = q53 ^ q45
    q58 = q56 ^ q57
    q59 = q55 ^ q45
    return [q45, q59, q52, q57, q53, q49, q58, q55, q56]


def lowdepth17(inp):
    x0, x1, x2, x3 = inp
    wires = []

    def emit(name, v):
        wires.append((name, v))
        return v

    t1 = emit("t1", x2 ^ x3)
    t2 = emit("t2", x2 & x0)
    t3 = emit("t3", x1 ^ t2)
    t4 = emit("t4", x0 ^ x1)
    t5 = emit("t5", x3 ^ t2)
    t6 = emit("t6", t5 & t4)
    t7 = emit("t7", t3 & t1)

    # Fig. 6 has n8 = NAND(x0,x3), t9 = t4*n8.  Over AND/XOR:
    # t9 = t4 XOR (t4 AND (x0 AND x3)).
    n8_product = emit("n8_product", x0 & x3)
    p9 = emit("p9", t4 & n8_product)
    t9 = emit("t9", t4 ^ p9)

    # Likewise n10 = NAND(x2,x1), t11 = t1*n10.
    n10_product = emit("n10_product", x2 & x1)
    p11 = emit("p11", t1 & n10_product)
    t11 = emit("t11", t1 ^ p11)

    y0 = emit("y0", t2 ^ t11)
    y1 = emit("y1", x3 ^ t7)
    y2 = emit("y2", t2 ^ t9)
    y3 = emit("y3", x1 ^ t6)
    assert len(wires) == 17
    return wires, [y0, y1, y2, y3]


def main():
    ts = targets()
    target_set = set(ts)
    target_space = span(ts[:4])
    assert len(target_space) == 16

    compatible = []
    total = 0
    for basis in itertools.permutations(range(1, 16), 4):
        if rank_masks(basis) != 4:
            continue
        total += 1
        wires, outs = lowdepth17([lf(m) for m in basis])
        if span(outs) != target_space:
            continue
        coverage = sum(v in target_set for _, v in wires)
        compatible.append((coverage, basis, [n for n, v in wires if v in target_set]))

    compatible.sort(reverse=True)
    print("GL(4,2) maps =", total)
    print("compatible inverse-output maps =", len(compatible))
    print("max direct 102-factor coverage =", compatible[0][0])
    print("examples =", compatible[:10])
    assert total == 20160
    assert len(compatible) == 60
    assert compatible[0][0] == 4


if __name__ == "__main__":
    main()
