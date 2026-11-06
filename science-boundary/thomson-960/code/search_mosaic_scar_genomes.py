#!/usr/bin/env python3
"""Thomson-960 record hunt by recombining twelve independently chosen defect cores.

Previous successful scar-braid search found distinct near-record N960 minima,
but repeated whole-sphere smooth deformations and entire R->W/R->A/B event
fields returned to the same few basins. Change the representation: at each of
the 12 record defect components choose a *different* elite donor's full
displacement field, smoothly glue these local displacement patches, and
minimize every generated 960-particle Coulomb structure.

Donors include symmetry-distinct R (record), A, B, W=R+.029215 and D2=R+.011674,
with each nontrivial displacement transported through all three C3 orbits.
A lightweight population evolves discrete twelve-site donor genomes and
continuous patch widths/amplitudes; every genome is scored by a compiled exact
Coulomb force quench, not by an approximate motif objective.

No N961 weighted saddle/soft-mode restriction, no imposed symmetry on children.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from collections import Counter

import numpy as np

import search_composed_shears as sh
import search_hamiltonian_scar_braid as hb
import search_recombined_novel_scar_fields as ev
import search_size_beam as sb

RECORD=444368.3924061973
DONORS=('R','W','A','B','D2')


def load_fields(fewshots,elite_json):
    R,parents,diagnostics=ev.load_event_parents(fewshots,elite_json)
    d2=fewshots/'problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json'
    D2=sb.load_cert(d2)
    D2a,meta=ev.align_perm(R,D2,221960)
    diagnostics['D2']=meta
    centers,degrees,ncomps=hb.scar_centers(R)
    assert len(centers)==12, (len(centers),degrees,ncomps)
    fields=[np.zeros_like(R)]
    names=['R']
    for donor in ('W','A','B','D2'):
        pts=D2a if donor=='D2' else parents[donor]
        three,errors=sh.group_events(R,pts)
        diagnostics[donor]['orbit_label_errors']=errors
        diagnostics[donor]['field_rms']=float(np.sqrt(np.mean(np.sum(three[0]**2,axis=1))))
        for k,v in enumerate(three):
            fields.append(v)
            names.append(f'{donor}-{k}')
    return R,centers,np.asarray(fields),names,diagnostics


def stitched_child(R,centers,fields,genome,width,amplitude,backdrop):
    # The blend is spatially localized around each defect core; distant
    # elastic accommodation occurs *only* through physical N960 relaxation.
    cosines=R@centers.T
    distances=np.arccos(np.clip(cosines,-1,1))
    gauss=np.exp(-.5*(distances/width)**2)
    weights=gauss/(backdrop+np.sum(gauss,axis=1,keepdims=True))
    v=np.zeros_like(R)
    for core,field_id in enumerate(genome):
        if field_id:
            v+=weights[:,core,None]*fields[field_id]
    return sh.expmap(R,amplitude*v)


def random_genome(rng,num_fields):
    if rng.random()<.45:
        gene=np.zeros(12,dtype=int)
        k=int(rng.integers(2,9))
        ids=rng.choice(12,k,replace=False)
        gene[ids]=rng.integers(1,num_fields,size=k)
        return gene
    return rng.integers(0,num_fields,size=12)


def mutate_genome(g,rng,num_fields):
    g=np.asarray(g,int).copy()
    n=int(rng.choice([1,2,3,4,6,9],p=[.18,.26,.22,.14,.13,.07]))
    ids=rng.choice(12,n,replace=False)
    for i in ids:
        if rng.random()<.22: g[i]=0
        elif rng.random()<.45:
            # preserve the same donor but try a new C3 orientation
            z=max(g[i]-1,0)//3
            g[i]=1+3*z+int(rng.integers(3))
        else:g[i]=int(rng.integers(1,num_fields))
    return g


def remix(parent1,parent2,rng):
    a=np.asarray(parent1,int).copy();b=np.asarray(parent2,int)
    centers=rng.choice(12,size=int(rng.integers(2,10)),replace=False)
    a[centers]=b[centers]
    return a


def append_genome_population(pop,genome,E,params,limit=38):
    # Distinct genotypes need not give distinct basins. Limit how many of
    # the same energy basin can dominate the search selection, so that
    # recombination learns from genuinely different structural outcomes.
    code=tuple(int(v) for v in genome)
    if any(tuple(x['gene'])==code and E>=x['energy']-2e-7 for x in pop):
        return
    pop[:]=[x for x in pop if tuple(x['gene'])!=code]
    pool=sorted(pop+[{'gene':list(code),'energy':float(E),'params':params}],
                key=lambda x:x['energy'])
    kept=[];basins=[]
    for x in pool:
        k=next((i for i,v in enumerate(basins) if abs(v-x['energy'])<6e-5),None)
        if k is None:
            basins.append(x['energy'])
            k=len(basins)-1
        if sum(abs(y['energy']-basins[k])<6e-5 for y in kept)>=4:
            continue
        kept.append(x)
        if len(kept)>=limit:break
    pop[:]=kept


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots',type=pathlib.Path)
    ap.add_argument('--elite-json',type=pathlib.Path,required=True)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--trials',type=int,default=600)
    ap.add_argument('--maxiter',type=int,default=750)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    R,centers,fields,names,diagnostics=load_fields(args.few_shots,args.elite_json)
    energy0=hb.energy_gradient_selftest(sb.xyz_to_vars(R))
    assert abs(energy0-RECORD)<3e-6
    print('DONORS',names,'PARENTS',diagnostics,'CENTERS',len(centers),flush=True)
    pop=[]
    archive=[]
    known=[RECORD,444368.3956862258,444368.4029728613,
           444368.4040805305,444368.42162124,444368.4109930844]
    basins=[]
    for group in range(1,13,3):
        for k in range(3):
            gene=np.full(12,group+k,int)
            append_genome_population(pop,gene,RECORD+.2,
                {'width':.75,'amp':1.0,'seed_class':names[group+k]})
    best=RECORD
    record_candidates=0
    for t in range(args.trials):
        if t%6==0 or not pop:
            gene=random_genome(rng,len(fields))
            recipe='random-genes'
        else:
            a=pop[int(rng.integers(min(18,len(pop))))]
            if len(pop)>1 and rng.random()<.48:
                b=pop[int(rng.integers(len(pop)))]
                gene=remix(a['gene'],b['gene'],rng)
                recipe='crossover'
            else:
                gene=np.asarray(a['gene'],int).copy()
                recipe='mutation'
            gene=mutate_genome(gene,rng,len(fields))
        width=float(np.exp(rng.uniform(math.log(.24),math.log(1.0))))
        amp=float(rng.choice([-1.,1.])*np.exp(rng.uniform(math.log(.55),math.log(3.2))))
        backdrop=float(rng.uniform(.01,.12))
        X=stitched_child(R,centers,fields,gene,width,amp,backdrop)
        spacing=hb.min_spacing(X)
        contractions=0
        while spacing<.042 and contractions<8:
            X=hb.expmap(R,sh.logmap(R,X)*.6)
            spacing=hb.min_spacing(X)
            contractions+=1
        if spacing<.042:
            archive.append({'trial':t,'recipe':recipe,'skip':'collision'})
            continue
        E,Y,nit,ok,gr=hb.polish(X,args.maxiter)
        if gr>2e-4:
            E,Y,nmore,ok2,gr=hb.polish(Y,1500)
            nit+=nmore
        params={'width':width,'amp':amp,'backdrop':backdrop,
                'contractions':contractions,'trial':t}
        append_genome_population(pop,gene,E,params)
        novel=E<RECORD+.35 and all(abs(E-ref)>1e-5 for ref in known)
        new_basin=novel and all(abs(E-z['energy'])>6e-5 for z in basins)
        if new_basin:
            basins.append({'energy':E,'points':Y.copy(),'trial':t,
                          'gene':gene.tolist(),'params':params})
            basins.sort(key=lambda x:x['energy'])
            if len(basins)>22:basins.pop()
            print('NOVEL',t,recipe,'E',f'{E:.12f}',
                  'delta',f'{E-RECORD:+.9f}',
                  'nparents',len(set(gene)),'gene',gene.tolist(),flush=True)
        if E<best-2e-7:
            best=E
            print('BEST',t,recipe,'E',f'{E:.12f}',
                  'delta',f'{E-RECORD:+.9f}',flush=True)
        if E<RECORD-2e-7:
            dest=args.out/f'CANDIDATE-{args.seed}-{t}.json'
            dest.write_text(json.dumps({'energy':E,'points':Y.tolist(),
                                        'gene':gene.tolist(),'seed':args.seed,
                                        'trial':t,'gradient_rms':gr})+'\n')
            record_candidates+=1
            print('CANDIDATE',dest,E,flush=True)
        archive.append({'trial':t,'recipe':recipe,
                        'gene':gene.tolist(),'energy':E,'delta_record':E-RECORD,
                        'new_basin':new_basin,'num_nonzero':int(np.sum(gene!=0)),
                        'width':width,'amp':amp,'contractions':contractions,
                        'nit':nit,'grad_rms':gr})
        if t%12==0:
            print('TRIAL',t,'E',f'{E:.12f}','delta',f'{E-RECORD:+.7f}',
                  'new',new_basin,'basins',len(basins),'best',best,flush=True)
        if t%20==0 or t==args.trials-1:
            out={'seed':args.seed,'trials_done':t+1,'target':args.trials,
                 'best_energy':best,'delta_record':best-RECORD,
                 'subrecord_candidates':record_candidates,
                 'source_elite':str(args.elite_json),
                 'donor_names':names,'donor_diagnostics':diagnostics,
                 'genome_population':pop,'rows':archive,
                 'novel_basins':[{'energy':z['energy'],'trial':z['trial'],
                                 'gene':z['gene'],'params':z['params'],
                                 'points':z['points'].tolist()}
                                  for z in basins[:12]]}
            (args.out/'result.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('FINAL',args.seed,'best',f'{best:.12f}',
          'delta',f'{best-RECORD:+.9f}','new_basins',len(basins),
          'candidates',record_candidates,flush=True)


if __name__=='__main__':
    main()
