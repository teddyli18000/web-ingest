#!/usr/bin/env python3
"""Mobile fractional-occupancy continuation from symmetric N=972 to N=960.

A fixed-ghost continuation delays but does not prevent a finite-lambda scar
collapse.  Here the selected 12-particle tetrahedral orbit carries charge
lambda while *all 972 coordinates remain movable*.  The other 960 particles
retain unit charge.  The weighted pair energy is

    sum_{i<j} q_i q_j / r_ij,

with q=1 on active particles and q=lambda on the selected orbit.  At lambda=0
the 12 fractional particles decouple exactly; the remaining 960 coordinates
are then independently polished under the ordinary Thomson objective.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import minimize

import diagnose_soft_modes as sm
import search_size_beam as sb
import search_t_orbit_transfer_batch_v2 as robust
from analyze_twinned_motif import load_xyz
from search_972_twin_orbit_removal import recover_axis,graph,core_distance
from search_learned_event_grammar import defect_signature

PI=math.pi
base=robust.base


def parse_schedule(s):
    vals=[float(z) for z in s.split(',') if z.strip()]
    if not vals or abs(vals[0]-1.0)>1e-12 or abs(vals[-1])>1e-12:
        raise ValueError('schedule must start at 1 and end at 0')
    if any(vals[i+1]>vals[i]+1e-14 for i in range(len(vals)-1)):
        raise ValueError('schedule must be nonincreasing')
    return vals


def sig_json(x):
    sig=defect_signature(x)
    return {'coord':[[int(a),int(b)] for a,b in sig['coord']],
            'twin_count':int(sig['twins']),
            'components':[list(map(int,t)) for t in sig['components']]}


def weighted_terms_grad(v,charges):
    x,dth,dph=sm.vars_to_xyz(v); n=len(x)
    dots=np.clip(x@x.T,-1.0,1.0)
    r2=np.maximum(2.0-2.0*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1.0/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0.0)
    qq=np.multiply.outer(charges,charges)
    ga=(qq*w)@x
    gt=np.sum(ga*dth,axis=1); gp=np.sum(ga*dph,axis=1)
    tri=np.triu_indices(n,1)
    terms=(qq[tri]*inv[tri]).astype(float,copy=False)
    return terms,np.column_stack([gt,gp]).ravel(),x


def stable_weighted_relax(x0,charges,maxiter):
    q0=sm.xyz_to_vars(x0); ref,_,_=weighted_terms_grad(q0,charges)
    ref=np.asarray(ref,np.longdouble); E0=float(np.sum(ref,dtype=np.longdouble)); n=len(x0)
    def fg(q):
        t,g,_=weighted_terms_grad(q,charges)
        de=float(np.sum(np.asarray(t,np.longdouble)-ref,dtype=np.longdouble))
        return de,g
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',bounds=bounds,
               options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':70,'maxcor':35})
    de,g=fg(r.x); x,_,_=sm.vars_to_xyz(r.x)
    grms=float(np.linalg.norm(g)/math.sqrt(len(g)))
    return E0+de,x,int(r.nit),bool(r.success),str(r.message),grms


def angular_rms(a,b):
    dots=np.clip(np.sum(a*b,axis=1),-1.0,1.0)
    return float(np.sqrt(np.mean(np.arccos(dots)**2)))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('xyz972'); ap.add_argument('few_shots')
    ap.add_argument('--orbit-index',type=int,required=True)
    ap.add_argument('--schedule',default='1,.85,.7,.6,.5,.4,.3,.22,.16,.11,.07,.04,.02,.008,.002,0')
    ap.add_argument('--maxiter',type=int,default=1800); ap.add_argument('--seed',type=int,default=97212)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    live,_=sb.find_live(pathlib.Path(args.few_shots)); x=load_xyz(args.xyz972)
    if len(x)!=972: raise ValueError(f'expected 972 points, got {len(x)}')
    x_parent=x.copy()
    s2,n2=recover_axis(x,PI,args.seed); s3,n3=recover_axis(x,2*PI/3,args.seed+1)
    group,perms,worst,rms,A,a2,a3=base.exact_t_group_from_axes(x,n2,n3)
    orbits=base.build_orbits(perms,len(x)); generic={i:o for i,o in enumerate(orbits) if len(o)==12}
    if args.orbit_index not in generic:
        raise ValueError(f'orbit {args.orbit_index} is not a generic 12-orbit; available={sorted(generic)}')
    orbit=np.asarray(generic[args.orbit_index],int); mask=np.ones(len(x),bool); mask[orbit]=False
    nb,edges,z=graph(x); dist=core_distance(nb,z)
    print('PARENT','orbit',args.orbit_index,'axis',s2,s3,'validate',worst,rms,
          'all6',bool(np.all(z[orbit]==6)),'core',int(np.min(dist[orbit])),
          'sig_active',sig_json(x[mask]),flush=True)
    rows=[]
    schedule=parse_schedule(args.schedule)
    for lam in schedule:
        charges=np.ones(len(x),float); charges[orbit]=float(lam)
        E,x,nit,ok,msg,grms=stable_weighted_relax(x,charges,args.maxiter)
        active=x[mask]
        row={'lambda':lam,'weighted_energy':float(E),'nit':nit,'success':ok,'message':msg,
             'gradient_rms':grms,'active_signature':sig_json(active),
             'active_rms_from_parent':angular_rms(active,x_parent[mask]),
             'ghost_rms_from_parent':angular_rms(x[orbit],x_parent[orbit])}
        rows.append(row)
        print('L',lam,'Ew',f'{E:.12f}','grms',f'{grms:.3g}','nit',nit,'ok',ok,
              'twins',row['active_signature']['twin_count'],'coord',row['active_signature']['coord'],
              'active_rms',f"{row['active_rms_from_parent']:.6g}",
              'ghost_rms',f"{row['ghost_rms_from_parent']:.6g}",flush=True)
    active=x[mask].copy()
    Epre=float(rows[-1]['weighted_energy'])
    Efinal,zfinal,nit,ok=sb.stable_relax(active,4200)
    fsig=sig_json(zfinal)
    print('FINAL','pre',f'{Epre:.12f}','polished',f'{Efinal:.12f}','dLive',f'{Efinal-live:+.12g}',
          'twins',fsig['twin_count'],'coord',fsig['coord'],'nit',nit,'ok',ok,flush=True)
    out={'live_score':float(live),'orbit_index':args.orbit_index,'orbit':orbit.tolist(),
         'group_validation_max':float(worst),'group_validation_rms_max':float(rms),
         'all_six':bool(np.all(z[orbit]==6)),'min_core_distance':int(np.min(dist[orbit])),
         'schedule':schedule,'rows':rows,'pre_polish_energy':Epre,
         'final_energy':float(Efinal),'delta_live':float(Efinal-live),'final_signature':fsig,
         'final_points':zfinal.tolist(),'final_ghost_points':x[orbit].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if Efinal<live-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('candidate below live; verify independently\n')

if __name__=='__main__': main()
