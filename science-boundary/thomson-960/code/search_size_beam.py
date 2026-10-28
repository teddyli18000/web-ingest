#!/usr/bin/env python3
"""Multi-step neighboring-size beam search for Thomson N=960.

Extends the one-cycle Amore-Wales-style size oscillation to several consecutive
particle insertions/removals before returning to N=960.  At every intermediate
N, branch over several high-contribution removals or low-potential spherical
Voronoi insertions, fully relax, deduplicate by energy, and keep a small beam of
the lowest distinct minima. This allows two/three defect-rearrangement events
to accumulate before returning to the target size.

Routes:
  down: 960 -> 960-depth -> 960
  up:   960 -> 960+depth -> 960

Requires numpy/scipy. All local minimizations use stable termwise pair-energy
differences accumulated in long double.
"""
from __future__ import annotations
import argparse, json, math, pathlib, re
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import ConvexHull

PI=math.pi
P007=pathlib.Path('problems/p007-thomson-problem')

def find_live(root):
    best=None
    for md in (root/P007/'shots').glob('*/*/SHOT.md'):
        m=re.search(r'^claimed_score\s*=\s*"([0-9.]+)"',md.read_text(),re.M)
        if m:
            item=(float(m.group(1)),md.parent)
            if best is None or item[0]<best[0]: best=item
    if best is None: raise RuntimeError('no merged p007 shot')
    return best

def load_cert(path):
    d=json.loads(path.read_text()); x=np.array([[a/q,b/q,c/q] for a,b,c,q in d['points']],float)
    return x/np.linalg.norm(x,axis=1)[:,None]
def xyz_to_vars(x):
    return np.column_stack([np.arccos(np.clip(x[:,2],-1,1)),np.arctan2(x[:,1],x[:,0])]).ravel()
def vars_to_xyz(v):
    a=v.reshape(-1,2); th,ph=a[:,0],a[:,1]; st,ct=np.sin(th),np.cos(th); cp,sp=np.cos(ph),np.sin(ph)
    x=np.column_stack([st*cp,st*sp,ct]); dth=np.column_stack([ct*cp,ct*sp,-st]); dph=np.column_stack([-st*sp,st*cp,np.zeros_like(st)])
    return x,dth,dph

def terms_grad(v):
    x,dth,dph=vars_to_xyz(v); n=len(x); dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0); ga=w@x
    gt=np.sum(ga*dth,axis=1); gp=np.sum(ga*dph,axis=1); tri=np.triu_indices(n,1)
    return inv[tri],np.column_stack([gt,gp]).ravel(),x
def stable_relax(x0,maxiter=1300):
    q0=xyz_to_vars(x0); ref,_,_=terms_grad(q0); ref=np.asarray(ref,np.longdouble); E0=float(np.sum(ref,dtype=np.longdouble)); n=len(x0)
    def fg(q):
        t,g,_=terms_grad(q); return float(np.sum(np.asarray(t,np.longdouble)-ref,dtype=np.longdouble)),g
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':70,'maxcor':35})
    de,_=fg(r.x); x,_,_=vars_to_xyz(r.x); return E0+de,x,int(r.nit),bool(r.success)
def energy_contrib(x):
    d=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*d,1e-300); np.fill_diagonal(r2,np.inf); inv=1/np.sqrt(r2)
    return np.sum(inv,axis=1)
def insertion_sites(x):
    h=ConvexHull(x); sites=[]
    for tri in h.simplices:
        a,b,c=x[tri]; n=np.cross(b-a,c-a); nn=np.linalg.norm(n)
        if nn<1e-14: continue
        n=n/nn
        if float(n@a)<0: n=-n
        sites.append(n)
    y=np.array(sites); vals=np.empty(len(y))
    for lo in range(0,len(y),300):
        z=y[lo:lo+300]; dots=np.clip(z@x.T,-1,1); vals[lo:lo+len(z)]=np.sum(1/np.sqrt(np.maximum(2-2*dots,1e-15)),axis=1)
    return y,vals

def branch_remove(state,p,tag):
    E,x,hist=state; c=energy_contrib(x); ids=np.argsort(c)[-p:][::-1]; out=[]
    for rank,j in enumerate(ids):
        y=np.delete(x,int(j),axis=0); e,z,nit,ok=stable_relax(y)
        h=hist+[{'move':'remove','index':int(j),'rank':rank,'pre_contrib':float(c[j]),'energy':e,'n':len(z)}]
        print(f'{tag} remove rank={rank} idx={j} n={len(z)} E={e:.12f} nit={nit} ok={ok}',flush=True); out.append((e,z,h))
    return out
def branch_insert(state,p,tag):
    E,x,hist=state; sites,vals=insertion_sites(x); ids=np.argsort(vals)[:p]; out=[]
    for rank,j in enumerate(ids):
        y=np.vstack([x,sites[j]]); e,z,nit,ok=stable_relax(y)
        h=hist+[{'move':'insert','site':int(j),'rank':rank,'pre_potential':float(vals[j]),'energy':e,'n':len(z)}]
        print(f'{tag} insert rank={rank} site={j} n={len(z)} E={e:.12f} nit={nit} ok={ok}',flush=True); out.append((e,z,h))
    return out
def dedup_keep(states,beam,tol=2e-7):
    states=sorted(states,key=lambda s:s[0]); keep=[]
    for s in states:
        if all(abs(s[0]-q[0])>tol for q in keep): keep.append(s)
        if len(keep)>=beam: break
    return keep

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--route',choices=['down','up'],required=True); ap.add_argument('--depth',type=int,default=2); ap.add_argument('--branch',type=int,default=3); ap.add_argument('--beam',type=int,default=2); ap.add_argument('--out',required=True)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots); live_score,shot=find_live(root); x=load_cert(shot/'certificate.json'); E0,x,nit,ok=stable_relax(x,900)
    print(f'live={shot.relative_to(root)} verifier={live_score:.10f} polished={E0:.12f} route={args.route} depth={args.depth} branch={args.branch} beam={args.beam}',flush=True)
    beam=[(E0,x,[])]
    outward='remove' if args.route=='down' else 'insert'; inward='insert' if args.route=='down' else 'remove'
    for step in range(args.depth):
        cand=[]
        for b,state in enumerate(beam): cand+=(branch_remove(state,args.branch,f'out{step+1}/b{b}') if outward=='remove' else branch_insert(state,args.branch,f'out{step+1}/b{b}'))
        beam=dedup_keep(cand,args.beam); print('KEEP outward',step+1,[(len(s[1]),s[0]) for s in beam],flush=True)
    for step in range(args.depth):
        cand=[]
        for b,state in enumerate(beam): cand+=(branch_remove(state,args.branch,f'in{step+1}/b{b}') if inward=='remove' else branch_insert(state,args.branch,f'in{step+1}/b{b}'))
        beam=dedup_keep(cand,args.beam); print('KEEP inward',step+1,[(len(s[1]),s[0]) for s in beam],flush=True)
    finals=[s for s in beam if len(s[1])==960]
    if not finals: raise RuntimeError('beam did not return to N=960')
    best=min(finals,key=lambda s:s[0]); E,x,hist=best; imp=E0-E
    print(f'BEST E960={E:.12f} improvement_vs_polished={imp:.12g} delta_vs_live={E-live_score:+.12g}',flush=True)
    out={'route':args.route,'depth':args.depth,'branch':args.branch,'beam':args.beam,'live_score':live_score,'polished_live_energy':E0,'best_float_energy':E,'improvement':imp,'delta_vs_live':E-live_score,'history':hist,'final_beam':[{'energy':s[0],'history':s[2]} for s in finals],'best_points':x.tolist() if E<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
