#!/usr/bin/env python3
"""Traverse legal 1-swap paths through BPZ obstruction hit-count <=2.

Start from one of the four exact FunSearch t=9 one-hit representatives.  Every
state is a 367-point C7^5 independent set.  Edges are all private one-for-one
swaps, so independence and cardinality are preserved exactly.  We keep states
with one or two points in the fixed obstruction D and treat hit-count zero as a
breakthrough exit.  This strictly enlarges the exact one-hit component search:
a path may temporarily worsen from one obstruction hit to two before returning
to one and finally zero.

If the BFS frontier empties before ``--max-states``, the entire <=2-hit component
is exhausted exactly.  If the cap is reached, the result is diagnostic only.
"""
import argparse,json,sys
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
    ap.add_argument('--max-states',type=int,default=20000)
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
    Dset=c['D']; Dmask=sum(1<<z for z in Dset)
    start=sum(1<<z for z in c['S'])
    if (start&Dmask).bit_count()!=1:raise RuntimeError('start one-hit invariant failed')

    seen={start}; q=deque([(start,0)])
    expanded=0; transitions=0; max_depth=0; found=None
    hit_hist={}; degree_hist={}; new_by_depth={}; max_frontier=1
    while q and expanded<args.max_states:
        bits,depth=q.popleft(); expanded+=1; max_depth=max(max_depth,depth)
        hc0=(bits&Dmask).bit_count()
        if hc0 not in (1,2):raise RuntimeError(f'kept state hit count {hc0}')
        hit_hist[str(hc0)]=hit_hist.get(str(hc0),0)+1
        pp=t10.private(bits,nb)
        kept=0
        for a,x in pp:
            nxt=bits^(1<<a)^(1<<x)
            hc=(nxt&Dmask).bit_count()
            if hc==0:
                found=(nxt,depth+1,a,x,hc0);break
            if hc not in (1,2):continue
            kept+=1; transitions+=1
            if nxt in seen:continue
            if len(seen)>=args.max_states:
                # Preserve a nonempty frontier marker without admitting an
                # unrecorded state into the exact seen set.
                q.append((nxt,depth+1));break
            seen.add(nxt);q.append((nxt,depth+1))
            new_by_depth[str(depth+1)]=new_by_depth.get(str(depth+1),0)+1
        degree_hist[str(kept)]=degree_hist.get(str(kept),0)+1
        if found:break
        max_frontier=max(max_frontier,len(q))
        if len(seen)>=args.max_states and q:break
        if expanded%500==0:
            print('PROGRESS',json.dumps({'expanded':expanded,'seen':len(seen),'frontier':len(q),'depth':depth,'hits':hc0},sort_keys=True),flush=True)

    complete=found is None and not q
    status={
        'method':'funsearch-t9-hitcount-le2-private-swap-component',
        'candidate':found is not None,
        'complete':complete,
        'capped':found is None and not complete,
        'score':134753,
        'case_index':args.case,
        'obstruction_index':c['obstruction_index'],
        'max_states':args.max_states,
        'states_expanded':expanded,
        'states_seen':len(seen),
        'frontier_remaining':len(q),
        'max_frontier':max_frontier,
        'max_depth_expanded':max_depth,
        'transitions_examined':transitions,
        'hit_count_histogram':hit_hist,
        'kept_degree_histogram':degree_hist,
        'new_states_by_depth':new_by_depth,
    }
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if found is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
        print(('DONE' if complete else 'CAPPED'),json.dumps(status,sort_keys=True),flush=True)
        return

    Xbits,exit_depth,removed,replacement,from_hits=found
    X=set(t10.values(Xbits))
    if len(X)!=f.N or X&Dset or not f.independent(X,digits):raise RuntimeError('zero-hit exit replay failed')
    Ibits,pairs,orient,PH,PV=c['witness']
    points,xp=f.build(Ibits,Xbits,pairs,PH,PV,ring)
    if len(points)!=f.TARGET:raise RuntimeError(f'target score drift {len(points)}')
    status.update({
        'score':len(points),'exit_depth':exit_depth,'exit_from_hits':from_hits,
        'removed':removed,'replacement':replacement,
        'private_pairs':[list(z) for z in pairs],'orientation':list(orient),
        'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
