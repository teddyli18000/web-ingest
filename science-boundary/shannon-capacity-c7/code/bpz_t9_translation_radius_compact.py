#!/usr/bin/env python3
"""Exact compact radius-k repair for any min-hit-one translated public BPZ auxiliary.

The 38-public-seed FFT scan has exactly 20 seed/obstruction cases whose best
translation intersects the obstruction in one point.  We deterministically
reconstruct the 20 distinct near states, select one by --near-index, and solve
all radius-k repairs exactly.

For near state S with unique bad x in D, a new point y can be used after deleting
x plus optional old owners iff every point of N[y] cap S other than x is among
the optional deletions.  The SAT model uses one variable per candidate addition
with support size <= k-1, one variable per optional old owner, implications
addition -> required deletion, at most k-1 optional deletions, at least k
additions, and the exact binary-cube clique cover of C7^5 among additions.
A SAT model is replayed and materialized as a 134770-point C7^10 certificate.
"""
import argparse
import json
import sys
from itertools import combinations, product
from pathlib import Path

import numpy as np
from pysat.formula import IDPool
from pysat.solvers import Minicard

import bpz_t9_aux_translation_fft as f

Q=7; D=5; U=Q**D; N=367; T=9; TARGET=N*N+T*T


def enc(w):
    v=0; m=1
    for x in w:
        v += x*m; m *= Q
    return v


def cube(a):
    for b in product((0,1), repeat=D):
        yield enc(tuple((a[j]+b[j])%Q for j in range(D)))


def find_near_states(tan_root, family_root, ring, digits, obs):
    raw=json.loads((tan_root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    fam=json.loads((family_root/'data'/'family-f.json').read_text())
    states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    Fobs=[(m,w,np.fft.fftn(f.arr(f.values(m),digits))) for m,w in obs.items()]
    seen=set(); out=[]
    for name,S in seeds:
        if len(S)!=N or not f.independent(S,digits): raise RuntimeError(f'invalid seed {name}')
        FS=np.fft.fftn(f.arr(S,digits))
        for oi,(mask,witness,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=1: continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==1):
                t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    S2=set(f.shift_set(S,t,digits,sign)); hits=S2&Dset
                    if len(hits)!=1: continue
                    key=(oi,tuple(sorted(S2)))
                    if key in seen: continue
                    seen.add(key)
                    out.append((name,oi,t,sign,S2,next(iter(hits)),Dset,witness))
    out.sort(key=lambda z:(z[0],z[1],z[2],z[3],tuple(sorted(z[4]))))
    if len(out)!=20: raise RuntimeError(f'near-state drift: {len(out)} != 20')
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path)
    ap.add_argument('output',type=Path); ap.add_argument('status',type=Path)
    ap.add_argument('--near-index',type=int,required=True); ap.add_argument('--radius',type=int,required=True)
    args=ap.parse_args(); k=args.radius
    if not 1<=k<=12: raise SystemExit('radius out of supported range')

    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import Ring
    ring=Ring(D); digits=tuple(ring.decode(v) for v in range(U))
    raw=json.loads((root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0']))
    nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    obs=f.obstruction_witnesses(I0,ring,digits,nb)
    near=find_near_states(root,args.family_root,ring,digits,obs)
    if not 0<=args.near_index<len(near): raise SystemExit('near-index out of range')
    name,oi,t,sign,S,bad,Dset,witness=near[args.near_index]

    owners=sorted(S-{bad}); owner_set=set(owners); Sset=set(S)
    supports={}; hist={}
    for y in range(U):
        if y in Sset or y in Dset: continue
        sup=tuple(x for x in ring.NB[y] if x in owner_set)
        bc=len(sup); hist[bc]=hist.get(bc,0)+1
        if bc<=k-1: supports[y]=sup
    candidates=sorted(supports); cset=set(candidates)
    pool=IDPool(); Y={y:pool.id(('y',y)) for y in candidates}; R={x:pool.id(('r',x)) for x in owners}
    solver=Minicard(); implications=0
    for y,sup in supports.items():
        for x in sup:
            solver.add_clause([-Y[y],R[x]]); implications+=1
    solver.add_atmost(list(R.values()),k-1)
    solver.add_atmost([-Y[y] for y in candidates],len(candidates)-k)
    cubes=0; cube_lits=0
    for a in range(U):
        lits=[Y[v] for v in cube(digits[a]) if v in cset]
        if len(lits)>=2:
            solver.add_atmost(lits,1); cubes+=1; cube_lits+=len(lits)
    setup={
        'near_index':args.near_index,'seed':name,'obstruction_index':oi,
        'translation':list(t),'translation_sign':sign,'mandatory_bad':bad,'radius':k,
        'obstruction_size':len(Dset),'candidate_additions':len(candidates),
        'support_size_histogram':{str(a):b for a,b in sorted(hist.items())},
        'optional_owner_variables':len(owners),'support_implications':implications,
        'cube_constraints':cubes,'cube_literal_total':cube_lits,'target_additions':k,
        'target_10d_score':TARGET,
    }
    print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=solver.solve(); model=solver.get_model() if sat else None; solver.delete()
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        st={'candidate':False,'sat':False,'method':'bpz-t9-translated-compact-exact-radius-repair','score':134753,'setup':setup}
        args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n'); print('UNSAT',json.dumps(st,sort_keys=True),flush=True); return

    pos={z for z in model if z>0}; adds=[y for y in candidates if Y[y] in pos]
    if len(adds)<k: raise RuntimeError(f'SAT selected only {len(adds)} additions')
    adds=adds[:k]
    if not f.independent(set(adds),digits): raise RuntimeError('SAT additions conflict')
    needed=set()
    for y in adds: needed.update(supports[y])
    if len(needed)>k-1: raise RuntimeError('owner budget replay failed')
    removals={bad}|needed
    for x in owners:
        if len(removals)>=k: break
        if x not in removals: removals.add(x)
    if len(removals)!=k: raise RuntimeError('could not balance removals')
    repaired=(S-removals)|set(adds)
    if len(repaired)!=N or repaired&Dset or not f.independent(repaired,digits): raise RuntimeError('repair replay failed')
    Ibits,pairs,orient,PH,PV=witness
    points,xp=f.build(Ibits,sum(1<<z for z in repaired),pairs,PH,PV,ring)
    if len(points)!=TARGET: raise RuntimeError(f'target score drift {len(points)}')
    st={
        'candidate':True,'sat':True,'method':'bpz-t9-translated-compact-exact-radius-repair','score':len(points),
        'near_index':args.near_index,'seed':name,'obstruction_index':oi,'translation':list(t),'translation_sign':sign,
        'radius':k,'remove_X':sorted(removals),'add_X':adds,'required_owner_removals':sorted(needed),
        'private_pairs':[list(z) for z in pairs],'orientation':list(orient),'PH':PH,'PV':PV,
        'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'setup':setup,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps(st,sort_keys=True),flush=True)

if __name__=='__main__': main()
