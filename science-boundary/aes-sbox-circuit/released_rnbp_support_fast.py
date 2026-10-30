#!/usr/bin/env python3
"""Faster exact-support released-AND RNBP.

This preserves the search semantics of released_rnbp_support_synth.py but avoids
scanning every candidate pair for targets whose current Boyar-Peralta distance is
small.  If a target has distance d, a new helper w reduces it iff target XOR w
(or, when legal, target XOR w XOR affine-constant) is representable by exactly
(d-1) old signals.  For d-1 <= 4 those old-support XOR sets are already cached,
so reducer helpers can be generated directly from the target.  Only higher
support distances fall back to recursive pair-by-pair testing.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import time

import released_and_skeleton as ras
import released_rnbp_support_synth as rr

INF=rr.INF


def reducer_map(Dist, targets, WD, S, sx, C):
    reducers=collections.defaultdict(set)
    fallback=[]
    for i,d in enumerate(Dist):
        if not (0<d<INF):
            continue
        r=d-1
        if r<=4:
            for u in sx[r]:
                w=targets[i]^u
                if w in WD:
                    reducers[w].add(i)
                if r>=1:
                    wn=targets[i]^C^u
                    if wn in WD:
                        reducers[wn].add(i)
        else:
            fallback.append(i)
    if fallback:
        for w in WD:
            for i in fallback:
                if rr.candidate_reduces(S,sx,targets[i],C,Dist[i],w):
                    reducers[w].add(i)
    return reducers, fallback


def synthesize(base,seed,max_linear=67,max_support=9,elite=1):
    sk=ras.extract_skeleton(base); C=1<<sk['const_bit']
    rows=rr.target_rows(sk); targets=[t for t,_ in rows]
    rng=random.Random(seed)
    S={1<<i for i in range(8)}; sx=rr.init_sx(S)
    names={1<<i:f'x{i}' for i in range(8)}
    gates=[]; released=set(); linear=0; trace=[]
    rr.release_ready(sk,S,sx,names,gates,released)
    Dist=[rr.min_distance(S,sx,t,C,max_support) for t in targets]

    while linear<max_linear and any(d!=0 for d in Dist):
        added_ands=rr.release_ready(sk,S,sx,names,gates,released)
        if added_ands:
            rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        if all(d==0 for d in Dist):
            break

        WD=rr.pair_candidates(S,C)
        reducers,fallback=reducer_map(Dist,targets,WD,S,sx,C)
        ones=[i for i,d in enumerate(Dist) if d==1]
        preempt=False
        if ones:
            choices=[i for i in ones if targets[i] in WD]
            if not choices:
                raise AssertionError(('distance1 without pair witness',ones))
            w=targets[choices[0]]; preempt=True
            reductions=sorted(reducers.get(w,set()))
            if choices[0] not in reductions:
                reductions.append(choices[0]); reductions.sort()
        else:
            if not reducers:
                finite=[d for d in Dist if 0<d<INF]
                return None,{'status':'stuck_no_reducing_pair','seed':seed,'linear':linear,
                             'released_ands':len(released),'finite_distances':finite,
                             'trace_tail':trace[-20:]}
            # Minimizing sum(Dist) is exactly maximizing the number of one-step
            # reductions.  With equal count, maximizing the post-step squared
            # norm is equivalent to minimizing sum(2*d-1) over reduced targets.
            scored=[]
            for w,inds in reducers.items():
                inds=sorted(inds)
                count=len(inds)
                penalty=sum(2*Dist[i]-1 for i in inds)
                scored.append((-count,penalty,w,inds))
            scored.sort(key=lambda x:(x[0],x[1],x[2]))
            bestkey=scored[0][:2]
            pool=[x for x in scored if x[:2]==bestkey]
            pool=pool[:max(1,elite)] if elite>0 else pool
            _,_,w,reductions=rng.choice(pool)

        op,a,b=WD[w]
        out=f'w{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:
            Dist[i]-=1
        S.add(w); names[w]=out; rr.add_sx(sx,w); linear+=1

        rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        added_ands=rr.release_ready(sk,S,sx,names,gates,released)
        if added_ands:
            rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)

        rec={'linear':linear,'released_ands':len(released),
             'positive_sum':sum(d for d in Dist if 0<d<INF),
             'finite_remaining':sum(0<d<INF for d in Dist),
             'inf_remaining':sum(d==INF for d in Dist),
             'preemptive':preempt,'pair_candidates':len(WD),
             'reducing_candidates':len(reducers),'fallback_targets':len(fallback),
             'reductions':len(reductions),'new_ands':added_ands}
        trace.append(rec)
        print(json.dumps({'progress':rec,'seed':seed}),flush=True)

    if any(d!=0 for d in Dist):
        return None,{'status':'budget_exhausted','seed':seed,'linear':linear,
                     'released_ands':len(released),'dist':Dist,'trace_tail':trace[-20:]}
    outs=[names[t] for t in sk['outputs']]
    c=ras.prune({'gates':gates,'outputs':outs})
    ok=ras.independent_check(c)
    if not ok[0]:
        raise AssertionError(('AES check failed',ok))
    summary={'status':'found','seed':seed,'linear':linear,
             'released_ands':len(released),'candidate_gates':len(c['gates']),
             'candidate_stats':dict(collections.Counter(g['op'] for g in c['gates'])),
             'verified_all_256':True,'trace_tail':trace[-20:]}
    return c,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=sorted(ras.SOURCES),default='fs-101')
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--max-linear',type=int,default=67)
    ap.add_argument('--max-support',type=int,default=9)
    ap.add_argument('--elite',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    t0=time.time(); c,s=synthesize(base,args.seed,args.max_linear,args.max_support,args.elite)
    s['elapsed_s']=round(time.time()-t0,3)
    if c is not None:
        (out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__':
    main()
