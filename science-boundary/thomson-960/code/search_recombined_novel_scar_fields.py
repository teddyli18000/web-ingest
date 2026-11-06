#!/usr/bin/env python3
"""Recombine a newly discovered N960 near-record motif with historic R/A/B.

The newly and independently verified R+0.029215 basin W came from a coherent
Hamiltonian scar dipole, not from R/A/B transition searches. Align W with the
accepted C3 record by multi-start rigid ICP and Hungarian assignment, then
build its full 960-particle spherical logarithmic displacement field R->W.
Generate the three C3 orbit-equivalent copies and compose them with the
historically known R->A and R->B fields, including noncommutative sequential
moves and simultaneous sphere exponentials.

This searches genuinely untried nonlinear coordinated fields. Every offspring
is fully unconstrained-relaxed in the genuine N960 Coulomb objective using a
numba-compiled exact pairwise gradient with trial-relative stable summation.
New low-energy parents can reproduce; any sub-record candidate is persisted.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import linear_sum_assignment

import search_composed_shears as sh
import search_hamiltonian_scar_braid as hb
import search_size_beam as sb
import search_topology_morph as tm

RECORD=444368.3924061973


def normalized(x):
    x=np.asarray(x,float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def align_perm(R,Y,seed):
    # Multi-start rigid ICP initializes the atom-to-atom Hungarian assignment;
    # once assigned, Kabsch and Hungarian jointly refine the correspondence.
    rng=np.random.default_rng(seed)
    near,rotation,_=tm.icp(Y,R,rng,starts=24,iters=19)
    cur=Y@rotation
    for _ in range(6):
        cost=np.maximum(0.,2-2*np.clip(R@cur.T,-1,1))
        ii,jj=linear_sum_assignment(cost)
        assert np.array_equal(ii,np.arange(960))
        linked=cur[jj]
        T=tm.kabsch(linked,R)
        cur=cur@T
    cost=np.maximum(0.,2-2*np.clip(R@cur.T,-1,1))
    _,idx=linear_sum_assignment(cost)
    linked=cur[idx]
    rms=float(np.sqrt(np.mean(np.sum((R-linked)**2,axis=1))))
    maximum=float(np.max(np.linalg.norm(R-linked,axis=1)))
    return linked,{'nearest_icp_rms':float(near),'match_rms':rms,
                   'match_max':maximum,'labeled_points_reordered':int(np.count_nonzero(idx!=np.arange(960)))}


def load_event_parents(fewshots,elite_json):
    record,shot=sb.find_live(fewshots)
    if abs(record-RECORD)>1e-7:raise RuntimeError(('live score changed',record))
    R=normalized(sb.load_cert(shot/'certificate.json'))
    a=json.loads(pathlib.Path('science-boundary/thomson-960/data/neighbor-soft-003280.json').read_text())
    b=json.loads(pathlib.Path('science-boundary/thomson-960/data/basin-b-010566.json').read_text())
    elite=json.loads(elite_json.read_text())
    W=normalized(next(row['points'] for row in elite['minima'] if row['origin_tag']=='7-dipole'))
    out=[('A',normalized(a['points'])),('B',normalized(b['points'])),('W',W)]
    aligned={}
    diagnostics={}
    for k,y in out:
        direct=float(np.sqrt(np.mean(np.sum((R-y)**2,axis=1))))
        if k in ('A','B') and direct<0.09:
            yy=y
            meta={'direct_labeled_rms':direct,'match_rms':direct,'no_alignment_needed':True}
        else:
            yy,meta=align_perm(R,y,seed=abs(sum(map(ord,k)))*960)
            meta['direct_labeled_rms']=direct
        aligned[k]=yy;diagnostics[k]=meta
    return R,aligned,diagnostics


def normalize_field(R,v):
    return v-np.sum(v*R,axis=1)[:,None]*R


def construct(R,base,fields,indices,coefficients,sequential):
    if sequential:
        x=base.copy()
        for key,idx,c in zip(fields,indices,coefficients):
            f=sh.parallel_transport(R,x,key[idx])
            x=sh.expmap(x,c*f)
    else:
        v=np.zeros_like(R)
        for key,idx,c in zip(fields,indices,coefficients):
            v+=c*key[idx]
        v=sh.parallel_transport(R,base,normalize_field(R,v))
        x=sh.expmap(base,v)
    return x


def terms(rng,pattern,fields):
    W,A,B=fields['W'],fields['A'],fields['B']
    coeff=[];fs=[];ids=[]
    def add(f,j,c):
        fs.append(f);ids.append(int(j));coeff.append(float(c))
    if pattern=='W-single':
        add(W,rng.integers(3),rng.uniform(-2.0,2.0))
    elif pattern=='W-pair':
        j,k=rng.choice(3,2,replace=False)
        amp=rng.uniform(0.45,1.75)
        add(W,j,amp*rng.choice([-1.,1.]))
        add(W,k,amp*rng.uniform(-1.3,1.3))
    elif pattern=='W-triple':
        amp=rng.uniform(.4,1.6)
        c=rng.normal(size=3)
        c/=max(.5,float(np.std(c)))
        for j in range(3):add(W,j,amp*c[j])
    elif pattern=='W-A-coupled':
        add(W,rng.integers(3),rng.uniform(-1.8,1.8))
        add(A,rng.integers(3),rng.uniform(-1.8,1.8))
        if rng.random()<.55:add(W,rng.integers(3),rng.uniform(-.85,.85))
    elif pattern=='W-B-coupled':
        add(W,rng.integers(3),rng.uniform(-1.7,1.7))
        add(B,rng.integers(3),rng.uniform(-1.6,1.6))
        if rng.random()<.40:add(A,rng.integers(3),rng.uniform(-1.0,1.0))
    elif pattern=='W-A-commutator':
        j=int(rng.integers(3));k=int(rng.integers(3))
        a=float(rng.uniform(.35,1.6))*float(rng.choice([-1,1]))
        b=float(rng.uniform(.35,1.6))*float(rng.choice([-1,1]))
        for f,i,c in ((W,j,a),(A,k,b),(W,j,-a),(A,k,-b)):add(f,i,c)
    elif pattern=='W-ABA':
        k=int(rng.integers(3));j=int(rng.integers(3))
        add(A,j,rng.uniform(-1.3,1.3))
        add(W,k,rng.uniform(-1.7,1.7))
        add(A,(j+1)%3,rng.uniform(-1.3,1.3))
    else:
        raise ValueError(pattern)
    return fs,ids,coeff


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots',type=pathlib.Path)
    ap.add_argument('--elite-json',type=pathlib.Path,required=True)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--trials',type=int,default=550)
    ap.add_argument('--maxiter',type=int,default=900)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    R,parents,diagnostics=load_event_parents(args.few_shots,args.elite_json)
    event={}
    for k,y in parents.items():
        event[k],maperr=sh.group_events(R,y)
        diagnostics[k]['base_field_rms']=float(np.sqrt(np.mean(np.sum(event[k][0]**2,axis=1))))
        diagnostics[k]['C3_label_map_max_error']=max(maperr)
        print('PARENT',k,diagnostics[k],flush=True)
    cosmat={}
    for a,b in (('W','A'),('W','B'),('A','B')):
        v=event[a][0].ravel();w=event[b][0].ravel()
        cosmat[f'{a}/{b}']=float(v@w/np.linalg.norm(v)/np.linalg.norm(w))
    print('FIELD_OVERLAPS',cosmat,flush=True)
    reference=hb.energy_gradient_selftest(sb.xyz_to_vars(R))
    assert abs(reference-RECORD)<3e-6
    # Elite archive retains R/W/A/B with common R particle labels and may gain
    # new better parents; no symmetry restriction is imposed during relaxation.
    pool=[]
    for name,y in [('R',R)]+[(k,parents[k]) for k in ('W','A','B')]:
        E,x,nit,ok,gr=hb.polish(y,1650)
        if E<RECORD+.15 and all(abs(E-z['energy'])>4e-7 for z in pool):
            pool.append({'energy':E,'points':x,'tag':'seed-'+name})
        print('SEED',name,'energy',f'{E:.12f}','nit',nit,'grad',gr,flush=True)
    pool.sort(key=lambda z:z['energy'])
    best=min(p['energy'] for p in pool)
    records=[]
    patterns=['W-single','W-pair','W-triple','W-A-coupled',
              'W-B-coupled','W-A-commutator','W-ABA']
    candidate_count=0
    for t in range(args.trials):
        pattern=str(rng.choice(patterns,p=[.14,.16,.11,.23,.18,.10,.08]))
        seq=pattern in ('W-A-commutator','W-ABA') or rng.random()<.4
        # Reuse strong minima but periodically start anew at the record.
        if t%9==0:parent=pool[0]
        else:
            ranks=np.arange(min(12,len(pool)))
            weights=np.exp(-ranks/.9/3)
            weights/=weights.sum()
            parent=pool[int(rng.choice(ranks,p=weights))]
        base=parent['points']
        fs,ids,coeff=terms(rng,pattern,event)
        proposed=construct(R,base,fs,ids,coeff,seq)
        mind=hb.min_spacing(proposed)
        contractions=0
        while mind<.039 and contractions<7:
            proposed=hb.expmap(base,sh.logmap(base,proposed)*.5)
            mind=hb.min_spacing(proposed)
            contractions+=1
        if mind<.039:
            continue
        startE=hb.energy_abs(sb.xyz_to_vars(proposed))
        E,Y,nit,ok,grad=hb.polish(proposed,args.maxiter)
        if grad>2e-4:
            E,Y,nmore,ok2,grad=hb.polish(Y,1250)
            nit+=nmore
        new=E<RECORD+.25 and all(abs(E-z['energy'])>4e-7 for z in pool)
        if new:
            pool.append({'energy':E,'points':Y.copy(),'tag':f'{t}-{pattern}'})
            pool.sort(key=lambda z:z['energy'])
            pool=pool[:22]
        if E<best-2e-7:
            best=E
            print('BEST',t,pattern,'E',f'{E:.12f}','delta',f'{E-RECORD:+.9f}',
                  'parent',parent['tag'],'new',new,flush=True)
        if E<RECORD-2e-7:
            out=args.out/f'CANDIDATE-{args.seed}-{t}.json'
            out.write_text(json.dumps({'energy':E,'points':Y.tolist(),
                'seed':args.seed,'trial':t,'pattern':pattern,
                'parent':parent['tag'],'gradient_rms':grad})+'\n')
            candidate_count+=1
            print('CANDIDATE',out,'energy',E,flush=True)
        row={'trial':t,'pattern':pattern,'sequential':seq,'parent':parent['tag'],
             'parent_energy':parent['energy'],'start_energy':startE,
             'energy':E,'delta_record':E-RECORD,'new':new,'nit':nit,'gradient_rms':grad,
             'coefficients':coeff,'orbit_ids':ids,'min_spacing':mind,
             'contractions':contractions}
        records.append(row)
        if t%12==0:
            print('TRIAL',t,pattern,'E',f'{E:.12f}','delta',f'{E-RECORD:+.7f}',
                  'new',new,'pool',len(pool),'best',f'{best:.12f}',flush=True)
        if t%20==0 or t==args.trials-1:
            out={'seed':args.seed,'trials_done':t+1,'trials_target':args.trials,
                 'best_energy':best,'best_delta':best-RECORD,
                 'sub_record_candidates':candidate_count,
                 'source_elite':str(args.elite_json),'parent_diagnostics':diagnostics,
                 'field_cosines':cosmat,'rows':records,
                 'elite_pool':[{'energy':z['energy'],'tag':z['tag'],
                                'points':z['points'].tolist()} for z in pool[:14]]}
            (args.out/'result.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('FINAL',args.seed,'BEST',f'{best:.12f}',
          'DELTA',f'{best-RECORD:+.9f}','CANDIDATES',candidate_count,flush=True)


if __name__=='__main__':
    main()
