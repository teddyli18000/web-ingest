#!/usr/bin/env python3
"""Exact radius-5 repair by bounded support-union closure.

For a one-hit translated auxiliary S, any 5-for-5 repair removes the mandatory
bad point plus at most four other old points.  For every possible new point y,
let supp(y) be the old non-bad points conflicting with y.  A radius-5 repair is
therefore exactly five pairwise nonconflicting new points outside S and D whose
support union has size at most four.

Rather than encode the owner-cardinality constraint in SAT, compute the complete
closure of support masks under union while the union has at most four owners.
For each reachable owner mask U, the usable new points are exactly those with
support contained in U.  Exhaustively test whether this small pool contains an
independent 5-set.  This is equivalent to the compact radius-5 SAT but avoids its
hard global cardinality search.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f
import bpz_t9_translation_radius_compact as rc

Q=7; D=5; U=Q**D; N=367; TARGET=N*N+9*9


def find_independent5(pool, ring):
    chosen=[]
    def dfs(start):
        need=5-len(chosen)
        if need==0: return tuple(chosen)
        if len(pool)-start<need: return None
        for i in range(start,len(pool)):
            v=pool[i]
            if any(v in ring.NB[u] for u in chosen): continue
            chosen.append(v)
            z=dfs(i+1)
            if z is not None: return z
            chosen.pop()
        return None
    return dfs(0)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path)
    ap.add_argument('output',type=Path); ap.add_argument('status',type=Path)
    ap.add_argument('--near-index',type=int,required=True)
    args=ap.parse_args()

    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import Ring
    ring=Ring(D); digits=tuple(ring.decode(v) for v in range(U))
    raw=json.loads((root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0']))
    nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    obs=f.obstruction_witnesses(I0,ring,digits,nb)
    near=rc.find_near_states(root,args.family_root,ring,digits,obs)
    if not 0<=args.near_index<len(near): raise SystemExit('near-index out of range')
    name,oi,t,sign,S,bad,Dset,witness=near[args.near_index]

    owners=sorted(S-{bad}); owner_pos={x:i for i,x in enumerate(owners)}; Sset=set(S)
    groups={}; hist={}
    for y in range(U):
        if y in Sset or y in Dset: continue
        m=0
        for x in ring.NB[y]:
            i=owner_pos.get(x)
            if i is not None: m |= 1<<i
        bc=m.bit_count(); hist[bc]=hist.get(bc,0)+1
        if bc<=4: groups.setdefault(m,[]).append(y)
    if 0 in groups:
        # A support-zero point would already give a radius-1 repair, contradicting
        # the exact one-repair scan; keep this as a strong cross-check.
        raise RuntimeError(f'unexpected support-zero candidates: {groups[0][:10]}')

    base=sorted(groups)
    expanders=[m for m in base if m.bit_count()<4]
    reachable=set(base)
    frontier=set(expanders)
    rounds=0; unions_tested=0
    while frontier:
        rounds+=1; new=set()
        for a in frontier:
            for b in expanders:
                unions_tested+=1
                u=a|b
                if u.bit_count()>4 or u in reachable: continue
                new.add(u)
        if not new: break
        reachable.update(new)
        frontier={m for m in new if m.bit_count()<4}

    masks=sorted(reachable,key=lambda m:(m.bit_count(),m))
    eligible_masks=0; pools_tested=0; max_pool=0; vertices_scanned=0
    winner=None
    for owner_mask in masks:
        pool=[]
        sub=owner_mask
        while sub:
            pool.extend(groups.get(sub,()))
            sub=(sub-1)&owner_mask
        # support zero was asserted absent.
        if len(pool)<5: continue
        eligible_masks+=1; max_pool=max(max_pool,len(pool)); vertices_scanned+=len(pool)
        pool=sorted(set(pool))
        if len(pool)<5: continue
        pools_tested+=1
        add=find_independent5(pool,ring)
        if add is None: continue
        needed=set()
        for i,x in enumerate(owners):
            if owner_mask>>i & 1: needed.add(x)
        # The independent set may use only a strict subset of owner_mask. Recompute
        # exact required owners from the selected additions before replay.
        exact_needed=set()
        for y in add:
            for x in ring.NB[y]:
                if x in owner_pos: exact_needed.add(x)
        if len(exact_needed)>4: raise RuntimeError('owner-union replay overflow')
        removals={bad}|exact_needed
        for x in owners:
            if len(removals)>=5: break
            if x not in removals: removals.add(x)
        repaired=(S-removals)|set(add)
        if len(repaired)!=N or repaired&Dset or not f.independent(repaired,digits):
            raise RuntimeError('radius5 replay failed')
        winner=(owner_mask,add,removals,exact_needed,repaired,witness,len(pool))
        break

    setup={
        'near_index':args.near_index,'seed':name,'obstruction_index':oi,
        'translation':list(t),'translation_sign':sign,'mandatory_bad':bad,
        'obstruction_size':len(Dset),'support_size_histogram':{str(a):b for a,b in sorted(hist.items())},
        'support_groups':len(groups),'expander_support_masks':len(expanders),
        'reachable_owner_masks':len(reachable),'closure_rounds':rounds,'union_operations_tested':unions_tested,
        'eligible_owner_masks':eligible_masks,'pools_tested':pools_tested,'pool_vertices_scanned':vertices_scanned,
        'max_candidate_pool':max_pool,'radius':5,'target_10d_score':TARGET,
    }
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        st={'candidate':False,'method':'bpz-t9-translated-exact-radius5-support-union','score':134753,'setup':setup}
        args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(st,sort_keys=True),flush=True); return

    owner_mask,add,removals,needed,repaired,witness,pool_size=winner
    Ibits,pairs,orient,PH,PV=witness
    points,xp=f.build(Ibits,sum(1<<z for z in repaired),pairs,PH,PV,ring)
    if len(points)!=TARGET: raise RuntimeError(f'target score drift {len(points)}')
    st={
        'candidate':True,'method':'bpz-t9-translated-exact-radius5-support-union','score':len(points),
        'near_index':args.near_index,'seed':name,'obstruction_index':oi,'translation':list(t),'translation_sign':sign,
        'remove_X':sorted(removals),'add_X':list(add),'required_owner_removals':sorted(needed),
        'winning_pool_size':pool_size,'private_pairs':[list(z) for z in pairs],'orientation':list(orient),
        'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'setup':setup,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps(st,sort_keys=True),flush=True)

if __name__=='__main__': main()
