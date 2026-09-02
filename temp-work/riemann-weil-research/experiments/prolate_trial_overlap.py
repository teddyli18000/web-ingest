#!/usr/bin/env python3
"""Exploratory Connes-prolate trial vs cutoff-free CvS ground state.

This intentionally separates two arithmetic regimes:
- the Weil matrix and its eigensystem are built from the pinned Arb verifier and
  diagonalized with mpmath at high precision;
- the prolate trial direction is generated in float64 from the *differential
  operator* in an orthonormal Legendre basis (not scipy.special.pro_ang1, which
  becomes unreliable for the large bandwidths here).

Therefore overlaps are meaningful exploratory diagnostics. Rayleigh/residual
numbers inherit the float64 trial-vector floor and are NOT certificates.
"""

import argparse
import importlib.util
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np
from numpy.polynomial.legendre import legval
from scipy.integrate import quad


def load_upstream(path):
    spec = importlib.util.spec_from_file_location("arb_verifier", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def legendre_t2_even(M):
    """Matrix of multiplication by t^2 on phi_l, l=0,2,... orthonormal Legendre."""
    ls = np.arange(0, 2 * M, 2, dtype=int)
    T2 = np.zeros((M, M), dtype=float)

    def ap(l):
        return (l + 1) / math.sqrt((2 * l + 1) * (2 * l + 3))

    def am(l):
        if l == 0:
            return 0.0
        return l / math.sqrt((2 * l - 1) * (2 * l + 1))

    for i, l in enumerate(ls):
        T2[i, i] = ap(l) * am(l + 1)
        if l > 0:
            T2[i, i] += am(l) * ap(l - 1)
        if i + 1 < M:
            v = ap(l) * ap(l + 1)
            T2[i, i + 1] = v
            T2[i + 1, i] = v
    return ls, T2


def connes_h_lambda(C, M):
    """Return h_lambda as the zero-integral combination of h_0 and h_4.

    PW_lambda rescales to
      -d/dt((1-t^2)d/dt) + (2*pi*C)^2 t^2, t in [-1,1].
    h_0 is the first even eigenfunction; h_4 is the third even eigenfunction.
    In the orthonormal Legendre basis the integral depends only on the l=0
    coefficient, so the unique zero-integral combination is exact up to the
    float64 eigensolve.
    """
    lam = math.sqrt(C)
    c = 2 * math.pi * C
    ls, T2 = legendre_t2_even(M)
    H = np.diag(ls * (ls + 1.0)) + (c * c) * T2
    evals, evecs = np.linalg.eigh(H)
    v0 = evecs[:, 0]
    v4 = evecs[:, 2]
    ratio = v4[0] / v0[0]
    vh = v4 - ratio * v0
    vh /= np.linalg.norm(vh)

    coeff = np.zeros(int(ls[-1]) + 1, dtype=float)
    for a, l in zip(vh, ls):
        coeff[l] = a * math.sqrt((2 * l + 1) / 2.0)

    def h_phys(x):
        y = np.asarray(x, dtype=float) / lam
        return legval(y, coeff)

    return {
        "lambda": lam,
        "bandwidth": c,
        "operator_eigenvalues_even_first5": evals[:5],
        "legendre_even_coeffs": vh,
        "poly_coeffs": coeff,
        "h": h_phys,
        "h_at_zero": float(h_phys(0.0)),
        "integral_proxy_l0": float(vh[0]),
    }


def k_of_t(C, h, t):
    lam = math.sqrt(C)
    u = math.exp(t)
    nmax = int(math.floor(lam / u + 1e-13))
    if nmax < 1:
        return 0.0
    xs = u * np.arange(1, nmax + 1, dtype=float)
    return math.sqrt(u) * float(np.sum(h(xs)))


def trial_fourier_coeffs(C, N, h):
    """Coefficients in the [0,L] Fourier basis used by the CvS matrix.

    With centered log coordinate t=log u in [-L/2,L/2] and y=t+L/2,
      c_k = L^{-1/2} int k_lambda(e^t) exp(-2*pi*i*k*y/L) dt.
    The constructed k_lambda is inversion-even to numerical precision, hence
      c_k = (-1)^k 2/sqrt(L) int_0^{L/2} k(t) cos(2*pi*k*t/L) dt.
    """
    L = math.log(C)
    lam = math.sqrt(C)
    # On t>=0 nmax changes only at log(lam/n), n=1,...,floor(lam).
    breaks = [0.0]
    for n in range(1, int(math.floor(lam)) + 1):
        b = math.log(lam / n)
        if 1e-15 < b < L / 2 - 1e-15:
            breaks.append(b)
    breaks.append(L / 2)
    breaks = sorted(set(breaks))

    vals = []
    vals_no_shift = []
    quad_errors = []
    for k in range(-N, N + 1):
        kk = abs(k)
        omega = 2 * math.pi * kk / L
        total = 0.0
        err = 0.0
        for a, b in zip(breaks[:-1], breaks[1:]):
            val, e = quad(
                lambda t: k_of_t(C, h, t) * math.cos(omega * t),
                a,
                b,
                epsabs=2e-13,
                epsrel=2e-13,
                limit=200,
            )
            total += val
            err += e
        centered = 2.0 * total / math.sqrt(L)
        vals_no_shift.append(centered)
        vals.append(((-1.0) ** kk) * centered)
        quad_errors.append(err)
    v = np.array(vals, dtype=float)
    v_alt = np.array(vals_no_shift, dtype=float)
    v /= np.linalg.norm(v)
    v_alt /= np.linalg.norm(v_alt)
    return v, v_alt, max(quad_errors), breaks


def arb_mid_to_mp(a, digits):
    return mp.mpf(a.mid().str(digits, radius=False))


def cutoff_free_even_eigensystem(up, C, N, prec_bits, dps):
    mp.mp.dps = dps
    Aarb, DIM = up.build_arb_tau(C, N, prec_bits)
    A = mp.matrix(DIM, DIM)
    ndig = dps + 20
    for i in range(DIM):
        for j in range(DIM):
            A[i, j] = arb_mid_to_mp(Aarb[i, j], ndig)

    # Orthonormal reversal-even projector.
    V = mp.matrix(DIM, N + 1)
    V[N, 0] = 1
    invsqrt2 = 1 / mp.sqrt(2)
    for k in range(1, N + 1):
        V[N - k, k] = invsqrt2
        V[N + k, k] = invsqrt2
    E = V.T * A * V
    eigs, vecs = mp.eigsy(E)
    # eigsy sorted ascending.
    v_even = vecs[:, 0]
    v_full = V * v_even
    norm = mp.sqrt(sum(v_full[i] ** 2 for i in range(DIM)))
    v_full = v_full / norm
    return A, E, eigs, v_full


def mp_dot_float(vmp, vf):
    return sum(vmp[i] * mp.mpf(repr(float(vf[i]))) for i in range(len(vf)))


def diagnostics_for_N(up, C, N, pro, prec_bits, dps):
    trial, trial_alt, qerr, breaks = trial_fourier_coeffs(C, N, pro["h"])
    A, E, eigs, ground = cutoff_free_even_eigensystem(up, C, N, prec_bits, dps)

    ov = abs(mp_dot_float(ground, trial))
    ov_alt = abs(mp_dot_float(ground, trial_alt))

    # Exploratory Rayleigh and residual; trial coefficients are only float64.
    tv = mp.matrix([mp.mpf(repr(float(x))) for x in trial])
    tnorm = mp.sqrt(sum(x*x for x in tv))
    tv /= tnorm
    At = A * tv
    ray = (tv.T * At)[0]
    residual = mp.sqrt(sum((At[i] - ray * tv[i]) ** 2 for i in range(2*N+1)))
    gap = eigs[1] - eigs[0]
    excess = ray - eigs[0]
    angle_bound_sq = excess / gap if gap > 0 else mp.inf

    return {
        "N": N,
        "ground_eigenvalue": mp.nstr(eigs[0], 60),
        "second_even_eigenvalue": mp.nstr(eigs[1], 60),
        "even_gap": mp.nstr(gap, 60),
        "lambda2_over_lambda1": mp.nstr(eigs[1] / eigs[0], 30),
        "absolute_overlap_centered_phase": mp.nstr(ov, 40),
        "absolute_overlap_without_minus1k": mp.nstr(ov_alt, 40),
        "sign_aligned_l2_distance": mp.nstr(mp.sqrt(max(mp.mpf(0), 2 - 2*ov)), 40),
        "trial_rayleigh_float64_coeffs": mp.nstr(ray, 60),
        "trial_excess_over_ground_float64_coeffs": mp.nstr(excess, 60),
        "trial_residual_norm_float64_coeffs": mp.nstr(residual, 60),
        "exploratory_excess_over_gap": mp.nstr(angle_bound_sq, 40),
        "quadrature_error_estimate_max": repr(qerr),
        "positive_half_breakpoints": [repr(x) for x in breaks],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--upstream-script", required=True)
    p.add_argument("--upstream-commit", required=True)
    p.add_argument("--C", type=int, default=13)
    p.add_argument("--Ns", default="4,8,12,16")
    p.add_argument("--prolate-M", type=int, default=120)
    p.add_argument("--prec", type=int, default=1200)
    p.add_argument("--dps", type=int, default=180)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    up = load_upstream(args.upstream_script)
    pro = connes_h_lambda(args.C, args.prolate_M)
    L = math.log(args.C)
    ts = np.linspace(-L/2, L/2, 101)
    kv = np.array([k_of_t(args.C, pro["h"], float(t)) for t in ts])
    krev = np.array([k_of_t(args.C, pro["h"], float(-t)) for t in ts])
    inversion_rel = float(np.linalg.norm(kv-krev) / np.linalg.norm(kv))

    rows = []
    for N in [int(x) for x in args.Ns.split(",") if x.strip()]:
        print(f"[prolate-trial] C={args.C} N={N}", flush=True)
        rows.append(diagnostics_for_N(up, args.C, N, pro, args.prec, args.dps))

    out = {
        "status": "exploratory_prolate_trial_vs_cutoff_free_ground",
        "warning": "Weil matrix/eigenpairs are high-precision cutoff-free midpoints; prolate trial and its Fourier coefficients are float64. Overlaps are exploratory. Rayleigh/residual values are NOT certificates and are limited by float64 trial-vector accuracy.",
        "source": "Connes 2026 formula (17): k_lambda=E(h_lambda), h_lambda zero-integral linear combination of h_0,lambda and h_4,lambda",
        "upstream_commit": args.upstream_commit,
        "C": args.C,
        "lambda": repr(pro["lambda"]),
        "L_log_C": repr(L),
        "prolate_bandwidth_2piC": repr(pro["bandwidth"]),
        "prolate_legendre_dimension": args.prolate_M,
        "h_lambda_at_zero_float64": repr(pro["h_at_zero"]),
        "h_lambda_integral_l0_proxy_float64": repr(pro["integral_proxy_l0"]),
        "k_inversion_relative_l2_grid_float64": repr(inversion_rel),
        "prolate_even_operator_eigenvalues_first5": [repr(float(x)) for x in pro["operator_eigenvalues_even_first5"]],
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()
