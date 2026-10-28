#!/usr/bin/env python3
"""Reproducibly harvest the low-lying +0.00328 neighbor of the live p007 record.

Uses the canonicalized softest C3-breaking Hessian doublet from
search_soft_pair.py, phase 0, with a small geodesic push. The first scan showed
that the record basin boundary is near 0.008 rad RMS and repeatedly lands in a
minimum ~0.003280 above the record. This script freezes one coordinate
realization for second-hop basin-graph exploration.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("--amp",type=float,default=0.010)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.few_shots)
    live_score,shot=sm.find_live(root)
    x0=sm.load_cert(shot/"certificate.json")
    q0=sm.xyz_to_vars(x0)
    e0,_=sm.fg(q0)
    H,raw,Qrot,calls=sm.build_hessian(q0,3e-6,1e6)
    rng=np.random.default_rng(20261027)
    v0=rng.normal(size=len(q0)); v0-=Qrot@(Qrot.T@v0)
    vals,vecs=eigsh(H,k=6,which="SA",tol=2e-5,maxiter=500,ncv=40,v0=v0)
    order=np.argsort(vals); vals=vals[order]; vecs=vecs[:,order]
    V=vecs[:,:2].copy(); V-=Qrot@(Qrot.T@V); V,_=np.linalg.qr(V)
    V,M,resid,anchor_idx,anchor_comp,maperr=sp.canonicalize_pair(V,q0)
    qs=sp.exp_perturb(q0,V[:,0],args.amp)
    start_e,_=sm.fg(qs)
    e,x,nit,ok=sp.relax_q(qs,1600)
    delta=e-e0
    print(f"live={shot.relative_to(root)} score={live_score:.10f} base={e0:.12f}")
    print(f"lambda0={vals[0]:.12g} lambda1={vals[1]:.12g} amp={args.amp:.6f}")
    print(f"start={start_e:.12f} relaxed={e:.12f} delta={delta:.12g} nit={nit} ok={ok}")
    print("c3_pair_matrix="+np.array2string(M,precision=9)+f" resid={resid:.3e} maperr={maperr:.3e}")
    if not (5e-4 < delta < 2e-2):
        raise RuntimeError(f"did not reach expected low neighbor; delta={delta}")
    out={
      "source_shot":str(shot.relative_to(root)),"source_verifier_score":live_score,
      "base_double_energy":e0,"neighbor_double_energy":e,"delta":delta,
      "amp":args.amp,"pair_eigenvalues":[float(vals[0]),float(vals[1])],
      "c3_pair_matrix":M.tolist(),"c3_subspace_residual":resid,
      "canonical_anchor_point":anchor_idx,"canonical_anchor_component":anchor_comp,
      "relax_iterations":nit,"relax_success":ok,"points":x.tolist()
    }
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(",",":"))+"\n")

if __name__=="__main__": main()
