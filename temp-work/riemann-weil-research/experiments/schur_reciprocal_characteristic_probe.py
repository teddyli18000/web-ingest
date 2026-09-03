#!/usr/bin/env python3
"""Exploratory zeros of the Schur rational numerator.

For r=S/R from the Schur normal, poles of r are zeros of the CvS ground-state
Fourier denominator R and are the already-known finite zeta-zero approximants.
This probe computes the nonzero zeros of S, equivalently the poles of z^2/r,
and compares them after physical rescaling with real critical points Xi'(t)=0.

Matrix construction is Arb cutoff-free. Polynomial roots and Xi' comparisons
are high-precision midpoint diagnostics, not interval root certificates.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import mpmath as mp
from flint import arb, ctx


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def xi(s):
    return mp.mpf('0.5') * s * (s - 1) * mp.power(mp.pi, -s / 2) * mp.gamma(s / 2) * mp.zeta(s)


def Xi(t):
    return mp.re(xi(mp.mpf('0.5') + 1j * t))


def Xi_prime(t):
    return mp.diff(Xi, t)


def critical_points(count: int):
    # Rolle critical point between consecutive known critical-line zeros.
    gammas = [mp.im(mp.zetazero(k)) for k in range(1, count + 2)]
    out = []
    for j in range(count):
        lo, hi = gammas[j], gammas[j + 1]
        # Search robustly from the midpoint; Xi' has at least one real root here.
        mid = (lo + hi) / 2
        try:
            z = mp.findroot(Xi_prime, (lo + (hi-lo)*mp.mpf('0.2'), hi - (hi-lo)*mp.mpf('0.2')), solver='anderson', tol=mp.eps*1024)
        except Exception:
            z = mp.findroot(Xi_prime, mid, tol=mp.eps*1024)
        if not (lo < z < hi):
            raise RuntimeError(f'critical point escaped interval {j+1}: {z}')
        out.append(z)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base-script', type=Path, required=True)
    ap.add_argument('--upstream-script', type=Path, required=True)
    ap.add_argument('--upstream-commit', required=True)
    ap.add_argument('--c', type=int, required=True)
    ap.add_argument('--N', type=int, required=True)
    ap.add_argument('--prec', type=int, required=True)
    ap.add_argument('--dps', type=int, required=True)
    ap.add_argument('--compare-count', type=int, default=5)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()

    ctx.prec = args.prec
    mp.mp.dps = args.dps
    digits = args.dps + 30

    base = load(args.base_script, 'pole_base')
    upstream = load(args.upstream_script, 'upstream')

    A, _ = upstream.build_arb_tau(args.c, args.N, args.prec)
    E = base.project_even(A, args.N)
    Lfac, piv = base.signed_ldlt(E)
    v = base.schur_normal_even(Lfac, args.N)
    root2 = mp.sqrt(2)
    u = {0: base.amid(v[0], digits)}
    for k in range(1, args.N + 1):
        u[k] = u[-k] = base.amid(v[k], digits) / root2

    center = args.N
    psi = {0: mp.mpf('0')}
    for m in range(-args.N, args.N + 1):
        if m != 0:
            psi[m] = mp.mpf(m) * base.amid(A[m + center, center], digits)

    # S=P_S/D_N is even while D_N is odd, so P_S(z)=z*h(z^2).
    # At positive node k: P_S(k)=u_k psi(k) D_N'(k).
    xs = [mp.mpf(k*k) for k in range(1, args.N + 1)]
    ys = [u[k] * psi[k] * base.Dprime(args.N, k) / mp.mpf(k) for k in range(1, args.N + 1)]
    h_asc = base.interpolate_ascending(xs, ys)
    coeff_desc = list(reversed(h_asc))
    lead = coeff_desc[0]
    coeff_desc = [x / lead for x in coeff_desc]
    roots_x = mp.polyroots(coeff_desc, maxsteps=5000, error=False, extraprec=150)
    roots_x = sorted(roots_x, key=lambda z: (float(mp.re(z)), float(mp.im(z))))

    tol_im = mp.power(10, -(args.dps // 3))
    positive = []
    for x in roots_x:
        if abs(mp.im(x)) < tol_im and mp.re(x) > 0:
            positive.append(mp.sqrt(mp.re(x)))

    a = mp.log(args.c) / (2 * mp.pi)
    physical = [z / a for z in positive]
    ncmp = min(args.compare_count, len(physical))
    crit = critical_points(ncmp)

    rows = []
    for j in range(ncmp):
        rows.append({
            'index': j + 1,
            'dimensionless_r_zero': mp.nstr(positive[j], 80),
            'physical_r_zero': mp.nstr(physical[j], 80),
            'xi_prime_real_critical_point': mp.nstr(crit[j], 80),
            'absolute_error': mp.nstr(abs(physical[j] - crit[j]), 50),
        })

    out = {
        'status': 'exploratory_reciprocal_characteristic_pole_probe',
        'warning': 'Cutoff-free matrix/pivots use Arb. Polynomial roots and Xi-prime matching are high-precision midpoint diagnostics, not interval root certificates.',
        'interpretation': 'Nonzero zeros of r=S/R are poles of z^2/r. If rescaled r converges to i xi-prime/xi, these should approach real Xi-prime critical points.',
        'upstream_commit': args.upstream_commit,
        'c': args.c,
        'N': args.N,
        'prec_bits': args.prec,
        'mpmath_dps': args.dps,
        'schur_pivot_mid': piv[args.N].mid().str(80, radius=False),
        'all_nonzero_r_zeros_positive_real': len(positive) == args.N - 1,
        'positive_nonzero_r_zero_count': len(positive),
        'expected_count': args.N - 1,
        'rows': rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
