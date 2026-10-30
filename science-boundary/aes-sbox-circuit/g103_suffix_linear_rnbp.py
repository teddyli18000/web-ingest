#!/usr/bin/env python3
"""Resynthesize the pure-linear suffix of the 32-AND NIST G103 AES circuit.

The last nonlinear gate is a32. Everything after it is a 22-gate XOR/XNOR
network. Treat the 17 wires crossing that cut as independent affine inputs and
synthesize the exact eight-output linear map with Boyar-Peralta support distance.

For this pure-linear subproblem, quotient out the affine constant coordinate:
with a two-input XOR/XNOR gate, either output polarity costs one gate, so support
distance depends only on the 17-dimensional linear part. Exact polarity is chosen
again when a target output is materialized. This prevents high-weight affine
outputs from becoming artificial INF targets and gives an exact BP distance over
the represented linear map.

A suffix of 19 gates already gives 32 AND + 49 prefix-linear + 19 suffix = 100.
A 20/21-gate suffix is useful with an independently compressed prefix.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import time
from collections import defaultdict

import released_and_skeleton as ras


def split(c):
    last=max(i for i,g in enumerate(c['gates']) if g['op']=='AND')
    prefix=[dict(g) for g in c['gates'][:last+1]]
    suffix=[dict(g) for g in c['gates'][last+1:]]
    assert all(g['op']!='AND' for g in suffix)
    produced_suffix={g['out'] for g in suffix}
    boundary=[];seen=set()
    for g in suffix:
        for w in (g['a'],g['b']):
            if w not in produced_suffix and w not in seen:
                seen.add(w);boundary.append(w)
    return last,prefix,suffix,boundary


def formal_suffix(suffix,boundary,outputs):
    m=len(boundary);C=1<<m
    vals={w:1<<i for i,w in enumerate(boundary)}
    guide=set()
    for g in suffix:
        a,b=vals[g['a']],vals[g['b']]
        vals[g['out']]=a^b^(C if g['op']=='XNOR' else 0)
        guide.add(vals[g['out']]&(C-1))
    targets=[vals[o] for o in outputs]
    qtargets=[t&(C-1) for t in targets]
    assert len(set(qtargets))==len(qtargets),qtargets
    return m,C,vals,targets,qtargets,guide


def init_sx(S,K):
    sx=[set() for _ in range(K+1)];sx[0]={0}
    for w in S:
        for k in range(K,1,-1):sx[k].update(w^v for v in sx[k-1])
        sx[1].add(w)
    return sx


def add_sx(sx,w):
    for k in range(len(sx)-1,1,-1):sx[k].update(w^v for v in sx[k-1])
    sx[1].add(w)


def pair_map(S):
    xs=list(S);out={}
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            v=a^b
            if v and v not in S:out.setdefault(v,(a,b))
    return out


def reducer_map(Dist,targets,WD,sx):
    reducers=defaultdict(set)
    for i,d in enumerate(Dist):
        if d<=0:continue
        r=d-1
        if r>=len(sx):continue
        for w in WD:
            if (targets[i]^w) in sx[r]:reducers[w].add(i)
    return reducers


def synthesize(c,seed,budget,max_support=10,elite=24,policy='classic'):
    last,prefix,orig_suffix,boundary=split(c)
    m,C,vals,targets,qtargets,guide=formal_suffix(orig_suffix,boundary,c['outputs'])
    S={1<<i for i in range(m)};sx=init_sx(S,max_support)
    # quotient vector -> concrete wire + exact affine vector (with constant bit)
    names={1<<i:boundary[i] for i in range(m)}
    exact={1<<i:1<<i for i in range(m)}
    Dist=[q.bit_count()-1 for q in qtargets]
    rng=random.Random(seed);gates=[];trace=[]

    while len(gates)<budget and any(d!=0 for d in Dist):
        WD=pair_map(S);reducers=reducer_map(Dist,qtargets,WD,sx)
        ones=[i for i,d in enumerate(Dist) if d==1 and qtargets[i] in WD]
        if ones:
            i=rng.choice(ones);w=qtargets[i]
            reductions=sorted(reducers.get(w,set()))
            if i not in reductions:reductions.append(i);reductions.sort()
            preempt=True
        else:
            if not reducers:
                return None,{'status':'stuck','seed':seed,'budget':budget,'used':len(gates),
                             'policy':policy,'dist':Dist,'boundary':boundary,'trace_tail':trace[-12:]}
            scored=[]
            for w,inds0 in reducers.items():
                inds=sorted(inds0);count=len(inds);penalty=sum(2*Dist[i]-1 for i in inds)
                isguide=1 if w in guide else 0
                if policy=='hard':key=(-count,-penalty,w)
                elif policy=='guide':key=(-count,penalty,-isguide,w)
                else:key=(-count,penalty,w)
                scored.append((key,w,inds))
            scored.sort(key=lambda z:z[0]);best=scored[0][0][:-1]
            pool=[z for z in scored if z[0][:-1]==best][:max(1,elite)]
            _,w,reductions=rng.choice(pool);preempt=False

        a,b=WD[w]
        xor_exact=exact[a]^exact[b]
        desired=xor_exact
        target_hits=[i for i,q in enumerate(qtargets) if q==w]
        if target_hits:
            # Distinct output linear parts were asserted above. Materialize the
            # exact requested polarity immediately when its quotient appears.
            desired=targets[target_hits[0]]
        op='XOR' if xor_exact==desired else 'XNOR'
        if op=='XNOR':assert xor_exact^C==desired
        out=f'__suffix_{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:Dist[i]-=1
        S.add(w);names[w]=out;exact[w]=desired;add_sx(sx,w)
        rec={'used':len(gates),'dist':list(Dist),'reductions':len(reductions),
             'preemptive':preempt,'reducing_candidates':len(reducers),'policy':policy}
        trace.append(rec)

    if any(d!=0 for d in Dist):
        return None,{'status':'budget_exhausted','seed':seed,'budget':budget,'used':len(gates),
                     'policy':policy,'dist':Dist,'boundary':boundary,'trace_tail':trace[-12:]}
    out_names=[names[q] for q in qtargets]
    # Sanity: each chosen output wire has the exact requested affine polarity.
    for q,t in zip(qtargets,targets):assert exact[q]==t,(q,exact[q],t)
    suffix={'gates':gates,'outputs':out_names,'boundary':boundary}
    full=ras.prune({'gates':prefix+gates,'outputs':out_names})
    ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('reattached suffix failed AES',ok))
    return (suffix,full),{'status':'found','seed':seed,'budget':budget,'used':len(gates),
                          'policy':policy,'boundary':boundary,'original_suffix_gates':len(orig_suffix),
                          'original_prefix_gates':len(prefix),'full_gates':len(full['gates']),
                          'verified_all_256':True,'trace_tail':trace[-12:]}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--family',choices=['nist-g103'],default='nist-g103')
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--budget',type=int,required=True)
    ap.add_argument('--max-support',type=int,default=10);ap.add_argument('--elite',type=int,default=24)
    ap.add_argument('--policy',choices=['classic','hard','guide'],default='classic')
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit(args.family);assert ras.independent_check(c)[0]
    t0=time.time();res,s=synthesize(c,args.seed,args.budget,args.max_support,args.elite,args.policy)
    s['elapsed_s']=round(time.time()-t0,3)
    if res is not None:
        suffix,full=res
        (out/'suffix.json').write_text(json.dumps(suffix,indent=2)+'\n')
        (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__':main()
