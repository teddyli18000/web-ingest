#!/usr/bin/env python3
"""Scan the full distinct signed-coordinate orbit of BPZ-X for t=10.

Translations are handled by FFT.  Any zero-hit image gives score 134789; any
one-hit image is repaired simply by deleting that hit, giving |X|=366 and score
134769.  Every candidate is replayed exactly before materialization.
"""
import argparse,json,sys
from itertools import permutations
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    obs,ostats=t10.obstruction_witnesses(I0,ring,digits,nb); Fobs=[(m,w,np.fft.fftn(t10.arr(t10.values(m),digits))) for m,w in obs.items()]
    images={}
    for perm in permutations(range(t10.D)):
        for negmask in range(1<<t10.D):
            S=frozenset(t10.enc(tuple(((-digits[v][perm[j]])%t10.Q if ((negmask>>j)&1) else digits[v][perm[j]]) for j in range(t10.D))) for v in X0)
            if len(S)!=367 or not t10.independent(S,digits): raise RuntimeError('signed image invalid')
            images.setdefault(S,(perm,negmask))
    print('ORBIT',json.dumps({'raw':120*32,'distinct':len(images)},sort_keys=True),flush=True)
    best=None; hist={}; cases=0; winner=None
    for ii,(Sfro,meta) in enumerate(images.items()):
        S=set(Sfro); perm,negmask=meta; FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1; corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16); mn=int(corr.min()); hist[str(mn)]=hist.get(str(mn),0)+1
            rec={'image':ii,'perm':list(perm),'negmask':negmask,'obstruction_index':oi,'min_hits':mn,'obstruction_size':mask.bit_count()}
            if best is None or mn<best['min_hits']:
                best=rec; print('NEW_BEST',json.dumps(best,sort_keys=True),flush=True)
            if mn>1: continue
            Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==mn):
                tr=tuple(int(z) for z in idx); Xfull=set(t10.shift_set(S,tr,digits,1)); hits=Xfull&Dset
                if len(hits)>1: continue
                X=Xfull-Dset; score=(t10.N-t10.T)**2+2*t10.T*len(X)
                if score<=t10.BASELINE: continue
                winner=(ii,perm,negmask,oi,tr,X,hits,w,score,mask); break
            if winner: break
        if ii%64==63: print('PROGRESS',json.dumps({'images_done':ii+1,'best':best},sort_keys=True),flush=True)
        if winner: break
    status={'method':'bpz-t10-bpzX-full-distinct-signed-coordinate-orbit-all-translations','candidate':winner is not None,'score':t10.BASELINE if winner is None else winner[8],'raw_signed_transforms':120*32,'distinct_signed_images':len(images),'cases':cases,'best':best,'min_hit_histogram':hist,'obstruction_stats':ostats}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    ii,perm,negmask,oi,tr,X,hits,w,score,mask=winner; Ibits,pairs,o,PH,PV=w; pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=score: raise RuntimeError('score replay failed')
    status.update({'score':score,'winning_image':ii,'winning_perm':list(perm),'winning_negmask':negmask,'winning_obstruction_index':oi,'winning_translation':list(tr),'deleted_auxiliary_hits':sorted(hits),'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
