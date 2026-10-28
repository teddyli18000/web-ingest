#!/usr/bin/env python3
import json, urllib.request

MASK=(1<<256)-1
BASE='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/'
URLS={
    'primary': BASE+'certificate.json',
    'mixed': BASE+'mixed-core18-certificate.json',
}

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def input_tables():
    d={}
    for b in range(8):
        v=0
        for x in range(256):
            if (x>>b)&1: v|=1<<x
        d[f'x{b}']=v
    return d

def op(op,a,b):
    if op=='XOR': return a^b
    if op=='XNOR': return (~(a^b))&MASK
    if op=='AND': return a&b
    raise ValueError(op)

def evaluate(c):
    vals=input_tables()
    for g in c['gates']:
        vals[g['out']]=op(g['op'], vals[g['a']], vals[g['b']])
    return vals

def external_inputs(c, lo, hi):
    made={g['out'] for g in c['gates'][lo:hi]}
    deps=[]
    seen=set()
    for g in c['gates'][lo:hi]:
        for w in (g['a'],g['b']):
            if w not in made and w not in seen:
                seen.add(w); deps.append(w)
    return deps

def used_after(c, lo, hi):
    made={g['out'] for g in c['gates'][lo:hi]}
    used=[]; seen=set()
    for g in c['gates'][hi:]:
        for w in (g['a'],g['b']):
            if w in made and w not in seen:
                seen.add(w); used.append(w)
    for w in c['outputs']:
        if w in made and w not in seen:
            seen.add(w); used.append(w)
    return used

def expr_in_basis(target, basis):
    # basis: [(name, truth)] ; brute force is exact because cuts are tiny.
    n=len(basis)
    for m in range(1<<n):
        v=0; names=[]
        for i,(name,t) in enumerate(basis):
            if (m>>i)&1:
                v ^= t; names.append(name)
        if v==target:
            return names
    return None

def rank(vs):
    piv=[]
    for x in vs:
        y=x
        for p in piv:
            y=min(y,y^p)
        if y:
            piv.append(y); piv.sort(reverse=True)
    return len(piv)

def analyze(name,c):
    assert len(c['gates'])==103
    vals=evaluate(c)
    core_in=external_inputs(c,42,60)
    core_out=used_after(c,42,60)
    middle_in=external_inputs(c, 26 if name=='primary' else 28, 42)
    print(f'[{name}] core_inputs={core_in}')
    print(f'[{name}] core_outputs_used={core_out}')
    print(f'[{name}] core_input_rank={rank([vals[w] for w in core_in])} affine_rank={rank([vals[w] for w in core_in]+[MASK])}')
    print(f'[{name}] middle_external_input_count={len(middle_in)} middle_external_inputs={middle_in}')
    print(f'[{name}] core_input_hex={[hex(vals[w]) for w in core_in]}')
    print(f'[{name}] core_output_hex={[hex(vals[w]) for w in core_out]}')
    return vals,core_in,core_out

def main():
    cs={k:fetch(u) for k,u in URLS.items()}
    data={k:analyze(k,c) for k,c in cs.items()}
    pv,pi,po=data['primary']; mv,mi,mo=data['mixed']

    print('\n[affine maps: mixed core inputs from primary core inputs]')
    pb=[(w,pv[w]) for w in pi]+[('1',MASK)]
    all_m=True
    for w in mi:
        e=expr_in_basis(mv[w],pb)
        print(w,'=',e)
        all_m &= e is not None
    print('mixed_inputs_in_primary_affine_span=',all_m)

    print('\n[affine maps: primary core inputs from mixed core inputs]')
    mb=[(w,mv[w]) for w in mi]+[('1',MASK)]
    all_p=True
    for w in pi:
        e=expr_in_basis(pv[w],mb)
        print(w,'=',e)
        all_p &= e is not None
    print('primary_inputs_in_mixed_affine_span=',all_p)

    print('\n[core used-output cross-span]')
    pob=[(w,pv[w]) for w in po]+[('1',MASK)]
    mob=[(w,mv[w]) for w in mo]+[('1',MASK)]
    pm=[]
    for w in mo:
        e=expr_in_basis(mv[w],pob); pm.append(e)
        print('mixed',w,'from primary outputs =',e)
    print('all_mixed_outputs_in_primary_affine_span=',all(e is not None for e in pm))
    mp=[]
    for w in po:
        e=expr_in_basis(pv[w],mob); mp.append(e)
        print('primary',w,'from mixed outputs =',e)
    print('all_primary_outputs_in_mixed_affine_span=',all(e is not None for e in mp))

    # Check whether the nine final-AND right-hand/core factors are merely permuted.
    def final_core_factors(c,vals):
        coremade={g['out'] for g in c['gates'][42:60]}
        r=[]
        for g in c['gates'][60:78]:
            hits=[w for w in (g['a'],g['b']) if w in coremade]
            r.append((g['out'],hits[0] if hits else None, vals[hits[0]] if hits else None))
        return r
    pf=final_core_factors(cs['primary'],pv); mf=final_core_factors(cs['mixed'],mv)
    print('\n[final AND core-factor truth-table multiset equal]', sorted(v for _,_,v in pf)==sorted(v for _,_,v in mf))
    print('primary_factors=',[(o,w,hex(v) if v is not None else None) for o,w,v in pf])
    print('mixed_factors=',[(o,w,hex(v) if v is not None else None) for o,w,v in mf])

if __name__=='__main__':
    main()
