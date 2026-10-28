#!/usr/bin/env python3
"""Solver-free 5-AND lower bound for the merged-102 zero-state ODC core.

The fixed 102 tail allows all nine core factors to be arbitrary on core input
0000, but requires them exactly on the other 15 inputs.  Take the independent
factor basis B = (q45,q59,q52,q57).  Each basis output may independently choose
its value at 0000, giving 16 possible complete 4-output functions.

For every such completion:
  1. the four nonlinear coordinate classes modulo affine functions have rank 4;
  2. every nonzero scalar combination has algebraic degree >= 3, hence cannot
     be computed modulo affine functions with <=1 AND (one AND of affine forms
     plus affine correction has degree <=2).

Elementary packing argument: in a minimal r-AND XAG, the r AND-output classes
modulo affine functions can be chosen linearly independent.  The 4-dimensional
target nonlinear span V lies in their span.  Since every nonzero v in V needs
at least 2 ANDs, V cannot intersect the span of the first AND-output class.
Thus a 4-dimensional V and that independent 1-dimensional class require
r >= 4 + 1 = 5.

This is the j=0 / mu=2 packing bound, but the proof above is included so the
claim does not depend on an external solver or implementation.
"""


def var(i):
    v = 0
    for x in range(16):
        if (x >> i) & 1:
            v |= 1 << x
    return v


def mobius_anf(tt):
    c = [(tt >> x) & 1 for x in range(16)]
    for i in range(4):
        for m in range(16):
            if (m >> i) & 1:
                c[m] ^= c[m ^ (1 << i)]
    return c


def degree(tt):
    c = mobius_anf(tt)
    return max((m.bit_count() for m, bit in enumerate(c) if bit), default=-1)


def gf2_rank(vs):
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


def quotient_rank_mod_affine(vs):
    # Quotient dimension = rank(affine generators + targets) - rank(affine).
    one = (1 << 16) - 1
    affine = [one] + [var(i) for i in range(4)]
    return gf2_rank(affine + list(vs)) - gf2_rank(affine)


def target_basis():
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
    q57 = q53 ^ q45
    q59 = q55 ^ q45
    return [q45, q59, q52, q57]


def main():
    base = target_basis()
    assert all((t & 1) == 0 for t in base)  # live core maps 0000 -> 0000

    completion_reports = []
    for zero_bits in range(16):
        completed = [t ^ ((zero_bits >> i) & 1) for i, t in enumerate(base)]
        qr = quotient_rank_mod_affine(completed)
        assert qr == 4, (zero_bits, qr)

        scalar_degrees = []
        for mask in range(1, 16):
            f = 0
            for i, t in enumerate(completed):
                if (mask >> i) & 1:
                    f ^= t
            deg = degree(f)
            scalar_degrees.append(deg)
            assert deg >= 3, (zero_bits, mask, deg)

        completion_reports.append(
            {
                "zero_bits": f"{zero_bits:04b}",
                "quotient_rank_mod_affine": qr,
                "min_nonzero_scalar_degree": min(scalar_degrees),
                "max_nonzero_scalar_degree": max(scalar_degrees),
            }
        )

    print("checked completions:", len(completion_reports))
    print("all quotient ranks:", sorted(set(r["quotient_rank_mod_affine"] for r in completion_reports)))
    print("all minimum scalar degrees:", sorted(set(r["min_nonzero_scalar_degree"] for r in completion_reports)))
    print("all maximum scalar degrees:", sorted(set(r["max_nonzero_scalar_degree"] for r in completion_reports)))
    print("packing lower bound: AND count >= 4 + 2 - 1 = 5")


if __name__ == "__main__":
    main()
