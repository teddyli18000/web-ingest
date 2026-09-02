#!/usr/bin/env python3
"""Prime-power ablation experiment for cutoff-free even Schur pivots.

Build the exact Arb cutoff-free CvS matrix at c,N, then remove one selected
prime-power term q=p^k from the finite prime sum by adding its contribution
back to A = W02 - WR - Wp.  Baseline and ablated matrices are projected to the
same orthonormal even basis and factored by signed interval LDL^T.

This is a causal structural diagnostic, not a statement about the zeta Weil
form after ablation (the ablated form is artificial).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import mpmath as mp
from flint import arb, arb_mat, ctx


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("upstream", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


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


def signed_interval_ldlt(E: arb_mat):
    dim = E.nrows()
    d = [None] * dim
    Lf = [[arb(0) for _ in range(dim)] for _ in range(dim)]
    rows = []
    for i in range(dim):
        s = E[i, i]
        for k in range(i):
            s = s - Lf[i][k] * Lf[i][k] * d[k]
        if s > 0:
            sign = 1
        elif s < 0:
            sign = -1
        else:
            rows.append((i, s, 0))
            return rows, i
        d[i] = s
        for j in range(i + 1, dim):
            t = E[j, i]
            for k in range(i):
                t = t - Lf[j][k] * Lf[i][k] * d[k]
            Lf[j][i] = t / d[i]
        rows.append((i, s, sign))
    return rows, None


def contribution_full(module, c: int, N: int, prec: int, q_target: int):
    ctx.prec = prec
    hit = None
    for q, p in module.prime_powers_up_to(c):
        if int(q) == q_target:
            hit = (int(q), int(p))
            break
    if hit is None:
        raise ValueError(f"q={q_target} is not a prime power in cutoff c={c}")
    q, p = hit
    L = arb(c).log()
    PI = arb.pi()
    y = arb(q).log()
    weight = arb(p).log() * (arb(q) ** arb('-0.5'))
    dim = 2 * N + 1
    P = arb_mat(dim, dim)
    for i in range(dim):
        n = i - N
        for j in range(i, dim):
            m = j - N
            if n == m:
                kernel = 2 * (1 - y / L) * (2 * PI * n * y / L).cos()
            else:
                kernel = (
                    (2 * PI * m * y / L).sin()
                    - (2 * PI * n * y / L).sin()
                ) / (PI * (n - m))
            val = weight * kernel
            P[i, j] = val
            P[j, i] = val
    return P, {"q": q, "p": p, "weight_mid": weight.mid().str(60, radius=False), "omega_mid": (y/L).mid().str(60, radius=False)}


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
    ap.add_argument("--c", type=int, default=100)
    ap.add_argument("--Nmax", type=int, default=80)
    ap.add_argument("--prec", type=int, default=5000)
    ap.add_argument("--q", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    module = load_module(args.upstream_script)
    A, _ = module.build_arb_tau(args.c, args.Nmax, args.prec)
    Pq, qmeta = contribution_full(module, args.c, args.Nmax, args.prec, args.q)
    A_abl = A + Pq  # A contains -Wp; add selected source back to remove it.

    base_rows, base_undet = signed_interval_ldlt(project_even(A, args.Nmax))
    abl_rows, abl_undet = signed_interval_ldlt(project_even(A_abl, args.Nmax))

    mp.mp.dps = 100
    common = min(len(base_rows), len(abl_rows))
    comparisons = []
    for i in range(common):
        _, sb, signb = base_rows[i]
        _, sa, signa = abl_rows[i]
        mb = mp.mpf(sb.mid().str(100, radius=False))
        ma = mp.mpf(sa.mid().str(100, radius=False))
        item = {
            "N": i,
            "baseline_sign": signb,
            "ablated_sign": signa,
            "baseline_pivot": ball(sb),
            "ablated_pivot": ball(sa),
        }
        if mb != 0 and ma != 0:
            item["log10_abs_ablated_over_baseline_mid"] = mp.nstr(mp.log10(abs(ma / mb)), 40)
            item["delta_minus_log10_abs_mid"] = mp.nstr(-mp.log10(abs(ma)) + mp.log10(abs(mb)), 40)
        comparisons.append(item)

    target_ns = [32, 40, 48, 56, 64, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80]
    selected = [comparisons[n] for n in target_ns if n < len(comparisons)]
    # Rank by absolute log response, excluding N=0 and any zero/undetermined cases.
    ranked = [x for x in comparisons[1:] if "log10_abs_ablated_over_baseline_mid" in x]
    ranked.sort(key=lambda x: abs(float(x["log10_abs_ablated_over_baseline_mid"])), reverse=True)

    out = {
        "status": "rigorous_interval_prime_power_ablation_schur",
        "warning": "The ablated matrix is an artificial control, not the zeta Weil form. Log ratios use interval midpoints; pivot signs are interval-rigorous where nonzero.",
        "upstream_commit": args.upstream_commit,
        "c": args.c,
        "Nmax": args.Nmax,
        "prec_bits": args.prec,
        "removed_prime_power": qmeta,
        "baseline_undetermined_at": base_undet,
        "ablated_undetermined_at": abl_undet,
        "baseline_all_positive_through_computed": all(r[2] == 1 for r in base_rows),
        "ablated_inertia_prefix_signs": [r[2] for r in abl_rows],
        "selected": selected,
        "top_response_modes": ranked[:20],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "q": qmeta,
        "baseline_undetermined_at": base_undet,
        "ablated_undetermined_at": abl_undet,
        "ablated_negative_pivots": [r[0] for r in abl_rows if r[2] < 0],
        "selected": [{"N": x["N"], "log10_ratio": x.get("log10_abs_ablated_over_baseline_mid")} for x in selected],
        "top_response": [{"N": x["N"], "log10_ratio": x.get("log10_abs_ablated_over_baseline_mid")} for x in ranked[:8]],
    }, indent=2))


if __name__ == "__main__":
    main()
