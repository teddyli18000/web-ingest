#!/usr/bin/env python3
"""Spherical string / climbing-image search between two frozen N=960 minima.

This is the generic form of string_record_neighbor.py.  Endpoints are JSON files
containing a 960x3 `points` array and must have a meaningful pointwise
correspondence (as A and B do, since both descend from the same record labeling).
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np

import string_record_neighbor as sr


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=960:
        raise ValueError(f'{path}: expected 960 points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None],d


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('left_json'); ap.add_argument('right_json')
    ap.add_argument('--images',type=int,default=7)
    ap.add_argument('--iterations',type=int,default=180)
    ap.add_argument('--eta',type=float,default=2.5e-4)
    ap.add_argument('--max-step',type=float,default=7e-4)
    ap.add_argument('--climb-iterations',type=int,default=120)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    L,Lmeta=load_seed(args.left_json); R,Rmeta=load_seed(args.right_json)
    images=sr.interpolate_endpoints(L,R,args.images); hist=[]
    for it in range(args.iterations):
        vals=[]; grads=[]
        for x in images:
            E,g=sr.energy_grad(x); vals.append(E); grads.append(g)
        maxstep=0.0; new=[images[0]]
        for i in range(1,len(images)-1):
            y,s=sr.capped_descent(images[i],grads[i],args.eta,args.max_step)
            new.append(y); maxstep=max(maxstep,s)
        new.append(images[-1]); images,total=sr.reparameterize(new)
        if it%10==0 or it==args.iterations-1:
            imax=int(np.argmax(vals)); barrier=max(vals)-min(vals[0],vals[-1])
            print(f'iter={it} maxE={max(vals):.12f} imax={imax} barrier={barrier:.9g} arc={total:.6g} step={maxstep:.3e}',flush=True)
            hist.append({'iteration':it,'energies':vals,'max_index':imax,'arc':total,'max_step':maxstep})

    vals=[sr.energy_grad(x)[0] for x in images]; imax=int(np.argmax(vals))
    if imax in (0,len(images)-1): raise RuntimeError('maximum collapsed to endpoint')
    saddle=images[imax].copy(); climb=[]
    for it in range(args.climb_iterations):
        E,g=sr.energy_grad(saddle); tmp=images.copy(); tmp[imax]=saddle
        tau=sr.path_tangent(tmp,imax)
        saddle,s=sr.climb_step(saddle,g,tau,args.eta,args.max_step*0.7)
        grms=float(np.sqrt(np.mean(np.sum(g*g,axis=1))))
        if it%10==0 or it==args.climb_iterations-1:
            print(f'climb={it} E={E:.12f} grad_rms={grms:.6g} step={s:.3e}',flush=True)
            climb.append({'iteration':it,'energy':E,'grad_rms':grms,'step':s})

    Es,gs=sr.energy_grad(saddle); grms=float(np.sqrt(np.mean(np.sum(gs*gs,axis=1))))
    out={'left_json':str(args.left_json),'right_json':str(args.right_json),
         'left_energy':sr.energy_grad(L)[0],'right_energy':sr.energy_grad(R)[0],
         'images':args.images,'iterations':args.iterations,
         'path_energies':[sr.energy_grad(x)[0] for x in images],
         'max_image_index':imax,'history':hist,'climbing_energy':Es,
         'climbing_gradient_rms':grms,'climb_history':climb,
         'saddle_points':saddle.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
