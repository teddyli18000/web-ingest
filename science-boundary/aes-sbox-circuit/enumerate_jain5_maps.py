#!/usr/bin/env python3
"""Enumerate all GL(4,2) input maps for Jain's 17-gate five-AND core.

This independently reproduces the 60 compatible maps mentioned in the merged
105-gate Few Shots shot, then ranks them against the live 103 circuit's middle
cut.  It uses only exact 16-state truth tables and GF(2) arithmetic.
"""
import itertools, json
MASK=(1<<16)-1

def var(i):
    v=0
    for x in range(16):
        if (x>>i)&1:v|=1<<x
    return v
A,B,C,D=[var(i) for i in range(4)]
VARS=[A,B,C,D]
def lf(mask):
    v=0
    for i,t in enumerate(VARS):
        if (mask>>i)&1:v^=t
    return v
def rank_masks(xs):
    p=[]
    for x in xs:
        y=x
        for q in p:y=min(y,y^q)
        if y:p.append(y);p.sort(reverse=True)
    return len(p)
def span(bs):
    return {sum([],[]) if False else _xor_subset(bs,m) for m in range(1<<len(bs))}
def _xor_subset(bs,m):
    v=0
    for i,b in enumerate(bs):
        if (m>>i)&1:v^=b
    return v

def primary_targets():
    a,b,c,d=A,B,C,D
    w42=a&b; w43=w42^c; w44=w43&d; w45=b^w44; w46=w42&c; w47=d^w46
    w48=a&w47; w49=w43^w48; w50=w48^b; w51=w49&w50; w52=w51^a; w53=w52^w49
    w54=w45&w53; w55=w54^w47; w56=w55^w49; w57=w53^w45; w58=w56^w57; w59=w55^w45
    return [w45,w59,w52,w57,w53,w49,w58,w55,w56],[w45,w52,w49,w55]

def jain17(inp, stop_after_last_and=False):
    j51,j49,j41,j48=inp; ws=list(inp)
    j50=j41^j48; ws.append(j50)
    d52=j50&j51; ws.append(d52)
    d53=j49^d52; ws.append(d53)
    d54=j41&d53; ws.append(d54)
    d55=d54^j48; ws.append(d55)
    d56=j49^j51; ws.append(d56)
    d57=j48^d52; ws.append(d57)
    d58=d57&d56; ws.append(d58)
    d59=j49^d58; ws.append(d59)
    d60=d53^d59; ws.append(d60)
    d61=j49&d60; ws.append(d61)
    d62=d53^d61; ws.append(d62)
    d63=d55&d62; ws.append(d63)
    if stop_after_last_and:return ws
    d64=j41^d63; ws.append(d64)
    d65=d55^d64; ws.append(d65)
    d66=j51^d61; ws.append(d66)
    d67=d65^d66; ws.append(d67)
    return ws

# 15-signal external cut of the live 103 primary middle layer.  The current
# four core inputs expressed in that cut are exact bit masks below.
U_COORDS=[
    int('000010111100011',2), # w35
    int('000001001111100',2), # w33
    int('001100110001111',2), # w38
    int('110000000011111',2), # w41
]
def cut_form(mask):
    v=0
    for i,u in enumerate(U_COORDS):
        if (mask>>i)&1:v^=u
    return v

def main():
    targets,vbasis=primary_targets(); targetset=set(targets); V=span(vbasis)
    # A rank-four Jain output basis in the published 17-gate topology:
    # d55,d59,d64,d66 are wire indices 8,12,17,19 when inputs occupy 0..3.
    outpos=(8,12,17,19)
    compatible=[]
    for tup in itertools.permutations(range(1,16),4):
        if rank_masks(tup)!=4:continue
        ws=jain17([lf(m) for m in tup])
        if span([ws[i] for i in outpos])==V:
            pre=jain17([lf(m) for m in tup],True)
            cov=sum(t in set(ws) for t in targets)
            precov=sum(t in set(pre) for t in targets)
            cut=[cut_form(m) for m in tup]
            weights=[x.bit_count() for x in cut]
            separate_tree=sum(max(0,w-1) for w in weights)
            compatible.append({
                'basis_masks':list(tup),
                'target_coverage_in_published_17':cov,
                'target_coverage_before_last_4_xors':precov,
                'external_cut_weights':weights,
                'separate_tree_bound':separate_tree,
            })
    assert len(compatible)==60,len(compatible)
    compatible.sort(key=lambda r:(r['separate_tree_bound'],-r['target_coverage_in_published_17'],r['basis_masks']))
    result={
        'gl4_size':20160,
        'compatible_count':60,
        'max_published_17_target_coverage':max(r['target_coverage_in_published_17'] for r in compatible),
        'max_preterminal_target_coverage':max(r['target_coverage_before_last_4_xors'] for r in compatible),
        'maps':compatible,
    }
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
