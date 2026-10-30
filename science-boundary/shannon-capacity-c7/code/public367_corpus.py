#!/usr/bin/env python3
"""Build a validated public C7^5 367-set corpus for cross-basin fiber search.

Sources are supplied by the caller at pinned commits.  The corpus includes BPZ
I0/X, the 36 molind Family-F maxima, every 367-point witness exposed by the
molind u1/u2 verifier scripts, and the deterministically reconstructed DeepMind
FunSearch 367-set.  Every set is independently replayed under the exact C7^5
conflict rule, exact duplicates are merged, and a stable SHA256 over sorted
integer vertex IDs identifies each distinct set.
"""
from __future__ import annotations
import argparse,hashlib,json,runpy,sys
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10
from bpz_t9_funsearch_fft import funsearch_seed,FUNSEARCH_COMMIT

TAN_COMMIT="c753408492dde92a239708986d16c15dbf6c3235"
C7FIVE_COMMIT="ae81e0d24b356aef3d388238f6fb4d02c4aa32a5"

def extract_367(ns,digits):
    out=[]
    for name,v in ns.items():
        if name.startswith('__'):continue
        try:
            if len(v)!=367:continue
            words=[]
            for w in v:
                if not isinstance(w,(tuple,list)) or len(w)!=5:raise ValueError
                q=tuple(int(x) for x in w)
                if any(not 0<=x<7 for x in q):raise ValueError
                words.append(t10.enc(q))
            S=frozenset(words)
            if len(S)==367 and t10.independent(S,digits):out.append((name,S))
        except Exception:
            pass
    return out

def digest(S):
    payload=','.join(map(str,sorted(S))).encode()
    return hashlib.sha256(payload).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    raw=json.loads((a.tan_root/'data'/'base_c7.json').read_text())
    digits=tuple(t10.dec(v) for v in range(t10.U))
    seeds=[]
    seeds.append(('bpz-I0',frozenset(map(int,raw['I0']))))
    seeds.append(('bpz-X',frozenset(map(int,raw['X']))))
    fam=json.loads((a.c7five_root/'data'/'family-f.json').read_text())
    for i,s in enumerate(fam['states']):seeds.append((f'family-f-{i}',frozenset(map(int,s))))
    for fn,label in [('u1.py','u1'),('u2.py','u2')]:
        ns=runpy.run_path(str(a.c7five_root/'verify'/fn))
        for var,S in extract_367(ns,digits):seeds.append((f'{label}:{var}',S))
    seeds.append(('funsearch',frozenset(funsearch_seed(digits))))
    provenance=defaultdict(list)
    by={}
    for name,S in seeds:
        if len(S)!=367 or not t10.independent(S,digits):raise RuntimeError(('invalid',name,len(S)))
        h=digest(S);by.setdefault(h,S);provenance[h].append(name)
    rows=[]
    for h,S in sorted(by.items()):
        rows.append({'sha256':h,'sources':sorted(provenance[h]),'points':sorted(S)})
    # Exact duplicate accounting; no affine/orbit quotient is silently applied.
    out={'method':'validated-public-c7p5-367-corpus','raw_seed_labels':len(seeds),'distinct_exact_sets':len(rows),'tan_commit':TAN_COMMIT,'c7five_commit':C7FIVE_COMMIT,'funsearch_commit':FUNSEARCH_COMMIT,'sets':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='sets'},sort_keys=True));print('labels',[r['sources'] for r in rows])
if __name__=='__main__':main()
