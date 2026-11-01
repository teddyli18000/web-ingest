#!/usr/bin/env python3
"""Exact arbitrary {AND,XOR,XNOR} multi-output suffix synthesis after FS101 g90.

The 101-gate record has ten gates after g90.  This encoding fixes the prefix
through g90 but imposes *no* identity, count, or truth-function constraints on
the removed suffix gates.  Each of k new gates:

  * chooses two distinct wires from all prefix wires or earlier new gates;
  * chooses AND, XOR, or XNOR;
  * is represented exactly on all 256 AES inputs.

Outputs already available in the prefix may be used for free.  Each remaining
AES output selects one new gate with the exact required 256-bit truth table.
Thus k=9 is a direct 100-gate decision problem (and pruning may only improve it).
The formulation is a side-divisor multi-output exact-synthesis SAT instance,
matching the window-resynthesis direction used by modern eSLIM/resub work while
retaining all 8 AES input variables and every prefix side-divisor.

`--force-original` with k=10 pins all selector/op variables to the known suffix
and serves as a semantic encoding/reconstruction control.  A free SAT witness is
always reconstructed into the complete circuit and independently checked on all
256 AES inputs.  Solver timeout/unknown is not an exclusion.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Cadical153

import released_and_skeleton as ras
import search_arch_seed as sas

MASK=(1<<256)-1
OPS=("AND","XOR","XNOR")


def add_exactly_one(cnf,pool,lits):
    cnf.extend(CardEnc.equals(lits=lits,bound=1,vpool=pool,encoding=EncType.seqcounter).clauses)


def op_clauses(sel,a,b,v,op):
    """CNF for sel -> (v = op(a,b))."""
    z=-sel
    if op=='AND':
        return [[z,-a,-b,v],[z,a,-v],[z,b,-v]]
    if op=='XOR':
        return [[z,a,b,-v],[z,-a,-b,-v],[z,-a,b,v],[z,a,-b,v]]
    return [[z,a,b,v],[z,-a,-b,v],[z,-a,b,-v],[z,a,-b,-v]]


def prefix_data(c,cut_wire='g90'):
    prefix=next(i for i,g in enumerate(c['gates']) if g['out']==cut_wire)+1
    vals=sas.inputs_truth()
    for g in c['gates'][:prefix]: vals[g['out']]=sas.op_eval(g['op'],vals[g['a']],vals[g['b']])
    names=[f'x{i}' for i in range(8)]+[g['out'] for g in c['gates'][:prefix]]
    truths=[vals[n] for n in names]
    return prefix,names,truths


def build(c,k,force_original=False):
    prefix,names,truths=prefix_data(c)
    nbase=len(names); pool=IDPool(); cnf=CNF()
    V=[[pool.id(('v',g,t)) for t in range(256)] for g in range(k)]
    UA=[[pool.id(('a',g,t)) for t in range(256)] for g in range(k)]
    UB=[[pool.id(('b',g,t)) for t in range(256)] for g in range(k)]
    selA=[]; selB=[]; opv=[]

    for g in range(k):
        nsrc=nbase+g
        A=[pool.id(('sa',g,j)) for j in range(nsrc)]
        B=[pool.id(('sb',g,j)) for j in range(nsrc)]
        O=[pool.id(('op',g,op)) for op in OPS]
        selA.append(A); selB.append(B); opv.append(O)
        add_exactly_one(cnf,pool,A); add_exactly_one(cnf,pool,B); add_exactly_one(cnf,pool,O)

        # Gates are commutative. A-index < B-index is WLOG and also enforces
        # the official verifier's distinct-wire operand rule.
        for i in range(nsrc):
            for j in range(i+1):
                cnf.append([-A[i],-B[j]])

        for side,S,U in (('a',A,UA[g]),('b',B,UB[g])):
            for j,s in enumerate(S):
                if j<nbase:
                    tr=truths[j]
                    for t,u in enumerate(U):
                        cnf.append([-s,u if ((tr>>t)&1) else -u])
                else:
                    q=j-nbase
                    for t,u in enumerate(U):
                        x=V[q][t]
                        cnf.append([-s,-x,u]); cnf.append([-s,x,-u])

        for oi,op in enumerate(OPS):
            s=O[oi]
            for t in range(256): cnf.extend(op_clauses(s,UA[g][t],UB[g][t],V[g][t],op))

    _,targets=sas.eval_circuit(c)
    base_by={}
    for n,tr in zip(names,truths): base_by.setdefault(tr,[]).append(n)
    target_meta=[]; outsel={}
    for oi,tr in enumerate(targets):
        if tr in base_by:
            target_meta.append({'output':oi,'kind':'prefix','wire':base_by[tr][0]})
            continue
        S=[pool.id(('out',oi,g)) for g in range(k)]
        outsel[oi]=S; add_exactly_one(cnf,pool,S)
        for g,s in enumerate(S):
            for t in range(256): cnf.append([-s,V[g][t] if ((tr>>t)&1) else -V[g][t]])
        target_meta.append({'output':oi,'kind':'local'})

    original=None
    if force_original:
        if k!=len(c['gates'])-prefix: raise ValueError(('force-original requires old suffix size',len(c['gates'])-prefix))
        local=c['gates'][prefix:]
        name_to_base={n:i for i,n in enumerate(names)}
        local_out={q['out']:i for i,q in enumerate(local)}
        for g,q in enumerate(local):
            def idx(w):
                if w in name_to_base:return name_to_base[w]
                return nbase+local_out[w]
            ia,ib=idx(q['a']),idx(q['b']); ia,ib=sorted((ia,ib))
            cnf.append([selA[g][ia]]);cnf.append([selB[g][ib]]);cnf.append([opv[g][OPS.index(q['op'])]])
        for oi,S in outsel.items():
            w=c['outputs'][oi]
            if w not in local_out: raise AssertionError(('target not local under force-original',oi,w))
            cnf.append([S[local_out[w]]])
        original=[dict(g) for g in local]

    return {'cnf':cnf,'pool':pool,'prefix':prefix,'names':names,'truths':truths,'nbase':nbase,
            'V':V,'selA':selA,'selB':selB,'opv':opv,'outsel':outsel,'target_meta':target_meta,
            'k':k,'original':original}


def reconstruct(c,d,model):
    pos={x for x in model if x>0}; names=list(d['names']); gates=[dict(g) for g in c['gates'][:d['prefix']]]
    local_names=[]
    for g in range(d['k']):
        ia=next(i for i,x in enumerate(d['selA'][g]) if x in pos)
        ib=next(i for i,x in enumerate(d['selB'][g]) if x in pos)
        op=next(OPS[i] for i,x in enumerate(d['opv'][g]) if x in pos)
        avail=names+local_names
        out=f'__ms{g}'
        gates.append({'op':op,'a':avail[ia],'b':avail[ib],'out':out}); local_names.append(out)
    outputs=[]
    for m in d['target_meta']:
        oi=m['output']
        if m['kind']=='prefix': outputs.append(m['wire']); continue
        S=d['outsel'][oi]; g=next(i for i,x in enumerate(S) if x in pos); outputs.append(local_names[g])
    full=ras.prune({'gates':gates,'outputs':outputs})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('SAT suffix reconstruction failed AES',ok))
    return full


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--k',type=int,required=True)
    ap.add_argument('--force-original',action='store_true'); ap.add_argument('--conf-budget',type=int,default=2000000)
    ap.add_argument('--out',required=True); args=ap.parse_args(); out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101');assert len(c['gates'])==101 and ras.independent_check(c)[0]
    d=build(c,args.k,args.force_original);t0=time.time()
    with Cadical153(bootstrap_with=d['cnf'].clauses) as solver:
        if args.conf_budget>0:
            solver.conf_budget(args.conf_budget);sat=solver.solve_limited()
        else:sat=solver.solve()
        model=solver.get_model() if sat is True else None
    summary={'k':args.k,'force_original':args.force_original,'prefix_gates':d['prefix'],'prefix_sources':d['nbase'],
             'local_targets':sorted(d['outsel']),'vars':d['pool'].top,'clauses':len(d['cnf'].clauses),
             'conf_budget':args.conf_budget,'sat':sat is True,'unsat':sat is False,'timed_out':sat is None,
             'seconds':round(time.time()-t0,3),
             'family_scope':'fixed FS101 prefix through g90; arbitrary k-gate AND/XOR/XNOR DAG using any prefix side-divisors; exact AES outputs'}
    if model is not None:
        full=reconstruct(c,d,model);summary['candidate_gates']=len(full['gates']);summary['verified_all_256']=True
        summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in OPS}
        (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
