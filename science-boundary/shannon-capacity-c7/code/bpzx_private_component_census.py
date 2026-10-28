#!/usr/bin/env python3
"""Enumerate the full private-neighbour exchange component of public BPZ X.

A state move replaces one old point by an outside point having exactly that one
old point as conflict owner.  These neutral 1-for-1 moves preserve a 367-point
C7^5 independent set.  We exhaust the connected component containing BPZ X and
record the maximum number of distinct private owners.  Reaching >=11 would
open t>=11 Gao/BPZ constructions; a completed max<=10 rules that out for this
entire neutral component.
"""
import argparse,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    if len(X0)!=367 or not t10.independent(X0,digits): raise RuntimeError('BPZ X invalid')
    start=sum(1<<z for z in X0)
    comp,pm=t10.component(start,nb)
    hist={}; maxowners=-1; maxpairs=-1; best=[]
    for b in comp:
        pp=pm[b]; owners=len({a for a,q in pp}); pairs=len(pp)
        hist[str(owners)]=hist.get(str(owners),0)+1
        if owners>maxowners:
            maxowners=owners; maxpairs=pairs; best=[b]
        elif owners==maxowners:
            maxpairs=max(maxpairs,pairs)
            if len(best)<20: best.append(b)
    ibits=sum(1<<z for z in I0)
    status={
        'method':'bpz-X-private-neighbour-component-census',
        'component_states':len(comp),
        'contains_bpz_I0':ibits in comp,
        'max_private_owners':maxowners,
        'max_private_pairs_among_max_owner_states':maxpairs,
        'owner_histogram':hist,
        't11_state_exists':maxowners>=11,
        'sample_best_states':[sorted(t10.values(b)) for b in best[:3]],
    }
    args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print(json.dumps(status,sort_keys=True))

if __name__=='__main__': main()
