#!/usr/bin/env python3
"""Continue the certified weighted N961 A/H index-one saddle along occupancy rays.

Start at q886=q960=q380=2/3 and move towards one of three deletion vertices,
always conserving q886+q960+q380=2. The branch is corrected by rotation-gauged
Newton-MINRES with complex-step analytic Hessian-vector products. Acceptance
requires a small physical-gradient residual and a checked index-one Hessian.
Only accepted stationary geometries are projected into real unit-charge N960.
Failed continuation is reported as an algorithmic failure, not a proven fold.
"""
from __future__ import annotations
import argparse
import json
import math
import pathlib

import numpy as np
from scipy.sparse.linalg import minres

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_size_beam as sbeam
from search_n961_three_occupancy_simplex import LABELS, classify
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
import refine_n961_weighted_saddle as rf
import validate_n961_weighted_edge as vw

N = 961
STEPS = (0.01, 0.025, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.48, 0.62, 0.78, 0.90)
PROBES = {0.08, 0.25, 0.48, 0.78}


def ray_charges(zero_label, s):
    c = np.ones(N, float)
    c[list(LABELS)] = 2.0 / 3.0
    for label in LABELS:
        c[label] += s * ((0.0 if label == zero_label else 1.0) - 2.0 / 3.0)
    assert abs(float(np.sum(c)) - 960.0) < 1e-10
    return c


def state(q, c):
    e, grad = rf.energy_grad(q, c)
    Q = sm.rotation_basis(q)
    g = grad / sm.physical_scale(q)
    g -= Q @ (Q.T @ g)
    return float(e), g, float(np.linalg.norm(g) / math.sqrt(2 * N))


def correct(q, c, grad_tol, max_newton, step_cap):
    q = q.copy()
    hist = []
    for it in range(max_newton):
        e, g, grms = state(q, c)
        if grms < grad_tol:
            return q, hist, True
        H, _, project, _, _, calls = vw.build_rot_projected_hessian(q, c, 1e-20, 1.0)
        dy, info = minres(H, -g, rtol=3e-4, maxiter=340)
        dy = project(dy)
        yn = float(np.linalg.norm(dy))
        if yn == 0:
            return q, hist, False
        rms = yn / math.sqrt(N)
        if rms > step_cap:
            dy *= step_cap / rms
            yn = float(np.linalg.norm(dy))
        accepted = False
        for alpha in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625):
            qt = sp.exp_perturb(q, dy / yn, alpha * yn / math.sqrt(N))
            et, gt, rt = state(qt, c)
            if rt < grms * (1.0 - 1e-5):
                q = qt
                accepted = True
                hist.append({'iteration': it, 'energy': et, 'gradient_rms_before': grms,
                             'gradient_rms_after': rt, 'newton_rms': rms,
                             'step_factor': alpha, 'minres_info': int(info),
                             'hvp_calls': calls['n']})
                break
        if not accepted:
            hist.append({'iteration': it, 'energy': e, 'gradient_rms_before': grms,
                         'line_search_failed': True, 'minres_info': int(info),
                         'hvp_calls': calls['n']})
            return q, hist, False
    return q, hist, state(q, c)[2] < grad_tol


def project_n960(x, label, live, outdir, tag, maxiter):
    energy, y, nit, ok = sbeam.stable_relax(np.delete(x, label, axis=0), maxiter)
    row = {'delete_index': int(label), 'energy': float(energy),
           'delta_live': float(energy - live), 'class': classify(energy, live),
           'iterations': int(nit), 'success': bool(ok)}
    if energy < live - 2e-7:
        path = outdir / (tag + '-del' + str(label) + '-CANDIDATE.json')
        path.write_text(json.dumps({'energy': energy, 'points': y.tolist(),
                                    'source': tag, 'delete_index': label}) + '\n')
        row['candidate_file'] = path.name
    return row


def probe_sides(q, c, mode, s, live, outdir, maxiter):
    rows = []
    for sign in (-1, 1):
        qs = sp.exp_perturb(q, sign * mode, 0.0002)
        xs = sm.vars_to_xyz(qs)[0]
        ew, relaxed, nit, ok, msg, grms = stable_weighted_relax(xs, c, 2200)
        projections = [project_n960(relaxed, lab, live, outdir,
                                    f'side-s{s:.4f}-sign{sign}', maxiter) for lab in LABELS]
        rows.append({'sign': sign, 'weighted_energy': float(ew),
                     'weighted_gradient_rms': float(grms), 'weighted_iterations': int(nit),
                     'weighted_success': bool(ok), 'weighted_message': str(msg),
                     'projections': projections})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('refined_json')
    ap.add_argument('--zero-label', type=int, choices=LABELS, required=True)
    ap.add_argument('--steps', default=','.join(str(s) for s in STEPS))
    ap.add_argument('--gradient-tol', type=float, default=4e-5)
    ap.add_argument('--max-newton', type=int, default=24)
    ap.add_argument('--step-cap', type=float, default=0.005)
    ap.add_argument('--project-maxiter', type=int, default=3600)
    ap.add_argument('--live-score', type=float, required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    baseline = json.loads(pathlib.Path(args.refined_json).read_text())
    x = np.asarray(baseline['saddle_points'], float)
    assert x.shape == (N, 3)
    q = sm.xyz_to_vars(x / np.linalg.norm(x, axis=1)[:, None])
    s0 = 0.0
    c0 = ray_charges(args.zero_label, s0)
    e0, g0, r0 = state(q, c0)
    assert r0 < args.gradient_tol
    assert abs(e0 - baseline['final_energy']) < 1e-6

    rows = []
    for s in (float(v) for v in args.steps.split(',')):
        c = ray_charges(args.zero_label, s)
        qtrial, nhist, success = correct(q, c, args.gradient_tol,
                                         args.max_newton, args.step_cap)
        e, g, grms = state(qtrial, c)
        row = {'s': s, 'charges': [float(c[lab]) for lab in LABELS],
               'energy': e, 'gradient_rms': grms, 'newton_steps': nhist,
               'root_converged': bool(success)}
        if not success:
            row['status'] = 'newton_failure_not_proven_fold'
            rows.append(row)
            print('STOP',args.zero_label,s,'newton_failure','grms',grms,flush=True)
            break

        vals, V, Q, modes, nc = rf.lowest(qtrial, c, 6, tol=8e-6)
        idx = int(np.sum(vals < -1e-3))
        row['hessian_lowest'] = [float(v) for v in vals]
        row['mode_residuals'] = modes
        row['negative_internal_modes'] = idx
        row['hvp_calls_modes'] = nc
        row['status'] = 'index_one' if idx == 1 and vals[0] < -1e-3 and vals[1] > 1e-3 else 'index_change_or_degeneracy'
        print('POINT',args.zero_label,s,'E',f'{e:.12f}','grms',f'{grms:.4g}',
              'lambdas',[round(float(v),7) for v in vals[:3]],
              'index',idx,flush=True)
        if row['status'] != 'index_one':
            rows.append(row)
            break

        x = sm.vars_to_xyz(qtrial)[0]
        row['saddle_points'] = x.tolist()
        row['projections'] = [project_n960(x,lab,args.live_score,outdir,
                                           f'saddle-s{s:.4f}',args.project_maxiter)
                              for lab in LABELS]
        if s in PROBES:
            v = V[:, 0].copy()
            v -= Q @ (Q.T @ v)
            v /= np.linalg.norm(v)
            row['unstable_sides'] = probe_sides(qtrial,c,v,s,args.live_score,
                                                 outdir,args.project_maxiter)
            print('SIDES',args.zero_label,s,
                  [[(p['delete_index'],p['class'],round(p['delta_live'],8))
                    for p in side['projections']] for side in row['unstable_sides']],flush=True)
        print('PROJECTIONS',args.zero_label,s,
              [(p['delete_index'],p['class'],round(p['delta_live'],8))
               for p in row['projections']],flush=True)

        rows.append(row)
        q = qtrial
        s0 = s
        (outdir / 'branch.json').write_text(json.dumps({
            'zero_label': args.zero_label, 'baseline_energy': e0,
            'baseline_gradient_rms': r0, 'last_accepted_s': s0, 'rows': rows
        }, separators=(',',':')) + '\n')

    output = {'zero_label': args.zero_label, 'baseline_energy': e0,
              'baseline_gradient_rms': r0, 'last_accepted_s': s0,
              'requested_steps': args.steps, 'gradient_tolerance': args.gradient_tol,
              'method': 'fixed-occupancy implicit saddle continuation by complex-step HVP Newton-MINRES',
              'rows': rows}
    (outdir / 'branch.json').write_text(json.dumps(output, separators=(',', ':')) + '\n')
    print('DONE',args.zero_label,'accepted_s',s0,'states',
          len([r for r in rows if r.get('status') == 'index_one']),flush=True)


if __name__ == '__main__':
    main()
