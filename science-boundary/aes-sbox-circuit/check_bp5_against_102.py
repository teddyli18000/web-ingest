#!/usr/bin/env python3
"""Exhaust GL(4,2) mappings of the classic 5-AND/11-XOR GF(16) inverter.

Question: can the fixed 16-gate Boyar-Peralta inverter, under any invertible
input basis, already expose enough of the nine factors used by the merged 102
AES tail that one appended XOR/XNOR gate would produce a 17-gate replacement?

Result expected from exhaustive enumeration: no.  The maximum number of target
factors already present among the four inputs and sixteen gate outputs is four.
"""
from itertools import permutations

MASK = (1 << 16) - 1


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


def bp_wires(masks):
    x1, x2, x3, x4 = [lf(m) for m in masks]
    ws = [x1, x2, x3, x4]
    t1 = x1 ^ x2; ws.append(t1)
    t2 = x1 & x3; ws.append(t2)
    t3 = x4 ^ t2; ws.append(t3)
    t4 = t1 & t3; ws.append(t4)
    y4 = x2 ^ t4; ws.append(y4)
    t5 = x3 ^ x4; ws.append(t5)
    t6 = x2 ^ t2; ws.append(t6)
    t7 = t6 & t5; ws.append(t7)
    y2 = x4 ^ t7; ws.append(y2)
    t8 = x3 ^ y2; ws.append(t8)
    t9 = t3 ^ y2; ws.append(t9)
    t10 = x4 & t9; ws.append(t10)
    y1 = t10 ^ t8; ws.append(y1)
    t11 = t3 ^ t10; ws.append(t11)
    t12 = y4 & t11; ws.append(t12)
    y3 = t12 ^ t1; ws.append(y3)
    assert len(ws) == 20  # 4 inputs + 16-gate network
    return ws


def main():
    ts = targets()
    best = []
    count = 0
    max_direct = -1
    for basis in permutations(range(1, 16), 4):
        if rank_masks(basis) != 4:
            continue
        count += 1
        ws = bp_wires(basis)
        direct = sum(t in set(ws) for t in ts)
        if direct > max_direct:
            max_direct = direct
            best = [basis]
        elif direct == max_direct:
            best.append(basis)
    assert count == 20160
    print("GL(4,2) maps =", count)
    print("max direct 102-factor coverage =", max_direct)
    print("number of maximizing bases =", len(best))
    print("examples =", best[:20])
    assert max_direct == 4
    print("Therefore fixed BP-16 plus one appended XOR/XNOR cannot expose all nine targets.")


if __name__ == "__main__":
    main()
