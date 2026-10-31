#!/usr/bin/env python3
"""Probe path-dependent two-occupancy loops at the shared N961 A/R hub.

The common N961 hub has two distinguished labels: deleting 886 returns the live
record R, while deleting inserted label 960 returns A.  Prior one-dimensional
fractional continuations established genuine hysteresis: the same endpoint
occupancy can retain different N960 projection history.

This program turns that observation into a search operator.  First establish the
R-side fractional endpoint (q886,q960)=(1,0) by adiabatically fading label960.
Then execute a closed rectangle in the independent occupancy plane and return to
exactly (1,0).  Clockwise and counter-clockwise loops change the order in which
the two strain fields are removed/restored.  If the operations do not commute,
the active 960-body geometry can return on a different branch even though the
endpoint charges are identical.

At the base point, every loop corner, and the final endpoint, project to genuine
N=960 by deleting either distinguished label and restoring unit charges on all
remaining particles.  This is a 2-D path-dependence test, not a denser lambda
scan.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from collections import Counter

import numpy as np

import search_live_size_bounce as sbounce
import search_size_beam as sbeam
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_n961_occupancy_exchange import classify, sig_json

I886 = 886
I960 = 960


def kabsch_rms(ref: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    H = x.T @ ref
    U, _, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1.0
        R = U @ Vt
    y = x @ R
    d = np.linalg.norm(y - ref, axis=1)
    return float(np.sqrt(np.mean(d * d))), float(np.max(d))


def project(x: np.ndarray, delete_idx: int, live: float, maxiter: int):
    z = np.delete(x, int(delete_idx), axis=0)
    e, y, nit, ok = sbeam.stable_relax(z, maxiter)
    return {
        'delete_index': int(delete_idx),
        'energy': float(e),
        'delta_live': float(e-live),
        'class': classify(e, live),
        'signature': sig_json(y),
        'nit': int(nit),
        'success': bool(ok),
        'points': y.tolist(),
    }


def linear_segment(a: tuple[float,float], b: tuple[float,float], steps: int):
    for j in range(1, steps+1):
        u = j / steps
        yield ((1-u)*a[0] + u*b[0], (1-u)*a[1] + u*b[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('A_json')
    ap.add_argument('--q960-peak', type=float, required=True,
                    help='rectangle peak q960, starting from endpoint q960=0')
    ap.add_argument('--q886-floor', type=float, required=True,
                    help='rectangle floor q886, starting from endpoint q886=1')
    ap.add_argument('--orientation', choices=['886-first','960-first'], required=True)
    ap.add_argument('--segment-steps', type=int, default=5)
    ap.add_argument('--fade-schedule', default='1,.8,.6,.4,.25,.15,.1,.05,.02,0')
    ap.add_argument('--live-score', type=float, required=True)
    ap.add_argument('--hub-maxiter', type=int, default=3200)
    ap.add_argument('--weighted-maxiter', type=int, default=1800)
    ap.add_argument('--project-maxiter', type=int, default=3200)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    peak = float(args.q960_peak); floor = float(args.q886_floor)
    if not (0 <= peak <= 1 and 0 <= floor <= 1):
        raise ValueError('occupancies must lie in [0,1]')
    if args.segment_steps < 1:
        raise ValueError('segment-steps must be >=1')

    _, A = sbounce.load_points(pathlib.Path(args.A_json))
    vc = sbounce.voronoi_candidates(A); sel = vc[3]
    hub = sbounce.relax(np.vstack([A, np.asarray(sel['point'])[None,:]]), args.hub_maxiter)
    x = np.asarray(hub['points'], float)
    if abs(hub['energy'] - 445303.247369582) > 5e-4:
        raise RuntimeError(f'unexpected hub energy {hub["energy"]}')
    print('HUB', f"{hub['energy']:.12f}", 'tri', sel['triangle'], flush=True)

    fade = [float(z) for z in args.fade_schedule.split(',') if z.strip()]
    if not fade or abs(fade[0]-1) > 1e-12 or abs(fade[-1]) > 1e-12:
        raise ValueError('fade schedule must run from 1 to 0')
    if any(fade[i+1] > fade[i] + 1e-14 for i in range(len(fade)-1)):
        raise ValueError('fade schedule must decrease')

    trace = []
    for q960 in fade:
        charges = np.ones(961, float); charges[I886] = 1.0; charges[I960] = q960
        ew, x, nit, ok, msg, grms = stable_weighted_relax(x, charges, args.weighted_maxiter)
        trace.append({'stage':'fade','q886':1.0,'q960':q960,'weighted_energy':float(ew),
                      'gradient_rms':float(grms),'nit':int(nit),'success':bool(ok)})
        print('FADE', q960, f'{ew:.12f}', f'grms={grms:.3g}', 'nit', nit, flush=True)

    xbase = x.copy()
    base_active = np.delete(xbase, I960, axis=0)
    projections = []
    for di in (I886, I960):
        pr = project(xbase, di, args.live_score, args.project_maxiter)
        pr.update({'stage':'base','corner':0,'q886':1.0,'q960':0.0})
        projections.append(pr)
        print('PROJECT base', di, pr['class'], f"{pr['energy']:.12f}", f"d={pr['delta_live']:+.9g}", flush=True)

    p0 = (1.0, 0.0)
    p1 = (floor, 0.0)
    p2 = (floor, peak)
    p3 = (1.0, peak)
    if args.orientation == '886-first':
        corners = [p0, p1, p2, p3, p0]
    else:
        corners = [p0, p3, p2, p1, p0]

    corner_records = []
    step_index = 0
    for c in range(4):
        for q886, q960 in linear_segment(corners[c], corners[c+1], args.segment_steps):
            step_index += 1
            charges = np.ones(961, float); charges[I886] = q886; charges[I960] = q960
            ew, x, nit, ok, msg, grms = stable_weighted_relax(x, charges, args.weighted_maxiter)
            rec = {'stage':'loop','segment':c,'step_index':step_index,'q886':float(q886),'q960':float(q960),
                   'weighted_energy':float(ew),'gradient_rms':float(grms),'nit':int(nit),'success':bool(ok)}
            trace.append(rec)
            print('STEP', c, step_index, f'q886={q886:.6g}', f'q960={q960:.6g}',
                  f'Ew={ew:.12f}', f'grms={grms:.3g}', 'nit', nit, flush=True)
        qr = corners[c+1]
        rms, mx = kabsch_rms(base_active, np.delete(x, I960, axis=0))
        cr = {'corner':c+1,'q886':float(qr[0]),'q960':float(qr[1]),
              'active_rms_vs_base':rms,'active_max_vs_base':mx,
              'sig_del886':sig_json(np.delete(x,I886,axis=0)),
              'sig_del960':sig_json(np.delete(x,I960,axis=0))}
        corner_records.append(cr)
        print('CORNER', c+1, qr, f'active_rms={rms:.6g}', f'max={mx:.6g}', flush=True)
        for di in (I886, I960):
            pr = project(x, di, args.live_score, args.project_maxiter)
            pr.update({'stage':'corner','corner':c+1,'q886':float(qr[0]),'q960':float(qr[1])})
            projections.append(pr)
            print('PROJECT corner', c+1, 'del', di, pr['class'], f"{pr['energy']:.12f}",
                  f"d={pr['delta_live']:+.9g}", flush=True)

    end_active = np.delete(x, I960, axis=0)
    end_rms, end_max = kabsch_rms(base_active, end_active)
    endpoint = {'q886':1.0,'q960':0.0,'active_rms_vs_base':end_rms,'active_max_vs_base':end_max,
                'sig_del886':sig_json(np.delete(x,I886,axis=0)),
                'sig_del960':sig_json(end_active)}
    final_projs = [p for p in projections if p['stage']=='corner' and p['corner']==4]
    best = min(projections, key=lambda r:r['energy'])
    distinct = []
    for p in sorted(projections, key=lambda r:r['energy']):
        if any(abs(p['energy']-z['energy'])<2e-7 and p['signature']['coord']==z['signature']['coord'] for z in distinct):
            continue
        z = {k:v for k,v in p.items() if k!='points'}
        distinct.append(z)
    out = {'live_score':float(args.live_score),'hub_energy':float(hub['energy']),'hub_triangle':sel['triangle'],
           'q960_peak':peak,'q886_floor':floor,'orientation':args.orientation,
           'segment_steps':args.segment_steps,'trace':trace,'corners':corner_records,'endpoint':endpoint,
           'projections':projections,'distinct_projection_summary':distinct,
           'best_projection':{k:v for k,v in best.items() if k!='points'}}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best['energy'] < args.live_score - 2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(best,separators=(',',':'))+'\n')


if __name__ == '__main__':
    main()
