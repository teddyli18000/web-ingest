#!/usr/bin/env python3
"""Rigorous prime-edge Schur residuals in the cutoff-free CvS path.

At a prime-power threshold c=q=p^k the entering source has zero matrix value,
so the left/right matrix Q_N(log q) is the same.  For the nested orthonormal
even basis, write

    E_N = [[B, b], [b^T, c]],   s_N = c - b^T B^{-1} b.

The projection of the full all-ones source vector to this basis is

    r_N = (1, sqrt(2), ..., sqrt(2)).

If r_N=(r_<, eta), define the edge residual

    R_{N,q} = eta - r_<^T B^{-1} b.

Combined with the upstream rank-one prime-edge jump

    Delta Q_N' = -a_q 11^T,
    a_q = 2 Lambda(q)/(sqrt(q) log q) = 2/(k sqrt(q)),

ordinary Schur differentiation gives

    Delta s_N' = -a_q R_{N,q}^2 <= 0.

This script rigorously encloses R_{N,q}, R^2, a_q and the impulse a_q R^2
using Arb.  It is a structural diagnostic, not an RH proof.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("upstream", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prime_power_decomposition(q: int):
    for p in range(2, q + 1):
        # cheap primality check
        prime = p >= 2 and all(p % d for d in range(2, int(p ** 0.5) + 1))
        if not prime:
            continue
        x = p
        k = 1
        while x < q:
            x *= p
            k += 1
        if x == q:
            return p, k
    raise ValueError(f"q={q} is not a prime power")


def project_even(A: arb_mat, N: int) -> arb_mat:
    E = arb_mat(N + 1, N + 1)
    root2 = arb(2).sqrt()
    center = N
    E[0, 0] = A[center, center]
    for k in range(1, N + 1):
        E[0, k] = (A[center, center + k] + A[center, center - k]) / root2
        E[k, 0] = E[0, k]
    for k in range(1, N + 1):
        for j in range(k, N + 1):
            v = (
                A[center + k, center + j] + A[center + k, center - j]
                + A[center - k, center + j] + A[center - k, center - j]
            ) / 2
            E[k, j] = v
            E[j, k] = v
    return E


def signed_ldlt(E: arb_mat):
    """Unpivoted signed interval LDL. Returns (L,d,signs)."""
    n = E.nrows()
    L = [[arb(0) for _ in range(n)] for _ in range(n)]
    d = [None] * n
    signs = []
    for i in range(n):
        L[i][i] = arb(1)
        s = E[i, i]
        for k in range(i):
            s -= L[i][k] * L[i][k] * d[k]
        if s > 0:
            sign = 1
        elif s < 0:
            sign = -1
        else:
            raise RuntimeError(f"undetermined pivot at N={i}: {s}")
        d[i] = s
        signs.append(sign)
        for j in range(i + 1, n):
            t = E[j, i]
            for k in range(i):
                t -= L[j][k] * L[i][k] * d[k]
            L[j][i] = t / d[i]
    return L, d, signs


def solve_Lt_x_eq_ell(L, ell, n):
    """Solve L_prefix^T x = ell for unit-lower L_prefix."""
    x = [arb(0) for _ in range(n)]
    for i in range(n - 1, -1, -1):
        t = ell[i]
        for j in range(i + 1, n):
            t -= L[j][i] * x[j]
        # diagonal of L is exactly 1
        x[i] = t
    return x


def ball(x: arb, digits=70):
    return {
        "lower": x.lower().str(digits, radius=False),
        "mid": x.mid().str(digits, radius=False),
        "upper": x.upper().str(digits, radius=False),
        "rad": x.rad().str(25, radius=False),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-script", type=Path, required=True)
    ap.add_argument("--upstream-commit", required=True)
    ap.add_argument("--q", type=int, required=True)
    ap.add_argument("--Nmax", type=int, default=32)
    ap.add_argument("--prec", type=int, default=3000)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    p, k = prime_power_decomposition(args.q)
    module = load_module(args.upstream_script)
    ctx.prec = args.prec

    # At c=q the entering q-source has zero matrix value, so the matrix itself
    # is the continuous edge value used in the derivative-jump calculation.
    A, _ = module.build_arb_tau(args.q, args.Nmax, args.prec)
    E = project_even(A, args.Nmax)
    L, d, signs = signed_ldlt(E)

    root2 = arb(2).sqrt()
    a_q = arb(2) / (arb(k) * arb(args.q).sqrt())
    rows = []
    for N in range(args.Nmax + 1):
        if N == 0:
            residual = arb(1)
        else:
            # For the block step N, ell is row N of the LDL lower factor.
            # From b = L_old D_old ell, B^{-1}b = L_old^{-T} ell.
            ell = [L[N][j] for j in range(N)]
            x = solve_Lt_x_eq_ell(L, ell, N)
            residual = root2
            residual -= x[0]  # old constant mode has source coefficient 1
            for j in range(1, N):
                residual -= root2 * x[j]
        r2 = residual * residual
        impulse = a_q * r2
        rows.append({
            "N": N,
            "schur_pivot_sign": signs[N],
            "schur_pivot": ball(d[N]),
            "residual": ball(residual),
            "residual_squared": ball(r2),
            "impulse_magnitude_aq_R2": ball(impulse),
        })

    # Midpoint rankings are only for navigation; all stored balls are rigorous.
    ranked = sorted(
        rows,
        key=lambda r: float(r["impulse_magnitude_aq_R2"]["mid"]),
        reverse=True,
    )
    out = {
        "status": "rigorous_prime_edge_schur_residuals",
        "meaning": "At the prime-power edge c=q, Delta s_N' = -a_q R_{N,q}^2. The reported a_q R^2 balls rigorously enclose the nonnegative impulse magnitude, conditional only on the pinned CvS normalization used by the upstream edge identity.",
        "upstream_commit": args.upstream_commit,
        "q": args.q,
        "prime": p,
        "exponent": k,
        "Nmax": args.Nmax,
        "prec_bits": args.prec,
        "a_q_equals_2_over_k_sqrt_q": ball(a_q),
        "all_ldlt_pivots_strictly_signed": True,
        "ldlt_signs": signs,
        "rows": rows,
        "largest_impulse_modes_midpoint_order": [r["N"] for r in ranked[:12]],
        "selected": [rows[n] for n in (0,1,2,4,8,12,16,20,24,28,32) if n <= args.Nmax],
        "warning": "This certifies the finite-path edge residuals and impulse magnitudes, not positivity for arbitrary support and not RH.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "q": args.q,
        "p": p,
        "k": k,
        "a_q_mid": out["a_q_equals_2_over_k_sqrt_q"]["mid"],
        "signs": signs,
        "top_impulse_modes": [
            {"N": r["N"], "impulse_mid": r["impulse_magnitude_aq_R2"]["mid"], "R_mid": r["residual"]["mid"]}
            for r in ranked[:8]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
