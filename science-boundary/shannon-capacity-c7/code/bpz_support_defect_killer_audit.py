#!/usr/bin/env python3
"""Audit private-pair killer colors of the exact k=5/k=6 support defects.

This is a small structural diagnostic for the pinned BPZ/Tandon C7 base.
For every listed five-dimensional replacement, report its exact support against
B=I0\R and the unique private-pair color (if any) whose two endpoints both
conflict with the replacement.  The frontier note proves killer popcount <= 1
for every non-B nonzero-support candidate; this script independently replays
that fact for the raw +1 defect witnesses.
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path

K5_OWNERS = [1644,13347,13600,13692,14040]
K5_ADD = [3709,13684,14335,15959,16045,16050]
K6 = [
 ([8888,10960,13347,13600,13692,14040],[6494,10659,13649,13684,14335,15959,16045]),
 ([1644,11305,13347,13600,13692,14040],[3709,11298,13684,14335,15959,16045,16050]),
 ([1644,13248,13347,13600,13692,14040],[3709,13297,13684,14335,15959,16045,16050]),
 ([1644,1741,13347,13600,13692,14040],[3709,13684,14335,15959,16045,16050,16147]),
]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args()
    root=a.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json'; raw=json.loads(p.read_text())
    base,_t,_e,axioms=load_base(p)
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    I=set(map(int,raw['I0'])); pairs=[tuple(map(int,q)) for q in raw['private_pairs']]
    R={x for x,_ in pairs}; B=I-R
    if len(B)!=359 or len(pairs)!=8: raise RuntimeError(('base drift',len(B),len(pairs)))
    def meta(z:int):
        S=sorted(ring.NB[z]&B)
        killers=[i for i,(u,v) in enumerate(pairs) if u in ring.NB[z] and v in ring.NB[z]]
        if len(killers)>1: raise RuntimeError(('multi-killer',z,killers))
        return {'v':z,'support':S,'support_size':len(S),'killer':killers[0] if killers else None}
    cases=[]
    for name,owners,add in [('k5',K5_OWNERS,K5_ADD)]+[(f'k6_{i}',o,y) for i,(o,y) in enumerate(K6)]:
        ms=[meta(z) for z in add]
        for m in ms:
            if not set(m['support'])<=set(owners): raise RuntimeError(('support escaped owners',name,m))
        cols=Counter(m['killer'] for m in ms if m['killer'] is not None)
        cases.append({'name':name,'owners':owners,'additions':ms,'killer_histogram':{str(k):v for k,v in sorted(cols.items())},'killer_free':sum(m['killer'] is None for m in ms),'distinct_killers':len(cols),'raw_gain':len(add)-len(owners)})
    out={'method':'exact-pinned-bpz-support-defect-killer-audit','private_pairs':[list(q) for q in pairs],'cases':cases}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
