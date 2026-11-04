#!/usr/bin/env python3
"""Test two-dimensional saddle-sheet holonomy in the N961 charge simplex.

For a fixed ray radius s, read independently continued saddles from two
different occupancy rays. Continue each index-one root to the SAME midpoint
occupancy by Newton-MINRES, without interpolating its geometry toward the
opposite solution. Compare the two final stationary roots after labelled
Kabsch alignment, independently check their Hessian indices, and delete
individual fractional particles to look for real N960 basins. Distinct
roots at identical charges would demonstrate multiple saddle sheets.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

import diagnose_soft_modes as sm
import refine_n961_weighted_saddle as rf
import search_soft_pair as sp
import search_size_beam as sbeam
from search_n961_occupancy_exchange import sig_json
from search_n961_simplex_sheet_crossing import kabsch_align
from search_n961_three_occupancy_simplex import LABELS, classify
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from continue_n961_weighted_saddle_simplex import ray_charges, correct, state


def read_branch(root, label):
    text=(root / f'thomson-weighted-saddle-ray-{label}' / 'branch.json').read_text()
    return json.JSONDecoder().raw_decode(text)[0]


def load_saddle(branch, s):
    matches=[r for r in branch['rows'] if r['s']==s and r['status']=='index_one']
    assert len(matches)==1, (branch['zero_label'],s,len(matches))
    x=np.asarray(matches[0]['saddle_points'],float)
    assert x.shape==(961,3)
    return sm.xyz_to_vars(x)


def project_960(x, label, live, maxiter, outdir, tag):
    e, y, nit, ok=sbeam.stable_relax(np.delete(x,label,axis=0),maxiter)
    row={'label':label,'energy':float(e),'delta_live':float(e-live),
         'class':classify(e,live),'success':bool(ok),'nit':int(nit),
         'coord':sig_json(y)['coord']}
    if e<live-2e-7:
        fname=tag+f'-del{label}-candidate.json'
        (outdir/fname).write_text(json.dumps({'points':y.tolist(),'energy':e,
                                               'delete_label':label,'source':tag})+'\n')
        row['candidate_file']=fname
    return row


def continue_side(q0,c_start,c_end,nsteps,maxnewton,cap,gtol,tag):
    q=q0.copy()
    hist=[]
    progress=0.0
    target=1.0/nsteps
    while progress<1-1e-12:
        frac=min(target,1.0)
        c=(1-frac)*c_start+frac*c_end
        qt,nh,ok=correct(q,c,gtol,maxnewton,cap)
        e,g,r=state(qt,c)
        if ok:
            hist.append({'fraction':frac,'energy':e,'grms':r,
                         'correction_steps':len(nh),'accepted':True})
            q=qt
            progress=frac
            target=min(1.0,progress+1.0/nsteps)
            print(tag,'ACCEPT',frac,f'E={e:.12f}',f'grad={r:.4g}',flush=True)
        else:
            newstep=(frac-progress)/2
            hist.append({'fraction':frac,'energy':e,'grms':r,
                         'correction_steps':len(nh),'accepted':False})
            print(tag,'RETRY',frac,'grad',r,'halfstep',newstep,flush=True)
            if newstep<0.002:
                return q,hist,False
            target=progress+newstep
    return q,hist,True


def release_sides(q,c,mode,tag,outdir,live,project_maxiter):
    rows=[]
    for sign in (-1,1):
        qs=sp.exp_perturb(q,sign*mode,0.0002)
        xs=sm.vars_to_xyz(qs)[0]
        ew,y,nit,ok,msg,grms=stable_weighted_relax(xs,c,2400)
        projs=[project_960(y,lab,live,project_maxiter,outdir,
                           tag+f'-sign{sign}') for lab in LABELS]
        rows.append({'sign':sign,'weighted_energy':ew,'gradient_rms':grms,
                     'nit':nit,'ok':ok,'projections':projs})
        print(tag,'RELEASE',sign,f'Ew={ew:.12f}',
              [(p['label'],p['class'],round(p['delta_live'],9)) for p in projs],
              flush=True)
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('artifacts')
    ap.add_argument('--a',type=int,choices=LABELS,required=True)
    ap.add_argument('--b',type=int,choices=LABELS,required=True)
    ap.add_argument('--s',type=float,required=True)
    ap.add_argument('--nsteps',type=int,default=6)
    ap.add_argument('--newton-max',type=int,default=28)
    ap.add_argument('--gradient-tol',type=float,default=4e-5)
    ap.add_argument('--step-cap',type=float,default=0.004)
    ap.add_argument('--project-maxiter',type=int,default=3600)
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    assert args.a!=args.b
    root=pathlib.Path(args.artifacts)
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    ds=[read_branch(root,l) for l in (args.a,args.b)]
    cs=[ray_charges(l,args.s) for l in (args.a,args.b)]
    mid=(cs[0]+cs[1])/2
    assert abs(float(np.sum(mid))-960)<1e-9
    assert np.min(mid)>=0
    rows=[]
    for i,lab in enumerate((args.a,args.b)):
        q0=load_saddle(ds[i],args.s)
        e,g,grms=state(q0,cs[i])
        assert grms<args.gradient_tol
        print('START',lab,'s',args.s,'E',e,'grad',grms,
              'charges',[float(cs[i][j]) for j in LABELS],flush=True)
        q,hist,ok=continue_side(q0,cs[i],mid,args.nsteps,args.newton_max,
                                args.step_cap,args.gradient_tol,str(lab))
        e,g,grms=state(q,mid)
        row={'start_label':lab,'complete':bool(ok),'energy':e,
             'gradient_rms':grms,'history':hist}
        if ok:
            vals,V,Q,diagnostics,ncalls=rf.lowest(q,mid,8,tol=8e-6)
            row['hessian_eigenvalues']=[float(x) for x in vals]
            row['ritz_residuals']=[r['ritz_residual'] for r in diagnostics]
            row['negative_modes']=int(np.sum(vals<-1e-3))
            row['saddle_points']=sm.vars_to_xyz(q)[0].tolist()
            print('FINAL',lab,'E',e,'grad',grms,'lows',vals[:5],
                  'negative',row['negative_modes'],flush=True)
            x=sm.vars_to_xyz(q)[0]
            row['projections']=[project_960(x,j,args.live_score,
                                      args.project_maxiter,outdir,
                                      f'mid{args.s}-{args.a}-{args.b}-from{lab}')
                                for j in LABELS]
            row['_mode']=V[:,0].tolist()
        rows.append(row)
        if not ok: print('INCOMPLETE',lab,'at',hist[-1],flush=True)
    comparable=all(r['complete'] for r in rows)
    comparison=None
    if comparable:
        xa=np.asarray(rows[0]['saddle_points'],float)
        xb=np.asarray(rows[1]['saddle_points'],float)
        y,rms,maxdiff=kabsch_align(xa,xb)
        gap=abs(rows[0]['energy']-rows[1]['energy'])
        is_distinct=gap>2e-5 or rms>2e-4
        comparison={'energy_gap':gap,'kabsch_rms_chord':rms,
                    'kabsch_max_chord':maxdiff,'different_stationary_roots':is_distinct,
                    'both_index_one':all(r['negative_modes']==1 for r in rows)}
        print('COMPARE',args.a,args.b,'s',args.s,comparison,flush=True)
        for row in rows if is_distinct else rows[:1]:
            q=sm.xyz_to_vars(np.asarray(row['saddle_points'],float))
            mode=np.asarray(row.pop('_mode'),float)
            mode/=np.linalg.norm(mode)
            row['unstable_sides']=release_sides(q,mid,mode,
                f'mid{args.s}-{args.a}-{args.b}-from{row["start_label"]}',
                outdir,args.live_score,args.project_maxiter)
    for row in rows:
        row.pop('_mode',None)
    output={'a':args.a,'b':args.b,'s':args.s,'mid_charges':[float(mid[j]) for j in LABELS],
            'rows':rows,'comparison':comparison,'source_run':41719943255,
            'live_score':args.live_score}
    (outdir/'result.json').write_text(json.dumps(output,separators=(',',':'))+'\n')


if __name__=='__main__':
    main()
