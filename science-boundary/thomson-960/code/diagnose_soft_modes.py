#!/usr/bin/env python3
"""Diagnose the lowest full-space tangent Hessian modes of the live p007 record.

The Hessian is represented matrix-free by centered finite differences of the
analytic angular gradient.  We transform to an orthonormal physical tangent
coordinate y=(dtheta, sin(theta)*dphi), so eigenvalues measure curvature per
RMS angular displacement rather than per raw azimuth coordinate.  The three
rigid-rotation zero modes are lifted with a large projector penalty before
calling ARPACK.

Requires numpy/scipy.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re

import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

P007 = pathlib.Path("problems/p007-thomson-problem")
PI = math.pi


def find_live(root: pathlib.Path):
    best = None
    for md in (root / P007 / "shots").glob("*/*/SHOT.md"):
        m = re.search(r'^claimed_score\s*=\s*"([0-9.]+)"', md.read_text(), re.M)
        if not m:
            continue
        item = (float(m.group(1)), md.parent)
        if best is None or item[0] < best[0]:
            best = item
    if best is None:
        raise RuntimeError("no merged p007 shot")
    return best


def load_cert(path: pathlib.Path) -> np.ndarray:
    raw = json.loads(path.read_text())
    x = np.array([[a/d, b/d, c/d] for a,b,c,d in raw["points"]], dtype=float)
    return x / np.linalg.norm(x, axis=1)[:,None]


def xyz_to_vars(x):
    th = np.arccos(np.clip(x[:,2], -1, 1))
    ph = np.arctan2(x[:,1], x[:,0])
    return np.column_stack([th,ph]).ravel()


def vars_to_xyz(v):
    a = v.reshape(-1,2)
    th, ph = a[:,0], a[:,1]
    st, ct = np.sin(th), np.cos(th)
    cp, sp = np.cos(ph), np.sin(ph)
    x = np.column_stack([st*cp, st*sp, ct])
    dth = np.column_stack([ct*cp, ct*sp, -st])
    dph = np.column_stack([-st*sp, st*cp, np.zeros_like(st)])
    return x, dth, dph


def fg(v):
    x, dth, dph = vars_to_xyz(v)
    dots = np.clip(x @ x.T, -1.0, 1.0)
    r2 = np.maximum(2.0 - 2.0*dots, 1e-300)
    np.fill_diagonal(r2, np.inf)
    inv = 1.0 / np.sqrt(r2)
    f = float(np.sum(np.triu(inv,1)))
    w = inv / r2
    np.fill_diagonal(w,0.0)
    gc = w @ x - np.sum(w,axis=1)[:,None]*x
    gt = np.sum(gc*dth,axis=1)
    gp = np.sum(gc*dph,axis=1)
    return f, np.column_stack([gt,gp]).ravel()


def physical_scale(q):
    a=q.reshape(-1,2)
    s=np.empty_like(a)
    s[:,0]=1.0
    s[:,1]=np.maximum(np.sin(a[:,0]), 1e-6)
    return s.ravel()


def rotation_basis(q):
    """Orthonormal rigid-rotation fields in physical tangent coordinates."""
    x,dth,dph=vars_to_xyz(q)
    st=np.maximum(np.linalg.norm(dph,axis=1),1e-8)
    eph=dph/st[:,None]
    cols=[]
    for axis in np.eye(3):
        dx=np.cross(np.broadcast_to(axis,x.shape),x)
        yth=np.sum(dx*dth,axis=1)
        yph=np.sum(dx*eph,axis=1)
        cols.append(np.column_stack([yth,yph]).ravel())
    R=np.column_stack(cols)
    Q,_=np.linalg.qr(R)
    return Q


def build_hessian(q0, fd_step, rot_penalty):
    n=len(q0)
    scale=physical_scale(q0)
    invs=1.0/scale
    Qrot=rotation_basis(q0)
    calls={"n":0}

    def raw_hy(y):
        yn=float(np.linalg.norm(y))
        if yn==0.0:
            return np.zeros_like(y)
        u=y/yn
        dq=invs*u
        _,gp=fg(q0 + fd_step*dq)
        _,gm=fg(q0 - fd_step*dq)
        calls["n"] += 2
        hq=(gp-gm)*(yn/(2.0*fd_step))
        return invs*hq

    def mv(y):
        z=raw_hy(np.asarray(y,dtype=float))
        # Lift the three exact rigid rotations so ARPACK returns internal modes.
        z += rot_penalty * (Qrot @ (Qrot.T @ y))
        return z

    H=LinearOperator((n,n), matvec=mv, dtype=float)
    return H, raw_hy, Qrot, calls


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("--k",type=int,default=14)
    ap.add_argument("--fd-step",type=float,default=3e-6)
    ap.add_argument("--rot-penalty",type=float,default=1e6)
    ap.add_argument("--seed",type=int,default=12345)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,shot=find_live(root)
    x=load_cert(shot/"certificate.json")
    q0=xyz_to_vars(x)
    e0,gq=fg(q0)
    scale=physical_scale(q0)
    gy=gq/scale
    H,raw_hy,Qrot,calls=build_hessian(q0,args.fd_step,args.rot_penalty)

    # Sanity check matrix symmetry in physical coordinates before eigensolving.
    rng=np.random.default_rng(args.seed)
    a=rng.normal(size=len(q0)); b=rng.normal(size=len(q0))
    a-=Qrot@(Qrot.T@a); b-=Qrot@(Qrot.T@b)
    a/=np.linalg.norm(a); b/=np.linalg.norm(b)
    Ha=raw_hy(a); Hb=raw_hy(b)
    sym_abs=abs(float(a@Hb-b@Ha))
    sym_rel=sym_abs/max(1.0,abs(float(a@Hb)),abs(float(b@Ha)))

    vals,vecs=eigsh(H,k=args.k,which="SA",tol=2e-5,maxiter=500,ncv=min(len(q0)-1,max(40,3*args.k)))
    order=np.argsort(vals); vals=vals[order]; vecs=vecs[:,order]

    rows=[]
    for j,lam in enumerate(vals):
        y=vecs[:,j]
        rot=float(np.sum((Qrot.T@y)**2))
        Hy=raw_hy(y) + args.rot_penalty*(Qrot@(Qrot.T@y))
        resid=float(np.linalg.norm(Hy-lam*y))
        rows.append({"index":j,"eigenvalue":float(lam),"rotation_overlap":rot,"residual":resid})
        print(f"mode={j:02d} lambda={lam:.12g} rot_overlap={rot:.3e} residual={resid:.3e}",flush=True)

    out={
        "live_shot":str(shot.relative_to(root)),
        "live_score":live_score,
        "double_energy":e0,
        "physical_gradient_rms":float(np.sqrt(np.mean(gy*gy))),
        "physical_gradient_max":float(np.max(np.abs(gy))),
        "fd_step":args.fd_step,
        "rotation_penalty":args.rot_penalty,
        "symmetry_abs":sym_abs,
        "symmetry_rel":sym_rel,
        "gradient_calls":calls["n"],
        "modes":rows,
    }
    print(f"live={out['live_shot']} score={live_score:.10f} Edouble={e0:.12f}")
    print(f"grad_rms={out['physical_gradient_rms']:.3e} grad_max={out['physical_gradient_max']:.3e}")
    print(f"hessian_sym_abs={sym_abs:.3e} rel={sym_rel:.3e} gradient_calls={calls['n']}")
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+"\n")

if __name__=="__main__":
    main()
