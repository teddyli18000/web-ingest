#!/usr/bin/env python3
"""Map the old T-symmetric N=960 minimum to the live C3 record by a spherical string.

This tests a different representation from minimum-centered kicks.  The old T
minimum and the live record have the same particle count but different global
scar organization.  After ICP + Hungarian point correspondence, a spherical
string is optimized using only the force perpendicular to the path.  Every
interior final image is then fully relaxed to expose intermediate basins, while
local energy maxima are classified by the full-space physical tangent Hessian.
Any near-index-1 maximum is refined on the same runner with hybrid eigenvector
following and certified by downhill relaxation on both reaction sides.
"""
from __future__ import annotations

import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_topology_morph as tm
import string_record_neighbor as sr
from string_between_seeds import path_diagnostics
from analyze_twinned_motif import load_xyz
from search_from_seed_modes import stable_relax_q
from search_learned_event_grammar import defect_signature
from refine_saddle_hybrid import lowest, constrained_relax, physical_grad
import search_soft_pair as sp

N=960


def sig_json(x):
    s=defect_signature(x)
    return {'coord':[[int(a),int(b)] for a,b in s['coord']],
            'components':[list(map(int,t)) for t in s['components']],
            'twins':int(s['twins'])}


def optimize_string(images,iters,eta,maxstep,tol):
    hist=[]; conv=False
    for it in range(iters):
        vals,perps,grads=path_diagnostics(images); new=[images[0]]; ms=0.0
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,s=sr.capped_descent(images[i],gp,eta,maxstep); new.append(y); ms=max(ms,s)
        new.append(images[-1]); images,arc=sr.reparameterize(new)
        if it%25==0 or it==iters-1:
            vals2,perps2,_=path_diagnostics(images); mp=max(perps2) if perps2 else 0.0
            print(f'STRING it={it} maxE={max(vals2):.12f} imax={int(np.argmax(vals2))} arc={arc:.7g} step={ms:.3e} perp={mp:.6g}',flush=True)
            hist.append({'iteration':it,'energies':vals2,'max_index':int(np.argmax(vals2)),'arc':arc,'max_step':ms,'max_perp':mp})
            if it>=50 and mp<tol: conv=True; break
    vals,perps,_=path_diagnostics(images)
    return images,vals,perps,hist,conv


def hessian_classify(x,k=10,fd=3e-6):
    q=sm.xyz_to_vars(x); E,gq=sm.fg(q); gp=gq/sm.physical_scale(q); gr=float(np.linalg.norm(gp)/math.sqrt(2*N))
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=900,ncv=max(40,4*k)); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return q,float(E),gr,vals,V,Q,int(calls['n'])


def refine_index1(x,outer=4):
    q=sm.xyz_to_vars(x); hist=[]
    for it in range(outer):
        vals,V,Q,c=lowest(q,k=6); mode=V[:,0].copy(); mode-=Q@(Q.T@mode); mode/=np.linalg.norm(mode)
        q,Eperp,cval,nit,ok,msg=constrained_relax(q,mode,2e5,450)
        vals2,V2,Q2,c2=lowest(q,k=6); m=V2[:,0].copy(); m-=Q2@(Q2.T@m); m/=np.linalg.norm(m)
        if float(m@mode)<0:m=-m
        g=physical_grad(q); g-=Q2@(Q2.T@g); g0=float(g@m); lam=float(vals2[0])
        coeff=-0.75*g0/lam if abs(lam)>0.1 else 0.0; lim=4e-4*math.sqrt(N); coeff=float(np.clip(coeff,-lim,lim))
        if coeff!=0:q=sp.exp_perturb(q,coeff*m,abs(coeff)/math.sqrt(N))
        E,_=sm.fg(q); gr=float(np.linalg.norm(physical_grad(q))/math.sqrt(2*N))
        hist.append({'outer':it,'lambda':lam,'reaction_gradient':g0,'perp_energy':Eperp,'perp_nit':nit,'perp_ok':ok,'step_rms':abs(coeff)/math.sqrt(N),'energy':float(E),'gradient_rms':gr})
        print(f'REFINE it={it} E={E:.12f} grad={gr:.4g} lambda={lam:+.6g} g0={g0:+.3g}',flush=True)
    q,E,gr,vals,V,Q,c=hessian_classify(sm.vars_to_xyz(q)[0],k=10)
    neg=int(np.sum(vals<-1e-3)); x=sm.vars_to_xyz(q)[0]
    sides=[]
    if neg==1:
        mode=V[:,0]
        for sign in (-1,1):
            qs=sp.exp_perturb(q,sign*mode,0.0015)
            e,raw,z,nit,ok,msg=stable_relax_q(qs,2200)
            sides.append({'sign':sign,'energy':float(e),'nit':nit,'success':ok,'signature':sig_json(z),'points':z.tolist()})
    return {'final_energy':E,'gradient_rms':gr,'negative_modes':neg,'lowest_eigenvalues':[float(v) for v in vals],
            'history':hist,'sides':sides,'saddle_points':x.tolist()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('old_t_xyz');ap.add_argument('few_shots');ap.add_argument('--images',type=int,default=17)
    ap.add_argument('--iterations',type=int,default=900);ap.add_argument('--seed',type=int,default=96031);ap.add_argument('--out',required=True);args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live,live_dir=tm.find_live(root); R=tm.cert_xyz(live_dir/'certificate.json'); T=load_xyz(args.old_t_xyz)
    rng=np.random.default_rng(args.seed); rms,Q,Ta=tm.icp(T,R,rng,starts=24,iters=20)
    cost=np.maximum(0.0,2-2*np.clip(R@Ta.T,-1,1)); ir,it=linear_sum_assignment(cost); assert np.array_equal(ir,np.arange(N)); Tm=Ta[it]
    hrms=float(np.sqrt(np.mean(np.sum((R-Tm)**2,axis=1))))
    print(f'ALIGN live={live:.10f} icp={rms:.7g} hungarian={hrms:.7g} oldT={sr.energy_grad(Tm)[0]:.12f}',flush=True)
    images=sr.interpolate_endpoints(R,Tm,args.images)
    images,vals,perps,hist,conv=optimize_string(images,args.iterations,2e-4,3e-4,1e-4)
    # Full relax every interior string image. This is cheap relative to the string
    # and directly reveals intermediate minima, even if the MEP is not fully converged.
    relaxed=[]
    for i,x in enumerate(images[1:-1],1):
        e,raw,z,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(x),2200); s=sig_json(z)
        relaxed.append({'image':i,'energy':float(e),'delta_vs_live':float(e-live),'nit':nit,'success':ok,'signature':s,
                        'points':z.tolist() if e<live-2e-7 else None})
        print(f'RELAX image={i} E={e:.12f} d={e-live:+.7g} twins={s["twins"]}',flush=True)
    # Classify each local maximum of the optimized discrete path.
    maxima=[i for i in range(1,len(vals)-1) if vals[i]>=vals[i-1] and vals[i]>=vals[i+1]]
    if not maxima: maxima=[int(np.argmax(vals))] if 0<int(np.argmax(vals))<len(vals)-1 else []
    portals=[]
    for i in maxima:
        q,E,gr,ev,V,Q,c=hessian_classify(images[i],k=10); neg=int(np.sum(ev<-1e-3))
        row={'image':i,'path_energy':vals[i],'gradient_rms':gr,'negative_modes':neg,'lowest_eigenvalues':[float(v) for v in ev]}
        print(f'PORTAL image={i} E={vals[i]:.12f} grad={gr:.4g} neg={neg} lows={ev[:5].tolist()}',flush=True)
        if neg==1 and gr<0.05: row['refined']=refine_index1(images[i])
        portals.append(row)
    best=min([{'energy':r['energy'],'points':r['points'],'source':f'image-{r["image"]}'} for r in relaxed]+[{'energy':live,'points':None,'source':'live'}],key=lambda r:r['energy'])
    # Include certified saddle-side minima from refinements.
    for p in portals:
        for s in p.get('refined',{}).get('sides',[]):
            if s['energy']<best['energy']:best={'energy':s['energy'],'points':s['points'] if s['energy']<live-2e-7 else None,'source':f'portal-{p["image"]}-side-{s["sign"]}'}
    out={'live_score':live,'live_shot':str(live_dir.relative_to(root)),'old_t_energy':sr.energy_grad(Tm)[0],
         'icp_nn_rms':rms,'hungarian_rms':hrms,'images':len(images),'string_converged':conv,
         'path_energies':vals,'path_perpendicular_gradient_rms':perps,'max_path_perpendicular_gradient_rms':max(perps) if perps else 0.0,
         'history':hist,'relaxed_images':relaxed,'portals':portals,'best_float_energy':best['energy'],'best_delta_vs_live':best['energy']-live,
         'best_source':best['source'],'best_points':best['points'] if best['energy']<live-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(f'BEST {best["energy"]:.12f} d={best["energy"]-live:+.9g} source={best["source"]}',flush=True)

if __name__=='__main__':main()
