#!/usr/bin/env python3
"""Exact blocker-budget repair for the public BPZ t=10 two-hit alignments.

A t=10 alignment with two obstruction hits becomes an allowed independent set
of size 365 after deleting those two forced hits.  Selecting r+1 pairwise
compatible outside vertices whose union of blockers against the 365 retained
points has size at most r, then deleting those blocker owners, yields an
allowed independent set of size 366.  The resulting ten-dimensional BPZ
construction has score 134769.

This driver regenerates the five public two-hit alignments exactly and feeds
their candidate/blocker graph to the pinned c7-five exchange_dfs.cpp solver.
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
import bpz_t10_aux_translation_fft as t10


def two_hit_cases(I0,X0,ring,digits,nbmask,family_root):
    obs,_=t10.obstruction_witnesses(I0,ring,digits,nbmask)
    fam=json.loads((family_root/'data'/'family-f.json').read_text())
    states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    Fobs=[(m,w,np.fft.fftn(t10.arr(t10.values(m),digits))) for m,w in obs.items()]
    out=[];seen=set()
    for name,S in seeds:
        FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=2: continue
            Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==2):
                tr=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    Sset=set(t10.shift_set(S,tr,digits,sign)); hits=Sset&Dset
                    if len(hits)!=2: continue
                    key=(name,oi,tuple(sorted(Sset)))
                    if key in seen: continue
                    seen.add(key)
                    out.append({'seed':name,'obstruction_index':oi,'translation':tr,'translation_sign':sign,'S':Sset,'hits':set(hits),'D':Dset,'witness':w})
    if len(out)!=5: raise RuntimeError(f'two-hit case drift {len(out)} != 5')
    return out


def export_input(path,S,hits,Dset,ring,budget):
    retained=sorted(S-hits); old_index={v:i for i,v in enumerate(retained)}
    blockers={};candidates=[]
    for y in range(t10.U):
        if y in S or y in Dset: continue
        b=0
        for z in ring.NB[y]:
            i=old_index.get(z)
            if i is not None: b|=1<<i
        if b.bit_count()<=budget:
            blockers[y]=b;candidates.append(y)
    candidates.sort(key=lambda y:(blockers[y].bit_count(),y));pi={v:i for i,v in enumerate(candidates)}
    n=len(candidates);cw=(n+63)//64;bw=(len(retained)+63)//64
    if bw!=6: raise RuntimeError(f'blocker word drift {bw}')
    full=(1<<n)-1;mask64=(1<<64)-1
    with path.open('w',encoding='ascii') as h:
        h.write(f'{n} {bw} {budget}\n')
        for v in candidates:
            incompatible=0
            for z in ring.NB[v]:
                j=pi.get(z)
                if j is not None: incompatible|=1<<j
            compatible=full^incompatible
            vals=[(blockers[v]>>(64*j))&mask64 for j in range(bw)]
            vals += [(compatible>>(64*j))&mask64 for j in range(cw)]
            h.write(' '.join(f'{q:x}' for q in vals)+'\n')
    return retained,candidates,blockers


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('family_root',type=Path);ap.add_argument('solver',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--case',type=int,required=True);ap.add_argument('--budget',type=int,default=4);ap.add_argument('--cutoff',type=int,default=540);args=ap.parse_args()
    if not 0<=args.case<5: raise SystemExit('case must be 0..4')
    if not 1<=args.budget<=9: raise SystemExit('budget must be 1..9')
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']))
    ring=Ring(t10.D);digits=tuple(ring.decode(v) for v in range(t10.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    cases=two_hit_cases(I0,X0,ring,digits,nb,args.family_root);c=cases[args.case]
    with tempfile.TemporaryDirectory() as td:
        inp=Path(td)/'exchange.txt';retained,candidates,blockers=export_input(inp,c['S'],c['hits'],c['D'],ring,args.budget)
        with inp.open('rb') as src:
            p=subprocess.run([str(args.solver),str(args.cutoff),'--budget-bitsets'],stdin=src,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,text=True)
    if p.returncode!=0: raise RuntimeError(f'exchange_dfs failed rc={p.returncode}: {p.stderr[-2000:]}')
    lines=[z for z in p.stdout.splitlines() if z.strip()]
    if not lines: raise RuntimeError('exchange_dfs produced no JSON')
    search=json.loads(lines[-1]);target=args.budget+1
    status={'method':'bpz-t10-two-hit-c7-five-blocker-budget-exchange-dfs','case_index':args.case,'seed':c['seed'],'obstruction_index':c['obstruction_index'],'translation':list(c['translation']),'translation_sign':c['translation_sign'],'forced_hits':sorted(c['hits']),'budget':args.budget,'target_additions':target,'candidate_vertices':len(candidates),'search':search,'solver_stderr_tail':p.stderr[-2000:],'candidate':search.get('status')=='witness','complete':search.get('status') in ('witness','exhausted'),'score':134753,'family_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5','exchange_solver_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not status['candidate']:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(search.get('status','UNKNOWN').upper(),json.dumps(status,sort_keys=True),flush=True);return
    chosen=[int(i) for i in search.get('chosen',[])]
    if len(chosen)!=target or any(not 0<=i<len(candidates) for i in chosen): raise RuntimeError(f'bad witness {chosen}')
    add=[candidates[i] for i in chosen];owner_ids=set()
    for y in add:
        b=blockers[y]
        while b:
            q=b&-b;owner_ids.add(retained[q.bit_length()-1]);b^=q
    if len(owner_ids)>args.budget: raise RuntimeError('blocker replay failed')
    rem=set(owner_ids)
    for q in retained:
        if len(rem)==args.budget: break
        if q not in rem: rem.add(q)
    if len(rem)!=args.budget: raise RuntimeError('could not pad retained removals')
    X=(set(retained)-rem)|set(add)
    if len(X)!=366 or X&c['D'] or not t10.independent(X,digits): raise RuntimeError('repair replay failed')
    Ibits,pairs,o,PH,PV=c['witness'];pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=134769: raise RuntimeError(f'score replay {len(pts)}')
    status.update({'score':len(pts),'removed_retained_points':sorted(rem),'added_auxiliary_points':add,'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
