#!/usr/bin/env python3
"""Scan m=219 d12-anchor A28/A29 local domains.

For every complete R(3,6,12) neighbourhood at e(A)=28 or 29, compute all
independent 5-sets, the transversal number tau(A), the number of hitting masks
by cardinality, and the degree sequence.  These are exact local consequences
for every B-column in a fixed-A/B gluing: its cross neighbourhood in A must be
a transversal of the independent 5-sets.
"""
from __future__ import annotations
import argparse,gzip,hashlib,itertools,json
from collections import Counter
from pathlib import Path

def decode_graph6(s):
    n=ord(s[0])-63;bits=[]
    for ch in s[1:]:
        z=ord(ch)-63;bits.extend((z>>k)&1 for k in range(5,-1,-1))
    a=[0]*n;p=0
    for j in range(1,n):
        for i in range(j):
            if bits[p]:a[i]|=1<<j;a[j]|=1<<i
            p+=1
    return a

def edge_count(a): return sum(x.bit_count() for x in a)//2

def independent_masks(a,k):
    out=[]
    for C in itertools.combinations(range(len(a)),k):
        if all(not ((a[u]>>v)&1) for u,v in itertools.combinations(C,2)):
            out.append(sum(1<<u for u in C))
    return out

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalog',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    rows=[]
    with gzip.open(a.catalog,'rt',encoding='ascii') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('>>'):continue
            g=decode_graph6(s)
            if len(g)!=12:continue
            e=edge_count(g)
            if e not in (28,29):continue
            I5=independent_masks(g,5);hist=Counter();examples={}
            for m in range(1<<12):
                if all(m&J for J in I5):
                    k=m.bit_count();hist[k]+=1
                    examples.setdefault(k,m)
            tau=min(hist)
            rows.append({'graph6':s,'edges':e,'degree_sequence':sorted(x.bit_count() for x in g),'independent5_count':len(I5),'transversal_number':tau,'hitting_histogram':{str(k):hist[k] for k in sorted(hist)},'one_minimum_transversal':[i for i in range(12) if examples[tau]>>i&1]})
    rows.sort(key=lambda r:(r['edges'],r['graph6']))
    assert sum(r['edges']==28 for r in rows)==8,len(rows)
    assert sum(r['edges']==29 for r in rows)==1,len(rows)
    out={'campaign':'m219-d12-A28-A29-domain-scan','source_sha256':sha(a.catalog),'counts':{'A28':8,'A29':1},'rows':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'tau_histogram':dict(Counter(r['transversal_number'] for r in rows)),'rows':len(rows)},sort_keys=True))
if __name__=='__main__':main()
