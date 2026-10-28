#!/usr/bin/env python3
"""Drive an incremental neutral walk from a FunSearch t=9 one-hit state.

A walk keeps the unique obstruction hit fixed and repeatedly performs legal
1-for-1 swaps among the other 366 points.  The C++ core updates C7^5 coverage
counts and unique-owner XORs incrementally.  If the bad point ever obtains a
non-obstruction replacement, the resulting zero-hit 367-set is replayed and
materialized as the nominal 134770-point BPZ t=9 certificate.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_fft import funsearch_seed, FUNSEARCH_COMMIT
from bpz_t9_funsearch_exchange_repair import distinct_signed_images


def onehit_cases(image_index, images, obs, digits):
    S0=set(images[image_index][0]);FS=np.fft.fftn(f.arr(S0,digits));out=[]
    for oi,(mask,witness) in enumerate(obs):
        Dset=set(f.values(mask));FD=np.fft.fftn(f.arr(Dset,digits))
        corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
        if int(corr.min())!=1:continue
        for idx in np.argwhere(corr==1):
            t=tuple(int(z) for z in idx);S=set(f.shift_set(S0,t,digits,1));hits=S&Dset
            if len(S)!=f.N or not f.independent(S,digits) or len(hits)!=1:raise RuntimeError('onehit replay drift')
            out.append({'obstruction_index':oi,'translation':t,'bad':next(iter(hits)),'S':S,'D':Dset,'witness':witness})
    out.sort(key=lambda z:(z['obstruction_index'],z['translation']))
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('walker',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path)
    ap.add_argument('--image',type=int,default=330);ap.add_argument('--case',type=int,required=True);ap.add_argument('--steps',type=int,default=5_000_000);ap.add_argument('--seed',type=int,required=True);ap.add_argument('--check-every',type=int,default=10000);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    obs=list(f.obstruction_witnesses(I0,ring,digits,nb).items());images=distinct_signed_images(funsearch_seed(digits),digits);cases=onehit_cases(args.image,images,obs,digits)
    if len(cases)!=20:raise RuntimeError(f'image {args.image} onehit drift {len(cases)}')
    if not 0<=args.case<len(cases):raise SystemExit('bad case')
    c=cases[args.case]
    with tempfile.TemporaryDirectory() as td:
        inp=Path(td)/'walk.txt';inp.write_text('bad '+str(c['bad'])+'\nselected '+' '.join(map(str,sorted(c['S'])))+'\nobstruction '+' '.join(map(str,sorted(c['D'])))+'\n')
        p=subprocess.run([str(args.walker),str(inp),str(args.steps),str(args.seed),str(args.check_every)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
    if p.returncode!=0:raise RuntimeError(f'walker failed rc={p.returncode}: {p.stderr[-4000:]}')
    lines=[z for z in p.stdout.splitlines() if z.strip()]
    if not lines:raise RuntimeError('walker produced no JSON')
    wr=json.loads(lines[-1]);status={'method':'funsearch-t9-onehit-incremental-neutral-random-walk','candidate':False,'score':134753,'image':args.image,'case':args.case,'obstruction_index':c['obstruction_index'],'translation':list(c['translation']),'initial_bad':c['bad'],'steps_requested':args.steps,'seed':args.seed,'walker':wr,'funsearch_source_commit':FUNSEARCH_COMMIT}
    if wr.get('found'):
        X=set(map(int,wr['selected']))
        if len(X)!=f.N or X&c['D'] or not f.independent(X,digits):raise RuntimeError('walker witness replay failed')
        Ibits,pairs,o,PH,PV=c['witness'];pts,xp=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring)
        if len(pts)!=f.TARGET:raise RuntimeError(f'score drift {len(pts)}')
        status.update({'candidate':True,'score':len(pts),'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'private_pairs':[list(q) for q in pairs],'orientation':list(o),'PH':PH,'PV':PV})
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('FOUND' if status['candidate'] else 'NONE'),json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
