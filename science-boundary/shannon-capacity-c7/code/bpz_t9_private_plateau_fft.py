#!/usr/bin/env python3
"""Exhaust BPZ t=9 obstructions against the 108 private-pair C7^5 plateau sets.

Wustep's independent C7 exploration records that the Polak--Schrijver 367-set
has eight public private-neighbour exchanges and exactly 108 of the 2^8 swap
subsets remain independent 367-sets.  This script reconstructs those 108 sets
from the pinned public R367.txt, validates them in Tan's Ring encoding, then
uses exact-replayed FFT correlation to scan all 7^5 translations against all
160 distinct BPZ t=9 obstruction masks.  Any zero-hit translated seed is
materialized as the 134770-point C7^10 construction.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f

WUSTEP_COMMIT = "d1633472321b27d4a5e93a5a27ccc98a19ee5af4"
PAIRS = (
    ((1,3,4,4,6),(2,3,5,4,6)),
    ((3,4,0,3,5),(2,4,6,3,5)),
    ((5,3,1,3,4),(5,3,2,3,5)),
    ((4,4,6,1,6),(5,4,6,0,6)),
    ((6,0,6,4,5),(6,1,6,5,5)),
    ((0,3,5,6,5),(6,3,5,0,5)),
    ((6,4,3,4,0),(6,4,2,4,6)),
    ((6,4,5,3,2),(6,5,5,3,1)),
)


def enc(word):
    return sum(int(x) * 7**j for j, x in enumerate(word))


def load_words(path):
    out=[]
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s or s.startswith('#'): continue
        parts=s.split()
        if len(parts)==5:
            w=tuple(map(int,parts))
        else:
            compact=''.join(ch for ch in s if ch.isdigit())
            if len(compact)!=5: raise RuntimeError(f'bad R367 line: {line!r}')
            w=tuple(map(int,compact))
        if any(x<0 or x>6 for x in w): raise RuntimeError('digit outside C7')
        out.append(enc(w))
    if len(out)!=367 or len(set(out))!=367: raise RuntimeError(f'R367 drift {len(out)}')
    return set(out)


def plateau(seed,digits):
    pp=[(enc(a),enc(b)) for a,b in PAIRS]
    for i,(a,b) in enumerate(pp):
        if a not in seed or b in seed: raise RuntimeError(f'private pair {i} drift')
    states=[]
    masks=[]
    seen=set()
    for mask in range(256):
        S=set(seed)
        for j,(a,b) in enumerate(pp):
            if mask>>j & 1:
                S.remove(a); S.add(b)
        if not f.independent(S,digits): continue
        key=tuple(sorted(S))
        if key in seen: raise RuntimeError('duplicate plateau state')
        seen.add(key); states.append(S); masks.append(mask)
    if len(states)!=108: raise RuntimeError(f'plateau drift {len(states)} != 108')
    return states,masks


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path)
    ap.add_argument('wustep_root',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('status',type=Path)
    args=ap.parse_args()

    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0']))
    ring=Ring(5); digits=tuple(ring.decode(v) for v in range(f.U))
    nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    obs=f.obstruction_witnesses(I0,ring,digits,nb)
    seed=load_words(args.wustep_root/'problems'/'c7-shannon'/'compute'/'R367.txt')
    if not f.independent(seed,digits): raise RuntimeError('wustep R367 not independent after coordinate-preserving encoding')
    states,masks=plateau(seed,digits)

    obs_items=list(obs.items())
    Fobs=[(m,w,np.fft.fftn(f.arr(f.values(m),digits))) for m,w in obs_items]
    hist=Counter(); best=10**9; best_rows=[]; zero_replays=0; winner=None
    for si,S in enumerate(states):
        FS=np.fft.fftn(f.arr(S,digits))
        for oi,(mask,witness,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            mn=int(corr.min()); hist[mn]+=1
            if mn<best:
                best=mn; best_rows=[]
            if mn==best and len(best_rows)<100:
                loc=np.argwhere(corr==mn)[0]
                best_rows.append({'state_index':si,'swap_mask':masks[si],'obstruction_index':oi,'min_hits':mn,'fft_translation':[int(z) for z in loc]})
            if mn!=0: continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    Xset=set(f.shift_set(S,t,digits,sign)); zero_replays+=1
                    if Xset&Dset: continue
                    if len(Xset)!=367 or not f.independent(Xset,digits): raise RuntimeError('zero replay independence drift')
                    Ibits,pairs,orient,PH,PV=witness
                    points,xp=f.build(Ibits,sum(1<<z for z in Xset),pairs,PH,PV,ring)
                    if len(points)!=f.TARGET: raise RuntimeError(f'target drift {len(points)}')
                    winner=(si,masks[si],oi,t,sign,points,xp,witness)
                    break
                if winner: break
            if winner: break
        if winner: break

    status={
        'method':'bpz-t9-wustep-private-pair-plateau-translation-fft',
        'candidate':winner is not None,
        'plateau_states':len(states),'private_pairs':len(PAIRS),'obstruction_masks':len(obs_items),
        'cases_scanned':sum(hist.values()),'min_hit_histogram':{str(k):v for k,v in sorted(hist.items())},
        'global_min_hits':best,'best_rows':best_rows,'zero_exact_replays':zero_replays,
        'wustep_source_commit':WUSTEP_COMMIT,
    }
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=134753
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
        print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    si,sm,oi,t,sign,points,xp,witness=winner
    Ibits,pairs,orient,PH,PV=witness
    status.update({
        'score':len(points),'winning_state_index':si,'winning_swap_mask':sm,
        'winning_obstruction_index':oi,'winning_translation':list(t),'translation_sign':sign,
        'private_pairs_witness':[list(z) for z in pairs],'orientation':list(orient),'PH':PH,'PV':PV,
        'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
