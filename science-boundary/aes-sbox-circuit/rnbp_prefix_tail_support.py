#!/usr/bin/env python3
"""Constructive true-support RNBP tails for the two 56-linear AES prefixes.

All 33 AND atoms have already been released, so this is a pure affine multi-target
problem over 97 available signals.  Unlike the exact ordered Z3 schedule, this
heuristic can cheaply explore many output-sharing orders.  AES outputs are normal
signals once generated and may feed later outputs.  Any <=11-gate tail produces
a <=100-gate complete circuit and is independently verified on all 256 inputs.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import time

import released_and_skeleton as ras
import rnbp_prefix_variant_tail as pv
import released_rnbp_support_synth as rr
import released_rnbp_support_fast as rf

INF=rr.INF


def synth_tail(base,weight,dev_index,dev_rank,seed,max_tail=11,max_support=10,elite=8):
    sk,S,names,prefix_gates,plin,stage,soft,applied,trace=pv.build_variant(
        base,weight,dev_index,dev_rank,67)
    if not applied or stage!=sk['n_and']:
        return None,{'status':'prefix_incomplete','prefix_linear':plin,'released_ands':stage}
    assert plin==56,(dev_index,dev_rank,plin)
    C=1<<sk['const_bit']; targets=list(sk['outputs'])
    S=set(S); names=dict(names); gates=[dict(g) for g in prefix_gates]
    sx=rr.init_sx(S); rng=random.Random(seed); tail=0; ttrace=[]
    Dist=[rr.min_distance(S,sx,t,C,max_support) for t in targets]

    while tail<max_tail and any(d!=0 for d in Dist):
        WD=rr.pair_candidates(S,C)
        reducers,fallback=rf.reducer_map(Dist,targets,WD,S,sx,C)
        ones=[i for i,d in enumerate(Dist) if d==1]
        preempt=False
        if ones:
            choices=[i for i in ones if targets[i] in WD]
            if not choices:
                raise AssertionError(('distance1 without pair witness',ones))
            # Randomize which ready output is emitted first; it becomes available
            # for subsequent shared output logic.
            i=rng.choice(choices); w=targets[i]; preempt=True
            reductions=sorted(reducers.get(w,set()))
            if i not in reductions: reductions.append(i); reductions.sort()
        else:
            if not reducers:
                return None,{'status':'stuck','prefix_linear':plin,'tail':tail,
                             'dist':Dist,'fallback_targets':fallback,
                             'trace_tail':ttrace[-12:]}
            scored=[]
            for w,inds in reducers.items():
                inds=sorted(inds); count=len(inds)
                penalty=sum(2*Dist[i]-1 for i in inds)
                # Secondary density term: helpers closer to exact output values
                # are preferred only after the BP sum/norm criteria.
                closeness=sum(min((targets[i]^w).bit_count(),
                                  (targets[i]^w^C).bit_count()) for i in range(8))
                scored.append((-count,penalty,closeness,w,inds))
            scored.sort(key=lambda x:(x[0],x[1],x[2],x[3]))
            # Diversify across the best few BP-equivalent / near-equivalent moves.
            best_count=scored[0][0]
            pool=[x for x in scored if x[0]==best_count][:max(1,elite)]
            _,_,_,w,reductions=rng.choice(pool)

        op,a,b=WD[w]; out=f'__tail_rnbp_{tail}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions: Dist[i]-=1
        S.add(w); names[w]=out; rr.add_sx(sx,w); tail+=1
        rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        rec={'tail':tail,'dist':list(Dist),'preemptive':preempt,
             'reductions':len(reductions),'reducing_candidates':len(reducers),
             'fallback_targets':len(fallback)}
        ttrace.append(rec)
        print(json.dumps({'progress':rec,'seed':seed,'variant':f'd{dev_index}r{dev_rank}'}),flush=True)

    if any(d!=0 for d in Dist):
        return None,{'status':'budget_exhausted','prefix_linear':plin,'tail':tail,
                     'dist':Dist,'trace_tail':ttrace[-12:]}
    c=ras.prune({'gates':gates,'outputs':[names[t] for t in targets]})
    ok=ras.independent_check(c)
    if not ok[0]: raise AssertionError(('AES check failed',ok))
    return c,{'status':'found','prefix_linear':plin,'tail':tail,
              'candidate_gates':len(c['gates']),
              'candidate_stats':dict(collections.Counter(g['op'] for g in c['gates'])),
              'verified_all_256':True,'trace_tail':ttrace[-12:]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=sorted(ras.SOURCES),default='fs-101')
    ap.add_argument('--deviation-index',type=int,required=True)
    ap.add_argument('--deviation-rank',type=int,required=True)
    ap.add_argument('--projection-weight',type=float,default=0.24)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--max-tail',type=int,default=11)
    ap.add_argument('--max-support',type=int,default=10)
    ap.add_argument('--elite',type=int,default=8)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    t0=time.time(); c,s=synth_tail(base,args.projection_weight,args.deviation_index,
                                   args.deviation_rank,args.seed,args.max_tail,
                                   args.max_support,args.elite)
    s.update({'seed':args.seed,'deviation_index':args.deviation_index,
              'deviation_rank':args.deviation_rank,'elapsed_s':round(time.time()-t0,3)})
    if c is not None: (out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__': main()
