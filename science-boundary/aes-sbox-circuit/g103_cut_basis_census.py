#!/usr/bin/env python3
"""Enumerate all 168 invertible bases of the three non-atomic G103 cut signals.

Cut immediately after the last AND a32.  The pure-linear suffix consumes 17
boundary signals, of which exactly t47,t48,t49 are non-atomic linear values.  A
prefix does not intrinsically need to expose those three named functions: any
ordered basis of their 3-dimensional GF(2) span is an equally valid interface if
the suffix is synthesized in the transformed coordinates.

This script enumerates GL(3,2), rewrites the eight suffix output linear forms and
all original suffix guide functions into each transformed cut basis, and runs a
small true-support RNBP portfolio.  It is a cheap interface census used to rank
bases before expensive prefix synthesis.  A heuristic miss is not a lower bound.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import random
from collections import defaultdict

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf


def rank3(rows):
    basis=[]
    for x in rows:
        y=x
        for b in basis:
            y=min(y,y^b)
        if y:
            basis.append(y)
            basis.sort(reverse=True)
    return len(basis)


def gl3():
    for rows in itertools.permutations(range(1,8),3):
        if rank3(rows)==3:
            yield rows


def coeff_map(rows):
    """old 3-bit coefficient mask -> new-basis 3-bit coefficient mask."""
    out={}
    for d in range(8):
        c=0
        for j in range(3):
            if (d>>j)&1:c^=rows[j]
        out[c]=d
    assert len(out)==8
    return out


def transform_mask(mask,extra_idx,cmap):
    c=0
    for k,idx in enumerate(extra_idx):
        if (mask>>idx)&1:c|=1<<k
    d=cmap[c]
    out=mask
    for idx in extra_idx:out&=~(1<<idx)
    for k,idx in enumerate(extra_idx):
        if (d>>k)&1:out|=1<<idx
    return out


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
        if d<=0 or d>=len(sx):continue
        r=d-1
        support=sx[r]
        for w in WD:
            if (targets[i]^w) in support:reducers[w].add(i)
    return reducers


def rnbp_cost(targets,guide,seed,policy,max_gates,max_support,elite):
    n=max(t.bit_length() for t in targets)
    S={1<<i for i in range(n)};sx=init_sx(S,max_support)
    Dist=[t.bit_count()-1 for t in targets]
    rng=random.Random(seed);used=0
    while used<max_gates and any(d!=0 for d in Dist):
        WD=pair_map(S);reducers=reducer_map(Dist,targets,WD,sx)
        ones=[i for i,d in enumerate(Dist) if d==1 and targets[i] in WD]
        if ones:
            i=rng.choice(ones);w=targets[i]
            inds=sorted(reducers.get(w,set()))
            if i not in inds:inds.append(i);inds.sort()
        else:
            if not reducers:return None,Dist
            scored=[]
            for w,inds0 in reducers.items():
                inds=sorted(inds0);count=len(inds);penalty=sum(2*Dist[i]-1 for i in inds)
                g=1 if w in guide else 0
                if policy=='hard': key=(-count,-penalty,w)
                elif policy=='guide': key=(-count,penalty,-g,w)
                else: key=(-count,penalty,w)
                scored.append((key,w,inds))
            scored.sort(key=lambda z:z[0])
            # Treat the final vector field as a deterministic tie breaker only;
            # diversify among the best primary BP score class.
            primary=scored[0][0][:-1]
            pool=[z for z in scored if z[0][:-1]==primary][:max(1,elite)]
            _,w,inds=rng.choice(pool)
        S.add(w);add_sx(sx,w);used+=1
        for i in inds:Dist[i]-=1
    return (used if all(d==0 for d in Dist) else None),Dist


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=['nist-g103'],default='nist-g103')
    ap.add_argument('--seeds',type=int,default=8)
    ap.add_argument('--max-gates',type=int,default=22)
    ap.add_argument('--max-support',type=int,default=10)
    ap.add_argument('--elite',type=int,default=24)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)

    c=ras.load_circuit(args.family);assert ras.independent_check(c)[0]
    last,prefix,suffix,boundary=suf.split(c)
    m,C,vals,aff_targets,qtargets,orig_guide=suf.formal_suffix(suffix,boundary,c['outputs'])
    extras=['t47','t48','t49'];extra_idx=[boundary.index(w) for w in extras]
    # Recreate every original suffix intermediate quotient as a guide vector.
    qvals={w:1<<i for i,w in enumerate(boundary)};guide=[]
    for g in suffix:
        q=qvals[g['a']]^qvals[g['b']]
        qvals[g['out']]=q;guide.append(q)

    rows=[]
    for mat in gl3():
        cmap=coeff_map(mat)
        ts=[transform_mask(t,extra_idx,cmap) for t in qtargets]
        gs={transform_mask(g,extra_idx,cmap) for g in guide}
        best=None;best_cfg=None;last_dist=None
        for policy in ('classic','hard','guide'):
            for seed in range(1,args.seeds+1):
                cost,dist=rnbp_cost(ts,gs,seed,policy,args.max_gates,args.max_support,args.elite)
                if cost is not None and (best is None or cost<best):
                    best=cost;best_cfg={'policy':policy,'seed':seed}
                if last_dist is None or sum(dist)<sum(last_dist):last_dist=list(dist)
        rows.append({
            'matrix_rows':list(mat),
            'coeff_map':[cmap[i] for i in range(8)],
            'identity':list(mat)==[1,2,4],
            'initial_supports':[t.bit_count() for t in ts],
            'initial_bp_sum':sum(t.bit_count()-1 for t in ts),
            'best_suffix_gates':best,
            'best_config':best_cfg,
            'best_residual_sum':sum(last_dist) if last_dist is not None else None,
            'best_residual':last_dist,
        })
    assert len(rows)==168,len(rows)
    rows.sort(key=lambda r:(999 if r['best_suffix_gates'] is None else r['best_suffix_gates'],
                            r['initial_bp_sum'],r['matrix_rows']))
    summary={
        'family':args.family,'cut_after_last_and':last,'boundary_count':len(boundary),
        'extras':extras,'extra_indices':extra_idx,'matrices':len(rows),
        'searched_seeds':args.seeds,'max_gates':args.max_gates,
        'found_le_19':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=19 for r in rows),
        'found_le_20':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=20 for r in rows),
        'found_le_21':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=21 for r in rows),
        'found_le_22':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=22 for r in rows),
        'top':rows[:40],
        'all':rows,
    }
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('top','all')},sort_keys=True),flush=True)
    for r in rows[:20]:print(json.dumps(r,sort_keys=True),flush=True)

if __name__=='__main__':main()
