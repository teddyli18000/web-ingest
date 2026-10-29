#!/usr/bin/env python3
"""Harvest low-energy C3 stationary states starting from the old T N=960 minimum.

The Amore-Wales T structure is put into a verified C3 frame. Basin hopping then
occurs only in the 320-representative C3 orbit space. Accepted low constrained
minima are retained for later full-space Morse-index classification.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import search_c3_smooth as c3

def load_points(path):
    x=np.loadtxt(path,dtype=float)
    if x.shape!=(960,3): raise ValueError(x.shape)
    return x/np.linalg.norm(x,axis=1)[:,None]

def cubic_value(x,n): return float(np.mean((x@n)**3))
def approximate_threefold_axis(x,seed=960):
    rng=np.random.default_rng(seed); cand=rng.normal(size=(12000,3)); cand/=np.linalg.norm(cand,axis=1)[:,None]
    vals=np.abs(np.mean((x@cand.T)**3,axis=0)); n=cand[int(np.argmax(vals))]
    def f(v):
        th,ph=v; q=np.array([math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),math.cos(th)])
        return -abs(cubic_value(x,q))
    r=minimize(f,[math.acos(np.clip(n[2],-1,1)),math.atan2(n[1],n[0])],method='Nelder-Mead',options={'xatol':1e-13,'fatol':1e-15,'maxiter':2000})
    th,ph=r.x; n=np.array([math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),math.cos(th)])
    return n/np.linalg.norm(n),-float(r.fun)
def rot_axis(n,ang): return Rotation.from_rotvec(ang*np.asarray(n)/np.linalg.norm(n)).as_matrix()
def refine_symmetry_axis(x,n):
    tree=cKDTree(x); best=None
    for ang in (2*math.pi/3,-2*math.pi/3):
        R0=rot_axis(n,ang); dist,dest=tree.query(x@R0.T,k=1)
        if len(np.unique(dest))!=len(x): continue
        H=x.T@x[dest]; U,S,Vt=np.linalg.svd(H); Rrow=U@Vt
        if np.linalg.det(Rrow)<0: U[:,-1]*=-1; Rrow=U@Vt
        R=Rrow.T; vals,vecs=np.linalg.eig(R); j=int(np.argmin(np.abs(vals-1)))
        axis=np.real(vecs[:,j]); axis/=np.linalg.norm(axis)
        if axis@n<0: axis=-axis
        d2,dest2=tree.query(x@R.T,k=1)
        item=(float(np.max(d2)),float(np.sqrt(np.mean(d2*d2))),axis,R)
        if best is None or item[0]<best[0]: best=item
    if best is None: raise RuntimeError('could not recover order-3 symmetry')
    return best
def align_axis_to_z(x,axis):
    rot,_=Rotation.align_vectors(np.array([[0.,0.,1.]]),np.array([axis])); y=rot.apply(x); y/=np.linalg.norm(y,axis=1)[:,None]
    tree=cKDTree(y); dist,dest=tree.query(c3.rz(y,2*math.pi/3),k=1)
    if len(np.unique(dest))!=len(y) or float(np.max(dist))>2e-6: raise RuntimeError(f'C3 verify failed {np.max(dist)}')
    return y,float(np.max(dist)),float(np.sqrt(np.mean(dist*dist)))
def local_move(v,rng):
    a=v.reshape(-1,2).copy(); th=a[:,0]; ph=a[:,1]
    if rng.random()<0.78:
        reps,_,_=c3.vars_to_full(v); reps=reps[:len(a)]; center=reps[int(rng.integers(len(a)))]
        ang=np.arccos(np.clip(reps@center,-1,1)); radius=float(rng.uniform(0.12,0.48)); w=np.exp(-0.5*(ang/radius)**2)
        amp=float(np.exp(rng.uniform(math.log(0.012),math.log(0.10)))); dth=rng.normal(size=len(a))*w; dp=rng.normal(size=len(a))*w
    else:
        amp=float(np.exp(rng.uniform(math.log(0.006),math.log(0.04)))); dth=rng.normal(size=len(a)); dp=rng.normal(size=len(a))
    rms=math.sqrt(float(np.mean(dth*dth+dp*dp)))
    if rms<1e-14: return v.copy(),0.0
    dth*=amp/rms; dp*=amp/rms; a[:,0]=np.clip(th+dth,1e-5,math.pi-1e-5); a[:,1]=ph+dp/np.maximum(np.sin(th),0.15)
    return a.ravel(),amp
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('points_dat'); ap.add_argument('--seed',type=int,default=701); ap.add_argument('--steps',type=int,default=90)
    ap.add_argument('--temperature',type=float,default=0.02); ap.add_argument('--retain-below',type=float,default=444368.48); ap.add_argument('--out',required=True); args=ap.parse_args()
    x=load_points(args.points_dat); n,cubic=approximate_threefold_axis(x,args.seed+17); maxerr,rmserr,axis,R=refine_symmetry_axis(x,n); y,alignmax,alignrms=align_axis_to_z(x,axis)
    reps=c3.c3_representatives(y); base=c3.polish(c3.xyz_to_vars(reps),1400); curv=base.x.copy(); cure=float(base.fun); best=cure; rng=np.random.default_rng(args.seed); accepted=0; rows=[]; minima=[]
    def retain(v,E,step,source):
        if E>args.retain_below or any(abs(q['energy']-E)<2e-7 for q in minima): return
        pts,_,_=c3.vars_to_full(v); minima.append({'energy':float(E),'step':int(step),'source':source,'points':pts.tolist()})
    retain(curv,cure,-1,'T-C3 base')
    print(f'axis={axis.tolist()} cubic={cubic:.6g} sym_max={maxerr:.3e} align_max={alignmax:.3e}',flush=True); print(f'C3_base={cure:.12f} nit={base.nit} ok={base.success}',flush=True)
    for step in range(args.steps):
        if step>0 and step%30==0 and rng.random()<0.7: curv=base.x.copy(); cure=float(base.fun)
        start,amp=local_move(curv,rng); estart,_=c3.fg(start); res=c3.polish(start,650); en=float(res.fun); de=en-cure; accept=de<=0 or rng.random()<math.exp(-de/max(args.temperature,1e-12))
        if accept: curv=res.x.copy(); cure=en; accepted+=1
        best=min(best,en); retain(res.x,en,step,'proposal'); rows.append({'step':step,'amp':amp,'start_energy':float(estart),'minimum_energy':en,'delta_from_current':de,'accepted':bool(accept),'nit':int(res.nit),'success':bool(res.success)})
        print(f'step={step:03d} amp={amp:.5f} start={estart:.6f} min={en:.12f} de={de:+.6g} acc={int(accept)} retained={len(minima)}',flush=True)
    minima.sort(key=lambda z:z['energy']); out={'seed':args.seed,'temperature':args.temperature,'steps':args.steps,'accepted':accepted,'axis':axis.tolist(),'cubic_abs_extremum':cubic,'symmetry_fit_max':maxerr,'symmetry_fit_rms':rmserr,'aligned_c3_max_error':alignmax,'aligned_c3_rms_error':alignrms,'base_energy':float(base.fun),'best_energy':float(best),'minima':minima,'rows':rows}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
