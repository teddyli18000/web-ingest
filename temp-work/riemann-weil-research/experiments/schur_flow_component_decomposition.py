#!/usr/bin/env python3
"""Decompose the threshold-free Schur log-flow into CvS matrix components.

For the even cutoff-free CvS matrix E_N(u), u=log c, write the pinned matrix
formula as

    E = E_pole + E_arch + E_prime
      = W02 - WR - Wp.

At a fixed threshold-free u0, with last Schur normal w=(-B^{-1}b,1),

    d/du log s_N = w^T E'(u0) w / s_N.

This script estimates the three component derivatives by centered differences
while keeping the active prime-power set fixed, and checks that their sum agrees
with both the total matrix directional derivative and the direct finite
difference of the Schur pivot.

The base pivot is a rigorous Arb ball. Derivatives, the Schur normal, and the
component decomposition use high-precision midpoints and are exploratory.
"""
from __future__ import annotations

import argparse, importlib.util, json
from pathlib import Path
import mpmath as mp
from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location('upstream', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prime_powers_fixed(c0: int):
    primes = []
    for x in range(2, c0 + 1):
        isprime = True
        for p in primes:
            if p * p > x:
                break
            if x % p == 0:
                isprime = False
                break
        if isprime:
            primes.append(x)
    out = []
    for p in primes:
        q = p
        while q <= c0:
            out.append((q, p))
            q *= p
    return out


def build_components(mod, c_str, N, prec, pdata):
    ctx.prec = prec
    S, CC, XC, L = mod.arb_closed_forms(N, c_str, prec)
    PI = arb.pi()
    sp2 = 16 * PI * PI
    l2 = L * L
    pref02 = 32 * L * (L / 4).sinh() ** 2
    kappa = mod.arb_kappa(L)
    J = mod.arb_J(L)
    weights = [arb(p).log() * (arb(q) ** arb('-0.5')) for q, p in pdata]
    positions = [arb(q).log() for q, p in pdata]

    def Ss(n):
        return S[n] if n >= 0 else -S[-n]

    D = 2 * N + 1
    pole = arb_mat(D, D)
    arch = arb_mat(D, D)
    prime = arb_mat(D, D)
    total = arb_mat(D, D)
    for i in range(D):
        n = i - N
        for j in range(i, D):
            m = j - N
            W02 = pref02 * (l2 - sp2 * m * n) / ((l2 + sp2 * m * m) * (l2 + sp2 * n * n))
            if n == m:
                WR = kappa + 2 * CC[abs(n)] + J - (2 / L) * XC[abs(n)]
            else:
                WR = (Ss(m) - Ss(n)) / (PI * (n - m))
            Wp = arb(0)
            for idx in range(len(weights)):
                y = positions[idx]
                if n == m:
                    qv = 2 * (1 - y / L) * (2 * PI * n * y / L).cos()
                else:
                    qv = ((2 * PI * m * y / L).sin() - (2 * PI * n * y / L).sin()) / (PI * (n - m))
                Wp += weights[idx] * qv
            vals = (W02, -WR, -Wp)
            for M, v in zip((pole, arch, prime), vals):
                M[i, j] = v
                M[j, i] = v
            v = vals[0] + vals[1] + vals[2]
            total[i, j] = v
            total[j, i] = v
    return {'pole_W02': pole, 'arch_minus_WR': arch, 'prime_minus_Wp': prime, 'total': total}


def project_even(A, N):
    root2 = arb(2).sqrt()
    c = N
    E = arb_mat(N + 1, N + 1)
    E[0, 0] = A[c, c]
    for k in range(1, N + 1):
        v = (A[c, c + k] + A[c, c - k]) / root2
        E[0, k] = v
        E[k, 0] = v
    for k in range(1, N + 1):
        for j in range(k, N + 1):
            v = (A[c + k, c + j] + A[c + k, c - j] + A[c - k, c + j] + A[c - k, c - j]) / 2
            E[k, j] = v
            E[j, k] = v
    return E


def last_positive_pivot(E):
    n = E.nrows()
    L = [[arb(0) for _ in range(n)] for _ in range(n)]
    d = []
    for i in range(n):
        L[i][i] = arb(1)
        s = E[i, i]
        for k in range(i):
            s -= L[i][k] * L[i][k] * d[k]
        if not (s > 0):
            raise RuntimeError(f'undetermined/nonpositive pivot {i}: {s}')
        d.append(s)
        for j in range(i + 1, n):
            t = E[j, i]
            for k in range(i):
                t -= L[j][k] * L[i][k] * d[k]
            L[j][i] = t / d[i]
    return d[-1]


def mid(x, digits):
    return mp.mpf(x.mid().str(digits, radius=False))


def to_mp(E, digits):
    return mp.matrix([[mid(E[i, j], digits) for j in range(E.ncols())] for i in range(E.nrows())])


def qform(w, H):
    return (w.T * H * w)[0]


def ball(x, digits=60):
    return {
        'lower': x.lower().str(digits, radius=False),
        'mid': x.mid().str(digits, radius=False),
        'upper': x.upper().str(digits, radius=False),
        'rad': x.rad().str(20, radius=False),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upstream-script', type=Path, required=True)
    ap.add_argument('--upstream-commit', required=True)
    ap.add_argument('--c0', type=int, default=100)
    ap.add_argument('--N', type=int, required=True)
    ap.add_argument('--prec', type=int, required=True)
    ap.add_argument('--dps', type=int, required=True)
    ap.add_argument('--hs', default='1e-6,1e-8')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()

    mp.mp.dps = args.dps
    digits = args.dps + 30
    mod = load_module(args.upstream_script)
    pdata = prime_powers_fixed(args.c0)
    u0 = mp.log(args.c0)

    def comps_at(u):
        c = mp.e ** u
        raw = build_components(mod, mp.nstr(c, digits), args.N, args.prec, pdata)
        return {k: project_even(v, args.N) for k, v in raw.items()}

    base = comps_at(u0)
    E0 = base['total']
    s0 = last_positive_pivot(E0)
    s0m = mid(s0, digits)
    M0 = to_mp(E0, digits)
    if args.N == 0:
        w = mp.matrix([1])
    else:
        B = M0[:args.N, :args.N]
        b = M0[:args.N, args.N]
        x = mp.lu_solve(B, b)
        w = mp.matrix(args.N + 1, 1)
        for i in range(args.N):
            w[i] = -x[i]
        w[args.N] = 1

    rows = []
    for hs in [x.strip() for x in args.hs.split(',') if x.strip()]:
        h = mp.mpf(hs)
        plus = comps_at(u0 + h)
        minus = comps_at(u0 - h)
        contributions = {}
        for key in ('pole_W02', 'arch_minus_WR', 'prime_minus_Wp'):
            Hp = to_mp(plus[key], digits)
            Hm = to_mp(minus[key], digits)
            H = (Hp - Hm) / (2 * h)
            contributions[key] = qform(w, H) / s0m
        component_sum = sum(contributions.values())
        Htot = (to_mp(plus['total'], digits) - to_mp(minus['total'], digits)) / (2 * h)
        directional_total = qform(w, Htot) / s0m
        sp = last_positive_pivot(plus['total'])
        sm = last_positive_pivot(minus['total'])
        direct_pivot_g = (mid(sp, digits) - mid(sm, digits)) / (2 * h * s0m)
        denom = abs(component_sum) if component_sum else mp.mpf('nan')
        cancellation = sum(abs(v) for v in contributions.values()) / denom
        rows.append({
            'h': hs,
            'component_log_flow': {k: mp.nstr(v, 70) for k, v in contributions.items()},
            'component_sum': mp.nstr(component_sum, 70),
            'directional_total': mp.nstr(directional_total, 70),
            'direct_pivot_fd_g': mp.nstr(direct_pivot_g, 70),
            'sum_abs_over_abs_sum': mp.nstr(cancellation, 50),
            'directional_minus_component_sum': mp.nstr(directional_total - component_sum, 40),
            'direct_pivot_minus_directional': mp.nstr(direct_pivot_g - directional_total, 40),
        })

    out = {
        'status': 'exploratory_schur_flow_component_decomposition',
        'warning': 'Base pivot is rigorous Arb; Schur normal and derivatives use high-precision midpoints. Active prime-power set is fixed, so this is valid only inside the threshold-free neighborhood.',
        'upstream_commit': args.upstream_commit,
        'c0': args.c0,
        'N': args.N,
        'prec_bits': args.prec,
        'mpmath_dps': args.dps,
        'active_prime_power_count': len(pdata),
        'pivot_at_c0': ball(s0),
        'schur_normal_l2_norm_midpoint': mp.nstr(mp.norm(w), 60),
        'rows': rows,
        'meaning': 'The three entries decompose g_N=(d/du)log s_N along the pinned W02-WR-Wp formula. sum_abs_over_abs_sum measures cancellation along the Schur normal, not matrix-wide cancellation.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
