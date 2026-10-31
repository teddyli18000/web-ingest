#!/usr/bin/env python3
"""Jointly synthesize the G103 prefix and suffix through a transformed cut basis.

The 103-gate NIST seed has 32 AND gates, 49 linear gates before/on the last-AND
cut, and a 22-gate pure-linear suffix.  Exactly three non-atomic linear signals
cross that cut.  Previous experiments optimized the prefix for the original
three signals and separately ranked GL(3,2) basis changes on the suffix.  This
script couples the two sides: the prefix is asked to materialize a chosen basis
B=R*E, and the suffix is synthesized in the same transformed coordinates.

A run is a constructive heuristic, not a lower bound.  Any <=100 candidate is
independently checked on all 256 AES inputs here and should then be passed to the
Few Shots official verifier by the orchestration workflow.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import time

import released_and_skeleton as ras
import released_rnbp_support_synth as rr
import released_rnbp_support_fast as rf
import g103_boundary_prefix_rnbp as bp
import g103_cut_basis_census as cb
import g103_suffix_linear_rnbp as suf

INF=rr.INF


def parse_rows(text):
    rows=tuple(int(x,0) for x in text.split(','))
    if len(rows)!=3 or cb.rank3(rows)!=3 or any(not 1<=x<8 for x in rows):
        raise argparse.ArgumentTypeError('basis rows must be three independent nonzero 3-bit integers')
    return rows


def basis_vectors(vals,extras,rows):
    old=[vals[w] for w in extras];out=[]
    for row in rows:
        v=0
        for k,x in enumerate(old):
            if (row>>k)&1:v^=x
        out.append(v)
    assert len(set(out))==3
    return out


def synthesize_prefix(c,rows,seed,budget,max_support,elite,extra_weight,guide=True):
    sk,C,vals,linear_vecs=bp.wire_vectors(c)
    last,orig_prefix,orig_suffix,boundary=bp.split(c)
    extras,_=cb.semantic_cut_extras(c,boundary)
    bvecs=basis_vectors(vals,extras,rows)

    targets=[];labels=[]
    for i,ab in enumerate(sk['ands']):
        targets += [ab['a'],ab['b']];labels += [f'a{i}',f'b{i}']
    for j,v in enumerate(bvecs):
        for k in range(extra_weight):
            targets.append(v);labels.append(f'basis{j}#{k}')

    rng=random.Random(seed);S={1<<i for i in range(8)};sx=rr.init_sx(S)
    names={1<<i:f'x{i}' for i in range(8)};gates=[];released=set();trace=[]
    rr.release_ready(sk,S,sx,names,gates,released)
    Dist=[rr.min_distance(S,sx,t,C,max_support) for t in targets]

    while sum(g['op']!='AND' for g in gates)<budget and any(d!=0 for d in Dist):
        added=rr.release_ready(sk,S,sx,names,gates,released)
        if added:rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        WD=rr.pair_candidates(S,C);reducers,fallback=rf.reducer_map(Dist,targets,WD,S,sx,C)
        ones=[i for i,d in enumerate(Dist) if d==1]
        if ones:
            choices=[i for i in ones if targets[i] in WD]
            if not choices:
                raise AssertionError(('distance1 without witness',ones))
            choices.sort(key=lambda i:(0 if labels[i].startswith('basis') else 1,i))
            i=choices[0];w=targets[i]
            reductions=sorted(reducers.get(w,set()))
            if i not in reductions:reductions.append(i);reductions.sort()
            preempt=True
        else:
            if not reducers:
                return None,{'status':'stuck','seed':seed,'linear':sum(g['op']!='AND' for g in gates),
                             'released_ands':len(released),'dist':Dist,'trace_tail':trace[-12:]}
            scored=[]
            for w,inds0 in reducers.items():
                inds=sorted(inds0);count=len(inds);penalty=sum(2*Dist[i]-1 for i in inds)
                bcount=sum(labels[i].startswith('basis') for i in inds)
                isguide=1 if (guide and (w in linear_vecs or w in bvecs)) else 0
                scored.append((-count,penalty,-bcount,-isguide,w,inds))
            scored.sort(key=lambda z:z[:-1]);best=scored[0][:-2]
            pool=[z for z in scored if z[:-2]==best][:max(1,elite)]
            *_,w,reductions=rng.choice(pool);preempt=False
        op,a,b=WD[w];out=f'__joint_prefix_{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:Dist[i]-=1
        S.add(w);names[w]=out;rr.add_sx(sx,w)
        rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        added=rr.release_ready(sk,S,sx,names,gates,released)
        if added:rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        trace.append({'linear':sum(g['op']!='AND' for g in gates),'released_ands':len(released),
                      'basis_ready':[v in S for v in bvecs],
                      'positive_sum':sum(d for d in Dist if 0<d<INF),
                      'inf_remaining':sum(d==INF for d in Dist),
                      'reductions':len(reductions),'fallback_targets':len(fallback),
                      'preemptive':preempt})

    linear=sum(g['op']!='AND' for g in gates)
    rr.release_ready(sk,S,sx,names,gates,released)
    if any(d!=0 for d in Dist) or len(released)!=sk['n_and'] or any(v not in names for v in bvecs):
        return None,{'status':'budget_exhausted','seed':seed,'linear':linear,
                     'released_ands':len(released),'basis_ready':[v in S for v in bvecs],
                     'dist':Dist,'trace_tail':trace[-12:]}

    # Every atomic cut value must already be an input or released AND atom.  The
    # three non-atomic positions are supplied by the chosen transformed basis.
    extra_pos={w:j for j,w in enumerate(extras)}
    input_names=[]
    for w in boundary:
        if w in extra_pos:input_names.append(names[bvecs[extra_pos[w]]])
        else:
            v=vals[w]
            if v not in names:raise AssertionError(('missing atomic boundary value',w,v))
            input_names.append(names[v])
    meta={'status':'found','seed':seed,'linear':linear,'released_ands':len(released),
          'basis_rows':list(rows),'basis_vectors':bvecs,'extras':extras,
          'boundary':boundary,'input_names':input_names,
          'original_prefix_linear':sum(g['op']!='AND' for g in orig_prefix),
          'trace_tail':trace[-12:]}
    return {'gates':gates,'input_names':input_names,'basis_vectors':bvecs,
            'basis_rows':list(rows),'extras':extras,'boundary':boundary},meta


def transformed_suffix_problem(c,rows):
    last,prefix,orig_suffix,boundary=suf.split(c)
    m,C,vals,targets,qtargets,orig_guide=suf.formal_suffix(orig_suffix,boundary,c['outputs'])
    extras,_=cb.semantic_cut_extras(c,boundary);extra_idx=[boundary.index(w) for w in extras]
    cmap=cb.coeff_map(rows)
    qtargets2=[cb.transform_mask(t,extra_idx,cmap) for t in qtargets]
    targets2=[q | (C if ((t>>m)&1) else 0) for q,t in zip(qtargets2,targets)]
    qvals={w:1<<i for i,w in enumerate(boundary)};guide=[]
    for g in orig_suffix:
        q=qvals[g['a']]^qvals[g['b']];qvals[g['out']]=q
        guide.append(cb.transform_mask(q,extra_idx,cmap))
    return boundary,extras,extra_idx,m,C,targets2,qtargets2,set(guide),len(orig_suffix)


def synthesize_suffix(c,rows,input_names,seed,budget,max_support,elite,policy):
    boundary,extras,extra_idx,m,C,targets,qtargets,guide,orig_n=transformed_suffix_problem(c,rows)
    assert len(input_names)==m
    S={1<<i for i in range(m)};sx=suf.init_sx(S,max_support)
    names={1<<i:input_names[i] for i in range(m)}
    exact={1<<i:1<<i for i in range(m)}
    Dist=[q.bit_count()-1 for q in qtargets]
    rng=random.Random(seed);gates=[];trace=[]

    while len(gates)<budget and any(d!=0 for d in Dist):
        WD=suf.pair_map(S);reducers=suf.reducer_map(Dist,qtargets,WD,sx)
        ones=[i for i,d in enumerate(Dist) if d==1 and qtargets[i] in WD]
        if ones:
            i=rng.choice(ones);w=qtargets[i]
            reductions=sorted(reducers.get(w,set()))
            if i not in reductions:reductions.append(i);reductions.sort()
            preempt=True
        else:
            if not reducers:
                return None,{'status':'stuck','seed':seed,'budget':budget,'used':len(gates),
                             'policy':policy,'dist':Dist,'trace_tail':trace[-12:]}
            scored=[]
            for w,inds0 in reducers.items():
                inds=sorted(inds0);count=len(inds);penalty=sum(2*Dist[i]-1 for i in inds)
                isguide=1 if w in guide else 0
                if policy=='hard':key=(-count,-penalty,w)
                elif policy=='guide':key=(-count,penalty,-isguide,w)
                else:key=(-count,penalty,w)
                scored.append((key,w,inds))
            scored.sort(key=lambda z:z[0]);primary=scored[0][0][:-1]
            pool=[z for z in scored if z[0][:-1]==primary][:max(1,elite)]
            _,w,reductions=rng.choice(pool);preempt=False

        a,b=WD[w];xor_exact=exact[a]^exact[b];desired=xor_exact
        hits=[i for i,q in enumerate(qtargets) if q==w]
        if hits:desired=targets[hits[0]]
        op='XOR' if xor_exact==desired else 'XNOR'
        if op=='XNOR':assert xor_exact^C==desired,(xor_exact,desired,C)
        out=f'__joint_suffix_{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:Dist[i]-=1
        S.add(w);names[w]=out;exact[w]=desired;suf.add_sx(sx,w)
        trace.append({'used':len(gates),'dist':list(Dist),'reductions':len(reductions),
                      'preemptive':preempt,'reducing_candidates':len(reducers)})

    if any(d!=0 for d in Dist):
        return None,{'status':'budget_exhausted','seed':seed,'budget':budget,'used':len(gates),
                     'policy':policy,'dist':Dist,'trace_tail':trace[-12:]}
    for q,t in zip(qtargets,targets):
        if exact[q]!=t:raise AssertionError(('target polarity mismatch',q,exact[q],t))
    outs=[names[q] for q in qtargets]
    return {'gates':gates,'outputs':outs}, {'status':'found','seed':seed,'budget':budget,
            'used':len(gates),'policy':policy,'original_suffix_gates':orig_n,'trace_tail':trace[-12:]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=parse_rows,required=True,
                    help='three comma-separated GL(3,2) row masks, e.g. 1,2,4')
    ap.add_argument('--prefix-seed',type=int,required=True)
    ap.add_argument('--prefix-budget',type=int,default=47)
    ap.add_argument('--prefix-max-support',type=int,default=8)
    ap.add_argument('--prefix-elite',type=int,default=16)
    ap.add_argument('--extra-weight',type=int,default=3)
    ap.add_argument('--suffix-seeds',type=int,default=8)
    ap.add_argument('--suffix-max-support',type=int,default=10)
    ap.add_argument('--suffix-elite',type=int,default=24)
    ap.add_argument('--target-total',type=int,default=100)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    t0=time.time()
    pres,pmeta=synthesize_prefix(c,args.basis_rows,args.prefix_seed,args.prefix_budget,
                                 args.prefix_max_support,args.prefix_elite,args.extra_weight,True)
    summary={'basis_rows':list(args.basis_rows),'prefix':pmeta,'target_total':args.target_total}
    if pres is None:
        summary['status']='prefix_miss';summary['elapsed_s']=round(time.time()-t0,3)
        (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        print(json.dumps({k:v for k,v in summary.items() if k!='prefix'},sort_keys=True),flush=True);return

    (out/'prefix.json').write_text(json.dumps(pres,indent=2)+'\n')
    n_and=sum(g['op']=='AND' for g in pres['gates']);n_lin=sum(g['op']!='AND' for g in pres['gates'])
    assert n_and==32,(n_and,n_lin)
    suffix_budget=args.target_total-n_and-n_lin
    summary['suffix_budget']=suffix_budget
    best=None;best_meta=None
    if suffix_budget>=0:
        for policy in ('classic','hard','guide'):
            for seed in range(1,args.suffix_seeds+1):
                sres,smeta=synthesize_suffix(c,args.basis_rows,pres['input_names'],seed,suffix_budget,
                                             args.suffix_max_support,args.suffix_elite,policy)
                if sres is not None and (best is None or len(sres['gates'])<len(best['gates'])):
                    best=sres;best_meta=smeta
                    if len(best['gates'])<=suffix_budget:break
            if best is not None and len(best['gates'])<=suffix_budget:break
    if best is None:
        summary['status']='suffix_miss';summary['suffix']=best_meta
    else:
        (out/'suffix.json').write_text(json.dumps(best,indent=2)+'\n')
        full=ras.prune({'gates':pres['gates']+best['gates'],'outputs':best['outputs']})
        ok=ras.independent_check(full)
        if not ok[0]:raise AssertionError(('joint candidate failed AES',ok))
        (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
        summary['status']='found';summary['suffix']=best_meta
        summary['full_gates']=len(full['gates']);summary['verified_all_256']=True
        summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
    summary['elapsed_s']=round(time.time()-t0,3)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('prefix','suffix')},sort_keys=True),flush=True)

if __name__=='__main__':main()
