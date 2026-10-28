#!/usr/bin/env python3
"""Exactly traverse the neutral one-swap component of a FunSearch one-hit state.

The unique obstruction hit `bad` is held fixed.  Every graph edge replaces a
non-bad old point by a private outside neighbour that lies outside the
obstruction, preserving a 367-point independent set with exactly the same one
obstruction hit.  At every reached state we test whether `bad` has acquired an
outside-obstruction private replacement.  Such an edge produces a zero-hit
367-set and hence a 134770 BPZ t=9 certificate.

If the BFS frontier empties before the state cap, the entire neutral component
for that obstruction case is exhausted exactly; this covers neutral paths of
arbitrary length, not a fixed Hamming radius.
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
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--case',type=int,required=True);ap.add_argument('--max-states',type=int,default=10000);args=ap.parse_args()
    if not 0<=args.case<20:raise SystemExit('case must be 0..19')
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    cc=cases(I0,ring,digits,nb);c=cc[args.case];S,bad,Dset=c['S'],c['bad'],c['D'];start=sum(1<<z for z in S);Dmask=sum(1<<z for z in Dset)
    if (start&Dmask)!=(1<<bad):raise RuntimeError('start one-hit invariant failed')

    seen={start};q=deque([(start,0)]);expanded=0;transitions=0;max_depth=0;found=None;degree_hist={};new_states_by_depth={}
    while q and expanded<args.max_states:
        bits,depth=q.popleft();expanded+=1;max_depth=max(max_depth,depth)
        pp=t10.private(bits,nb)
        neutral=[]
        for a,x in pp:
            if (Dmask>>x)&1:continue
            if a==bad:
                found=(bits,x,depth);break
            neutral.append((a,x))
        if found:break
        degree_hist[str(len(neutral))]=degree_hist.get(str(len(neutral)),0)+1
        for a,x in neutral:
            nxt=bits^(1<<a)^(1<<x);transitions+=1
            if nxt in seen:continue
            if (nxt&Dmask)!=(1<<bad):raise RuntimeError('neutral obstruction invariant failed')
            seen.add(nxt);q.append((nxt,depth+1));new_states_by_depth[str(depth+1)]=new_states_by_depth.get(str(depth+1),0)+1
        if expanded%1000==0:print('PROGRESS',json.dumps({'expanded':expanded,'seen':len(seen),'frontier':len(q),'depth':depth},sort_keys=True),flush=True)

    complete=not q and found is None
    status={'method':'funsearch-t9-onehit-exact-neutral-component','candidate':found is not None,'complete':complete,'capped':found is None and bool(q),'score':134753,'case_index':args.case,'obstruction_index':c['obstruction_index'],'bad':bad,'max_states':args.max_states,'states_expanded':expanded,'states_seen':len(seen),'frontier_remaining':len(q),'max_depth_expanded':max_depth,'transitions_examined':transitions,'neutral_degree_histogram':degree_hist,'new_states_by_depth':new_states_by_depth}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if found is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('DONE' if complete else 'CAPPED'),json.dumps({k:v for k,v in status.items() if k not in ('neutral_degree_histogram','new_states_by_depth')},sort_keys=True),flush=True);return

    bits,x,depth=found;Xbits=(bits^(1<<bad))|(1<<x);X=set(t10.values(Xbits))
    if len(X)!=f.N or X&Dset or not f.independent(X,digits):raise RuntimeError('zero-hit exit replay failed')
    Ibits,pairs,orient,PH,PV=c['witness'];points,xp=f.build(Ibits,Xbits,pairs,PH,PV,ring)
    if len(points)!=f.TARGET:raise RuntimeError(f'target score drift {len(points)}')
    status.update({'score':len(points),'exit_depth':depth,'replacement':x,'private_pairs':[list(z) for z in pairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps({k:v for k,v in status.items() if k not in ('neutral_degree_histogram','new_states_by_depth')},sort_keys=True),flush=True)

if __name__=='__main__':main()
