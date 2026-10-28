#!/usr/bin/env python3
"""Exact 16-state analysis of the merged 102-gate AES inversion-core interface.

The merged 102 shot retains the same abstract 18-gate six-AND core as the 103
record.  This script records the nine factors consumed by the final AND layer,
their rank modulo affine functions, and exact XOR relations among them.
"""

MASK = (1 << 16) - 1


def var(i):
    v = 0
    for x in range(16):
        if (x >> i) & 1:
            v |= 1 << x
    return v


def rank(vs):
    piv = {}
    for x in vs:
        y = x
        while y:
            p = y.bit_length() - 1
            if p in piv:
                y ^= piv[p]
            else:
                piv[p] = y
                break
    return len(piv)


def core_targets():
    a, b, c, d = [var(i) for i in range(4)]
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
    names = ["q45", "q59", "q52", "q57", "q53", "q49", "q58", "q55", "q56"]
    vals = [q45, q59, q52, q57, q53, q49, q58, q55, q56]
    return (a, b, c, d), names, vals


def main():
    ins, names, vals = core_targets()
    affine = [MASK, *ins]
    quotient_rank = rank(affine + vals) - rank(affine)
    print("target quotient rank modulo affine =", quotient_rank)
    assert quotient_rank == 4

    basis_names = names[:4]
    basis_vals = vals[:4]
    assert rank(affine + basis_vals) - rank(affine) == 4

    # In fact no affine correction is needed: all nine factors lie in the
    # ordinary linear span of q45,q59,q52,q57.
    for name, target in zip(names, vals):
        found = None
        for m in range(16):
            v = 0
            terms = []
            for i, b in enumerate(basis_vals):
                if (m >> i) & 1:
                    v ^= b
                    terms.append(basis_names[i])
            if v == target:
                found = terms
                break
        assert found is not None
        print(name, "=", " XOR ".join(found) if found else "0")

    expected = {
        "q45": ["q45"],
        "q59": ["q59"],
        "q52": ["q52"],
        "q57": ["q57"],
        "q53": ["q45", "q57"],
        "q49": ["q45", "q52", "q57"],
        "q58": ["q59", "q52"],
        "q55": ["q45", "q59"],
        "q56": ["q59", "q52", "q57"],
    }
    for name, target in zip(names, vals):
        v = 0
        for term in expected[name]:
            v ^= vals[names.index(term)]
        assert v == target


if __name__ == "__main__":
    main()
