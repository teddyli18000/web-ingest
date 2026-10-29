#!/usr/bin/env python3
"""Recursively resolve a transition-state maximum that collapses into a string endpoint.

For very shallow Thomson barriers, a converged coarse string can have every
interior image below the higher-energy endpoint even though a true saddle lies
inside the final segment.  This tool repeatedly zooms into the endpoint-adjacent
segment, rebuilds a denser local string, and minimizes only the gradient
component perpendicular to the path.  Once an interior maximum is resolved, it
is emitted in the same `saddle_points` format consumed by refine_saddle_hybrid.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np

import string_record_neighbor as sr
from string_between_seeds import load_seed, path_diagnostics


def optimize_segment(L,R,nimages,iters,eta,max_step):
    images=sr.interpolate_endpoints(L,R,nimages)
    hist=[]
    for it in range(iters):
        vals,perps,grads=path_diagnostics(images)
        new=[images[0]]; ms=0.0
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,s=sr.capped_descent(images[i],gp,eta,max_step)
            new.append(y); ms=max(ms,s)
        new.append(images[-1]); images,arc=sr.reparameterize(new)
        if it%20==0 or it==iters-1:
            vals2,perps2,_=path_diagnostics(images)
            imax=int(np.argmax(vals2)); mp=max(perps2) if perps2 else 0.0
            print(f'iter={it} max={max(vals2):.12f} imax={imax} arc={arc:.7g} step={ms:.3e} perp={mp:.6g}',flush=True)
            hist.append({'iteration':it,'max_index':imax,'energies':vals2,'arc':arc,
                         'max_step':ms,'max_perpendicular_gradient_rms':mp})
    vals,perps,_=path_diagnostics(images)
    return images,vals,perps,hist


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('left_json'); ap.add_argument('right_json')
    ap.add_argument('--images',type=int,default=17); ap.add_argument('--iterations',type=int,default=180)
    ap.add_argument('--levels',type=int,default=4); ap.add_argument('--eta',type=float,default=2e-4)
    ap.add_argument('--max-step',type=float,default=2.5e-4); ap.add_argument('--out',required=True)
    args=ap.parse_args()
    L,_=load_seed(args.left_json); R,_=load_seed(args.right_json)
    original_L=L.copy(); original_R=R.copy(); levels=[]; resolved=False
    chosen=None; chosen_vals=None; chosen_perps=None; chosen_imax=None
    for lev in range(args.levels):
        print(f'LEVEL {lev} endpoint_distance={sr.rms_geo(L,R):.9g}',flush=True)
        images,vals,perps,hist=optimize_segment(L,R,args.images,args.iterations,args.eta,args.max_step)
        imax=int(np.argmax(vals)); collapsed=imax in (0,len(images)-1)
        row={'level':lev,'left_energy':vals[0],'right_energy':vals[-1],'max_energy':max(vals),
             'max_index':imax,'endpoint_collapsed':collapsed,'rms_span':sr.rms_geo(L,R),
             'path_energies':vals,'max_perpendicular_gradient_rms':max(perps) if perps else 0.0,
             'history':hist}
        levels.append(row)
        print(f'LEVEL {lev} done max={max(vals):.12f} imax={imax} collapsed={collapsed}',flush=True)
        chosen,chosen_vals,chosen_perps,chosen_imax=images,vals,perps,imax
        if not collapsed:
            resolved=True; break
        if imax==0:
            # The unresolved saddle is inside the first segment.
            R=images[1].copy(); L=images[0].copy()
        else:
            # The unresolved saddle is inside the final segment.
            L=images[-2].copy(); R=images[-1].copy()

    if resolved:
        probe=chosen_imax
    else:
        # Keep the interior point adjacent to the endpoint maximum as the safest
        # minimum-mode seed even if the requested zoom depth did not fully resolve it.
        probe=1 if chosen_imax==0 else len(chosen)-2
    saddle=chosen[probe]
    E,g=sr.energy_grad(saddle)
    grms=float(np.sqrt(np.mean(np.sum(g*g,axis=1))))
    out={'left_json':str(args.left_json),'right_json':str(args.right_json),
         'original_left_energy':sr.energy_grad(original_L)[0],
         'original_right_energy':sr.energy_grad(original_R)[0],
         'resolved_interior_maximum':resolved,'levels':levels,
         'final_level_max_index':chosen_imax,'probe_index':probe,
         'probe_energy':E,'probe_gradient_rms':grms,
         'final_path_energies':chosen_vals,
         'final_path_perpendicular_gradient_rms':chosen_perps,
         'path_points':[x.tolist() for x in chosen],
         'saddle_points':saddle.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
