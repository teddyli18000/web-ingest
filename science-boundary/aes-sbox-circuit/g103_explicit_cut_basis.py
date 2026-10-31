#!/usr/bin/env python3
"""Exact explicit-prefix cost census for G103 GL(3,2) cut bases.

The NIST A32/G103 seed has exactly three non-atomic linear values crossing the
cut after its final AND.  In the source these are t47,t48,t49; normalized circuit
wire names differ, so they are detected by affine semantics.

Those three wires are terminal within the nonlinear prefix: they are not inputs
to any later prefix gate.  We may therefore remove their producer gates, keep the
rest of the 32-AND prefix fixed, and materialize any transformed basis of their
3-dimensional span at the cut.  This script exactly tests whether the three
basis outputs can be produced using at most three new XOR/XNOR gates from the
remaining prefix wires (allowing an earlier basis output to feed a later one),
materializes a witness, prunes the resulting prefix against its transformed cut
interface, and reports its actual AND/linear gate count.

Why the <=3 test is exact for the <=49-linear frontier: after deleting the three
old interface-only producers the fixed prefix has 46 linear gates.  A transformed
prefix with <=49 linear gates has room for at most three new gates.  Every missing
basis output must itself be produced by some gate, so there is no room for a
helper-only gate.  It suffices to try all orders in which the three target basis
values can themselves be generated from currently available wires.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf
import g103_cut_basis_census as cb


def affine_values(c):
    sk=ras.extract_skeleton(c);C=1<<sk['const_bit']
    vals={f'x{i}':1<<i for i in range(8)};and_no=0
    for g in c['gates']:
        a,b=vals[g['a']],vals[g['b']]
        if g['op']=='XOR':v=a^b
        elif g['op']=='XNOR':v=a^b^C
        elif g['op']=='AND':v=1<<(8+and_no);and_no+=1
        else:raise ValueError(g['op'])
        vals[g['out']]=v
    assert and_no==sk['n_and']
    return sk,C,vals


def basis_targets(extra_vals,rows):
    out=[]
    for row in rows:
        v=0
        for k,x in enumerate(extra_vals):
            if (row>>k)&1:v^=x
        out.append(v)
    assert len(set(out))==3
    return out


def pair_witness(available,target,C):
    items=sorted(available.items(),key=lambda kv:kv[1])
    byval={v:n for v,n in items}
    for va,na in items:
        vb=va^target
        nb=byval.get(vb)
        if nb is not None and nb!=na:
            return 'XOR',na,nb
        vb=va^target^C
        nb=byval.get(vb)
        if nb is not None and nb!=na:
            return 'XNOR',na,nb
    return None


def synthesize_at_cut(c,rows):
    last,prefix,suffix,boundary=suf.split(c)
    sk,C,vals=affine_values(c)
    extras,_=cb.semantic_cut_extras(c,boundary)
    extra_vals=[vals[w] for w in extras];targets=basis_targets(extra_vals,rows)

    # The old cut-extra producers are interface-only inside the prefix.
    consumers={w:[] for w in extras}
    for g in prefix:
        for w in extras:
            if g['a']==w or g['b']==w:consumers[w].append(g['out'])
    assert all(not xs for xs in consumers.values()),consumers
    producers={g['out']:g for g in prefix if g['out'] in extras}
    assert set(producers)==set(extras),(extras,producers)
    base=[dict(g) for g in prefix if g['out'] not in set(extras)]

    # Values/names still available after deleting the three terminal producers.
    available={1<<i:f'x{i}' for i in range(8)}
    for g in base:available.setdefault(vals[g['out']],g['out'])

    best=None
    for order in itertools.permutations(range(3)):
        av=dict(available);gates=[];names={}
        ok=True
        for ti in order:
            t=targets[ti]
            if t in av:
                names[ti]=av[t];continue
            hit=pair_witness(av,t,C)
            if hit is None:
                ok=False;break
            op,a,b=hit;out=f'__cut_basis_{len(gates)}'
            gates.append({'op':op,'a':a,'b':b,'out':out})
            av[t]=out;names[ti]=out
        if not ok:continue
        # Fill names for targets already generated indirectly/by duplicate order.
        for ti,t in enumerate(targets):
            if ti not in names and t in av:names[ti]=av[t]
        if len(names)!=3:continue
        rec=(len(gates),order,gates,names)
        if best is None or rec[0]<best[0]:best=rec
    if best is None:
        return None,{'rows':list(rows),'status':'needs_gt3'}

    added,order,newg,names=best
    raw={'gates':base+newg,'outputs':[]}
    extra_pos={w:k for k,w in enumerate(extras)}
    interface=[]
    for w in boundary:
        interface.append(names[extra_pos[w]] if w in extra_pos else w)
    raw['outputs']=interface
    pruned=ras.prune(raw)
    # Prefix-only prune is structural, not an AES check.  All 32 ANDs must remain.
    na=sum(g['op']=='AND' for g in pruned['gates'])
    nl=len(pruned['gates'])-na
    assert na==32,(rows,na,nl)
    return {'prefix':pruned,'interface':interface,'targets':targets,'extras':extras}, {
        'rows':list(rows),'status':'found','added_basis_gates':added,
        'prefix_gates':len(pruned['gates']),'prefix_and':na,'prefix_linear':nl,
        'basis_order':list(order),'basis_names':[names[i] for i in range(3)],
        'new_gates':newg,'extras':extras,
    }


def attach_suffix(c,prefix_rec,suffix_net):
    interface=prefix_rec['interface']
    mp={f'b{i}':w for i,w in enumerate(interface)}
    gates=[dict(g) for g in prefix_rec['prefix']['gates']]
    for j,g in enumerate(suffix_net['gates']):
        out=f'__basis_suffix_{j}'
        ng={'op':g['op'],'a':mp[g['a']],'b':mp[g['b']],'out':out}
        mp[g['out']]=out;gates.append(ng)
    full=ras.prune({'gates':gates,'outputs':[mp[o] for o in suffix_net['outputs']]})
    ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('transformed prefix/suffix failed AES',ok))
    return full


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rows',help='optional comma-separated GL(3,2) rows')
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    mats=[tuple(int(x,0) for x in args.rows.split(','))] if args.rows else list(cb.gl3())
    rows=[]
    for mat in mats:
        assert cb.rank3(mat)==3
        rec,meta=synthesize_at_cut(c,mat);rows.append(meta)
        if args.rows and rec is not None:
            (out/'prefix.json').write_text(json.dumps(rec,indent=2)+'\n')
        print(json.dumps(meta,sort_keys=True),flush=True)
    rows.sort(key=lambda r:(999 if r.get('prefix_linear') is None else r['prefix_linear'],r['rows']))
    summary={'matrices':len(rows),'prefix_le_48':sum(r.get('prefix_linear',999)<=48 for r in rows),
             'prefix_le_49':sum(r.get('prefix_linear',999)<=49 for r in rows),
             'cost_hist':{},'rows':rows}
    from collections import Counter
    summary['cost_hist']=dict(sorted(Counter(r.get('prefix_linear','gt49') for r in rows).items(),key=lambda kv:str(kv[0])))
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__':main()
