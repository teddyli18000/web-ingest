#!/usr/bin/env python3
"""Exact pairwise cross-output sharing search in the FS101 g90 suffix.

The ten gates after g90 form five independent output cones of sizes
  y3:2, y4:2, y5:1, y6:3, y7:2.
Individual one-gate compression of every cone has been exhaustively ruled out.
Therefore the next direct-100 family is cross-output sharing: choose any pair of
cones with old total L, delete both, and synthesize their two exact AES output
truth tables with L-1 completely arbitrary legal gates over all g90-prefix side
divisors and earlier new gates. Operations are AND/XOR/XNOR and operands are
distinct. Any SAT witness splices into the untouched other three cones and gives
100 gates before/after pruning.

The CNF is the same exact 256-pattern semantics as fs101_unrestricted_suffix_sat,
but only two output targets and at most four new gates are present, making this a
much smaller calibrated decomposition of the hard 9-gate global instance.
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
OPS=('AND','XOR','XNOR')
CONES={3:['g91','g92'],4:['g93','g94'],5:['g95'],6:['g96','g97','g98'],7:['g99','g100']}


def add_exactly_one(cnf,pool,lits):
    cnf.extend(CardEnc.equals(lits=lits,bound=1,vpool=pool,encoding=EncType.seqcounter).clauses)


def op_clauses(sel,a,b,v,op):
    z=-sel
    if op=='AND': return [[z,-a,-b,v],[z,a,-v],[z,b,-v]]
    if op=='XOR': return [[z,a,b,-v],[z,-a,-b,-v],[z,-a,b,v],[z,a,-b,v]]
    return [[z,a,b,v],[z,-a,-b,v],[z,-a,b,-v],[z,a,-b,-v]]


def prefix_data(c):
    cut=next(i for i,g in enumerate(c['gates']) if g['out']=='g90')+1
    vals=sas.inputs_truth()
    for g in c['gates'][:cut]: vals[g['out']]=sas.op_eval(g['op'],vals[g['a']],vals[g['b']])
    names=[f'x{i}' for i in range(8)]+[g['out'] for g in c['gates'][:cut]]
    return cut,names,[vals[n] for n in names]


def build(c,pair,k):
    cut,names,truths=prefix_data(c);nbase=len(names);pool=IDPool();cnf=CNF()
    V=[[pool.id(('v',g,t)) for t in range(256)] for g in range(k)]
    UA=[[pool.id(('a',g,t)) for t in range(256)] for g in range(k)]
    UB=[[pool.id(('b',g,t)) for t in range(256)] for g in range(k)]
    selA=[];selB=[];opv=[]
    for g in range(k):
        nsrc=nbase+g;A=[pool.id(('sa',g,j)) for j in range(nsrc)];B=[pool.id(('sb',g,j)) for j in range(nsrc)];O=[pool.id(('op',g,o)) for o in OPS]
        selA.append(A);selB.append(B);opv.append(O);add_exactly_one(cnf,pool,A);add_exactly_one(cnf,pool,B);add_exactly_one(cnf,pool,O)
        for i in range(nsrc):
            for j in range(i+1):cnf.append([-A[i],-B[j]])
        for S,U in ((A,UA[g]),(B,UB[g])):
            for j,s in enumerate(S):
                if j<nbase:
                    tr=truths[j]
                    for t,u in enumerate(U):cnf.append([-s,u if ((tr>>t)&1) else -u])
                else:
                    q=j-nbase
                    for t,u in enumerate(U):
                        x=V[q][t];cnf.append([-s,-x,u]);cnf.append([-s,x,-u])
        for oi,op in enumerate(OPS):
            for t in range(256):cnf.extend(op_clauses(O[oi],UA[g][t],UB[g][t],V[g][t],op))
    _vals,outs=sas.eval_circuit(c);outsel={}
    for oi in pair:
        tr=outs[oi];S=[pool.id(('out',oi,g)) for g in range(k)];outsel[oi]=S;add_exactly_one(cnf,pool,S)
        for g,s in enumerate(S):
            for t in range(256):cnf.append([-s,V[g][t] if ((tr>>t)&1) else -V[g][t]])
    return {'cnf':cnf,'pool':pool,'cut':cut,'names':names,'nbase':nbase,'selA':selA,'selB':selB,'opv':opv,'outsel':outsel,'k':k,'pair':pair}


def reconstruct(c,d,model):
    pos={x for x in model if x>0};new_names=[];new_gates=[]
    for g in range(d['k']):
        ia=next(i for i,x in enumerate(d['selA'][g]) if x in pos);ib=next(i for i,x in enumerate(d['selB'][g]) if x in pos)
        op=next(OPS[i] for i,x in enumerate(d['opv'][g]) if x in pos);avail=d['names']+new_names;out=f'__ps{g}'
        new_gates.append({'op':op,'a':avail[ia],'b':avail[ib],'out':out});new_names.append(out)
    chosen={oi:new_names[next(i for i,x in enumerate(S) if x in pos)] for oi,S in d['outsel'].items()}
    remove={w for oi in d['pair'] for w in CONES[oi]};gates=[];inserted=False
    for g in c['gates']:
        if g['out']=='g91' and not inserted:
            gates.extend(new_gates);inserted=True
        if g['out'] in remove:continue
        gates.append(dict(g))
    outputs=list(c['outputs'])
    for oi,w in chosen.items():outputs[oi]=w
    full=ras.prune({'gates':gates,'outputs':outputs});ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('pair SAT reconstruction failed AES',d['pair'],ok))
    return full


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pair',required=True);ap.add_argument('--conf-budget',type=int,default=1000000);ap.add_argument('--out',required=True);args=ap.parse_args()
    pair=tuple(int(x) for x in args.pair.split(','));
    if len(pair)!=2 or pair[0] not in CONES or pair[1] not in CONES or pair[0]>=pair[1]:raise ValueError(pair)
    old=sum(len(CONES[i]) for i in pair);k=old-1;out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101');assert len(c['gates'])==101 and ras.independent_check(c)[0]
    d=build(c,pair,k);t0=time.time()
    with Cadical153(bootstrap_with=d['cnf'].clauses) as solver:
        solver.conf_budget(args.conf_budget);sat=solver.solve_limited();model=solver.get_model() if sat is True else None
    summary={'pair':list(pair),'old_pair_gates':old,'target_pair_gates':k,'vars':d['pool'].top,'clauses':len(d['cnf'].clauses),'conf_budget':args.conf_budget,
             'sat':sat is True,'unsat':sat is False,'timed_out':sat is None,'seconds':round(time.time()-t0,3),'family_scope':'fixed FS101 through g90; replace two independent suffix output cones jointly by old-total-minus-one arbitrary legal AND/XOR/XNOR gates'}
    if model is not None:
        full=reconstruct(c,d,model);summary['candidate_gates']=len(full['gates']);summary['verified_all_256']=True;summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in OPS};(out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
