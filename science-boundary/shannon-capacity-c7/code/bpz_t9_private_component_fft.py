#!/usr/bin/env python3
"""Scan the full 243-state BPZ I0 private-swap component as auxiliary X seeds.

The t=9 obstruction enumeration already constructs the complete independent
1-for-1 private-neighbour component of the 367-point BPZ parent I0 and verifies
that it has 243 states.  Previous auxiliary scans used only I0 itself.  Here we
reuse every one of those 243 independent 367-sets as a candidate auxiliary X,
and exhaust all 7^5 translations against all 160 distinct t=9 obstruction
masks using exact-replayed FFT correlation.

A replayed zero-hit state materializes the 134770-point C7^10 construction and
is passed to the Few Shots verifier by the workflow.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('status',type=Path)
    args=ap.parse_args()

    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0']))
    ring=Ring(f.D); digits=tuple(ring.decode(v) for v in range(f.U))
    nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]

    start=sum(1<<z for z in I0)
    comp,_=f.component(start,nb)
    if len(comp)!=243: raise RuntimeError(f'private component drift {len(comp)}')
    states=[]
    for bits in sorted(comp):
        S=set(f.values(bits))
        if len(S)!=f.N or not f.independent(S,digits): raise RuntimeError('private component contains invalid state')
        states.append((bits,S))

    obs=f.obstruction_witnesses(I0,ring,digits,nb)
    obs_items=list(obs.items())
    Fobs=[(mask,w,np.fft.fftn(f.arr(f.values(mask),digits))) for mask,w in obs_items]

    hist=Counter(); best=10**9; best_rows=[]; cases=0; zero_fft=0; replays=0; winner=None
    for si,(state_bits,S) in enumerate(states):
        FS=np.fft.fftn(f.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            mn=int(corr.min()); hist[mn]+=1
            if mn<best:
                best=mn; best_rows=[]
            if mn==best and len(best_rows)<200:
                loc=np.argwhere(corr==mn)[0]
                best_rows.append({'state_index':si,'obstruction_index':oi,'min_hits':mn,'fft_translation':[int(z) for z in loc]})
            if mn!=0: continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                zero_fft+=1; t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    replays+=1; Xset=set(f.shift_set(S,t,digits,sign))
                    if len(Xset)!=f.N or not f.independent(Xset,digits): raise RuntimeError('translated component state replay failed')
                    if Xset&Dset: continue
                    Ibits,pairs,o,PH,PV=w
                    points,xp=f.build(Ibits,sum(1<<z for z in Xset),pairs,PH,PV,ring)
                    if len(points)!=f.TARGET: raise RuntimeError(f'target drift {len(points)}')
                    winner=(si,oi,t,sign,points,xp,w)
                    break
                if winner: break
            if winner: break
        print('STATE_DONE',json.dumps({'state_index':si,'cases':cases,'global_min_hits':best},sort_keys=True),flush=True)
        if winner: break

    status={
        'method':'bpz-t9-full-243-private-component-translation-fft',
        'candidate':winner is not None,'private_component_states':len(states),
        'obstruction_masks':len(obs_items),'seed_obstruction_cases':cases,
        'global_min_hits':best,'min_hit_histogram':{str(k):v for k,v in sorted(hist.items())},
        'best_rows':best_rows,'fft_zero_shifts_examined':zero_fft,'explicit_replays':replays,
        'tan_source_commit':'c753408492dde92a239708986d16c15dbf6c3235',
    }
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=134753
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
        print('NONE',json.dumps(status,sort_keys=True),flush=True); return

    si,oi,t,sign,points,xp,w=winner
    Ibits,pairs,o,PH,PV=w
    status.update({
        'score':len(points),'winning_state_index':si,'winning_obstruction_index':oi,
        'winning_translation':list(t),'translation_sign':sign,
        'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,
        'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
