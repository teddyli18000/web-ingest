#!/usr/bin/env python3
"""Materialize verifier-ready 134752 C7^10 seeds from the 20 public t=9 one-hit states.

The cases are exactly those reconstructed by ``bpz_t9_exchange_repair.one_hit_cases``
from the pinned BPZ X/I0 and public Family-F 367-sets.  Each case has a unique
auxiliary point in the BPZ t=9 obstruction.  Deleting that point leaves 366
obstruction-free auxiliary points and therefore a legal 134752-point C7^10
independent set.  Downstream searches are unrestricted in ten dimensions.
"""
import argparse
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_exchange_repair import one_hit_cases
from bpz_t9_funsearch_deleted_seed import build_deleted

SCORE=134752


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path)
    ap.add_argument('family_root',type=Path)
    ap.add_argument('certificate',type=Path)
    ap.add_argument('ids',type=Path)
    ap.add_argument('status',type=Path)
    ap.add_argument('--case',type=int,required=True)
    args=ap.parse_args()
    if not 0<=args.case<20: raise SystemExit('case must be 0..19')

    sys.path.insert(0,str(args.tan_root.resolve()))
    from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(f.D); digits=tuple(ring.decode(v) for v in range(f.U))
    nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    cs=one_hit_cases(I0,X0,ring,digits,nb,args.family_root)
    c=cs[args.case]
    X=set(c['S'])-{c['bad']}
    if len(X)!=366 or X&c['D'] or not f.independent(X,digits):
        raise RuntimeError('public deleted auxiliary replay failed')
    Ibits,pairs,orient,PH,PV=c['witness']
    points,xp=build_deleted(Ibits,sum(1<<q for q in X),pairs,PH,PV,ring)
    if len(points)!=SCORE or len(points)!=len(set(points)):
        raise RuntimeError(f'134752 seed score drift {len(points)}')

    args.certificate.parent.mkdir(parents=True,exist_ok=True)
    args.certificate.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    ids=sorted(int(p,7) for p in points)
    args.ids.parent.mkdir(parents=True,exist_ok=True)
    args.ids.write_text(''.join(f'{z}\n' for z in ids))
    st={
        'method':'bpz-t9-public-onehit-delete-bad',
        'case_index':args.case,'seed':c['seed'],'obstruction_index':c['obstruction_index'],
        'translation':list(c['translation']),'translation_sign':c['translation_sign'],
        'bad':c['bad'],'auxiliary_size':len(X),'score':len(points),
        'private_pairs':[list(q) for q in pairs],'orientation':list(orient),
        'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},
    }
    args.status.parent.mkdir(parents=True,exist_ok=True)
    args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n')
    print(json.dumps(st,sort_keys=True),flush=True)

if __name__=='__main__': main()
