#!/usr/bin/env python3
"""Exact one-point repair of every two-hit BPZ t=10 alignment.

A translated public 367-set meeting a t=10 obstruction in exactly two points
leaves a 365-point obstruction-free independent set after deleting the hits.
If any allowed ambient vertex is nonconfusable with those 365 retained points,
adding it gives |X|=366 and therefore a 10D certificate of

    (367-10)^2 + 20*366 = 134769.

All FFT two-hit shifts are replayed exactly before the free-add test.
"""
import argparse,json,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    obs,ostats=t10.obstruction_witnesses(I0,ring,digits,nb)
    if len(obs)!=16: raise RuntimeError(f't10 obstruction drift {len(obs)}')
    fam=json.loads((args.family_root/'data'/'family-f.json').read_text()); states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    Fobs=[(mask,w,np.fft.fftn(t10.arr(t10.values(mask),digits))) for mask,w in obs.items()]

    pair_cases=0; shifts=0; explicit=0; best_free=0; winner=None; pair_summaries=[]
    universe=set(range(t10.U))
    for name,S in seeds:
        FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16); mn=int(corr.min())
            if mn!=2: continue
            pair_cases+=1; Dset=set(t10.values(mask)); local_shifts=0; local_best=0
            for idx in np.argwhere(corr==2):
                shifts+=1; local_shifts+=1; tr=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    explicit+=1; Xfull=set(t10.shift_set(S,tr,digits,sign)); hits=Xfull&Dset
                    if len(Xfull)!=367 or not t10.independent(Xfull,digits): raise RuntimeError('translated seed replay failed')
                    if len(hits)!=2: continue
                    retained=Xfull-Dset
                    if len(retained)!=365: raise RuntimeError('retained size drift')
                    blocked=ring.nbhd(retained)
                    free=universe-Dset-blocked
                    local_best=max(local_best,len(free)); best_free=max(best_free,len(free))
                    if not free: continue
                    add=min(free); X=set(retained); X.add(add)
                    if len(X)!=366 or X&Dset or not t10.independent(X,digits): raise RuntimeError('free-add replay failed')
                    score=(t10.N-t10.T)**2+2*t10.T*len(X)
                    if score!=134769: raise RuntimeError(f'score formula drift {score}')
                    winner=(name,oi,tr,sign,X,hits,add,w,score,mask,len(free)); break
                if winner: break
            pair_summaries.append({'seed':name,'obstruction_index':oi,'two_hit_shifts':local_shifts,'max_free_additions_after_forced_deletion':local_best})
            print('PAIR_DONE',json.dumps(pair_summaries[-1],sort_keys=True),flush=True)
            if winner: break
        if winner: break

    status={'method':'bpz-t10-exact-two-hit-delete2-freeadd1','candidate':winner is not None,'score':134753 if winner is None else 134769,'obstruction_stats':ostats,'two_hit_seed_obstruction_pairs':pair_cases,'two_hit_fft_shifts':shifts,'explicit_replays':explicit,'max_free_additions_after_forced_deletion':best_free,'pair_summaries':pair_summaries}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    name,oi,tr,sign,X,hits,add,w,score,mask,nfree=winner; Ibits,pairs,o,PH,PV=w; pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=score: raise RuntimeError(f'candidate replay {len(pts)} != {score}')
    status.update({'score':score,'winning_seed':name,'winning_obstruction_index':oi,'winning_obstruction_size':mask.bit_count(),'winning_translation':list(tr),'translation_sign':sign,'deleted_auxiliary_hits':sorted(hits),'added_auxiliary_point':add,'free_addition_count':nfree,'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
