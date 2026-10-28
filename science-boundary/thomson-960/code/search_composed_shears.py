#!/usr/bin/env python3
"""Compose the three C3-equivalent global R->A shear events nonlinearly.

R is the live C3 record. A is the durable symmetry-broken +0.003280 neighbor
found by the softest full-space Hessian doublet and independently by size
oscillation. Because R is C3 symmetric, the full nonlinear pointwise log-map
R->A has two group-equivalent copies T v and T^2 v. A single event reaches one
A variant. This program asks what happens when two/three equivalent *global*
shear events are accumulated, a route not covered by linear mode kicks.

Two constructions are tested:
- simultaneous: exponentiate a signed sum of event fields at R;
- sequential: apply events one at a time, parallel-transporting each tangent
  field from R to the current configuration before the next exponential map.

Every start is fully relaxed without symmetry using a stable termwise pair
energy-difference objective. Requires numpy/scipy.
"""
from __future__ import annotations
import argparse, json, math, pathlib, re
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree, ConvexHull

PI=math.pi
N=960


def find_live(root):
    best=None
    for md in (root/'problems/p007-thomson-problem/shots').glob('*/*/SHOT.md'):
        m=re.search(r'^claimed_score\s*=\s*"([0-9.]+)"',md.read_text(),re.M)
        if m:
            item=(float(m.group(1)),md.parent)
            if best is None or item[0]<best[0]: best=item
    if best is None: raise RuntimeError('no merged p007 shot')
    return best


def cert_xyz(path):
    d=json.loads(path.read_text()); x=np.array([[a/q,b/q,c/q] for a,b,c,q in d['points']],float)
    return x/np.linalg.norm(x,axis=1)[:,None]

def float_xyz(path):
    d=json.loads(path.read_text()); p=d.get('points') if isinstance(d,dict) else d
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]

def rz(a):
    c,s=math.cos(a),math.sin(a); return np.array([[c,-s,0.],[s,c,0.],[0.,0.,1.]])

def logmap(x,y):
    dot=np.clip(np.sum(x*y,axis=1),-1,1); th=np.arccos(dot)
    w=y-dot[:,None]*x; nw=np.linalg.norm(w,axis=1); v=np.zeros_like(x); m=nw>1e-14
    v[m]=w[m]*(th[m]/nw[m])[:,None]; return v

def expmap(x,v):
    a=np.linalg.norm(v,axis=1); y=np.empty_like(x); m=a>1e-14
    y[~m]=x[~m]; y[m]=np.cos(a[m,None])*x[m]+np.sin(a[m,None])*v[m]/a[m,None]
    return y/np.linalg.norm(y,axis=1)[:,None]

def parallel_transport(x,y,v):
    # Exact shortest-geodesic parallel transport on unit sphere.
    den=1.0+np.sum(x*y,axis=1)
    if np.min(den)<1e-5: raise RuntimeError('near-antipodal transport')
    coef=np.sum(v*y,axis=1)/den
    out=v-coef[:,None]*(x+y)
    # remove tiny numerical radial leakage at y
    out-=np.sum(out*y,axis=1)[:,None]*y
    return out

def group_events(R,A):
    v0=logmap(R,A); tree=cKDTree(R); out=[v0]; maperrs=[]
    for k in (1,2):
        M=rz(2*PI*k/3); rot=R@M.T; dist,dest=tree.query(rot,k=1)
        if len(np.unique(dest))!=N or float(np.max(dist))>2e-7:
            raise RuntimeError(f'C3 map failed k={k} max={np.max(dist)}')
        v=np.zeros_like(v0); v[dest]=v0@M.T; out.append(v); maperrs.append(float(np.max(dist)))
    return out,maperrs

def xyz_to_vars(x):
    return np.column_stack([np.arccos(np.clip(x[:,2],-1,1)),np.arctan2(x[:,1],x[:,0])]).ravel()
def vars_to_xyz(v):
    a=v.reshape(-1,2); th,ph=a[:,0],a[:,1]; st,ct=np.sin(th),np.cos(th); cp,sp=np.cos(ph),np.sin(ph)
    x=np.column_stack([st*cp,st*sp,ct]); dth=np.column_stack([ct*cp,ct*sp,-st]); dph=np.column_stack([-st*sp,st*cp,np.zeros_like(st)])
    return x,dth,dph
TRI=np.triu_indices(N,1)
def terms_grad(q):
    x,dth,dph=vars_to_xyz(q); dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0); ga=w@x
    gt=np.sum(ga*dth,axis=1); gp=np.sum(ga*dph,axis=1)
    return inv[TRI],np.column_stack([gt,gp]).ravel(),x
def raw_energy(x):
    d=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*d,1e-300); np.fill_diagonal(r2,np.inf)
    return float(np.sum(np.asarray((1/np.sqrt(r2))[TRI],np.longdouble),dtype=np.longdouble))
def stable_relax(x0,maxiter=1700):
    q0=xyz_to_vars(x0); ref,_,_=terms_grad(q0); ref=np.asarray(ref,np.longdouble); E0=float(np.sum(ref,dtype=np.longdouble))
    def fg(q):
        t,g,_=terms_grad(q); return float(np.sum(np.asarray(t,np.longdouble)-ref,dtype=np.longdouble)),g
    bounds=[(1e-8,PI-1e-8),(None,None)]*N
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':70,'maxcor':40})
    de,_=fg(r.x); x,_,_=vars_to_xyz(r.x); return E0+de,x,int(r.nit),bool(r.success)
def coord_counts(x):
    h=ConvexHull(x); nb=[set() for _ in range(N)]
    for t in h.simplices:
        a,b,c=map(int,t); nb[a].update((b,c));nb[b].update((a,c));nb[c].update((a,b))
    z=np.array([len(s) for s in nb]); return {str(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))}

def parse_sequence(s):
    vals=[]
    for token in s.split(','):
        token=token.strip(); sign=-1 if token.startswith('-') else 1; token=token.lstrip('+-')
        k=int(token)
        if k not in (0,1,2): raise ValueError('events must be 0,1,2 with optional sign')
        vals.append((k,sign))
    return vals

def make_start(R,events,seq,scale,kind):
    if kind=='simultaneous':
        v=np.zeros_like(R)
        for k,s in seq: v+=s*events[k]
        return expmap(R,scale*v)
    X=R.copy()
    for k,s in seq:
        # event is defined at R; transport to current X before applying it.
        w=parallel_transport(R,X,s*events[k])
        X=expmap(X,scale*w)
    return X

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--neighbor-json',required=True)
    ap.add_argument('--sequence',required=True,help='comma sequence, e.g. 0,1,2 or 0,1,-2')
    ap.add_argument('--kind',choices=['simultaneous','sequential'],required=True)
    ap.add_argument('--scales',default='0.55,0.75,0.95,1.15,1.35'); ap.add_argument('--out',required=True)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots); live_score,live_dir=find_live(root)
    R=cert_xyz(live_dir/'certificate.json'); A=float_xyz(pathlib.Path(args.neighbor_json)); events,maperrs=group_events(R,A)
    seq=parse_sequence(args.sequence); scales=[float(z) for z in args.scales.split(',') if z]
    base_rms=float(np.sqrt(np.mean(np.sum(events[0]*events[0],axis=1))))
    print(f'live={live_score:.10f} kind={args.kind} seq={seq} base_event_rms={base_rms:.7g} maperrs={maperrs}',flush=True)
    rows=[]; best=1e99; bestx=None
    for scale in scales:
        X=make_start(R,events,seq,scale,args.kind); start=raw_energy(X); E,Y,nit,ok=stable_relax(X)
        cc=coord_counts(Y) if E<live_score+0.2 else None
        row={'scale':scale,'start_energy':start,'energy':E,'delta_vs_live':E-live_score,'nit':nit,'success':ok,'coord_counts':cc}
        rows.append(row); print(f'scale={scale:.3f} start={start:.9f} E={E:.12f} dlive={E-live_score:+.9g} nit={nit} coord={cc}',flush=True)
        if E<best: best=E; bestx=Y.copy()
    out={'kind':args.kind,'sequence':args.sequence,'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),
         'base_event_rms':base_rms,'c3_mapping_max_errors':maperrs,'rows':rows,'best_float_energy':best,'best_delta_vs_live':best-live_score,
         'best_points':bestx.tolist() if best<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
