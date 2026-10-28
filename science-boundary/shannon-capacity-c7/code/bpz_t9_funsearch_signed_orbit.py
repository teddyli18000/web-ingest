#!/usr/bin/env python3
"""Scan the full distinct signed-coordinate orbit of FunSearch's C7^5 367-set.

Translations are handled by FFT.  The remaining coordinate automorphisms are
permutations and independent sign reversals x -> -x.  The 5-cycle stabilizer of
the FunSearch seed reduces the raw 120*32 transforms to 768 distinct seeds;
this script constructs and deduplicates them explicitly.  Every FFT zero is
replayed combinatorially before materializing a 134770-point C7^10 certificate.
"""
import argparse
import json
import sys
from itertools import permutations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_fft import FUNSEARCH_COMMIT, funsearch_seed


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0']))
    ring=Ring(f.D); digits=tuple(ring.decode(v) for v in range(f.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    obs=list(f.obstruction_witnesses(I0,ring,digits,nb).items()); seed=funsearch_seed(digits)

    images={}
    for perm in permutations(range(f.D)):
        for negmask in range(1<<f.D):
            S=frozenset(f.enc(tuple(((-digits[v][perm[j]])%f.Q if ((negmask>>j)&1) else digits[v][perm[j]]) for j in range(f.D))) for v in seed)
            if len(S)!=367 or not f.independent(S,digits): raise RuntimeError('signed image invalid')
            images.setdefault(S,(perm,negmask))
    if len(images)!=768: raise RuntimeError(f'signed orbit drift: {len(images)} != 768')

    Fobs=[(mask,w,np.fft.fftn(f.arr(f.values(mask),digits))) for mask,w in obs]
    best=None; hist={}; winner=None; cases=0; per=[]
    for ii,(Sfro,meta) in enumerate(images.items()):
        perm,negmask=meta; S=set(Sfro); FS=np.fft.fftn(f.arr(S,digits)); ibest=999
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1; corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16); mn=int(corr.min()); ibest=min(ibest,mn); hist[str(mn)]=hist.get(str(mn),0)+1
            rec={'image':ii,'perm':list(perm),'negmask':negmask,'obstruction_index':oi,'min_hits':mn}
            if best is None or mn<best['min_hits']:
                best=rec; print('NEW_BEST',json.dumps(best,sort_keys=True),flush=True)
            if mn: continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                t=tuple(int(z) for z in idx)
                # Reflection is already represented in S; translation sign +1 suffices.
                X=set(f.shift_set(S,t,digits,1))
                if len(X)!=367 or not f.independent(X,digits): raise RuntimeError('signed/translated replay failed')
                if X&Dset: continue
                winner=(ii,perm,negmask,oi,t,X,w); break
            if winner: break
        per.append({'image':ii,'perm':list(perm),'negmask':negmask,'min_hits':ibest})
        if ii%32==31: print('PROGRESS',json.dumps({'images_done':ii+1,'best':best},sort_keys=True),flush=True)
        if winner: break

    status={'method':'bpz-t9-funsearch-full-distinct-signed-coordinate-orbit-all-translations-fft','candidate':winner is not None,'score':134753 if winner is None else 134770,'raw_signed_transforms':120*32,'distinct_signed_images':len(images),'seed_obstruction_cases':cases,'best':best,'min_hit_histogram':hist,'source_commit':FUNSEARCH_COMMIT}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    ii,perm,negmask,oi,t,X,w=winner; Ibits,pairs,orientation,PH,PV=w; points,xp=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring)
    if len(points)!=f.TARGET: raise RuntimeError(f'score drift {len(points)}')
    status.update({'score':len(points),'winning_image':ii,'winning_perm':list(perm),'winning_negmask':negmask,'winning_obstruction_index':oi,'winning_translation':list(t),'private_pairs':[list(z) for z in pairs],'orientation':list(orientation),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
