#!/usr/bin/env python3
"""Strengthened exact SAT for hard FS101 suffix output groups.

This wraps `fs101_suffix_group_sat.build` and optionally requires every new gate
to be live: each gate must feed a later new gate or a selected output.  The
liveness constraint is exact for a k-gate minimum once k-1 gates have been proved
UNSAT, because any k-gate solution containing a dead gate would immediately give
a <=k-1 solution by deleting it.

Intended protocol for the hard 7->6 triples:
  1. solve k=5 without liveness (exact <=5 test; dead padding is allowed);
  2. only if k=5 is UNSAT, solve k=6 with --require-live.
SAT witnesses are reconstructed and all-256 checked exactly as in the base
encoder.  Timeout remains inconclusive.
"""
from __future__ import annotations
import argparse,json,pathlib,time
from pysat.solvers import Cadical153
import released_and_skeleton as ras
import fs101_suffix_group_sat as base


def add_liveness(d):
    k=d['k'];nbase=d['nbase']
    for q in range(k):
        src=nbase+q;uses=[]
        for r in range(q+1,k):
            uses.append(d['selA'][r][src]);uses.append(d['selB'][r][src])
        for S in d['outsel'].values():uses.append(S[q])
        d['cnf'].append(uses)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--group',required=True);ap.add_argument('--k',type=int,required=True);ap.add_argument('--require-live',action='store_true');ap.add_argument('--conf-budget',type=int,default=1000000);ap.add_argument('--out',required=True);args=ap.parse_args()
    group=tuple(int(x) for x in args.group.split(','));out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101');assert len(c['gates'])==101 and ras.independent_check(c)[0]
    d=base.build(c,group,args.k)
    if args.require_live:add_liveness(d)
    t0=time.time()
    with Cadical153(bootstrap_with=d['cnf'].clauses) as solver:
        solver.conf_budget(args.conf_budget);sat=solver.solve_limited();model=solver.get_model() if sat is True else None
    summary={'group':list(group),'k':args.k,'require_live':args.require_live,'vars':d['pool'].top,'clauses':len(d['cnf'].clauses),'conf_budget':args.conf_budget,'sat':sat is True,'unsat':sat is False,'timed_out':sat is None,'seconds':round(time.time()-t0,3),'family_scope':'fixed FS101 through g90; arbitrary group-local AND/XOR/XNOR DAG; optional exact minimal-circuit liveness symmetry break'}
    if model is not None:
        full=base.reconstruct(c,d,model);summary['candidate_gates']=len(full['gates']);summary['verified_all_256']=True;(out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':main()
