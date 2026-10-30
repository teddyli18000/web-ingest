#!/usr/bin/env python3
"""Compress the NIST G103 nonlinear prefix while preserving its suffix interface.

Cut immediately after the last AND (a32).  The original circuit has 49 linear
helpers before/on that cut and a 22-gate pure-linear suffix.  The suffix boundary
contains many AND outputs plus only three non-atomic linear values (t47,t48,t49).

This search uses strict released-AND Boyar-Peralta support distance on all exact
AND operands plus the non-atomic boundary values, targeting 47 prefix-linear
gates.  A 47-linear boundary-preserving prefix plus an independently synthesized
21-gate suffix would give exactly 100 total gates.

Any completed prefix is reattached to the untouched original suffix and verified
on all 256 AES inputs; this gives a 101-gate intermediate certificate if the
47-linear target is met.
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
    prod_suffix={g['out'] for g in suffix};boundary=[];seen=set()
    for g in suffix:
        for w in (g['a'],g['b']):
            if w not in prod_suffix and w not in seen:
                seen.add(w);boundary.append(w)
    return last,prefix,suffix,boundary


def wire_vectors(c):
    sk=ras.extract_skeleton(c);C=1<<sk['const_bit']
    vals={f'x{i}':1<<i for i in range(8)};linear_vecs=set();and_no=0
    for g in c['gates']:
        a,b=vals[g['a']],vals[g['b']]
        if g['op']=='XOR':v=a^b;linear_vecs.add(v)
        elif g['op']=='XNOR':v=a^b^C;linear_vecs.add(v)
        elif g['op']=='AND':v=1<<(8+and_no);and_no+=1
        else:raise ValueError(g['op'])
        vals[g['out']]=v
    return sk,C,vals,linear_vecs


def reattach_original_suffix(c,suffix,boundary,vals,names,prefix_gates):
    mp={w:names[vals[w]] for w in boundary}
    gates=[dict(g) for g in prefix_gates]
    for j,g in enumerate(suffix):
        ng=dict(g)
        ng['a']=mp.get(g['a'],g['a']);ng['b']=mp.get(g['b'],g['b'])
        new=f'__orig_suffix_{j}'
        mp[g['out']]=new;ng['out']=new;gates.append(ng)
    outs=[mp[o] for o in c['outputs']]
    return ras.prune({'gates':gates,'outputs':outs})


def synthesize(c,seed,budget=47,max_support=8,elite=12,extra_weight=3,guide=True):
    sk,C,vals,linear_vecs=wire_vectors(c)
    last,orig_prefix,suffix,boundary=split(c)
    atoms={1<<i for i in range(8+sk['n_and'])}
    extras=[w for w in boundary if vals[w] not in atoms]
    assert extras==['t47','t48','t49'],extras

    targets=[];labels=[]
    for i,ab in enumerate(sk['ands']):
        targets += [ab['a'],ab['b']];labels += [f'a{i}',f'b{i}']
    for w in extras:
        for k in range(extra_weight):
            targets.append(vals[w]);labels.append(f'{w}#{k}')

    rng=random.Random(seed);S={1<<i for i in range(8)};sx=rr.init_sx(S)
    names={1<<i:f'x{i}' for i in range(8)};gates=[];released=set();trace=[]
    rr.release_ready(sk,S,sx,names,gates,released)
    Dist=[rr.min_distance(S,sx,t,C,max_support) for t in targets]

    while len([g for g in gates if g['op']!='AND'])<budget and any(d!=0 for d in Dist):
        added=rr.release_ready(sk,S,sx,names,gates,released)
        if added:rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        WD=rr.pair_candidates(S,C);reducers,fallback=rf.reducer_map(Dist,targets,WD,S,sx,C)
        ones=[i for i,d in enumerate(Dist) if d==1]
        if ones:
            choices=[i for i in ones if targets[i] in WD]
            if not choices:raise AssertionError(('distance1 without witness',ones))
            # Prefer required boundary values when they become ready.
            choices.sort(key=lambda i:(0 if labels[i].startswith('t') else 1,i))
            i=choices[0];w=targets[i]
            reductions=sorted(reducers.get(w,set()))
            if i not in reductions:reductions.append(i);reductions.sort()
            preempt=True
        else:
            if not reducers:
                return None,{'status':'stuck','seed':seed,'linear':sum(g['op']!='AND' for g in gates),
                             'released_ands':len(released),'dist':Dist,'extras':extras,'trace_tail':trace[-16:]}
            scored=[]
            for w,inds0 in reducers.items():
                inds=sorted(inds0);count=len(inds);penalty=sum(2*Dist[i]-1 for i in inds)
                isguide=1 if (guide and w in linear_vecs) else 0
                # Boundary-target reductions are a tertiary preference after the
                # exact BP sum/norm criteria; duplication via extra_weight is the
                # primary explicit coupling pressure.
                bcount=sum(labels[i].startswith('t') for i in inds)
                scored.append((-count,penalty,-bcount,-isguide,w,inds))
            scored.sort(key=lambda z:z[:-1]);best=scored[0][:-2]
            pool=[z for z in scored if z[:-2]==best][:max(1,elite)]
            *_,w,reductions=rng.choice(pool);preempt=False
        op,a,b=WD[w];out=f'w{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:Dist[i]-=1
        S.add(w);names[w]=out;rr.add_sx(sx,w)
        rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        added=rr.release_ready(sk,S,sx,names,gates,released)
        if added:rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        rec={'linear':sum(g['op']!='AND' for g in gates),'released_ands':len(released),
             'extras_ready':{w:(vals[w] in S) for w in extras},
             'positive_sum':sum(d for d in Dist if 0<d<INF),'inf_remaining':sum(d==INF for d in Dist),
             'reductions':len(reductions),'fallback_targets':len(fallback),'preemptive':preempt}
        trace.append(rec);print(json.dumps({'progress':rec,'seed':seed}),flush=True)

    linear=sum(g['op']!='AND' for g in gates)
    if any(d!=0 for d in Dist) or len(released)!=sk['n_and']:
        return None,{'status':'budget_exhausted','seed':seed,'linear':linear,
                     'released_ands':len(released),'extras_ready':{w:(vals[w] in S) for w in extras},
                     'dist':Dist,'trace_tail':trace[-16:]}
    for w in boundary:
        if vals[w] not in names:raise AssertionError(('missing boundary',w))
    full=reattach_original_suffix(c,suffix,boundary,vals,names,gates)
    ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('reattached original suffix failed AES',ok))
    prefix={'gates':gates,'boundary_map':{w:names[vals[w]] for w in boundary},'extras':extras}
    return (prefix,full),{'status':'found','seed':seed,'linear':linear,'released_ands':len(released),
                          'extra_weight':extra_weight,'extras':extras,'boundary_count':len(boundary),
                          'original_prefix_linear':sum(g['op']!='AND' for g in orig_prefix),
                          'original_suffix_gates':len(suffix),'full_gates':len(full['gates']),
                          'verified_all_256':True,'trace_tail':trace[-16:]}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--family',choices=['nist-g103'],default='nist-g103')
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--budget',type=int,default=47)
    ap.add_argument('--max-support',type=int,default=8);ap.add_argument('--elite',type=int,default=12)
    ap.add_argument('--extra-weight',type=int,default=3);ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit(args.family);assert ras.independent_check(c)[0]
    t0=time.time();res,s=synthesize(c,args.seed,args.budget,args.max_support,args.elite,args.extra_weight,True)
    s['elapsed_s']=round(time.time()-t0,3)
    if res is not None:
        prefix,full=res
        (out/'prefix.json').write_text(json.dumps(prefix,indent=2)+'\n')
        (out/'full-original-suffix.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__':main()
