#!/usr/bin/env python3
"""Resynthesize the pure-linear suffix of the 32-AND NIST G103 AES circuit.

The last nonlinear gate is a32.  Everything after it is a 22-gate XOR/XNOR
network.  Treat the wires crossing that cut as independent affine inputs and
synthesize the exact eight-output linear map with true Boyar-Peralta support
distance.  The resulting suffix is then reattached to the untouched original
prefix and verified on all 256 AES inputs.

A suffix of 19 gates would already give 32 AND + 49 prefix-linear + 19 suffix =
100 total.  A 20/21-gate suffix is still useful when paired with an independently
compressed boundary-preserving prefix.
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
import released_rnbp_support_fast as rf

INF=rr.INF


def split(c):
    last=max(i for i,g in enumerate(c['gates']) if g['op']=='AND')
    prefix=[dict(g) for g in c['gates'][:last+1]]
    suffix=[dict(g) for g in c['gates'][last+1:]]
    assert all(g['op']!='AND' for g in suffix)
    produced_suffix={g['out'] for g in suffix}
    boundary=[]
    seen=set()
    for g in suffix:
        for w in (g['a'],g['b']):
            if w not in produced_suffix and w not in seen:
                seen.add(w);boundary.append(w)
    return last,prefix,suffix,boundary


def formal_suffix(suffix,boundary,outputs):
    m=len(boundary);C=1<<m
    vals={w:1<<i for i,w in enumerate(boundary)}
    for g in suffix:
        a,b=vals[g['a']],vals[g['b']]
        vals[g['out']]=a^b^(C if g['op']=='XNOR' else 0)
    return m,C,vals,[vals[o] for o in outputs]


def synthesize(c,seed,budget,max_support=8,elite=16):
    last,prefix,orig_suffix,boundary=split(c)
    m,C,vals,targets=formal_suffix(orig_suffix,boundary,c['outputs'])
    S={1<<i for i in range(m)};sx=rr.init_sx(S)
    names={1<<i:boundary[i] for i in range(m)}
    rng=random.Random(seed);gates=[];Dist=[rr.min_distance(S,sx,t,C,max_support) for t in targets]
    trace=[]
    while len(gates)<budget and any(d!=0 for d in Dist):
        WD=rr.pair_candidates(S,C);reducers,fallback=rf.reducer_map(Dist,targets,WD,S,sx,C)
        ones=[i for i,d in enumerate(Dist) if d==1]
        if ones:
            choices=[i for i in ones if targets[i] in WD]
            if not choices:raise AssertionError(('distance1 without witness',ones))
            i=rng.choice(choices);w=targets[i]
            reductions=sorted(reducers.get(w,set()))
            if i not in reductions:reductions.append(i);reductions.sort()
            preempt=True
        else:
            if not reducers:
                return None,{'status':'stuck','seed':seed,'budget':budget,'used':len(gates),
                             'dist':Dist,'boundary':boundary,'trace_tail':trace[-12:]}
            scored=[]
            for w,inds0 in reducers.items():
                inds=sorted(inds0);count=len(inds);penalty=sum(2*Dist[i]-1 for i in inds)
                scored.append((-count,penalty,w,inds))
            scored.sort(key=lambda z:(z[0],z[1],z[2]));best=scored[0][:2]
            pool=[z for z in scored if z[:2]==best][:max(1,elite)]
            _,_,w,reductions=rng.choice(pool);preempt=False
        op,a,b=WD[w];out=f'__suffix_{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:Dist[i]-=1
        S.add(w);names[w]=out;rr.add_sx(sx,w)
        rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        rec={'used':len(gates),'dist':list(Dist),'reductions':len(reductions),
             'preemptive':preempt,'reducing_candidates':len(reducers),'fallback_targets':len(fallback)}
        trace.append(rec)
    if any(d!=0 for d in Dist):
        return None,{'status':'budget_exhausted','seed':seed,'budget':budget,'used':len(gates),
                     'dist':Dist,'boundary':boundary,'trace_tail':trace[-12:]}
    suffix={'gates':gates,'outputs':[names[t] for t in targets]}
    full=ras.prune({'gates':prefix+gates,'outputs':suffix['outputs']})
    ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('reattached suffix failed AES',ok))
    return (suffix,full),{'status':'found','seed':seed,'budget':budget,'used':len(gates),
                          'boundary':boundary,'original_suffix_gates':len(orig_suffix),
                          'original_prefix_gates':len(prefix),
                          'full_gates':len(full['gates']),'verified_all_256':True,
                          'trace_tail':trace[-12:]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=['nist-g103'],default='nist-g103')
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--budget',type=int,required=True)
    ap.add_argument('--max-support',type=int,default=8)
    ap.add_argument('--elite',type=int,default=16)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit(args.family);assert ras.independent_check(c)[0]
    t0=time.time();res,s=synthesize(c,args.seed,args.budget,args.max_support,args.elite)
    s['elapsed_s']=round(time.time()-t0,3)
    if res is not None:
        suffix,full=res
        (out/'suffix.json').write_text(json.dumps(suffix,indent=2)+'\n')
        (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__':main()
