#!/usr/bin/env python3
"""Scan the explicit c7-five U1 367-witness against all BPZ t=9 obstructions.

The pinned c7-five verifier `verify/u1.py` contains literal CORE and FREE_WITNESS
strings and defines its independent 367-set as `core + extra`.  We parse those
literals statically rather than executing the verifier module.  Both coordinate
orders are tested because the source verifier writes words most-significant
coordinate first whereas Tan's Ring integer encoding is least-significant first;
either reversal is a graph automorphism, but their placement relative to the
fixed BPZ obstruction is different.
"""
import argparse, ast, json, sys
from pathlib import Path
from collections import Counter
import numpy as np
import bpz_t9_aux_translation_fft as f


def literals(path):
    tree=ast.parse(path.read_text())
    vals={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ('CORE','FREE_WITNESS') and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
                vals[name]=node.value.value
    if set(vals)!= {'CORE','FREE_WITNESS'}:
        raise RuntimeError(f'U1 literal drift: {sorted(vals)}')
    words=[]
    for key in ('CORE','FREE_WITNESS'):
        for tok in vals[key].split():
            if len(tok)!=5 or any(c not in '0123456' for c in tok): raise RuntimeError('bad U1 word')
            words.append(tuple(map(int,tok)))
    if len(words)!=367 or len(set(words))!=367: raise RuntimeError(f'U1 size drift {len(words)}')
    return words


def enc_lsd(w): return sum(x*7**i for i,x in enumerate(w))
def enc_msd(w): return sum(x*7**(4-i) for i,x in enumerate(w))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('c7five_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0']))
    ring=Ring(5); digits=tuple(ring.decode(v) for v in range(f.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    obs=f.obstruction_witnesses(I0,ring,digits,nb); obs_items=list(obs.items())
    W=literals(args.c7five_root/'verify'/'u1.py')
    seeds=[]; seen=set()
    for name,enc in [('u1-lsd',enc_lsd),('u1-msd',enc_msd)]:
        S={enc(w) for w in W}; key=tuple(sorted(S))
        if len(S)!=367 or not f.independent(S,digits): raise RuntimeError(f'{name} not independent')
        if key not in seen: seen.add(key); seeds.append((name,S))
    Fobs=[(m,w,np.fft.fftn(f.arr(f.values(m),digits))) for m,w in obs_items]
    hist=Counter(); best=999; rows=[]; winner=None; cases=0
    for name,S in seeds:
        FS=np.fft.fftn(f.arr(S,digits)); sbest=999
        for oi,(mask,wit,FD) in enumerate(Fobs):
            cases+=1; corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16); mn=int(corr.min()); hist[mn]+=1; sbest=min(sbest,mn)
            if mn<best: best=mn; rows=[]
            if mn==best and len(rows)<100:
                idx=np.argwhere(corr==mn)[0]; rows.append({'seed':name,'obstruction_index':oi,'min_hits':mn,'translation':[int(z) for z in idx]})
            if mn: continue
            Dset=set(f.values(mask))
            for idx in np.argwhere(corr==0):
                t=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    X=set(f.shift_set(S,t,digits,sign))
                    if X&Dset: continue
                    if len(X)!=367 or not f.independent(X,digits): raise RuntimeError('zero replay failed')
                    Ibits,pairs,o,PH,PV=wit; pts,xp=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring)
                    if len(pts)!=f.TARGET: raise RuntimeError('score drift')
                    winner=(name,oi,t,sign,pts,xp,wit); break
                if winner: break
            if winner: break
        print('SEED_DONE',json.dumps({'seed':name,'best':sbest},sort_keys=True),flush=True)
        if winner: break
    st={'method':'bpz-t9-c7five-u1-witness-translation-fft','candidate':winner is not None,'seed_count':len(seeds),'cases':cases,'global_min_hits':best,'min_hit_histogram':{str(k):v for k,v in sorted(hist.items())},'best_rows':rows,'c7five_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        st['score']=134753; args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(st,sort_keys=True)); return
    name,oi,t,sign,pts,xp,wit=winner; Ibits,pairs,o,PH,PV=wit
    st.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(t),'translation_sign':sign,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(st,sort_keys=True))
if __name__=='__main__': main()
