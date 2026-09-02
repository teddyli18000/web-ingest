#!/usr/bin/env python3
"""High-precision guard for notes/017-global-loewner-source-and-chuk-symbol.md.

Numerical identity check only; not a positivity or RH certificate.
"""

import argparse, json, math
from pathlib import Path
import mpmath as mp


def primes_up_to(n):
    ps = []
    for x in range(2, n + 1):
        if all(x % p for p in ps if p * p <= x):
            ps.append(x)
    return ps


def prime_powers_below(c):
    out = []
    for p in primes_up_to(int(math.ceil(c))):
        q = p
        while q < c:
            out.append((q, p))
            q *= p
    return sorted(out)


def geom(L, z, tol):
    w = 2 * mp.pi * z / L
    gs = gcc = gx1 = gx2 = mp.mpc(0)
    plain = mp.mpf(0)
    for k in range(100000):
        ck = 2 * k + mp.mpf("0.5")
        e = mp.exp(-ck * L)
        den = ck * ck + w * w
        gs += e / den
        if z != 0:
            gcc += e * w * w / (ck * den)
        gx1 += e * ck / den
        gx2 += e * (ck * ck - w * w) / den**2
        plain += e / ck
        if abs(e) < tol and k > 4:
            return gs, gcc, gx1, gx2, plain
    raise RuntimeError("geometric series did not converge")


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
    gs, *_ = geom(L, z, tol)
    return ((mp.digamma(a + 1j * mp.pi * z / L) -
             mp.digamma(a - 1j * mp.pi * z / L)) / (4j) - w * gs)


def G02_source(C, z):
    L = mp.log(C)
    return 32 * L * mp.sinh(L / 4)**2 * z / (L**2 + 16 * mp.pi**2 * z**2)


def prime_source(C, z):
    L = mp.log(C)
    return mp.fsum(
        mp.log(p) / mp.sqrt(q) *
        mp.sin(2 * mp.pi * z * mp.log(q) / L) / mp.pi
        for q, p in prime_powers_below(C)
    )


def B_source(C, z):
    L = mp.log(C)
    a = mp.mpf("0.25")
    base = ((mp.digamma(a + 1j * mp.pi * z / L) +
             mp.digamma(a - 1j * mp.pi * z / L)) / 2 - mp.log(mp.pi))
    primes = mp.fsum(
        2 * mp.log(p) / mp.sqrt(q) *
        mp.cos(2 * mp.pi * z * mp.log(q) / L)
        for q, p in prime_powers_below(C)
    )
    return base - primes


def Phi(C, z, tol):
    return (G02_source(C, z) + S_source(C, z, tol) / mp.pi +
            prime_source(C, z) +
            mp.sin(2 * mp.pi * z) * B_source(C, z) / (2 * mp.pi))


def direct_entry(C, m, n, tol):
    L = mp.log(C)
    pref = 32 * L * mp.sinh(L / 4)**2
    sp2 = 16 * mp.pi**2
    W02 = pref * (L**2 - sp2 * m * n) / (
        (L**2 + sp2 * m * m) * (L**2 + sp2 * n * n))

    if m != n:
        WR = (S_source(C, mp.mpf(m), tol) -
              S_source(C, mp.mpf(n), tol)) / (mp.pi * (n - m))
    else:
        z = mp.mpf(n)
        _, gcc, gx1, gx2, _ = geom(L, z, tol)
        a = mp.mpf("0.25")
        psi = mp.digamma(a + 1j * mp.pi * z / L)
        psi1 = mp.polygamma(1, a + 1j * mp.pi * z / L)
        CC = mp.mpf(0) if n == 0 else -mp.re(psi - mp.digamma(a)) / 2 + mp.re(gcc)
        XC = mp.re(psi1) / 4 - L * mp.re(gx1) - mp.re(gx2)
        WR = kappa(L) + 2 * CC + Jfun(L) - (2 / L) * XC

    Wp = mp.mpf(0)
    for q, p in prime_powers_below(C):
        wt, y = mp.log(p) / mp.sqrt(q), mp.log(q)
        if m != n:
            Wp += wt * (
                mp.sin(2 * mp.pi * m * y / L) -
                mp.sin(2 * mp.pi * n * y / L)
            ) / (mp.pi * (n - m))
        else:
            Wp += wt * 2 * (1 - y / L) * mp.cos(2 * mp.pi * n * y / L)
    return W02 - WR - Wp


def source_entry(C, m, n, tol):
    if m != n:
        return (Phi(C, mp.mpf(m), tol) -
                Phi(C, mp.mpf(n), tol)) / (m - n)
    return mp.diff(lambda zz: Phi(C, zz, tol), mp.mpf(n))


def constant_error(C, tol):
    L = mp.log(C)
    *_, plain = geom(L, mp.mpf(0), tol)
    lhs = kappa(L) + Jfun(L) + 2 * plain + mp.digamma(mp.mpf("0.25"))
    return abs(lhs - mp.log(mp.pi))


def pole_residue_error(C, tol):
    """Symmetric transverse limit cancels the O(eps) regular-part error."""
    L = mp.log(C)
    z0 = 1j * L / (4 * mp.pi)
    expected = L * mp.sinh(L / 4)**2 / (2 * mp.pi**2)
    eps = mp.mpf(10) ** (-(mp.mp.dps // 3))
    plus = eps * Phi(C, z0 + eps, tol)
    minus = (-eps) * Phi(C, z0 - eps, tol)
    observed = (plus + minus) / 2
    return abs(observed - expected), observed, expected


def run_case(C, radius, tol):
    worst, pair = mp.mpf(0), None
    for m in range(-radius, radius + 1):
        for n in range(-radius, radius + 1):
            err = abs(direct_entry(C, m, n, tol) - source_entry(C, m, n, tol))
            if err > worst:
                worst, pair = err, [m, n]
    ce = constant_error(C, tol)
    re, ro, rx = pole_residue_error(C, tol)
    return {
        "C": C,
        "node_radius": radius,
        "max_matrix_entry_abs_error": mp.nstr(worst, 30),
        "worst_pair": pair,
        "constant_identity_abs_error": mp.nstr(ce, 30),
        "first_upper_pole_residue_abs_error": mp.nstr(re, 30),
        "first_upper_pole_residue_observed": mp.nstr(ro, 30),
        "first_upper_pole_residue_expected": mp.nstr(rx, 30),
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
    keys = ("max_matrix_entry_abs_error", "constant_identity_abs_error",
            "first_upper_pole_residue_abs_error")
    passed = all(mp.mpf(row[k]) < threshold for row in rows for k in keys)
    out = {
        "status": "PASS" if passed else "FAIL",
        "meaning": ("Numerical guard for the exact N-independent CvS "
                    "confluent-Loewner source; not a positivity or RH certificate."),
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
