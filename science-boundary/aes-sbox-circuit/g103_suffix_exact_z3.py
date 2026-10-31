#!/usr/bin/env python3
"""Exact bounded synthesis of the pure-linear G103 suffix with XOR/XNOR gates.

Cut immediately after the last AND of the NIST A32/G103 circuit.  The prefix has
32 AND + 49 linear gates and the remaining suffix is an affine map from 17 live
boundary wires to eight outputs, currently using 22 XOR/XNOR gates.  Therefore a
19-gate realization of the *identity* cut basis gives a 100-gate AES S-box
certificate immediately.

For a requested GL(3,2) basis of the three non-atomic cut signals, this script
encodes a straight-line network of at most K two-input XOR/XNOR gates in Z3.  Each
gate selects two earlier wires and optionally toggles the affine constant bit.
Each of the eight required output affine forms selects one input or synthesized
wire.  The encoding is exact for this fixed cut basis and gate bound.  SAT yields
a concrete network; UNSAT is a proof for this suffix model; UNKNOWN is only a
solver timeout.

When the basis is identity, the synthesized suffix is reattached to the original
49-linear prefix and independently checked on all 256 AES inputs.  Any resulting
<=100 circuit is ready for the Few Shots official verifier.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf
import g103_cut_basis_census as cb


def parse_rows(text):
    rows=tuple(int(x,0) for x in text.split(','))
    if len(rows)!=3 or cb.rank3(rows)!=3 or any(not 1<=x<8 for x in rows):
        raise argparse.ArgumentTypeError('basis rows must be three independent nonzero 3-bit integers')
    return rows


def problem(c,rows):
    last,prefix,suffix,boundary=suf.split(c)
    m,C,vals,targets,qtargets,orig_guide=suf.formal_suffix(suffix,boundary,c['outputs'])
    extras,_=cb.semantic_cut_extras(c,boundary);extra_idx=[boundary.index(w) for w in extras]
    cmap=cb.coeff_map(rows)
    q2=[cb.transform_mask(q,extra_idx,cmap) for q in qtargets]
    t2=[q | (C if ((t>>m)&1) else 0) for q,t in zip(q2,targets)]
    return last,prefix,suffix,boundary,extras,extra_idx,m,C,t2,q2


def zselect(z3,idx,values):
    expr=values[0]
    for i in range(1,len(values)):
        expr=z3.If(idx==i,values[i],expr)
    return expr


def solve_bound(z3,m,C,targets,k,timeout_ms):
    width=m+1
    vals=[z3.BitVecVal(1<<i,width) for i in range(m)]
    A=[];B=[];XN=[]
    s=z3.Solver();s.set(timeout=timeout_ms)

    for j in range(k):
        n=m+j
        a=z3.Int(f'a_{j}');b=z3.Int(f'b_{j}');xn=z3.Bool(f'xn_{j}')
        s.add(a>=0,a<n,b>=0,b<n,a<b)
        va=zselect(z3,a,vals);vb=zselect(z3,b,vals)
        v=va ^ vb ^ z3.If(xn,z3.BitVecVal(C,width),z3.BitVecVal(0,width))
        # A useful gate must create a value not already available.  This is safe:
        # duplicate affine wires can always be removed without harming fanout.
        for old in vals:s.add(v!=old)
        vals.append(v);A.append(a);B.append(b);XN.append(xn)

    O=[]
    for oi,t in enumerate(targets):
        o=z3.Int(f'o_{oi}');s.add(o>=0,o<len(vals))
        s.add(zselect(z3,o,vals)==z3.BitVecVal(t,width));O.append(o)

    # Every synthesized gate must feed a later gate or an output.  This removes
    # dead-gate symmetries and makes "K gates" equivalent to an irredundant <=K
    # witness: if a smaller witness exists, the outer driver will test that bound.
    for j in range(k):
        idx=m+j
        users=[o==idx for o in O]
        for q in range(j+1,k):users.extend((A[q]==idx,B[q]==idx))
        s.add(z3.Or(users))

    t0=time.time();r=s.check();elapsed=time.time()-t0
    if r==z3.unknown:
        return {'status':'unknown','reason':s.reason_unknown(),'elapsed_s':round(elapsed,3)},None
    if r==z3.unsat:
        return {'status':'unsat','elapsed_s':round(elapsed,3)},None
    model=s.model()
    gates=[]
    names=[f'b{i}' for i in range(m)]
    exact=[1<<i for i in range(m)]
    for j in range(k):
        a=model.eval(A[j]).as_long();b=model.eval(B[j]).as_long();xn=z3.is_true(model.eval(XN[j],model_completion=True))
        out=f's{j}';g={'op':'XNOR' if xn else 'XOR','a':names[a],'b':names[b],'out':out}
        gates.append(g);names.append(out);exact.append(exact[a]^exact[b]^(C if xn else 0))
    outs=[model.eval(o).as_long() for o in O]
    assert [exact[i] for i in outs]==targets
    net={'gates':gates,'outputs':[names[i] for i in outs]}
    meta={'status':'sat','elapsed_s':round(elapsed,3),'output_indices':outs,
          'gate_ops':{'XOR':sum(g['op']=='XOR' for g in gates),'XNOR':sum(g['op']=='XNOR' for g in gates)}}
    return meta,net


def attach_identity(c,prefix,boundary,net):
    mp={f'b{i}':w for i,w in enumerate(boundary)}
    gates=[dict(g) for g in prefix]
    for j,g in enumerate(net['gates']):
        out=f'__exact_suffix_{j}'
        ng={'op':g['op'],'a':mp[g['a']],'b':mp[g['b']],'out':out}
        mp[g['out']]=out;gates.append(ng)
    full=ras.prune({'gates':gates,'outputs':[mp[o] for o in net['outputs']]})
    ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('identity suffix failed AES',ok))
    return full


def main():
    import z3
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=parse_rows,default=(1,2,4))
    ap.add_argument('--min-gates',type=int,default=19)
    ap.add_argument('--max-gates',type=int,default=19)
    ap.add_argument('--timeout-ms',type=int,default=300000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    if args.min_gates<0 or args.max_gates<args.min_gates:raise SystemExit('invalid gate bounds')
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    last,prefix,old_suffix,boundary,extras,extra_idx,m,C,targets,qtargets=problem(c,args.basis_rows)
    rows=[];winner=None
    for k in range(args.min_gates,args.max_gates+1):
        meta,net=solve_bound(z3,m,C,targets,k,args.timeout_ms)
        meta['gates']=k;rows.append(meta);print(json.dumps(meta,sort_keys=True),flush=True)
        if meta['status']=='sat':winner=(k,net);break
        if meta['status']=='unknown':break
    summary={'basis_rows':list(args.basis_rows),'boundary_count':m,'extras':extras,'extra_indices':extra_idx,
             'original_suffix_gates':len(old_suffix),'prefix_gates':len(prefix),'prefix_linear':sum(g['op']!='AND' for g in prefix),
             'results':rows,'best_sat_gates':None if winner is None else winner[0]}
    if winner is not None:
        k,net=winner;(out/'suffix.json').write_text(json.dumps(net,indent=2)+'\n')
        if tuple(args.basis_rows)==(1,2,4):
            full=attach_identity(c,prefix,boundary,net)
            (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
            summary['full_gates']=len(full['gates']);summary['verified_all_256']=True
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},sort_keys=True),flush=True)

if __name__=='__main__':main()
