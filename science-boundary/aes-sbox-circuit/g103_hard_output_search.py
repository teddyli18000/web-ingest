#!/usr/bin/env python3
"""Target the stable y2/y6 failure mode of the 32-AND NIST G103 skeleton.

True-support RNBP repeatedly reaches all 32 AND atoms within the 68-linear budget
but strands AES outputs y2 and y6.  This script keeps the same strict released-AND
search until all nonlinear atoms are available, then experiments with three
output-phase interventions instead of more random full reruns:

* hard: among equal sum-distance improvements, reduce higher-distance outputs;
* guide: prefer pair helpers already present in the original 103-gate circuit;
* cone6: explicitly reconstruct missing one-gate-available helpers from the
  original transitive linear cone of y6, then resume support-distance RNBP.

Any <=68-linear completion gives 32+68=100 total gates and is independently
verified on all 256 AES inputs.
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


def formal_gate_vectors(c):
    sk=ras.extract_skeleton(c); C=1<<sk['const_bit']
    vals={f'x{i}':1<<i for i in range(8)}; gate_vec={}; ai=0
    for g in c['gates']:
        a,b=vals[g['a']],vals[g['b']]
        if g['op']=='XOR':v=a^b
        elif g['op']=='XNOR':v=a^b^C
        elif g['op']=='AND':v=1<<(8+ai);ai+=1
        else:raise ValueError(g['op'])
        vals[g['out']]=v;gate_vec[g['out']]=v
    return sk,vals,gate_vec


def output_cone(c,oi):
    byout={g['out']:g for g in c['gates']}; needed=set(); stack=[c['outputs'][oi]]
    while stack:
        w=stack.pop()
        if w in needed or w not in byout:continue
        needed.add(w);g=byout[w];stack.extend([g['a'],g['b']])
    return needed


def choose_classic_or_policy(Dist,targets,WD,reducers,guide,policy,rng,elite):
    ones=[i for i,d in enumerate(Dist) if d==1]
    if ones:
        choices=[i for i in ones if targets[i] in WD]
        if not choices:raise AssertionError(('distance1 without pair witness',ones))
        i=rng.choice(choices);w=targets[i]
        inds=sorted(reducers.get(w,set()))
        if i not in inds:inds.append(i);inds.sort()
        return w,inds,True
    if not reducers:return None,None,False
    scored=[]
    for w,inds0 in reducers.items():
        inds=sorted(inds0);count=len(inds)
        penalty=sum(2*Dist[i]-1 for i in inds)
        isguide=1 if w in guide else 0
        if policy=='hard':
            key=(-count,-penalty,-isguide,w)
        elif policy=='guide':
            key=(-count,penalty,-isguide,w)
        else:
            key=(-count,penalty,w)
        scored.append((key,w,inds))
    scored.sort(key=lambda z:z[0]);best=scored[0][0][:-1]
    pool=[z for z in scored if z[0][:-1]==best][:max(1,elite)]
    _,w,inds=rng.choice(pool)
    return w,inds,False


def synthesize(base,seed,policy,max_linear=68,max_support=8,elite=8):
    sk=ras.extract_skeleton(base); C=1<<sk['const_bit']
    rows=rr.target_rows(sk);targets=[t for t,_ in rows]
    out_start=2*sk['n_and']; rng=random.Random(seed)
    _,vals,gate_vec=formal_gate_vectors(base)
    guide={gate_vec[g['out']] for g in base['gates'] if g['op']!='AND'}
    cone6=output_cone(base,6)

    S={1<<i for i in range(8)};sx=rr.init_sx(S)
    names={1<<i:f'x{i}' for i in range(8)};gates=[];released=set();linear=0;trace=[]
    rr.release_ready(sk,S,sx,names,gates,released)
    Dist=[rr.min_distance(S,sx,t,C,max_support) for t in targets]
    cone_mode=False;cone_added=0

    while linear<max_linear and any(d!=0 for d in Dist):
        added=rr.release_ready(sk,S,sx,names,gates,released)
        if added:rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        if all(d==0 for d in Dist):break
        if len(released)==sk['n_and'] and policy=='cone6':cone_mode=True

        WD=rr.pair_candidates(S,C)
        chosen=None;reductions=[];preempt=False;reason='rnbp'
        if cone_mode and Dist[out_start+6]!=0:
            # Walk the original y6 transitive cone topologically.  Only choose a
            # missing linear gate whose exact original operands are already in S.
            for g in base['gates']:
                if g['out'] not in cone6 or g['op']=='AND':continue
                v=gate_vec[g['out']]
                if v in S:continue
                av,bv=vals[g['a']],vals[g['b']]
                if av in S and bv in S and v in WD:
                    chosen=v;reason='cone6';cone_added+=1;break

        reducers,fallback=rf.reducer_map(Dist,targets,WD,S,sx,C)
        if chosen is not None:
            reductions=sorted(reducers.get(chosen,set()))
        else:
            phase_policy=policy if len(released)==sk['n_and'] else 'classic'
            chosen,reductions,preempt=choose_classic_or_policy(
                Dist,targets,WD,reducers,guide,phase_policy,rng,elite)
            if chosen is None:
                return None,{'status':'stuck','seed':seed,'policy':policy,'linear':linear,
                             'released_ands':len(released),'dist':Dist,
                             'trace_tail':trace[-20:]}

        op,a,b=WD[chosen];out=f'w{len(gates)}'
        gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
        for i in reductions:Dist[i]-=1
        S.add(chosen);names[chosen]=out;rr.add_sx(sx,chosen);linear+=1
        rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        added=rr.release_ready(sk,S,sx,names,gates,released)
        if added:rr.initialize_covered_inf(Dist,targets,S,sx,C,max_support)
        rec={'linear':linear,'released_ands':len(released),'reason':reason,
             'cone_added':cone_added,'remaining_outputs':{f'y{i}':Dist[out_start+i] for i in range(8) if Dist[out_start+i]!=0},
             'positive_sum':sum(d for d in Dist if 0<d<INF),'inf_remaining':sum(d==INF for d in Dist),
             'reductions':len(reductions),'fallback_targets':len(fallback)}
        trace.append(rec);print(json.dumps({'progress':rec,'seed':seed,'policy':policy}),flush=True)

    if any(d!=0 for d in Dist):
        return None,{'status':'budget_exhausted','seed':seed,'policy':policy,'linear':linear,
                     'released_ands':len(released),'cone_added':cone_added,'dist':Dist,
                     'trace_tail':trace[-20:]}
    c=ras.prune({'gates':gates,'outputs':[names[t] for t in sk['outputs']]})
    ok=ras.independent_check(c)
    if not ok[0]:raise AssertionError(('AES check failed',ok))
    return c,{'status':'found','seed':seed,'policy':policy,'linear':linear,
              'released_ands':len(released),'cone_added':cone_added,
              'candidate_gates':len(c['gates']),'verified_all_256':True,
              'candidate_stats':dict(collections.Counter(g['op'] for g in c['gates'])),
              'trace_tail':trace[-20:]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=['nist-g103'],default='nist-g103')
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--policy',choices=['classic','hard','guide','cone6'],required=True)
    ap.add_argument('--max-linear',type=int,default=68)
    ap.add_argument('--max-support',type=int,default=8)
    ap.add_argument('--elite',type=int,default=8)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.family);assert ras.independent_check(base)[0]
    t0=time.time();c,s=synthesize(base,args.seed,args.policy,args.max_linear,args.max_support,args.elite)
    s['elapsed_s']=round(time.time()-t0,3)
    if c is not None:(out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__':main()
