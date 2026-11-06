#!/usr/bin/env python3
"""Constructive AES circuit evolution by exact two-/three-gate cone refactoring.

Unlike one-root ODC resubstitution, this preserves only each *cone output*:
both internal functions and the nonlinear AND basis may change. Examples:
  XOR -> AND   <=>   AND -> XOR
  AND -> XOR   <=>   XOR -> AND
  XOR -> XOR   <=>   different XOR factorization

A neutral replacement yields another complete circuit of equal gate count.
A saving replacement is a direct candidate. A quality-diverse pool uses
nonlinear truth-function signatures and explores coordinated neutral changes.
Every generated accepted circuit is independently AES-checked on all 256 bytes.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import pathlib
import random
import time

import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1
OPS=('AND','XOR','XNOR')

def trace(c):
    v=census.input_tables(False)
    for g in c['gates']:
        v[g['out']]=census.op_eval(g['op'],v[g['a']],v[g['b']])
    return v

def fingerprint(c,v):
    return hashlib.sha256(b''.join(
        v[g['out']].to_bytes(32,'little')
        for g in c['gates'] if g['op']=='AND')).hexdigest()

def signature(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def uses_of(c):
    uses=collections.Counter(c['outputs'])
    for g in c['gates']:
        uses[g['a']]+=1;uses[g['b']]+=1
    return uses

def cones(c,uses):
    by={g['out']:i for i,g in enumerate(c['gates'])}
    seen=set()
    for j,g in enumerate(c['gates']):
        eligible=[by[w] for w in (g['a'],g['b'])
                  if w in by and uses[w]==1]
        if not eligible:continue
        for p in eligible:
            x=(j,tuple(sorted((p,))))
            if x not in seen:seen.add(x);yield x
            # Expand a second sole-consumer parent feeding either p or j.
            for node in (p,j):
                for w in (c['gates'][node]['a'],c['gates'][node]['b']):
                    q=by.get(w)
                    if q is None or q==p or uses[w]!=1:continue
                    if node==j and q not in eligible:continue
                    x=(j,tuple(sorted((p,q))))
                    if x not in seen:seen.add(x);yield x

def prior_sources(c,v,j,removed):
    # Every removed intermediate has exactly one consumer inside this cone.
    # Other gates in the original prefix cannot depend on those intermediates.
    banned={c['gates'][i]['out'] for i in removed}
    names=[f'x{k}' for k in range(8)]
    names.extend(g['out'] for k,g in enumerate(c['gates'][:j]) if k not in removed)
    names=[w for w in names if w not in banned]
    return names

def maps_from_sources(names,v):
    byval={}
    for w in names:byval.setdefault(v[w],w)
    vals=list(byval.items())
    andmap={};linearmap={}
    for a,(va,wa) in enumerate(vals):
        for vb,wb in vals[a+1:]:
            if va==vb:continue
            andmap.setdefault(va&vb,('AND',wa,wb))
            t=va^vb
            linearmap.setdefault(t,('XOR',wa,wb))
            linearmap.setdefault(t^MASK,('XNOR',wa,wb))
    return byval,andmap,linearmap

def possible_solutions(target,names,v,limit,rng,allow_and_linear=True):
    aliases,andmap,linearmap=maps_from_sources(names,v)
    sols=[]
    if target in aliases:sols.append(('alias',aliases[target]))
    for m in (andmap,linearmap):
        if target in m:sols.append(('one',*m[target]))
    if not allow_and_linear:return sols
    # Nonlinear basis mutation: AND(a,b) then XOR/XNOR with existing q.
    # This can transfer an AND atom into an entirely new truth-function basis.
    qnames=list(aliases.items());rng.shuffle(qnames)
    for qv,q in qnames:
        for pol in (0,1):
            t=target^qv^(MASK if pol else 0)
            if t in andmap:
                sols.append(('two',*andmap[t],'XNOR' if pol else 'XOR',q))
        if len(sols)>=limit:break
    # Linear reassociation: XOR(a,b) then XOR/XNOR with existing q.
    for qv,q in qnames:
        for pol in (0,1):
            t=target^qv^(MASK if pol else 0)
            if t in linearmap:
                sols.append(('two',*linearmap[t],'XNOR' if pol else 'XOR',q))
        if len(sols)>=limit:break
    # Alternate AND factorizations: XOR/XNOR(a,b) then AND with existing q.
    # Restrict this scan to nonlinear target functions where there is a
    # potentially useful AND operand containing the output one-set.
    for qv,q in qnames:
        if target&(~qv&MASK):continue
        hits=0
        for lv,expr in linearmap.items():
            if (lv&qv)==target:
                sols.append(('two',*expr,'AND',q))
                hits+=1
                if hits>=4:break
        if len(sols)>=limit:break
    rng.shuffle(sols)
    return sols[:limit]

def materialize(c,j,removed,sol):
    old=c['gates'][j]['out']; out='__new_cone_helper'
    remove=set(removed)|{j}
    source=sol[1] if sol[0]=='alias' else None
    gates=[]
    for k,g in enumerate(c['gates']):
        if k==j:
            if sol[0]=='one':
                _,op,a,b=sol
                gates.append({'op':op,'a':a,'b':b,'out':old})
            elif sol[0]=='two':
                _,op,a,b,op2,q=sol
                gates.append({'op':op,'a':a,'b':b,'out':out})
                gates.append({'op':op2,'a':out,'b':q,'out':old})
        elif k not in remove:gates.append(dict(g))
    if source is not None:
        for g in gates:
            if g['a']==old:g['a']=source
            if g['b']==old:g['b']=source
        outs=[source if w==old else w for w in c['outputs']]
    else:outs=list(c['outputs'])
    if any(g['a']==g['b'] for g in gates):return None
    nc=ras.prune({'gates':gates,'outputs':outs})
    return nc

def assert_positive_control():
    # Two-gate XOR cancellation requires rewriting the whole cone.
    c={'gates':[{'op':'XOR','a':'x0','b':'x1','out':'t'},
                {'op':'XOR','a':'t','b':'x1','out':'y'}],
       'outputs':['y']}
    v=trace(c);use=uses_of(c)
    j,parents=next(iter(cones(c,use)))
    names=prior_sources(c,v,j,parents)
    sols=possible_solutions(v['y'],names,v,16,random.Random(1))
    assert ('alias','x0') in sols
    nc=materialize(c,j,parents,('alias','x0'))
    assert not nc['gates'] and nc['outputs']==['x0']

def find_moves(c,rng,root_cap,solutions_cap,base_ands):
    vals=trace(c);us=uses_of(c)
    groups=list(cones(c,us));rng.shuffle(groups)
    candidates=[];stats=collections.Counter()
    for j,parents in groups[:root_cap]:
        source=prior_sources(c,vals,j,parents)
        target=vals[c['gates'][j]['out']]
        sols=possible_solutions(target,source,vals,solutions_cap,rng)
        old_cost=1+len(parents)
        for sol in sols:
            new_cost={'alias':0,'one':1,'two':2}[sol[0]]
            if new_cost>old_cost:continue
            nc=materialize(c,j,parents,sol)
            if nc is None:continue
            n=len(nc['gates']);stats['constructed']+=1
            if n>len(c['gates']):continue
            if not ras.independent_check(nc)[0]:
                raise AssertionError(('local replacement changed AES',j,parents,sol))
            stats['verified']+=1
            av=trace(nc)
            and_sig=fingerprint(nc,av)
            candidates.append((nc,{'root':j,'parents':list(parents),'solution':sol,
                                   'old_cost':old_cost,'new_cost':new_cost,
                                   'and_signature':and_sig,
                                   'and_changed':and_sig!=base_ands}))
            if n<len(c['gates']):
                stats['improvements']+=1
    return candidates,stats,len(groups)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',choices=['fs-101','nist-g103','fs-102','nist-g104'],default='fs-101')
    ap.add_argument('--rng',type=int,default=0)
    ap.add_argument('--seconds',type=int,default=240)
    ap.add_argument('--max-pool',type=int,default=80)
    ap.add_argument('--roots-per-step',type=int,default=7)
    ap.add_argument('--solutions-per-cone',type=int,default=45)
    ap.add_argument('--target',type=int,default=100)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();rng=random.Random(args.rng)
    assert_positive_control()
    output=pathlib.Path(args.out);output.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.seed);assert ras.independent_check(base)[0]
    best=base;original_and=fingerprint(base,trace(base))
    pool=[(base,original_and)];seen={signature(base)};and_seen={original_and}
    counts=collections.Counter();records=[];t0=time.monotonic();last_report=t0
    while time.monotonic()-t0 < args.seconds and len(best['gates'])>args.target:
        counts['steps']+=1
        # Best-first with enough random exploration to escape a frozen AND basis.
        if rng.random()<0.12:current=base
        else:current=rng.choice(pool)[0]
        moves,st,ngroups=find_moves(current,rng,args.roots_per_step,args.solutions_per_cone,original_and)
        counts.update(st);counts['groups_total']+=ngroups
        rng.shuffle(moves);moves.sort(key=lambda z:len(z[0]['gates']))
        for nc,rec in moves:
            h=signature(nc)
            if h in seen:continue
            seen.add(h);counts['new_states']+=1
            n=len(nc['gates'])
            if n<len(best['gates']):
                best=nc;event={'event':'improvement','gates':n,'step':counts['steps'],'witness':rec}
                print(json.dumps(event),flush=True)
                records.append(event)
                (output/'best.json').write_text(json.dumps(best,indent=2)+'\n')
            elif n>len(best['gates'])+1:continue
            aid=rec['and_signature']
            if aid not in and_seen:
                and_seen.add(aid);counts['distinct_and_skeletons']+=1
            if len(pool)>=args.max_pool:
                # Diversify by keeping novel AND-function bases, not just
                # permuted descriptions of the same old circuit.
                if aid in {x[1] for x in pool} and rng.random()<0.87:continue
                del pool[rng.randrange(len(pool))]
            pool.append((nc,aid))
            if n<=args.target:break
        if time.monotonic()-last_report>=30:
            last_report=time.monotonic()
            print(json.dumps({'event':'progress','seed':args.seed,'rng':args.rng,'step':counts['steps'],
                              'best':len(best['gates']),'states':len(seen),
                              'and_skeletons':len(and_seen),'pool':len(pool)}),flush=True)
    if not (output/'best.json').exists():
        (output/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={'seed':args.seed,'rng':args.rng,'status':'found' if len(best['gates'])<=args.target else 'completed',
             'baseline':len(base['gates']),'best_gates':len(best['gates']),
             'best_all_256':ras.independent_check(best)[0],
             'distinct_states':len(seen),'distinct_and_skeletons':len(and_seen),
             'counts':dict(counts),'pool':len(pool),'elapsed_s':round(time.monotonic()-t0,2),
             'representative_events':records[-10:],
             'mechanism':'joint 2/3 gate cone resynthesis, neutral nonlinear-basis mutation, population diversity'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    if len(best['gates'])<=args.target:(output/'candidate.json').write_text(json.dumps(best,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
