#!/usr/bin/env python3
"""Constructive shared-deletion TWO-anchor C7^10 repair.

Choose a high-quality point absent from the incumbent but present in another
verified 134753 mother code. Find an old point it blocks. Generate a fresh
point in that old point's 10D neighborhood that was absent from ALL mother
codes and is compatible with the first anchor. Release all prefix rows
containing their union of old blockers, then jointly force both anchors in
an exact full-row suffix-domain MILP. This creates candidate families that
cannot be expressed by mere recombination of known parent records.
"""
import argparse,collections,json,random,time
from pathlib import Path
from c7p004_cross_partition_anchor_repair import (
    P,DIG,NBR,NEIGH,bits,xy,extract,materialize,validate,solve
)

def word_for_pair(u,v,axes):
    other=[i for i in range(10) if i not in axes]
    d=[0]*10
    for i,k in enumerate(axes):d[k]=int(DIG[u,i])
    for i,k in enumerate(other):d[k]=int(DIG[v,i])
    return ''.join(map(str,d))

def conflicts(a,b):
    return bool((NEIGH[a[0]]>>b[0])&1) and bool((NEIGH[a[1]]>>b[1])&1)

def old_blockers(pair,rowmask):
    u,v=pair
    out=[]
    nb=NEIGH[v]
    for w in NBR[u]:
        w=int(w)
        mask=rowmask.get(w,0)&nb
        out.extend((w,z) for z in bits(mask))
    return out

def mutate(blocker,rng):
    a,b=blocker
    d=[int(v) for v in DIG[a]]+[int(v) for v in DIG[b]]
    for k in rng.sample(range(10),rng.choice((1,1,2,2,3,4))):
        d[k]=(d[k]+rng.choice((-1,1)))%7
    return (sum(d[i]*P[i] for i in range(5)),
            sum(d[5+i]*P[i] for i in range(5)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source_folder',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--source',type=int,default=0)
    p.add_argument('--seed',type=int,default=51)
    p.add_argument('--steps',type=int,default=220)
    p.add_argument('--seconds',type=float,default=3.)
    p.add_argument('--axes',default='0,1,2,3,7')
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    rng=random.Random(a.seed)
    parents=[]
    for i in range(4):
        w=json.loads((a.source_folder/f'source{i}.json').read_text())['points']
        assert len(w)==134753 and len(set(w))==134753
        parents.append(w)
    root=parents[a.source]
    family=set().union(*(set(W) for W in parents))
    missing=sorted(family-set(root))
    assert 4000<=len(missing)<=5000
    axes=tuple(map(int,a.axes.split(',')))
    state=extract(root,axes)
    current=134753
    accepted=0;max_change=0;found=None
    stats=collections.Counter()
    t0=time.monotonic()
    for step in range(a.steps):
        if step and step%50==0:
            words=materialize(state,axes)
            rotate=(step//50)%4
            axes=[tuple(map(int,a.axes.split(','))),
                  (0,1,2,5,7),(0,2,4,6,8),(0,1,2,3,6)][rotate]
            state=extract(words,axes)
        rowmask={u:sum(1<<v for v in V) for u,V in state.items()}
        first=xy(rng.choice(missing),axes)
        if first[1] in state.get(first[0],()):continue
        old=old_blockers(first,rowmask)
        if not 1<=len(old)<=4:
            stats['primary_blockers_outside_range']+=1
            continue
        valid=[]
        for _ in range(38):
            other=mutate(rng.choice(old),rng)
            if other==first or conflicts(first,other):continue
            if other[1] in state.get(other[0],()):continue
            if word_for_pair(*other,axes) in family:continue
            qblock=old_blockers(other,rowmask)
            if not qblock or len(qblock)>7:continue
            if not(set(old)&set(qblock)):continue
            group={first[0],other[0]} | {x for x,y in old+qblock}
            if len(group)>7:continue
            union=set(old)|set(qblock)
            valid.append((len(union),-len(set(old)&set(qblock)),rng.random(),
                          other,group,len(qblock)))
        if not valid:
            stats['no_novel_shared_anchor']+=1
            continue
        _,_,_,second,group,nblock=min(valid)
        block=sorted(group)
        if len(block)<6:
            neighbor={int(z) for u in block for z in NBR[u]
                      if int(z) in state and int(z) not in block}
            if neighbor:
                block+=rng.sample(sorted(neighbor),min(6-len(block),len(neighbor)))
        res=solve(state,block,[first,second],rng,a.seconds,maxdomain=350,maxvars=1100)
        if res is None:
            stats['large_block_model']+=1
            continue
        stats['solver_'+str(res['status'])]+=1
        if res['state'] is None:continue
        score=current+res['delta']
        if score>134753:
            verify=res['state']
            validate(verify)
            words=materialize(verify,axes)
            assert len(words)==score and len(set(words))==score
            (a.output/'certificate.json').write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
            found=score
            print('FOUND',json.dumps({'score':score,'step':step,'shared_blockers':nblock}),flush=True)
            break
        if res['changed'] and (score>=134753 or (score==134752 and rng.random()<.13)):
            state=res['state']
            current=score
            accepted+=1
            max_change=max(max_change,res['changed'])
            stats['accepted']+=1
            if accepted%30==0 and current==134753:validate(state)
        if step%35==0:
            print('PROGRESS',json.dumps({'step':step,'current':current,'accepted':accepted,
                'max_change':max_change,'statuses':dict(stats)}),flush=True)
    if found is None:
        if current==134753:
            validate(state)
            neutral=materialize(state,axes)
        else:neutral=root
        assert len(neutral)==134753 and len(set(neutral))==134753
        (a.output/'neutral.json').write_text(json.dumps({'points':neutral},separators=(',',':'))+'\n')
    summary={'method':'constructive-novel-shared-blocker-two-anchor',
             'parent':a.source,'seed':a.seed,'attempts':a.steps,'best':found or 134753,
             'has_new_record':found is not None,'accepted':accepted,
             'max_changed_in_one_move':max_change,'statuses':dict(stats),
             'seconds':round(time.monotonic()-t0,2)}
    (a.output/'status.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':
    main()
