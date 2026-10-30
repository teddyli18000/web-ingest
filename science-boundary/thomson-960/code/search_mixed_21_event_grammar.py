#!/usr/bin/env python3
"""Mixed finite-amplitude event grammar on the N=960 21-dislocation layer.

The base e564 minimum is C3 symmetric. We learn finite nonlinear displacement
fields from e564 to the independently discovered e553 and e558 descendants,
generate their C3 copies, and compose *different event families* rather than
repeating Hessian-mode kicks. Relaxed 21-dislocation descendants are then fed
straight into the scaffolded 21->20 topology interface on the same runner.
"""
from __future__ import annotations
import argparse,json,pathlib,itertools
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q
from search_e553_event_composition import kabsch,sphere_log,sphere_exp,c3_perm,rotate_event,TWOPI
from search_e564_scaffolded_flip import families,fixed_relax
from search_e564_defect_flip_parallel import topology,perturb

KNOWN_DEFAULT=[444368.5645391991,444368.5533454687,444368.5586189419,444368.5586189427,444368.54540130566]

def coord_counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def align_to_base(base,target):
    R=kabsch(target,base); y=target@R
    return y,sphere_log(base,y)

def c3_event_copies(base,event):
    out=[event]
    for k in (1,2):
        perm,R,_,_=c3_perm(base,k*TWOPI/3)
        out.append(rotate_event(event,perm,R))
    return out

def norm_event(v): return float(np.sqrt(np.mean(np.sum(v*v,axis=1))))

def cosine(a,b):
    x=float(np.sum(a*b)); d=float(np.linalg.norm(a)*np.linalg.norm(b)); return x/d if d else 0.0

def dedup_events(events,tol=0.99999):
    out=[]
    for name,v in events:
        u=v/max(np.linalg.norm(v),1e-300)
        if any(float(u@w)>tol for _,_,w in out): continue
        out.append((name,v,u))
    return [(n,v) for n,v,_ in out]

def pair_sites(A,B):
    scores=[]
    for i,(_,a) in enumerate(A):
        for j,(_,b) in enumerate(B): scores.append((abs(cosine(a,b)),i,j))
    useda=set(); usedb=set(); pairs=[]
    for s,i,j in sorted(scores,reverse=True):
        if i in useda or j in usedb: continue
        pairs.append((i,j,s)); useda.add(i); usedb.add(j)
        if len(useda)==min(len(A),len(B)): break
    return pairs

def patterns(kind,A,B):
    pairs=pair_sites(A,B); same={(i,j) for i,j,_ in pairs}; rows=[]
    if kind=='same-site':
        for i,j,_ in pairs:
            for s in (1.0,-1.0): rows.append((f'A{i}{"+" if s>0 else "-"}B{j}',[(A[i][1],1.0),(B[j][1],s)]))
    elif kind=='cross-site':
        for i in range(len(A)):
            for j in range(len(B)):
                if (i,j) not in same: rows.append((f'A{i}+B{j}',[(A[i][1],1.0),(B[j][1],1.0)]))
    elif kind=='difference':
        for i in range(len(A)):
            for j in range(len(B)): rows.append((f'A{i}-B{j}',[(A[i][1],1.0),(B[j][1],-1.0)]))
        for i,j in itertools.combinations(range(len(B)),2): rows.append((f'B{i}-B{j}',[(B[i][1],1.0),(B[j][1],-1.0)]))
    elif kind=='support3':
        for i,j in itertools.combinations(range(len(A)),2):
            for k in range(len(B)): rows.append((f'A{i}+A{j}+B{k}',[(A[i][1],1),(A[j][1],1),(B[k][1],1)]))
        for i in range(len(A)):
            for j,k in itertools.combinations(range(len(B)),2): rows.append((f'A{i}+B{j}+B{k}',[(A[i][1],1),(B[j][1],1),(B[k][1],1)]))
    else: raise ValueError(kind)
    return rows,pairs

def new_basin(basins,e,cc,known,tol=2e-6):
    if any(abs(e-k)<tol for k in known): return False
    return not any(abs(e-b['energy'])<tol and cc==b['coord_counts'] for b in basins)

def scaffold_one(x,max_families,mults,fixed_maxiter,release_maxiter):
    try: fam=families(x)
    except Exception as exc: return {'error':str(exc),'rows':[],'basins':[]}
    rows=[]; bas=[]
    for fi,(t,q) in enumerate(fam[:max_families]):
        for m in mults:
            start=perturb(x,q,t*m,'balanced'); sc=coord_counts(start); qstart=sm.xyz_to_vars(start); Es,_=sm.fg(qstart)
            Ef,rawf,qf,xf,nitf,okf,msgf=fixed_relax(qstart,list(q),fixed_maxiter); fc=coord_counts(xf)
            Er,rawr,xr,nitr,okr,msgr=stable_relax_q(qf,maxiter=release_maxiter); rc=coord_counts(xr)
            r={'family':fi,'threshold':float(t),'quad':list(q),'multiplier':m,'start_energy':Es,'start_coord':sc,'fixed_energy':Ef,'fixed_coord':fc,'fixed_nit':nitf,'fixed_success':okf,'release_energy':Er,'release_coord':rc,'release_nit':nitr,'release_success':okr}
            rows.append(r)
            print(f'SCAFF f={fi} m={m:g} fixed={Ef:.12f} {fc} release={Er:.12f} {rc}',flush=True)
            if not any(abs(Er-b['energy'])<2e-6 and rc==b['coord_counts'] for b in bas):
                bas.append({'energy':Er,'coord_counts':rc,'family':fi,'multiplier':m,'points':xr.tolist()})
    bas.sort(key=lambda z:z['energy'])
    return {'families':[{'threshold':float(t),'quad':list(q)} for t,q in fam],'rows':rows,'basins':bas[:12]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('base_json'); ap.add_argument('e553_json'); ap.add_argument('e558a_json'); ap.add_argument('e558b_json')
    ap.add_argument('--kind',choices=['same-site','cross-site','difference','support3'],required=True)
    ap.add_argument('--scales',default='0.45,0.7,0.95,1.2,1.5')
    ap.add_argument('--maxiter',type=int,default=1800); ap.add_argument('--keep',type=int,default=12)
    ap.add_argument('--scaffold-top',type=int,default=2); ap.add_argument('--scaffold-families',type=int,default=4)
    ap.add_argument('--scaffold-mults',default='1.05,1.25,1.6')
    ap.add_argument('--fixed-maxiter',type=int,default=900); ap.add_argument('--release-maxiter',type=int,default=1800)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    mb,base=load_seed(pathlib.Path(args.base_json)); _,x553=load_seed(pathlib.Path(args.e553_json)); _,x558a=load_seed(pathlib.Path(args.e558a_json)); _,x558b=load_seed(pathlib.Path(args.e558b_json))
    _,v553=align_to_base(base,x553); _,v558a=align_to_base(base,x558a); _,v558b=align_to_base(base,x558b)
    A=[(f'A{i}',v) for i,v in enumerate(c3_event_copies(base,v553))]
    B0=[]
    for tag,v0 in [('Ba',v558a),('Bb',v558b)]:
        for i,v in enumerate(c3_event_copies(base,v0)): B0.append((f'{tag}{i}',v))
    B=dedup_events(B0)
    pats,pairs=patterns(args.kind,A,B); scales=[float(s) for s in args.scales.split(',') if s]
    print('EVENTS A',[(n,norm_event(v)) for n,v in A],flush=True); print('EVENTS B',[(n,norm_event(v)) for n,v in B],flush=True)
    print('PAIR',pairs,'patterns',len(pats),'scales',scales,flush=True)
    rows=[]; basins=[]; known=list(KNOWN_DEFAULT)
    for pi,(tag,terms) in enumerate(pats):
        combo=sum(c*v for v,c in terms); cr=norm_event(combo)
        if cr<1e-7: continue
        for s in scales:
            start=sphere_exp(base,s*combo); qs=sm.xyz_to_vars(start); Es,_=sm.fg(qs)
            e,raw,z,nit,ok,msg=stable_relax_q(qs,maxiter=args.maxiter); cc=coord_counts(z)
            r={'pattern':tag,'pattern_index':pi,'scale':s,'combo_rms':cr,'start_energy':Es,'energy':e,'coord_counts':cc,'nit':nit,'success':ok}
            rows.append(r); print(f'EV {tag} s={s:g} combo={cr:.5g} start={Es:.7f} E={e:.12f} {cc}',flush=True)
            if new_basin(basins,e,cc,known):
                basins.append(dict(r,points=z.tolist())); basins.sort(key=lambda q:q['energy']); basins=basins[:args.keep]
    candidates=[b for b in basins if b['coord_counts'].get('7')==21]
    if not candidates:
        candidates=[{'energy':float(json.loads(pathlib.Path(args.e553_json).read_text()).get('energy',444368.5533454687)),'coord_counts':coord_counts(x553),'pattern':'fallback-e553','scale':0,'points':x553.tolist()},{'energy':float(json.loads(pathlib.Path(args.e558a_json).read_text()).get('energy',444368.5586189419)),'coord_counts':coord_counts(x558a),'pattern':'fallback-e558a','scale':0,'points':x558a.tolist()}]
    candidates.sort(key=lambda q:q['energy']); scaff=[]; best20=None
    for b in candidates[:args.scaffold_top]:
        print(f'SCAFFOLD SOURCE E={b["energy"]:.12f} pattern={b["pattern"]}',flush=True)
        sd=scaffold_one(np.asarray(b['points'],float),args.scaffold_families,[float(x) for x in args.scaffold_mults.split(',') if x],args.fixed_maxiter,args.release_maxiter)
        sd['source_energy']=b['energy']; sd['source_pattern']=b['pattern']; sd['source_scale']=b['scale']; scaff.append(sd)
        for q in sd.get('basins',[]):
            if q['coord_counts'].get('7')==20 and (best20 is None or q['energy']<best20['energy']): best20=q
    out={'kind':args.kind,'base_energy':float(mb.get('energy',mb.get('full_energy',float('nan')))),'event_rms':{'A':[norm_event(v) for _,v in A],'B':[norm_event(v) for _,v in B]},'event_names':{'A':[n for n,_ in A],'B':[n for n,_ in B]},'same_site_pairs':pairs,'patterns':len(pats),'scales':scales,'rows':rows,'new_lowest_basins':basins,'scaffold':scaff,'best_20_basin':best20}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best20 is not None:
        p=pathlib.Path(args.out).with_suffix('.best20.json'); p.write_text(json.dumps(best20,separators=(',',':'))+'\n'); print('BEST20',best20['energy'],best20['coord_counts'],'saved',p,flush=True)

if __name__=='__main__': main()
