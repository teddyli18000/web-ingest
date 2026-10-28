#!/usr/bin/env python3
"""Scan complete R(3,6,13/14) catalogues for the m=219,n11=0 branches.

For degree sequence 12^30 13^6, the induced graph H on the six degree-13
vertices has at least 9 edges (each degree-12 vertex has at most two H
neighbours). Hence a maximum-H-degree vertex has h>=3 H-neighbours. Anchoring
at that degree-13 vertex gives
    S=156+h, b-a=63-h, and b>=88,
so a=e(A)>=25+h>=28.

For degree sequence 12^31 13^4 14, anchor the unique degree-14 vertex. If h of
the four degree-13 vertices are in its neighbourhood,
    S=168+h, b-a=51-h, and b>=77,
so a>=26+h. This script authenticates the complete A catalogues and records
edge-stratum sizes/records for precisely these high-edge ranges.
"""
from __future__ import annotations

import argparse,gzip,hashlib,json
from collections import Counter
from pathlib import Path


def decode_graph6(s:str):
    n=ord(s[0])-63; bits=[]
    for ch in s[1:]:
        x=ord(ch)-63; bits.extend((x>>k)&1 for k in range(5,-1,-1))
    adj=[0]*n;p=0
    for j in range(1,n):
        for i in range(j):
            if bits[p]:adj[i]|=1<<j;adj[j]|=1<<i
            p+=1
    return adj

def edges(adj):return sum(x.bit_count() for x in adj)//2

def degseq(adj):return sorted(x.bit_count() for x in adj)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def scan(path,n,expected,lo):
    op=gzip.open if path.suffix=='.gz' else open
    hist=Counter();rows=[];total=0
    with op(path,'rt',encoding='ascii') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('>>'):continue
            a=decode_graph6(s);assert len(a)==n
            total+=1;e=edges(a);hist[e]+=1
            if e>=lo:rows.append({'graph6':s,'edges':e,'degree_sequence':degseq(a)})
    assert total==expected,(n,total,expected)
    return {'path':str(path),'sha256':sha(path),'total':total,
            'edge_histogram':{str(k):v for k,v in sorted(hist.items())},
            'selected_min_edges':lo,'selected_count':len(rows),'selected':rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--r36-13',type=Path,required=True);ap.add_argument('--r36-14',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    out={'r36_13_ge28':scan(a.r36_13,13,275086,28),
         'r36_14_ge26':scan(a.r36_14,14,263520,26),
         'derivation':{
           '12^30_13^6':{'H_edges_min':9,'anchor_H_degree_min':3,'A_edges_min':28},
           '12^31_13^4_14':{'unique_anchor_degree':14,'A_edges_min_by_h':'26+h, h in 0..4'}}}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'r36_13_ge28':out['r36_13_ge28']['selected_count'],'r36_14_ge26':out['r36_14_ge26']['selected_count'],
      'hist13':out['r36_13_ge28']['edge_histogram'],'hist14':out['r36_14_ge26']['edge_histogram']},sort_keys=True))
if __name__=='__main__':main()
