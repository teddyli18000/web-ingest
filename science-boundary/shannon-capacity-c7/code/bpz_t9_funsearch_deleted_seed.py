#!/usr/bin/env python3
"""Materialize a legal 134752 C7^10 seed from a FunSearch t=9 one-hit state.

The standard BPZ t=9 construction would score 134770 with a 367-point
obstruction-free auxiliary set. A representative FunSearch state has exactly
one auxiliary point in D=N(PH)∩N(PV). Deleting only that bad point leaves a
366-point obstruction-free auxiliary set and therefore a valid structured
C7^10 independent set of size

    (367-9)^2 + 2*9*366 = 134752.

This script intentionally stops there. Downstream full-space search is free to
augment the 134752 certificate with arbitrary C7^10 vertices, so it is not
restricted to repairing the five-dimensional BPZ template.
"""
import argparse
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_representative_case import cases

SCORE=134752


def build_deleted(Ibits,Xbits,pairs,PH,PV,ring):
    """Replay the BPZ t=9 construction without f.build's 134770-only assertion."""
    I=set(f.values(Ibits));X=set(f.values(Xbits));R={a for a,q in pairs};B=I-R
    NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('deleted auxiliary still hits obstruction')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    points=sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P)
    return points,(len(X0),len(XH),len(XV))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('ids',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--case',type=int,required=True);args=ap.parse_args()
    if not 0<=args.case<20:raise SystemExit('case must be 0..19')
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    c=cases(I0,ring,digits,nb)[args.case];X=set(c['S'])-{c['bad']}
    if len(X)!=366 or X&c['D'] or not f.independent(X,digits):raise RuntimeError('deleted auxiliary seed replay failed')
    Ibits,pairs,orient,PH,PV=c['witness'];points,xp=build_deleted(Ibits,sum(1<<q for q in X),pairs,PH,PV,ring)
    if len(points)!=SCORE or len(points)!=len(set(points)):raise RuntimeError(f'134752 seed score drift {len(points)}')
    args.certificate.parent.mkdir(parents=True,exist_ok=True);args.certificate.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    ids=sorted(int(p,7) for p in points);args.ids.parent.mkdir(parents=True,exist_ok=True);args.ids.write_text(''.join(f'{z}\n' for z in ids))
    st={'method':'bpz-t9-funsearch-onehit-delete-bad','case_index':args.case,'obstruction_index':c['obstruction_index'],'bad':c['bad'],'auxiliary_size':len(X),'score':len(points),'private_pairs':[list(q) for q in pairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}}
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(json.dumps(st,sort_keys=True))

if __name__=='__main__':main()
