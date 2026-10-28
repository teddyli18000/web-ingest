#!/usr/bin/env python3
"""Scan the exact portable U2 367-word witness against all BPZ t=9 obstructions."""
import argparse,json,runpy,sys
from pathlib import Path
import numpy as np
import bpz_t9_aux_translation_fft as f

def enc(w):return sum(int(x)*7**(4-i) for i,x in enumerate(w))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)];obs=f.obstruction_witnesses(I0,ring,digits,nb)
    ns=runpy.run_path(str(args.c7five_root/'verify'/'u2.py'),run_name='__u2_t9_probe__')
    words=ns.get('witness');
    if not isinstance(words,list) or len(words)!=367:raise RuntimeError('U2 witness drift')
    base={enc(w) for w in words}
    if len(base)!=367 or not f.independent(base,digits):raise RuntimeError('U2 witness independence drift')
    seeds=[('u2-lsd',base),('u2-msd',{f.enc(tuple(reversed(digits[v]))) for v in base})]
    obs_items=list(obs.items());Fobs=[(m,w,np.fft.fftn(f.arr(f.values(m),digits))) for m,w in obs_items]
    winner=None;best=None;hist={};per=[]
    for name,S in seeds:
        FS=np.fft.fftn(f.arr(S,digits));sb=999;sh={}
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16);mn=int(corr.min());sb=min(sb,mn);sh[str(mn)]=sh.get(str(mn),0)+1;hist[str(mn)]=hist.get(str(mn),0)+1
            rec={'seed':name,'obstruction_index':oi,'min_hits':mn}
            if best is None or mn<best['min_hits']:best=rec
            if mn:continue
            D=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                t=tuple(map(int,idx))
                for sign in (1,-1):
                    X=set(f.shift_set(S,t,digits,sign))
                    if len(X)!=367 or not f.independent(X,digits):raise RuntimeError('translation replay failed')
                    if X&D:continue
                    winner=(name,oi,t,sign,X,w);break
                if winner:break
            if winner:break
        per.append({'seed':name,'min_hits':sb,'histogram':sh})
        if winner:break
    status={'method':'bpz-t9-u2-portable-witness-two-coordinate-orders-all-translations-fft','candidate':winner is not None,'best':best,'per_seed':per,'min_hit_histogram':hist,'score':134753,'c7five_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'};args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True));return
    name,oi,t,sign,X,w=winner;Ibits,pairs,o,PH,PV=w;pts,xp=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring);status.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(t),'translation_sign':sign,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True))
if __name__=='__main__':main()
