#!/usr/bin/env python3
"""High-precision independent guard for notes/017-global-loewner-source-and-chuk-symbol.md.

This is a numerical identity check, not an RH or positivity certificate.
It compares the pinned cutoff-free CvS entry formulas with divided differences
of the explicit N-independent source Phi_C, and checks the constant identity
that collapses the archimedean diagonal correction to log(pi).
"""

import argparse
import json
import math
from pathlib import Path

import mpmath as mp


def primes_up_to(n):
    out = []
    for x in range(2, n + 1):
        if all(x % p for p in out if p * p <= x):
            out.append(x)
    return out


def prime_powers_below(c):
    out = []
    for p in primes_up_to(int(math.ceil(c))):
        q = p
        while q < c:
            out.append((q, p))
            q *= p
    out.sort()
    return out


def geom_terms(L, z, tol):
    w = 2 * mp.pi * z / L
    gs = mp.mpc(0)
    gcc = mp.mpc(0)
    gx1 = mp.mpc(0)
    gx2 = mp.mpc(0)
    plain = mp.mpf(0)
    k = 0
    while True:
        ck = 2 * k + mp.mpf("0.5")
        e = mp.exp(-ck * L)
        den = ck * ck + w * w
        gs += e / den
        if z != 0:
            gcc += e * w * w / (ck * den)
        gx1 += e * ck / den
        gx2 += e * (ck * ck - w * w) / (den * den)
        plain += e / ck
        if abs(e) < tol and k > 4:
            break
        k += 1
        if k > 100000:
            raise RuntimeError("geometric series did not converge")
    return gs, gcc, gx1, gx2, plain


def kappa(L):
    eL = mp.exp(L)
    return mp.log(4 * mp.pi * (eL - 1) / (eL + 1)) + mp.euler


def Jfun(L):
    U = mp.exp(L / 2)
    return -2 * mp.log(U + 1) + mp.log(U * U + 1) + 2 * mp.atan(U) + mp.log(2) - mp.pi / 2


def S_source(C, z, tol):
    L = mp.log(C)
    a = mp.mpf("0.25")
    w = 2 * mp.pi * z / L
    gs, _, _, _, _ = geom_terms(L, z, tol)
    return (
        (mp.digamma(a + 1j * mp.pi * z / L) - mp.digamma(a - 1j * mp.pi * z / L)) / (4j)
        - w * gs
    )


def G02_source(C, z):
    L = mp.log(C)
    return 32 * L * mp.sinh(L / 4) ** 2 * z / (L * L + 16 * mp.pi**2 * z * z)


def prime_source(C, z):
    L = mp.log(C)
    total = mp.mpc(0)
    for q, p in prime_powers_below(C):
        weight = mp.log(p) / mp.sqrt(q)
        total += weight * mp.sin(2 * mp.pi * z * mp.log(q) / L) / mp.pi
    return total


def B_source(C, z):
    L = mp.log(C)
    a = mp.mpf("0.25")
    total = (
        mp.digamma(a + 1j * mp.pi * z / L)
        + mp.digamma(a - 1j * mp.pi * z / L)
    ) / 2 - mp.log(mp.pi)
    for q, p in prime_powers_below(C):
        weight = mp.log(p) / mp.sqrt(q)
        total -= 2 * weight * mp.cos(2 * mp.pi * z * mp.log(q) / L)
    return total


def Phi(C, z, tol):
    return (
        G02_source(C, z)
        + S_source(C, z, tol) / mp.pi
        + prime_source(C, z)
        + mp.sin(2 * mp.pi * z) * B_source(C, z) / (2 * mp.pi)
    )


def direct_entry(C, m, n, tol):
    L = mp.log(C)
    sp2 = 16 * mp.pi**2
    pref02 = 32 * L * mp.sinh(L / 4) ** 2
    num = L * L - sp2 * m * n
    den = (L * L + sp2 * m * m) * (L * L + sp2 * n * n)
    W02 = pref02 * num / den

    if m != n:
        Sm = S_source(C, mp.mpf(m), tol)
        Sn = S_source(C, mp.mpf(n), tol)
        WR = (Sm - Sn) / (mp.pi * (n - m))
    else:
        z = mp.mpf(n)
        w = 2 * mp.pi * z / L
        _, gcc, gx1, gx2, _ = geom_terms(L, z, tol)
        a = mp.mpf("0.25")
        psi = mp.digamma(a + 1j * mp.pi * z / L)
        psi1 = mp.polygamma(1, a + 1j * mp.pi * z / L)
        if n == 0:
            CC = mp.mpf(0)
        else:
            CC = -mp.re(psi - mp.digamma(a)) / 2 + mp.re(gcc)
        XC = mp.re(psi1) / 4 - L * mp.re(gx1) - mp.re(gx2)
        WR = kappa(L) + 2 * CC + Jfun(L) - (2 / L) * XC

    Wp = mp.mpf(0)
    for q, p in prime_powers_below(C):
        weight = mp.log(p) / mp.sqrt(q)
        y = mp.log(q)
        if m != n:
            Wp += weight * (
                mp.sin(2 * mp.pi * m * y / L) - mp.sin(2 * mp.pi * n * y / L)
            ) / (mp.pi * (n - m))
        else:
            Wp += weight * 2 * (1 - y / L) * mp.cos(2 * mp.pi * n * y / L)
    return W02 - WR - Wp


def source_entry(C, m, n, tol):
    if m != n:
        return (Phi(C, mp.mpf(m), tol) - Phi(C, mp.mpf(n), tol)) / (m - n)
    # mpmath's arbitrary-precision differentiation is intentionally independent
    # of the closed-form diagonal assembly used in direct_entry.
    return mp.diff(lambda zz: Phi(C, zz, tol), mp.mpf(n))


def constant_identity_error(C, tol):
    L = mp.log(C)
    _, _, _, _, plain = geom_terms(L, mp.mpf(0), tol)
    lhs = kappa(L) + Jfun(L) + 2 * plain + mp.digamma(mp.mpf("0.25"))
    return abs(lhs - mp.log(mp.pi))


def first_pole_residue_error(C, tol):
    L = mp.log(C)
    z0 = 1j * L / (4 * mp.pi)
    expected = L * mp.sinh(L / 4) ** 2 / (2 * mp.pi**2)
    # Approach transversely on the real direction; extrapolation is unnecessary
    # at this precision because eps is chosen far above the arithmetic floor.
    eps = mp.mpf(10) ** (-(mp.mp.dps // 2))
    observed = eps * Phi(C, z0 + eps, tol)
    return abs(observed - expected), observed, expected


def run_case(C, radius, tol):
    worst = mp.mpf(0)
    worst_pair = None
    for m in range(-radius, radius + 1):
        for n in range(-radius, radius + 1):
            a = direct_entry(C, m, n, tol)
            b = source_entry(C, m, n, tol)
            err = abs(a - b)
            if err > worst:
                worst = err
                worst_pair = [m, n]
    const_err = constant_identity_error(C, tol)
    res_err, observed, expected = first_pole_residue_error(C, tol)
    return {
        "C": C,
        "node_radius": radius,
        "max_matrix_entry_abs_error": mp.nstr(worst, 30),
        "worst_pair": worst_pair,
        "constant_identity_abs_error": mp.nstr(const_err, 30),
        "first_upper_pole_residue_abs_error": mp.nstr(res_err, 30),
        "first_upper_pole_residue_observed": mp.nstr(observed, 30),
        "first_upper_pole_residue_expected": mp.nstr(expected, 30),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dps", type=int, default=100)
    ap.add_argument("--radius", type=int, default=3)
    ap.add_argument("--output", default="")
    args = ap.parse_args()

    mp.mp.dps = args.dps
    tol = mp.mpf(10) ** (-(args.dps + 15))
    threshold = mp.mpf(10) ** (-(args.dps // 2))

    rows = [run_case(C, args.radius, tol) for C in (13, 16, 17, 100)]
    passed = True
    for row in rows:
        for key in (
            "max_matrix_entry_abs_error",
            "constant_identity_abs_error",
            "first_upper_pole_residue_abs_error",
        ):
            if mp.mpf(row[key]) >= threshold:
                passed = False

    out = {
        "status": "PASS" if passed else "FAIL",
        "meaning": "Numerical guard for the exact N-independent CvS confluent-Loewner source; not a positivity or RH certificate.",
        "mpmath_dps": args.dps,
        "pass_threshold": mp.nstr(threshold, 10),
        "rows": rows,
    }
    text = json.dumps(out, indent=2) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
