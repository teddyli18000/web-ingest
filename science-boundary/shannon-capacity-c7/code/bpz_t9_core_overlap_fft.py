#!/usr/bin/env python3
"""Scan the portable c7-five core-overlap witnesses against all BPZ t=9 obstructions.

The portable core-overlap bundle contains two verified 367-word parents whose
intersection has size 315 and one verified 367-word witness.  These are far from
the 360-core Family-F component used by the original 38-seed scan.  For each of
the three explicit sets, this script scans all 160 t=9 obstruction masks and all
7^5 translations by exact-rounded FFT.  Every zero is replayed combinatorially
before materializing a 134770-point C7^10 certificate.
"""
import argparse,gzip,json,sys
from pathlib import Path
import numpy as np
import bpz_t9_aux_translation_fft as f

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)];obs=f.obstruction_witnesses(I0,ring,digits,nb)
    with gzip.open(args.c7five_root/'data'/'core-overlap.json.gz','rt') as h:b=json.load(h)
    if int(b.get('parent_intersection_size',-1))!=315:raise RuntimeError('core-overlap intersection drift')
    seeds=[('core-parent-0',set(map(int,b['parents'][0]))),('core-parent-1',set(map(int,b['parents'][1]))),('core-witness',set(map(int,b['witness'])))]
    for name,S in seeds:
        if len(S)!=367 or not f.independent(S,digits):raise RuntimeError(f'{name} invalid')
    obs_items=list(obs.items());Fobs=[(mask,w,np.fft.fftn(f.arr(f.values(mask),digits))) for mask,w in obs_items]
    winner=None;hist={};per=[];cases=0;best=None;near=[]
    for name,S in seeds:
        FS=np.fft.fftn(f.arr(S,digits));sb=999;sh={}
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1;corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16);mn=int(corr.min());sb=min(sb,mn);sh[str(mn)]=sh.get(str(mn),0)+1;hist[str(mn)]=hist.get(str(mn),0)+1
            rec={'seed':name,'obstruction_index':oi,'min_hits':mn}
            if best is None or mn<best['min_hits']:best=rec
            if mn==1:
                for idx in np.argwhere(corr==1)[:20]:near.append({**rec,'translation':[int(z) for z in idx]})
            if mn:continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    X=set(f.shift_set(S,t,digits,sign))
                    if len(X)!=367 or not f.independent(X,digits):raise RuntimeError('translation replay failed')
                    if X&Dset:continue
                    winner=(name,oi,t,sign,X,w);break
                if winner:break
            if winner:break
        per.append({'seed':name,'min_hits':sb,'histogram':sh});print('SEED_DONE',json.dumps(per[-1],sort_keys=True),flush=True)
        if winner:break
    status={'method':'bpz-t9-core-overlap-three-portable-seeds-all-translations-fft','candidate':winner is not None,'seed_count':3,'obstruction_masks':160,'cases':cases,'best':best,'per_seed':per,'min_hit_histogram':hist,'one_hit_examples':near[:100],'c7five_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'};args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True));return
    name,oi,t,sign,X,w=winner;Ibits,pairs,o,PH,PV=w;pts,xp=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring);status.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(t),'translation_sign':sign,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True))
if __name__=='__main__':main()
