#!/usr/bin/env python3
"""Scan all 2040 semilinear field coordinates for whole-skeleton interface sparsity.

This is a structural proxy, not a gate-count solver.  It measures the affine
forms required by every AND operand and final output after P(x)=c*x^(2^k), with
the unique target forms viewed over primary inputs + released AND atoms.
"""
from __future__ import annotations
import argparse, collections, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census

SBOX=[census.aes_sbox(x) for x in range(256)]

def transform_fast(sk,c,k):
    n=sk['n_and'];cb=sk['const_bit'];C=1<<cb
    pvals=[ras.semilinear(c,k,x) for x in range(256)]
    cols=[pvals[1<<j] for j in range(8)]
    inp=[]
    for i in range(8):
        v=0
        for j,z in enumerate(cols):
            if (z>>i)&1:v^=1<<j
        inp.append(v)
    def sub(v):
        r=C if ((v>>cb)&1) else 0
        for i in range(8):
            if (v>>i)&1:r^=inp[i]
        for a in range(n):
            if (v>>(8+a))&1:r^=1<<(8+a)
        return r
    ands=[{'a':sub(ab['a']),'b':sub(ab['b'])} for ab in sk['ands']]
    outs=[sub(v) for v in sk['outputs']]
    qmap={}
    for x in range(256):qmap[SBOX[pvals[x]]]=SBOX[x]
    q0=qmap[0];qcols=[qmap[1<<i]^q0 for i in range(8)]
    for y,z in qmap.items():
        q=q0
        for i,col in enumerate(qcols):
            if (y>>i)&1:q^=col
        assert q==z
    newouts=[]
    for j in range(8):
        v=C if ((q0>>j)&1) else 0
        for i,col in enumerate(qcols):
            if (col>>j)&1:v^=outs[i]
        newouts.append(v)
    return {'n_and':n,'const_bit':cb,'ands':ands,'outputs':newouts}

def form_cost(v,sk):
    support=(v & ((1<<sk['const_bit'])-1)).bit_count(); const=(v>>sk['const_bit'])&1
    if not const:return max(0,support-1)
    if support==0:return 1
    if support==1:return 2
    return support-1

def metrics(sk):
    forms=[]
    for ab in sk['ands']:forms.extend((ab['a'],ab['b']))
    forms.extend(sk['outputs']);uniq=list(dict.fromkeys(forms))
    pairfreq=collections.Counter()
    for v in uniq:
        support=[i for i in range(sk['const_bit']) if (v>>i)&1]
        for p in range(len(support)):
            for q in range(p+1,len(support)):pairfreq[(support[p],support[q])]+=1
    reuse=sum(max(0,n-1) for n in pairfreq.values())
    top_pairs=sum(sorted((n-1 for n in pairfreq.values() if n>1),reverse=True)[:20])
    weights=[(v & ((1<<sk['const_bit'])-1)).bit_count() for v in uniq]
    return {'unique_forms':len(uniq),'unique_naive_cost':sum(form_cost(v,sk) for v in uniq),
            'occurrence_naive_cost':sum(form_cost(v,sk) for v in forms),'support_sum':sum(weights),
            'max_support':max(weights),'repeated_pair_score':reuse,'top20_pair_score':top_pairs}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed-family',choices=sorted(ras.SOURCES),required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();base=ras.load_circuit(args.seed_family);sk=ras.extract_skeleton(base)
    rows=[]
    for k in range(8):
        for c in range(1,256):
            t=transform_fast(sk,c,k);m=metrics(t);m.update({'c':c,'k':k});rows.append(m)
    rows.sort(key=lambda r:(r['unique_naive_cost'],-r['repeated_pair_score'],r['support_sum']))
    for rank,r in enumerate(rows,1):r['rank_by_naive_then_pairs']=rank
    ident=next(r for r in rows if r['c']==1 and r['k']==0)
    known=next(r for r in rows if r['c']==0x3f and r['k']==5)
    result={'seed_family':args.seed_family,'n_and':sk['n_and'],'base_total':len(base['gates']),
            'base_linear':len(base['gates'])-sk['n_and'],'identity':ident,'pr31_map_0x3f_x32':known,'top50':rows[:50]}
    pathlib.Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'seed_family':args.seed_family,'identity':ident,'known':known,'best':rows[0]},sort_keys=True))

if __name__=='__main__':main()
