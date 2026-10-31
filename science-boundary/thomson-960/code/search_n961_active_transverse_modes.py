#!/usr/bin/env python3
"""Search active-geometry side exits at the N961 fractional A/R interface.

A one-dimensional charge continuation of label 960 crosses an N960 projection
boundary: an A-side fractional state near lambda=0.15 and an R-side state near
lambda=0.10 both remain on the same smooth weighted N961 branch.  The secant
between those two states is therefore an empirical boundary-crossing direction.

This script changes representation in two ways relative to the earlier full
weighted-Hessian probe:
  1. Search only the 960 retained particles.  The two tangent coordinates of
     fading label 960 are excluded because that particle is deleted before the
     genuine N960 return; soft modes localized on it would otherwise disappear.
  2. Project out the active component of the A/R branch secant in addition to
     rigid rotations, so the eigensolver returns directions transverse to the
     known occupancy-induced crossing rather than more of the same 1-D motion.

At the midpoint fractional state we diagonalize the principal active block of
the weighted N961 Hessian with label960 held at its relaxed position, perturb
the retained 960 points along the lowest transverse modes, then delete label960
and fully repolish under the ordinary N960 Thomson objective.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_live_size_bounce import load_points, voronoi_candidates, relax as size_relax
from search_n972_mobile_fractional_homotopy import stable_weighted_relax, weighted_terms_grad
from search_from_seed_modes import stable_relax_q
from search_n961_fractional_boundary_modes import classify, counts, parse_schedule

FADE = 960


def kabsch_align(ref: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Rigidly rotate labelled row-vector configuration x onto ref."""
    H = x.T @ ref
    U, _, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1.0
        R = U @ Vt
    y = x @ R
    err = np.linalg.norm(y - ref, axis=1)
    return y, float(np.sqrt(np.mean(err * err))), float(np.max(err))


def tangent_log(ref: np.ndarray, other: np.ndarray) -> np.ndarray:
    """Per-point sphere logarithm at ref, in physical (theta,phi) coordinates."""
    q = sm.xyz_to_vars(ref)
    _, eth, dph = sm.vars_to_xyz(q)
    st = np.maximum(np.linalg.norm(dph, axis=1), 1e-12)
    eph = dph / st[:, None]
    c = np.clip(np.sum(ref * other, axis=1), -1.0, 1.0)
    ang = np.arccos(c)
    v = other - c[:, None] * ref
    nv = np.linalg.norm(v, axis=1)
    dx = np.zeros_like(ref)
    good = nv > 1e-13
    dx[good] = v[good] * (ang[good] / nv[good])[:, None]
    dx[~good] = v[~good]
    return np.column_stack([np.sum(dx * eth, axis=1), np.sum(dx * eph, axis=1)]).ravel()


def active_weighted_hessian(q0_full, charges, fade_index, fd_step, rot_penalty,
                            secant, secant_penalty):
    """Principal active block of weighted N961 Hessian, with nuisance directions lifted."""
    nfull = len(q0_full) // 2
    if fade_index != nfull - 1:
        raise ValueError('this search currently requires the faded particle to be the final label')
    nact = nfull - 1
    scale = sm.physical_scale(q0_full)
    invs = 1.0 / scale
    qact = sm.xyz_to_vars(sm.vars_to_xyz(q0_full)[0][:-1])
    Qrot = sm.rotation_basis(qact)
    sec = np.asarray(secant, float).copy()
    sec -= Qrot @ (Qrot.T @ sec)
    sn = float(np.linalg.norm(sec))
    if sn < 1e-10:
        raise RuntimeError(f'branch secant vanished after rotation projection: {sn}')
    sec /= sn
    calls = {'n': 0}

    def grad(q):
        return weighted_terms_grad(q, charges)[1]

    def raw_active(ya):
        ya = np.asarray(ya, float)
        yn = float(np.linalg.norm(ya))
        if yn == 0.0:
            return np.zeros_like(ya)
        yf = np.zeros(2 * nfull, float)
        yf[:2 * nact] = ya / yn
        dq = invs * yf
        gp = grad(q0_full + fd_step * dq)
        gm = grad(q0_full - fd_step * dq)
        calls['n'] += 2
        hq = (gp - gm) * (yn / (2.0 * fd_step))
        hy = invs * hq
        return hy[:2 * nact]

    def mv(ya):
        ya = np.asarray(ya, float)
        z = raw_active(ya)
        z += rot_penalty * (Qrot @ (Qrot.T @ ya))
        z += secant_penalty * sec * float(sec @ ya)
        return z

    return LinearOperator((2 * nact, 2 * nact), matvec=mv, dtype=float), raw_active, Qrot, sec, calls


def project_return(x961: np.ndarray, live_score: float, maxiter: int):
    q = sm.xyz_to_vars(np.delete(x961, FADE, axis=0))
    e, raw, y, nit, ok, msg = stable_relax_q(q, maxiter=maxiter)
    return {
        'energy': float(e), 'delta_live': float(e - live_score),
        'class': classify(e, live_score), 'coord_counts': counts(y),
        'nit': int(nit), 'success': bool(ok), 'message': str(msg),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a_json')
    ap.add_argument('--lambda-hi', type=float, default=0.15)
    ap.add_argument('--lambda-value', type=float, default=0.125)
    ap.add_argument('--lambda-lo', type=float, default=0.10)
    ap.add_argument('--schedule', default='1,.8,.6,.4,.25,.15,.1,.075,.06,.05,.04,.03,.025,.02,.015,.01,.007,.005,.003,.001,0')
    ap.add_argument('--modes', default='0,1,2,3,4,5')
    ap.add_argument('--amps', default='.0015,.003,.006,.012,.02')
    ap.add_argument('--k', type=int, default=10)
    ap.add_argument('--fd-step', type=float, default=3e-6)
    ap.add_argument('--rot-penalty', type=float, default=1e6)
    ap.add_argument('--secant-penalty', type=float, default=1e6)
    ap.add_argument('--weighted-maxiter', type=int, default=1800)
    ap.add_argument('--return-maxiter', type=int, default=4200)
    ap.add_argument('--live-score', type=float, required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    hi, lam, lo = map(float, (args.lambda_hi, args.lambda_value, args.lambda_lo))
    if not (0.0 <= lo < lam < hi <= 1.0):
        raise ValueError(f'require 0 <= lo < lambda < hi <= 1, got {lo}, {lam}, {hi}')

    _, a = load_points(pathlib.Path(args.a_json))
    sel = voronoi_candidates(a)[3]
    hub = size_relax(np.vstack([a, np.asarray(sel['point'], float)[None, :]]), 3200)
    x = np.asarray(hub['points'], float)
    if abs(hub['energy'] - 445303.247369582) > 5e-4:
        raise RuntimeError(f'unexpected hub {hub["energy"]}')

    trace = []
    for lv in parse_schedule(args.schedule, hi):
        charges = np.ones(961, float); charges[FADE] = lv
        ew, x, nit, ok, msg, grms = stable_weighted_relax(x, charges, args.weighted_maxiter)
        trace.append({'lambda': lv, 'energy': float(ew), 'grms': float(grms), 'nit': int(nit), 'success': bool(ok)})
        print('CONT', 'L', lv, 'Ew', f'{ew:.12f}', 'grms', f'{grms:.3g}', 'nit', nit, 'ok', ok, flush=True)
    x_hi = x.copy()

    for lv in (lam, lo):
        charges = np.ones(961, float); charges[FADE] = lv
        ew, x, nit, ok, msg, grms = stable_weighted_relax(x, charges, args.weighted_maxiter)
        trace.append({'lambda': lv, 'energy': float(ew), 'grms': float(grms), 'nit': int(nit), 'success': bool(ok)})
        print('CONT', 'L', lv, 'Ew', f'{ew:.12f}', 'grms', f'{grms:.3g}', 'nit', nit, 'ok', ok, flush=True)
        if lv == lam:
            x_mid = x.copy()
        else:
            x_lo = x.copy()

    control_hi = project_return(x_hi, args.live_score, args.return_maxiter)
    baseline = project_return(x_mid, args.live_score, args.return_maxiter)
    control_lo = project_return(x_lo, args.live_score, args.return_maxiter)
    print('BRACKET', hi, control_hi['class'], f"{control_hi['energy']:.12f}",
          lam, baseline['class'], f"{baseline['energy']:.12f}",
          lo, control_lo['class'], f"{control_lo['energy']:.12f}", flush=True)
    if control_hi['class'] == control_lo['class']:
        raise RuntimeError(f'hi/lo no longer straddle distinct projection basins: {control_hi["class"]}/{control_lo["class"]}')

    hi_aligned, hi_rms, hi_max = kabsch_align(x_mid, x_hi)
    lo_aligned, lo_rms, lo_max = kabsch_align(x_mid, x_lo)
    y_hi = tangent_log(x_mid[:-1], hi_aligned[:-1])
    y_lo = tangent_log(x_mid[:-1], lo_aligned[:-1])
    secant = y_hi - y_lo
    secant_deriv_rms = float(np.linalg.norm(secant) / math.sqrt(960) / (hi - lo))

    q0 = sm.xyz_to_vars(x_mid)
    charges = np.ones(961, float); charges[FADE] = lam
    H, raw_active, Qrot, sec, calls = active_weighted_hessian(
        q0, charges, FADE, args.fd_step, args.rot_penalty, secant, args.secant_penalty)

    modes = [int(z) for z in args.modes.split(',') if z.strip()]
    amps = [float(z) for z in args.amps.split(',') if z.strip()]
    k = max(args.k, max(modes) + 1)
    rng = np.random.default_rng(1961000 + int(round(lam * 1e6)))
    v0 = rng.normal(size=1920)
    v0 -= Qrot @ (Qrot.T @ v0)
    v0 -= sec * float(sec @ v0)
    vals, V = eigsh(H, k=k, which='SA', tol=2e-5, maxiter=900, ncv=max(40, 3*k), v0=v0)
    order = np.argsort(vals); vals = vals[order]; V = V[:, order]
    print('ACTIVE_TRANSVERSE_EIGENVALUES', [float(v) for v in vals], flush=True)

    mode_diag = []
    rows = []
    qact = sm.xyz_to_vars(x_mid[:-1])
    for m in modes:
        d = V[:, m].copy()
        d -= Qrot @ (Qrot.T @ d)
        d -= sec * float(sec @ d)
        d /= np.linalg.norm(d)
        Hy = raw_active(d) + args.rot_penalty * (Qrot @ (Qrot.T @ d)) + args.secant_penalty * sec * float(sec @ d)
        resid = float(np.linalg.norm(Hy - vals[m] * d))
        diag = {'mode': m, 'eigenvalue': float(vals[m]), 'rotation_overlap': float(np.sum((Qrot.T @ d)**2)),
                'secant_overlap': float((sec @ d)**2), 'residual': resid}
        mode_diag.append(diag)
        print('MODE', m, 'eig', f'{vals[m]:.9g}', 'rot', f"{diag['rotation_overlap']:.3g}",
              'sec', f"{diag['secant_overlap']:.3g}", 'resid', f'{resid:.3g}', flush=True)
        for sign in (-1, 1):
            for amp in amps:
                qp = sp.exp_perturb(qact, d * sign, amp)
                e, raw, y, nit, ok, msg = stable_relax_q(qp, maxiter=args.return_maxiter)
                rec = {'mode': m, 'eigenvalue': float(vals[m]), 'sign': sign, 'amp': amp,
                       'energy': float(e), 'delta_live': float(e - args.live_score),
                       'class': classify(e, args.live_score), 'coord_counts': counts(y),
                       'nit': int(nit), 'success': bool(ok), 'message': str(msg)}
                rows.append(rec)
                print('RETURN', 'm', m, 's', sign, 'a', amp, rec['class'], f'{e:.12f}',
                      'dLive', f'{e-args.live_score:+.9g}', rec['coord_counts'], flush=True)

    rows.sort(key=lambda r: r['energy'])
    best = min([baseline['energy']] + [r['energy'] for r in rows])
    out = {
        'live_score': float(args.live_score), 'lambda_hi': hi, 'lambda': lam, 'lambda_lo': lo,
        'hub_energy': float(hub['energy']), 'hub_triangle': sel['triangle'], 'continuation_trace': trace,
        'control_hi': control_hi, 'baseline': baseline, 'control_lo': control_lo,
        'alignment': {'hi_rms': hi_rms, 'hi_max': hi_max, 'lo_rms': lo_rms, 'lo_max': lo_max},
        'secant_derivative_rms': secant_deriv_rms,
        'eigenvalues': [float(v) for v in vals], 'mode_diagnostics': mode_diag,
        'modes': modes, 'amps': amps, 'hessian_gradient_calls': calls['n'], 'rows': rows,
        'best_energy': float(best), 'best_delta_live': float(best - args.live_score),
    }
    pathlib.Path(args.out).write_text(json.dumps(out, separators=(',', ':')) + '\n')
    if best < args.live_score - 2e-7:
        pathlib.Path(str(args.out) + '.BREAKTHROUGH').write_text('active transverse candidate below live; verify independently\n')


if __name__ == '__main__':
    main()
