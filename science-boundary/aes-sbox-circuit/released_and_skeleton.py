#!/usr/bin/env python3
"""Whole-circuit released-AND affine representation and heuristic synthesis.

An XAG/XNAG circuit can be viewed as an ordered sequence of AND atoms.  Every
AND operand and every final output is affine in the eight primary inputs and
previously released AND atoms.  This representation deliberately removes named
linear boundaries (pre/middle/core/final/output): a linear helper may be kept
alive across any number of AND releases.

The synthesizer here is a calibration/search heuristic, not an exact solver.
Failure to beat or reproduce a circuit is evidence only about this heuristic.
"""
from __future__ import annotations
import argparse, collections, json, pathlib, random, urllib.request
import seed_family_census as census

SOURCES={
 "fs-101":census.DEFAULTS["fs-101"],
 "nist-g103":census.DEFAULTS["nist-g103"],
 "nist-g104":census.DEFAULTS["nist-g104"],
 "nist-a34-g110":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a34-ad4-g110-gd22-xx76-3.circ.txt",
 "nist-a28-g124":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt",
 "nist-a29-g137":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt",
}

def load_circuit(name):
    text=census.get(SOURCES[name])
    if text.lstrip().startswith('{'):
        c=json.loads(text)
    else:
        c,_=census.normalize_nist(census.parse_nist(text))
    return prune(c)

def prune(c):
    by={g['out']:g for g in c['gates']}; need=set(c['outputs']); stack=list(need)
    while stack:
        w=stack.pop(); g=by.get(w)
        if not g: continue
        for u in (g['a'],g['b']):
            if u not in need: need.add(u); stack.append(u)
    kept=[g for g in c['gates'] if g['out'] in need]
    mp={f'x{i}':f'x{i}' for i in range(8)}; out=[]
    for i,g in enumerate(kept):
        ng={'op':g['op'],'a':mp[g['a']],'b':mp[g['b']],'out':f'g{i}'}
        mp[g['out']]=ng['out']; out.append(ng)
    return {'gates':out,'outputs':[mp[o] for o in c['outputs']]}

def independent_check(c):
    vals={f'x{i}':census.input_tables(False)[f'x{i}'] for i in range(8)}
    for g in c['gates']:
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
    for x in range(256):
        y=sum(((vals[o]>>x)&1)<<i for i,o in enumerate(c['outputs']))
        if y!=census.aes_sbox(x): return False,x,y,census.aes_sbox(x)
    return True,None,None,None

def extract_skeleton(c):
    vals={f'x{i}':1<<i for i in range(8)}
    ands=[]; and_idx=0; const_bit=8
    # First pass determines AND count so the affine constant coordinate does not
    # collide with a future nonlinear atom.
    n_and=sum(g['op']=='AND' for g in c['gates']); const_bit=8+n_and; C=1<<const_bit
    vals={f'x{i}':1<<i for i in range(8)}
    for g in c['gates']:
        if g['op']=='XOR': v=vals[g['a']]^vals[g['b']]
        elif g['op']=='XNOR': v=vals[g['a']]^vals[g['b']]^C
        elif g['op']=='AND':
            ands.append({'a':vals[g['a']], 'b':vals[g['b']]})
            v=1<<(8+and_idx); and_idx+=1
        else: raise ValueError(g['op'])
        vals[g['out']]=v
    assert and_idx==n_and
    return {'n_and':n_and,'const_bit':const_bit,'ands':ands,'outputs':[vals[o] for o in c['outputs']]}

def rank(vecs):
    bs=[]
    for x in vecs:
        y=x
        for b in bs:y=min(y,y^b)
        if y:bs.append(y);bs.sort(reverse=True)
    return len(bs)

def affine_expr(target,available):
    """Return exact subset of available vectors XORing to target, or None."""
    piv={}
    for i,v in enumerate(available):
        y=v; mask=1<<i
        while y:
            p=y.bit_length()-1
            if p in piv:y^=piv[p][0];mask^=piv[p][1]
            else:piv[p]=(y,mask);break
    y=target;mask=0
    while y:
        p=y.bit_length()-1
        if p not in piv:return None
        y^=piv[p][0];mask^=piv[p][1]
    return [i for i in range(len(available)) if mask>>i&1]

def synthesize(base,seed,max_linear=100):
    # Legacy calibration heuristic retained for older scripts.
    sk=extract_skeleton(base); C=1<<sk['const_bit']; rng=random.Random(seed)
    S=[1<<i for i in range(8)]; names=[f'x{i}' for i in range(8)]; gates=[]; released=0
    targets=[]
    for ab in sk['ands']:targets.extend([ab['a'],ab['b']])
    targets.extend(sk['outputs'])
    while len([g for g in gates if g['op']!='AND'])<max_linear:
        progress=True
        while released<sk['n_and'] and sk['ands'][released]['a'] in S and sk['ands'][released]['b'] in S:
            a=S.index(sk['ands'][released]['a']);b=S.index(sk['ands'][released]['b']);out=f'w{len(gates)}'
            gates.append({'op':'AND','a':names[a],'b':names[b],'out':out});S.append(1<<(8+released));names.append(out);released+=1
        if released==sk['n_and'] and all(t in S for t in sk['outputs']):break
        missing=[t for t in targets if t not in S and affine_expr(t,S) is not None]
        if not missing:break
        t=rng.choice(missing); inds=affine_expr(t,S)
        if not inds or len(inds)<2:continue
        a,b=rng.sample(inds,2);v=S[a]^S[b];op='XOR'
        if (v^C) in [t]:v^=C;op='XNOR'
        if v in S:continue
        out=f'w{len(gates)}';gates.append({'op':op,'a':names[a],'b':names[b],'out':out});S.append(v);names.append(out)
    if released==sk['n_and'] and all(t in S for t in sk['outputs']):
        c=prune({'gates':gates,'outputs':[names[S.index(t)] for t in sk['outputs']]})
        if independent_check(c)[0]:return c
    return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--family',choices=sorted(SOURCES),default='fs-101');ap.add_argument('--seed',type=int,default=1);ap.add_argument('--max-linear',type=int,default=100);ap.add_argument('--out',required=True)
    a=ap.parse_args(); c=load_circuit(a.family); assert independent_check(c)[0]
    sk=extract_skeleton(c); res=synthesize(c,a.seed,a.max_linear); out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    summary={'family':a.family,'source_gates':len(c['gates']),'n_and':sk['n_and'],'source_linear':len(c['gates'])-sk['n_and'],'found':res is not None}
    if res is not None:(out/'candidate.json').write_text(json.dumps(res,indent=2)+'\n');summary['candidate_gates']=len(res['gates'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
