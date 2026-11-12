#!/usr/bin/env python3
"""Constructive cross-coordinate, blocker-anchored C7^10 repair.

Starts from four officially verified 134753-point solutions. In arbitrary
5+5 coordinate partitions, forces a novel ten-dimensional point, releases
all incumbent prefix rows blocking that point, and jointly reoptimizes the
COMPLETE legal suffix domains of these rows. Intermediate 134752 states are
allowed, but the incumbent 134753 is kept as a recovery checkpoint. Every
positive candidate is checked and exported for the Few Shots verifier.
"""
import argparse, collections, itertools, json, random, time
from pathlib import Path
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

U = 7**5
P = (1,7,49,343,2401)
DIG = np.array([[v//p%7 for p in P] for v in range(U)], dtype=np.int16)
OFF = np.array(list(itertools.product((-1,0,1),repeat=5)),dtype=np.int16)
NBR = np.sum(((DIG[:,None,:]+OFF[None,:,:])%7)*np.array(P),axis=2).astype(np.int32)
NEIGH = [sum(1<<int(w) for w in V) for V in NBR]
ALL = (1<<U)-1

def bits(m):
    while m:
        x=m&-m
        yield x.bit_length()-1
        m-=x

def xy(word,axes):
    other=[i for i in range(10) if i not in axes]
    return (sum(int(word[k])*P[j] for j,k in enumerate(axes)),
            sum(int(word[k])*P[j] for j,k in enumerate(other)))

def extract(words,axes):
    R=collections.defaultdict(set)
    for word in words:
        u,v=xy(word,axes)
        R[u].add(v)
    return dict(R)

def materialize(rows,axes):
    other=tuple(i for i in range(10) if i not in axes)
    out=[]
    for u,V in rows.items():
        for v in V:
            d=[0]*10
            for i,k in enumerate(axes):d[k]=int(DIG[u,i])
            for i,k in enumerate(other):d[k]=int(DIG[v,i])
            out.append(''.join(map(str,d)))
    return sorted(out)

def validate(rows):
    counts={u:sum(1<<v for v in V) for u,V in rows.items()}
    neigh={}
    for u,V in rows.items():
        cover=0
        for v in V:
            assert not (cover>>v)&1,('intrarow',u,v)
            cover|=NEIGH[v]
        neigh[u]=cover
    for u in rows:
        for j in NBR[u]:
            j=int(j)
            if j>u and j in rows:
                assert not (neigh[u]&counts[j]),('interrow',u,j)

def domains(rows,block,rowmask):
    used=set(block)
    RM={u:0 for u in rows}
    for u,V in rows.items():
        m=0
        for v in V:m|=NEIGH[v]
        RM[u]=m
    out={}
    for u in block:
        ext=0
        for w in NBR[u]:
            w=int(w)
            if w not in used:ext|=RM.get(w,0)
        out[u]=ALL^ext
        assert all((out[u]>>v)&1 for v in rows.get(u,()))
    return out

def solve(rows,block,anchor,randomizer,limit,maxdomain=350,maxvars=1050):
    rowmask={u:sum(1<<v for v in vs) for u,vs in rows.items()}
    dom=domains(rows,block,rowmask)
    if any(m.bit_count()>maxdomain for m in dom.values()):return None
    cand=[(u,v) for u in block for v in bits(dom[u])]
    n=len(cand)
    if n>maxvars or anchor not in cand:return None
    ix={p:i for i,p in enumerate(cand)}
    er=[];ec=[]
    for u in block:
        for v in bits(dom[u]):
            i=ix[(u,v)]
            for w in bits(NEIGH[v]&dom[u]):
                j=ix[(u,w)]
                if j>i:er.append(i);ec.append(j)
    for i,u in enumerate(block):
        for w in block[i+1:]:
            if w not in NBR[u]:continue
            for v in bits(dom[u]):
                ii=ix[(u,v)]
                for z in bits(NEIGH[v]&dom[w]):
                    er.append(ii);ec.append(ix[(w,z)])
    m=len(er)
    row=np.repeat(np.arange(m),2)
    col=np.column_stack((er,ec)).ravel()
    # Force one genuinely absent candidate while jointly solving all row conflicts.
    row=np.r_[row,m]
    col=np.r_[col,ix[anchor]]
    mat=coo_matrix((np.ones(len(row)),(row,col)),shape=(m+1,n)).tocsr()
    old={(u,v) for u in block for v in rows.get(u,())}
    tie=np.array([randomizer.random()*(1 if z not in old else .4) for z in cand])
    objective=-100000*np.ones(n)-tie
    z=milp(objective,integrality=np.ones(n),
           bounds=Bounds(np.zeros(n),np.ones(n)),
           constraints=LinearConstraint(mat,np.r_[np.full(m,-np.inf),1.],np.r_[np.ones(m),1.]),
           options={'mip_rel_gap':0,'time_limit':limit})
    if z.x is None:return {'status':int(z.status),'state':None}
    selected={u:set() for u in block}
    for (u,v),value in zip(cand,z.x):
        if value>.5:selected[u].add(v)
    newrows=dict(rows)
    for u in block:
        if selected[u]:newrows[u]=selected[u]
        else:newrows.pop(u,None)
    return {'status':int(z.status),'state':newrows,
            'delta':sum(len(selected[u])-len(rows.get(u,())) for u in block),
            'changed':sum(len(selected[u]^rows.get(u,set())) for u in block),
            'variables':n,'edges':m}

def perturb(words,rng):
    word=rng.choice(words)
    d=list(map(int,word))
    for k in rng.sample(range(10),rng.choice((1,2,2,3))):
        d[k]=(d[k]+rng.choice((-2,-1,1,2)))%7
    return ''.join(map(str,d))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_folder',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--source',type=int,default=0)
    ap.add_argument('--seed',type=int,default=45)
    ap.add_argument('--steps',type=int,default=250)
    ap.add_argument('--seconds',type=float,default=2.)
    ap.add_argument('--axes',default='0,1,2,3,7')
    a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    allwords=[]
    for i in range(4):
        x=json.loads((a.source_folder/f'source{i}.json').read_text())['points']
        assert len(x)==134753 and len(set(x))==134753
        allwords.append(x)
    rng=random.Random(a.seed)
    axes=tuple(map(int,a.axes.split(',')))
    original=allwords[a.source]
    state=extract(original,axes)
    initial=set(original)
    alternatives=set().union(*(set(x) for x in allwords))
    current=134753
    winner=None
    moves=0
    maxchanged=0
    distinct_novel=0
    fallback=0
    statuses=collections.Counter()
    begin=time.monotonic()
    for step in range(a.steps):
        if step and step%50==0:
            # Move the 5+5 factor interface itself; no fixed original core.
            full=materialize(state,axes)
            k=(step//50)%4
            axes=[tuple(map(int,a.axes.split(','))),
                  (0,1,2,5,7),(0,2,4,6,8),(0,1,2,3,6)][k]
            state=extract(full,axes)
        rowmask={u:sum(1<<v for v in V) for u,V in state.items()}
        if rng.random()<.35:
            candidate=perturb(materialize(state,axes) if step%50==0 else rng.choice(allwords),rng)
        else:
            candidate=rng.choice(allwords[rng.randrange(4)])
            if rng.random()<.6:
                candidate=rng.choice(tuple(alternatives))
        u,v=xy(candidate,axes)
        if v in state.get(u,()):continue
        blocked={int(w) for w in NBR[u] if rowmask.get(int(w),0)&NEIGH[v]}
        if len(blocked)>5:statuses['many_blocker_rows']+=1;continue
        block=sorted(blocked|{u})
        pool={int(z) for w in block for z in NBR[w] if int(z) in state and int(z) not in block}
        if len(block)<5 and pool:
            block+=rng.sample(sorted(pool),min(len(pool),5-len(block)))
        solved=solve(state,block,(u,v),rng,a.seconds)
        if solved is None:statuses['large_model']+=1;continue
        statuses['solver_'+str(solved['status'])]+=1
        if solved['state'] is None:continue
        trial=current+solved['delta']
        if trial>134753:
            candidate_rows=solved['state']
            validate(candidate_rows)
            words=materialize(candidate_rows,axes)
            assert len(words)==trial and len(set(words))==trial
            (a.output/'certificate.json').write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
            winner=trial;state=candidate_rows
            print('FOUND',trial,'step',step,flush=True)
            break
        if trial>=134753 or (trial==134752 and rng.random()<.12):
            state=solved['state']
            current=trial
            moves+=1
            maxchanged=max(maxchanged,solved['changed'])
            if trial==134753 and moves%40==0:
                validate(state)
        if step%30==0:
            print('PROGRESS',json.dumps({'step':step,'score':current,'moves':moves,
                  'max_changed':maxchanged,'solver':dict(statuses)}),flush=True)
    valid=None
    if winner is None:
        if current==134753:
            validate(state)
            words=materialize(state,axes)
        else:
            words=original
        valid=len(words)==134753 and len(set(words))==134753
        (a.output/'neutral.json').write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
    result={'method':'cross-partition-forced-anchor-dynamic-row-repair',
            'input_source':a.source,'seed':a.seed,'steps_requested':a.steps,
            'best':winner or 134753,'current':current,'accepted_moves':moves,
            'max_single_move_symmetric_difference':maxchanged,
            'solver_statuses':dict(statuses),'candidate_134754':winner is not None,
            'terminal_neutral_independently_checked':valid,
            'elapsed_seconds':round(time.monotonic()-begin,2)}
    (a.output/'status.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps(result,sort_keys=True),flush=True)

if __name__=='__main__':
    main()
