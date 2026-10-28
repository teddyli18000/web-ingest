#!/usr/bin/env python3
"""Exhaust Tay et al.'s 15-gate GF(2^4) inverter against merged-102 factors.

Tay et al. (TENCON 2018) give the GF(2^4) inversion region M23..M37:
5 AND + 10 XOR = 15 two-input gates.  We reconstruct it exactly from the
published equations and enumerate every GL(4,2) input basis.

For each basis whose four inverter outputs span the same inverse-output space
as the merged-102 core, count how many of the nine fixed-tail factors appear
as existing inverter wires.  We do this both exactly and with the complete
fixed-tail care mask 0xfffe (state 0000 ignored).

Expected result:
  compatible maps = 60
  max exact target coverage = 4/9
  max care-projected target coverage = 4/9
Thus the fixed published Tay15 network plus only two appended gates cannot be
a direct 17-gate replacement for the fixed 102 tail: at most six distinct
required factors could then be exposed.
"""
from itertools import permutations

CARE = 0xFFFE


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


def merged102_targets():
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


def tay15(inp):
    """Published M23..M37 network. Inputs are (M19,M20,M21,M22)."""
    m19, m20, m21, m22 = inp
    wires = []

    def emit(name, v, op):
        wires.append((name, v, op))
        return v

    m23 = emit("M23", m20 & m22, "AND")
    m24 = emit("M24", m19 ^ m20, "XOR")
    m25 = emit("M25", m23 ^ m24, "XOR")
    m26 = emit("M26", m21 & m25, "AND")
    m27 = emit("M27", m21 ^ m22, "XOR")
    m28 = emit("M28", m26 ^ m27, "XOR")
    m29 = emit("M29", m26 ^ m23, "XOR")
    m30 = emit("M30", m29 & m27, "AND")
    m31 = emit("M31", m22 ^ m30, "XOR")
    m32 = emit("M32", m27 ^ m23, "XOR")
    m33 = emit("M33", m19 & m32, "AND")
    m34 = emit("M34", m24 ^ m33, "XOR")
    m35 = emit("M35", m23 ^ m34, "XOR")
    m36 = emit("M36", m35 & m24, "AND")
    m37 = emit("M37", m19 ^ m36, "XOR")
    assert sum(op == "AND" for _, _, op in wires) == 5
    assert sum(op == "XOR" for _, _, op in wires) == 10
    outputs = [m28, m31, m34, m37]
    return wires, outputs


def main():
    targets = merged102_targets()
    target_space = span(targets[:4])
    target_space_care = span([t & CARE for t in targets[:4]])

    compatible = 0
    best_exact = -1
    best_care = -1
    best_examples = []

    total = 0
    for basis in permutations(range(1, 16), 4):
        if rank_masks(basis) != 4:
            continue
        total += 1
        wires, outputs = tay15([lf(m) for m in basis])
        if span(outputs) != target_space:
            continue
        compatible += 1
        wvals = {v for _, v, _ in wires}
        exact = sum(t in wvals for t in targets)

        # The same compatible maps remain compatible under the complete fixed-
        # tail care projection.  Count factor wires modulo state 0000.
        assert span([o & CARE for o in outputs]) == target_space_care
        wcare = {v & CARE for _, v, _ in wires}
        care = sum((t & CARE) in wcare for t in targets)

        score = (exact, care)
        if exact > best_exact or care > best_care:
            best_exact = max(best_exact, exact)
            best_care = max(best_care, care)
        if exact == 4 or care == 4:
            best_examples.append((basis, exact, care, [name for name, v, _ in wires if v in targets]))

    print("GL(4,2) maps =", total)
    print("compatible inverse-output maps =", compatible)
    print("max exact target coverage =", best_exact)
    print("max care-projected target coverage =", best_care)
    print("examples =", best_examples[:20])

    assert total == 20160
    assert compatible == 60
    assert best_exact == 4
    assert best_care == 4


if __name__ == "__main__":
    main()
