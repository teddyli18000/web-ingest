#!/usr/bin/env python3
"""Scan orientable t=11/10/9 subsets of the frozen U2 private-pair parent.

For a t-pair BPZ/Gao witness with a 367-point auxiliary independent set from
which h obstruction hits are deleted, the C7^10 score is

    367^2 + t^2 - 2*t*h.

Hence a Few Shots p004 improvement over 134753 requires:
  t=11: h<=2; t=10: h<=1; t=9: h=0.

The frozen U2 parent has 11 genuine private pairs but no orientation using all
11.  This script exactly enumerates every size-11/10/9 subset and every binary
orientation, deduplicates exact obstruction masks, and scans all translations
of the public 367-point seed catalog by exact-rounded FFT.  Promising FFT shifts
are replayed combinatorially before any certificate is emitted.
"""
import argparse
import json
import runpy
import sys
from itertools import combinations, product
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as base
from bpz_t9_funsearch_fft import funsearch_seed

N=367
BASELINE=134753
TS=(11,10,9)


def extract_367(ns,digits):
    out=[]
    for name,v in ns.items():
        if name.startswith('__'):continue
        try:
            if len(v)!=367:continue
        except Exception:
            continue
        try:
            words=[]
            for w in v:
                if not isinstance(w,(tuple,list)) or len(w)!=5:raise ValueError
                q=tuple(int(x) for x in w)
                if any(not 0<=x<7 for x in q):raise ValueError
                words.append(base.enc(q))
            S=frozenset(words)
            if len(S)==367 and base.independent(S,digits):out.append((name,set(S)))
        except Exception:pass
    uniq={}
    for name,S in out:uniq.setdefault(frozenset(S),name)
    return [(name,set(S)) for S,name in uniq.items()]


def validate_parent(parent,pairs,ring,digits):
    if len(parent)!=N or not base.independent(parent,digits):raise RuntimeError('parent invalid')
    if len(pairs)!=11 or len({a for a,q in pairs})!=11:raise RuntimeError('private pair count drift')
    for a,q in pairs:
        if a not in parent or q in parent:raise RuntimeError(f'bad private pair {(a,q)}')
        hits=[z for z in parent if q in ring.NB[z]]
        if hits!=[a]:raise RuntimeError(f'private replay failed {(a,q)} hits={hits}')


def witnesses(parent,pairs,ring,digits):
    Ibits=sum(1<<z for z in parent)
    by_t={t:{} for t in TS}
    stats={}
    for t in TS:
        raw=0; subset_with_orientation=0
        for idxs in combinations(range(len(pairs)),t):
            ps=tuple(pairs[i] for i in idxs)
            any_valid=False
            for orient in product((0,1),repeat=t):
                PH=[q if s else a for (a,q),s in zip(ps,orient)]
                PV=[a if s else q for (a,q),s in zip(ps,orient)]
                if not base.independent(PH,digits) or not base.independent(PV,digits):continue
                raw+=1;any_valid=True
                Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));mask=sum(1<<z for z in Dset)
                by_t[t].setdefault(mask,(Ibits,ps,orient,PH,PV))
            if any_valid:subset_with_orientation+=1
        hist={}
        for mask in by_t[t]:hist[str(mask.bit_count())]=hist.get(str(mask.bit_count()),0)+1
        stats[str(t)]={'raw_valid_orientations':raw,'subsets_with_valid_orientation':subset_with_orientation,'distinct_obstructions':len(by_t[t]),'obstruction_sizes':hist}
    return by_t,stats


def build(Ibits,X,pairs,PH,PV,ring):
    t=len(pairs);I=set(base.values(Ibits));R={a for a,q in pairs};B=I-R
    NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('auxiliary still intersects obstruction')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    expected=(N-t)**2+2*t*len(X)
    if len(P)!=expected:raise RuntimeError(f'score drift {len(P)} != {expected}')
    pts=sorted(''.join(map(str,ring.decode(a)+ring.decode(c))) for a,c in P)
    return pts,(len(X0),len(XH),len(XV))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('c7five_root',type=Path);ap.add_argument('parent_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    ring=Ring(base.D);digits=tuple(ring.decode(v) for v in range(base.U))
    frozen=json.loads(args.parent_json.read_text());parent=set(map(int,frozen['points']));pairs=[tuple(map(int,p)) for p in frozen['private_pairs']];validate_parent(parent,pairs,ring,digits)
    by_t,ostats=witnesses(parent,pairs,ring,digits);print('ORIENTABILITY',json.dumps(ostats,sort_keys=True),flush=True)

    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']))
    fam=json.loads((args.c7five_root/'data'/'family-f.json').read_text());seeds=[('bpz-X',X0),('bpz-I0',I0),('u2-parent',parent)]+[(f'family-f-{i}',set(map(int,s))) for i,s in enumerate(fam['states'])]
    for fn,label in (('u1.py','u1'),('u2.py','u2')):
        ns=runpy.run_path(str(args.c7five_root/'verify'/fn));seeds += [(f'{label}:{name}',S) for name,S in extract_367(ns,digits)]
    seeds.append(('funsearch',set(funsearch_seed(digits))))
    dedup={}
    for name,S in seeds:
        if len(S)!=N or not base.independent(S,digits):raise RuntimeError(f'invalid seed {name}')
        dedup.setdefault(frozenset(S),name)
    seeds=[(name,set(S)) for S,name in dedup.items()]
    print('SEEDS',json.dumps({'count':len(seeds),'names':[n for n,_ in seeds]},sort_keys=True),flush=True)

    best=None;hist={};cases=0;winner=None
    for t in TS:
        allowed=(t*t-65)//(2*t)  # largest integer h with t^2-2th >64
        if allowed<0 or not by_t[t]:continue
        Fobs=[(mask,w,np.fft.fftn(base.arr(base.values(mask),digits))) for mask,w in by_t[t].items()]
        for name,S in seeds:
            FS=np.fft.fftn(base.arr(S,digits));sbest=999
            for oi,(mask,w,FD) in enumerate(Fobs):
                cases+=1;corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16);mn=int(corr.min());sbest=min(sbest,mn);hist[f'{t}:{mn}']=hist.get(f'{t}:{mn}',0)+1
                rec={'t':t,'seed':name,'obstruction_index':oi,'min_hits':mn,'allowed_hits':allowed,'obstruction_size':mask.bit_count()}
                if best is None or (mn-allowed,best.get('t',0)*-1,mn)<(best['min_hits']-best['allowed_hits'],t*-1,best['min_hits']):best=rec;print('NEW_BEST',json.dumps(best,sort_keys=True),flush=True)
                if mn>allowed:continue
                Dset=set(base.values(mask))
                for idx in np.argwhere(corr<=allowed):
                    tr=tuple(int(z) for z in idx)
                    for sign in (1,-1):
                        Xfull=set(base.shift_set(S,tr,digits,sign))
                        if len(Xfull)!=N or not base.independent(Xfull,digits):raise RuntimeError('translated seed replay failed')
                        hits=Xfull&Dset
                        if len(hits)>allowed:continue
                        X=Xfull-Dset;score=N*N+t*t-2*t*len(hits)
                        if score<=BASELINE:continue
                        winner=(t,name,oi,tr,sign,X,hits,w,score,mask);break
                    if winner:break
                if winner:break
            print('SEED_DONE',json.dumps({'t':t,'seed':name,'best_hits':sbest},sort_keys=True),flush=True)
            if winner:break
        if winner:break

    status={'method':'u2-private-subsets-t11-t10-t9-all-orientations-public367-all-translations','candidate':winner is not None,'score':BASELINE if winner is None else winner[7],'parent_source':frozen.get('source'),'orientation_stats':ostats,'seed_count':len(seeds),'cases':cases,'best':best,'histogram':hist}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    t,name,oi,tr,sign,X,hits,w,score,mask=winner;Ibits,wpairs,orient,PH,PV=w;pts,xp=build(Ibits,X,wpairs,PH,PV,ring)
    if len(pts)!=score or score<=BASELINE:raise RuntimeError('candidate score replay failed')
    status.update({'score':score,'winning_t':t,'winning_seed':name,'winning_obstruction_index':oi,'winning_obstruction_size':mask.bit_count(),'winning_translation':list(tr),'translation_sign':sign,'deleted_auxiliary_hits':sorted(hits),'auxiliary_size':len(X),'private_pairs':[list(p) for p in wpairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
