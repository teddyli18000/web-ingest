#!/usr/bin/env python3
"""Exactly traverse the one-hit 1-swap component of a FunSearch t=9 state.

Unlike ``bpz_t9_funsearch_neutral_component.py``, the identity of the unique
obstruction hit is NOT fixed.  Every edge is a legal private one-for-one swap
that preserves a 367-point independent set and keeps exactly one point inside
the fixed obstruction D.  Thus the bad point may move within D.

At every state, a private swap of the current bad point to a vertex outside D
is a zero-hit exit and materializes the 134770 BPZ t=9 certificate.  If the BFS
frontier empties before the cap, the entire one-hit reconfiguration component
is exhausted exactly for arbitrary path length.
"""
import argparse
import json
import sys
from collections import deque
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_representative_case import cases


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('status',type=Path)
    ap.add_argument('--case',type=int,required=True)
    ap.add_argument('--max-states',type=int,default=10000)
    args=ap.parse_args()
    if not 0<=args.case<20:raise SystemExit('case must be 0..19')
    if args.max_states<=0:raise SystemExit('max-states must be positive')

    sys.path.insert(0,str(args.tan_root.resolve()))
    from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0']))
    ring=Ring(f.D)
    digits=tuple(ring.decode(v) for v in range(f.U))
    nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    c=cases(I0,ring,digits,nb)[args.case]
    S,Dset=c['S'],c['D']
    start=sum(1<<z for z in S)
    Dmask=sum(1<<z for z in Dset)
    if (start&Dmask).bit_count()!=1:raise RuntimeError('start one-hit invariant failed')

    seen={start}
    q=deque([(start,0)])
    expanded=0;transitions=0;max_depth=0;found=None
    degree_hist={};new_states_by_depth={};bad_hist={}
    while q and expanded<args.max_states:
        bits,depth=q.popleft();expanded+=1;max_depth=max(max_depth,depth)
        hits=bits&Dmask
        if hits.bit_count()!=1:raise RuntimeError('one-hit state invariant failed')
        bad=hits.bit_length()-1
        bad_hist[str(bad)]=bad_hist.get(str(bad),0)+1
        pp=t10.private(bits,nb)
        neutral=[]
        for a,x in pp:
            nxt=bits^(1<<a)^(1<<x)
            hc=(nxt&Dmask).bit_count()
            if hc==0:
                if a!=bad or ((Dmask>>x)&1):raise RuntimeError('zero-hit transition replay drift')
                found=(nxt,depth+1,a,x);break
            if hc==1:
                neutral.append((a,x,nxt))
            elif hc!=2:
                raise RuntimeError(f'unexpected obstruction hit count {hc}')
        if found:break
        degree_hist[str(len(neutral))]=degree_hist.get(str(len(neutral)),0)+1
        for a,x,nxt in neutral:
            transitions+=1
            if nxt in seen:continue
            seen.add(nxt);q.append((nxt,depth+1))
            new_states_by_depth[str(depth+1)]=new_states_by_depth.get(str(depth+1),0)+1
        if expanded%1000==0:
            print('PROGRESS',json.dumps({'expanded':expanded,'seen':len(seen),'frontier':len(q),'depth':depth},sort_keys=True),flush=True)

    complete=not q and found is None
    status={
        'method':'funsearch-t9-onehit-moving-bad-exact-component',
        'candidate':found is not None,
        'complete':complete,
        'capped':found is None and bool(q),
        'score':134753,
        'case_index':args.case,
        'obstruction_index':c['obstruction_index'],
        'max_states':args.max_states,
        'states_expanded':expanded,
        'states_seen':len(seen),
        'frontier_remaining':len(q),
        'max_depth_expanded':max_depth,
        'transitions_examined':transitions,
        'onehit_degree_histogram':degree_hist,
        'new_states_by_depth':new_states_by_depth,
        'bad_vertex_histogram':bad_hist,
    }
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if found is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
        print(('DONE' if complete else 'CAPPED'),json.dumps({k:v for k,v in status.items() if not k.endswith('histogram') and k!='new_states_by_depth'},sort_keys=True),flush=True)
        return

    Xbits,exit_depth,old_bad,replacement=found
    X=set(t10.values(Xbits))
    if len(X)!=f.N or X&Dset or not f.independent(X,digits):raise RuntimeError('zero-hit exit replay failed')
    Ibits,pairs,orient,PH,PV=c['witness']
    points,xp=f.build(Ibits,Xbits,pairs,PH,PV,ring)
    if len(points)!=f.TARGET:raise RuntimeError(f'target score drift {len(points)}')
    status.update({
        'score':len(points),
        'exit_depth':exit_depth,
        'removed_bad':old_bad,
        'replacement':replacement,
        'private_pairs':[list(z) for z in pairs],
        'orientation':list(orient),
        'PH':PH,'PV':PV,
        'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps({k:v for k,v in status.items() if not k.endswith('histogram') and k!='new_states_by_depth'},sort_keys=True),flush=True)

if __name__=='__main__':main()
