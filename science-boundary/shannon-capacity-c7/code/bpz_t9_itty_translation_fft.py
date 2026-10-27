#!/usr/bin/env python3
"""Scan all translations of the Itty R367 seed and its public companion against all BPZ t=9 obstruction masks."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import bpz_t9_aux_translation_fft as f

def load_r(path):
    out=[]
    for line in path.read_text().splitlines():
        if line.strip():
            w=tuple(map(int,line.split()))
            if len(w)!=f.D:raise RuntimeError('bad R367 line')
            out.append(f.enc(w))
    if len(out)!=f.N or len(set(out))!=f.N:raise RuntimeError('R367 size drift')
    return set(out)

def make_x(R,digits):
    # Recreate the companion map used by the public Itty C7^10 construction.
    rs=sorted(R)
    out=[]
    for rid in rs:
        w=digits[rid]
        out.append(f.enc(((2-w[1])%7,w[3],w[0],(2-w[2])%7,w[4])))
    # The public construction repairs companion entry 267 in its source ordering.
    # Since sorting destroys that ordering, reconstruct from the file order instead
    # in main; this helper is not used directly.
    return set(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('r367',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)];obs=f.obstruction_witnesses(I0,ring,digits,nb)
    r_order=[]
    for line in args.r367.read_text().splitlines():
        if line.strip():
            w=tuple(map(int,line.split()));r_order.append(f.enc(w))
    if len(r_order)!=f.N or len(set(r_order))!=f.N:raise RuntimeError('R367 size/uniqueness drift')
    R=set(r_order);X=[]
    for rid in r_order:
        w=digits[rid];X.append(f.enc(((2-w[1])%7,w[3],w[0],(2-w[2])%7,w[4])))
    X[267]=f.enc((1,5,6,3,5));X=set(X)
    seeds=[('itty-R367',R),('itty-companion',X)]
    for name,S in seeds:
        if len(S)!=f.N or not f.independent(S,digits):raise RuntimeError(f'{name} invalid')
    obs_items=list(obs.items());Fobs=[(m,w,np.fft.fftn(f.arr(f.values(m),digits))) for m,w in obs_items];cases=0;zero=0;replays=0;winner=None;best=None;hist={}
    for name,S in seeds:
        FS=np.fft.fftn(f.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            cases+=1;corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16);mn=int(corr.min());hist[str(mn)]=hist.get(str(mn),0)+1;rec={'seed':name,'obstruction_index':oi,'min_hits':mn}
            if best is None or mn<best['min_hits']:best=rec
            if mn:continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                zero+=1;t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    replays+=1;Xt=set(f.shift_set(S,t,digits,sign))
                    if len(Xt)!=f.N or not f.independent(Xt,digits):raise RuntimeError('translation replay invalid')
                    if Xt&Dset:continue
                    winner=(name,t,sign,Xt,w,oi);break
                if winner:break
            if winner:break
        if winner:break
    status={'method':'bpz-t9-Itty-R367-companion-all-translations-FFT','candidate':winner is not None,'seed_count':2,'obstruction_masks':len(obs_items),'cases':cases,'fft_zero_shifts':zero,'explicit_replays':replays,'best':best,'min_hit_histogram':hist,'itty_source_commit':'fe8966079013abaac21d1c08441500100f8e3b86'};args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    name,t,sign,Xt,w,oi=winner;Ibits,pairs,o,PH,PV=w;pts,xp=f.build(Ibits,sum(1<<z for z in Xt),pairs,PH,PV,ring);status.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(t),'translation_sign':sign,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
