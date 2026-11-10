#!/usr/bin/env python3
"""Constructive two-site cooperative retargeting of an AES gate network.

First retarget gate i to an arbitrary two-input AND/XOR/XNOR of earlier wires.
This may make the whole circuit WRONG. Then derive exact full-output cofactors
at a later gate j, in the perturbed circuit, and search legal two-input or
alias repairs. Prune all dead gates and independently verify the full 256-byte
AES S-box. This represents changed intermediate truth functions that are
absent from every semantic-parent hypergraph.

Return only complete validated <=100 shots or structurally novel <=101 seeds.
Search is prioritized by lost dependencies and small observability error;
it is NOT a complete exclusion search.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib, random, time
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1
OPS=('AND','XOR','XNOR')

def val(op,a,b):
    return census.op_eval(op,a,b)

def evaluate(c,replace_i=None,replace_j=None,alias_j=None):
    v=census.input_tables(False)
    for k,g in enumerate(c['gates']):
        if k==replace_i[0]:
            _,op,a,b=replace_i
            v[g['out']]=val(op,v[a],v[b])
        elif replace_j is not None and k==replace_j[0]:
            _,op,a,b=replace_j
            v[g['out']]=val(op,v[a],v[b])
        elif alias_j is not None and k==alias_j[0]:
            v[g['out']]=v[alias_j[1]]
        else:v[g['out']]=val(g['op'],v[g['a']],v[g['b']])
    return v,[v[w] for w in c['outputs']]

def baseline_trace(c):
    v=census.input_tables(False)
    for g in c['gates']:v[g['out']]=val(g['op'],v[g['a']],v[g['b']])
    return v,[v[w] for w in c['outputs']]

def flip_care(c,idx,goal):
    v=census.input_tables(False)
    for k,g in enumerate(c['gates']):
        f=val(g['op'],v[g['a']],v[g['b']])
        v[g['out']]=f^MASK if k==idx else f
    outs=[v[x] for x in c['outputs']]
    care=0
    for a,b in zip(goal,outs):care|=a^b
    return care

def repair_cofactors(c,mutated,j):
    def run(force):
        v=dict(mutated);v[c['gates'][j]['out']]=force
        for g in c['gates'][j+1:]:
            v[g['out']]=val(g['op'],v[g['a']],v[g['b']])
        return [v[w] for w in c['outputs']]
    return run(0),run(MASK)

def required_repair(goal,out0,out1):
    good0=good1=MASK
    for t,a,b in zip(goal,out0,out1):
        good0&=MASK^(t^a)
        good1&=MASK^(t^b)
    if (good0|good1)!=MASK:return None
    return good1&(MASK^good0),good0^good1

def apply(c,i,first,j=None,second=None,alias=None):
    gs=[dict(g) for g in c['gates']]
    op,a,b=first
    gs[i].update(op=op,a=a,b=b)
    if second is not None:
        op,a,b=second
        gs[j].update(op=op,a=a,b=b)
    outputs=list(c['outputs'])
    if alias is not None:
        old=gs[j]['out']
        for g in gs[j+1:]:
            if g['a']==old:g['a']=alias
            if g['b']==old:g['b']=alias
        outputs=[alias if x==old else x for x in outputs]
        del gs[j]
    return ras.prune({'gates':gs,'outputs':outputs})

def truth_and(c):
    v=census.input_tables(False)
    s=set()
    for g in c['gates']:
        v[g['out']]=val(g['op'],v[g['a']],v[g['b']])
        if g['op']=='AND':s.add(v[g['out']])
    return s

def check_toy():
    toy={'gates':[
        {'op':'XOR','a':'x0','b':'x1','out':'t'},
        {'op':'XOR','a':'t','b':'x2','out':'a'},
        {'op':'XOR','a':'a','b':'x1','out':'y'}],
        'outputs':['y']}
    _,target=baseline_trace(toy)
    v,_=evaluate(toy,(1,'XOR','x0','x2'))
    out0,out1=repair_cofactors(toy,v,2)
    req=required_repair(target,out0,out1)
    assert req is not None
    must1,care=req
    assert (v['a']&care)==must1
    new=apply(toy,1,('XOR','x0','x2'),2,alias='a')
    assert len(new['gates'])==1 and baseline_trace(new)[1]==target

def ranked_first(c,base,care,i,n_keep,rng):
    gate=c['gates'][i]
    avail=[f'x{k}' for k in range(8)]+[g['out'] for g in c['gates'][:i]]
    current=base[gate['out']]
    fanout=collections.Counter(c['outputs'])
    for g in c['gates']:
        fanout[g['a']]+=1;fanout[g['b']]+=1
    removable={w for w in (gate['a'],gate['b']) if w.startswith('g') and fanout[w]==1}
    scored=[]
    known=set()
    for ix,a in enumerate(avail):
        for b in avail[ix+1:]:
            if a==gate['a'] and b==gate['b'] or a==gate['b'] and b==gate['a']:
                # Other operators on the old parents are still new candidates.
                pass
            for op in OPS:
                if op==gate['op'] and {a,b}=={gate['a'],gate['b']}:continue
                v=val(op,base[a],base[b])
                if v in known:continue
                known.add(v)
                loss=removable - {a,b}
                mismatch=((v^current)&care).bit_count()
                # Better chance for later exact repair with few changed bits.
                score=(mismatch, -len(loss), int(op!=gate['op']))
                scored.append((score,(op,a,b)))
    scored.sort(key=lambda z:z[0])
    best=[x for _,x in scored[:n_keep*2] if len(removable-{x[1],x[2]})>0]
    if len(best)<n_keep:best+=[x for _,x in scored[:n_keep]]
    distinct=[];seen=set()
    for x in best:
        if x in seen:continue
        seen.add(x);distinct.append(x)
        if len(distinct)>=n_keep:break
    tail=[x for _,x in scored[n_keep*2:]]
    rng.shuffle(tail)
    distinct.extend(tail[:min(8,n_keep//4)])
    return distinct

def candidate_repairs(c,mutated,j,must1,care,limit):
    names=[f'x{k}' for k in range(8)]+[g['out'] for g in c['gates'][:j]]
    byval={}
    for w in names:byval.setdefault(mutated[w],w)
    opts=list(byval.items())
    count=0
    for value,w in opts:
        if (value&care)==must1:
            yield ('alias',w)
            count+=1
            if count>=limit:return
    for i,(x,a) in enumerate(opts):
        for y,b in opts[i+1:]:
            xx=x^y
            for op,z in (('XOR',xx),('XNOR',xx^MASK),('AND',x&y)):
                if (z&care)!=must1:continue
                yield ('gate',op,a,b)
                count+=1
                if count>=limit:return

def signature(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',choices=['fs-101','shear-102'],default='fs-101')
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=8)
    ap.add_argument('--first-choices',type=int,default=24)
    ap.add_argument('--later-distance',type=int,default=44)
    ap.add_argument('--per-repair',type=int,default=6)
    ap.add_argument('--seconds',type=int,default=300)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    if args.source=='shear-102':
        import make_and_shear_102 as shear
        c=shear.build()[1]
        baseline=ras.load_circuit('fs-101')
    else:
        c=ras.load_circuit('fs-101');baseline=c
    assert ras.independent_check(c)[0]
    check_toy()
    firstv,goal=baseline_trace(c)
    baseline_ands=truth_and(baseline)
    stats=collections.Counter()
    best=c;best_shots=[];seen={signature(c)}
    t0=time.monotonic();rng=random.Random(args.shard+256*len(c['gates']))
    for i in range(len(c['gates'])):
        if i%args.shards!=args.shard:continue
        stats['root_sites']+=1
        care=flip_care(c,i,goal)
        choices=ranked_first(c,firstv,care,i,args.first_choices,rng)
        for first in choices:
            if time.monotonic()-t0>=args.seconds:break
            stats['first_retargets']+=1
            vals,wrong=evaluate(c,(i,*first))
            if wrong==goal:stats['individually_valid_first']+=1
            lo=i+1;hi=min(len(c['gates']),i+1+args.later_distance)
            for j in range(lo,hi):
                stats['repair_sites']+=1
                z,o=repair_cofactors(c,vals,j)
                req=required_repair(goal,z,o)
                if req is None:continue
                must1,repaircare=req;stats['abstract_repair_possible']+=1
                for candidate in candidate_repairs(c,vals,j,must1,repaircare,args.per_repair):
                    stats['matching_repair_options']+=1
                    if candidate[0]=='alias':
                        updated=apply(c,i,first,j,alias=candidate[1])
                    else:
                        _,op,a,b=candidate
                        updated=apply(c,i,first,j,second=(op,a,b))
                    if len(updated['gates'])>len(c['gates']):continue
                    if any(g['a']==g['b'] for g in updated['gates']):continue
                    if not ras.independent_check(updated)[0]:
                        raise AssertionError(('cofactor matched but full AES failed',i,j,first,candidate))
                    h=signature(updated)
                    if h in seen:continue
                    seen.add(h);stats['new_verified_circuits']+=1
                    n=len(updated['gates'])
                    delta=len(truth_and(updated)^baseline_ands)
                    if n<len(best['gates']):
                        best=updated
                        record={'gates':n,'i':i,'j':j,'first':first,'repair':candidate,
                                'AND_truth_set_delta':delta}
                        best_shots.append(record)
                        (out/'best.json').write_text(json.dumps(updated,indent=2)+'\n')
                        print(json.dumps({'event':'new_best',**record}),flush=True)
                    elif n==len(c['gates']) and delta>0 and stats['archived_neutral']<12:
                        name=f'neutral-g{n}-d{delta}-{h[:14]}.json'
                        (out/name).write_text(json.dumps(updated,indent=2)+'\n')
                        stats['archived_neutral']+=1
                    if n<=100:break
                if len(best['gates'])<=100:break
            if len(best['gates'])<=100:break
        if len(best['gates'])<=100 or time.monotonic()-t0>=args.seconds:break
    if not (out/'best.json').exists():
        (out/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={'source':args.source,'shard':args.shard,'shards':args.shards,
             'baseline_gates':len(c['gates']),'best_gates':len(best['gates']),
             'best_AND_truth_set_delta':len(truth_and(best)^baseline_ands),
             'full_256_verified':ras.independent_check(best)[0],
             'stats':dict(stats),'witnesses':best_shots,
             'seconds':round(time.monotonic()-t0,2),
             'search':'two individually invalid function changes, joint full-output cofactor repair and automatic prune'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    if len(best['gates'])<=100:(out/'candidate.json').write_text(json.dumps(best,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':main()
