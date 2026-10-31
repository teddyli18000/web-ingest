#!/usr/bin/env python3
"""Exact 21-of-24 retained-guide census across the final four G103 AND atoms.

Starting before AND atom 28, the original normalized NIST G103 tail contains the
final four ordered AND atoms and 24 linear XOR/XNOR gates, with schedule
[0,0,2,0,22].  A 100-gate circuit with the same fixed prefix/nonlinear skeleton
may use only 21 local linear gates.

This script enumerates every 21-of-24 subset of the *original local linear
functions*, but does NOT preserve their original order, parent wires, or the old
last-AND boundary.  From the true fixed-prefix live-in affine values it repeatedly:

  1. releases the next fixed G103 AND atom whenever its exact two affine operands
     are available;
  2. materializes any retained linear guide that is XOR or XNOR of two currently
     available values;
  3. continues to monotone closure.

For a fixed retained subset this closure is exact and independent of scheduling
order.  Hence exhausting all C(24,3)=2024 deletion sets exactly answers this
retained-function family.  A success is reconstructed as a complete circuit and
checked on all 256 AES inputs.  A miss is only family-local: it does not exclude
100-gate tails containing genuinely new linear functions.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc


def pair_witness(S, target, C):
    xs=sorted(S); have=set(S)
    for ia,a in enumerate(xs):
        for b in xs[ia+1:]:
            if a^b==target:
                return ('XOR',a,b)
            if (a^b^C)==target:
                return ('XNOR',a,b)
    return None


def close_subset(c, start, selected, reconstruct=False):
    sk=ras.extract_skeleton(c); C=1<<sk['const_bit']
    vals,_outs,_cb=tw.vectorize(c); lo=tw.interval_boundaries(c)[start]
    prefix=[dict(g) for g in c['gates'][:lo]]
    live=tc.live_sources(c,vals,lo)
    vec_name={v:w for w,v in live}; S=set(vec_name)
    rem=set(selected); ai=start; events=[]

    while True:
        progress=False
        # Release every currently legal ordered AND atom.
        while ai<sk['n_and']:
            ab=sk['ands'][ai]
            if ab['a'] not in S or ab['b'] not in S:
                break
            atom=1<<(8+ai)
            if atom not in S:
                S.add(atom); events.append(('AND',ai,ab['a'],ab['b'],atom)); progress=True
            ai+=1

        ready=[]
        for v in sorted(rem):
            hit=pair_witness(S,v,C)
            if hit is not None:
                ready.append((v,hit))
        for v,hit in ready:
            if v not in rem: continue
            S.add(v); rem.remove(v); events.append(('LIN',v,*hit)); progress=True
        if not progress:
            break

    missing_outputs=[v for v in sk['outputs'] if v not in S]
    success=(ai==sk['n_and'] and not rem and not missing_outputs)
    meta={'success':success,'released_ands':ai-start,'remaining_guides':len(rem),
          'missing_outputs':len(missing_outputs),'events':len(events),
          'source_count':len(live)}
    if not success or not reconstruct:
        return None,meta

    gates=[dict(g) for g in prefix]
    names=dict(vec_name)
    for ev in events:
        if ev[0]=='AND':
            _,gi,a,b,atom=ev
            out=f'__tgs_{len(gates)}'
            gates.append({'op':'AND','a':names[a],'b':names[b],'out':out})
            names[atom]=out
        else:
            _,v,op,a,b=ev
            out=f'__tgs_{len(gates)}'
            gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
            names[v]=out
    full=ras.prune({'gates':gates,'outputs':[names[v] for v in sk['outputs']]})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('tail guide-subset witness failed AES',ok))
    return full,meta


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int,default=28)
    ap.add_argument('--keep',type=int,default=21); ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    vals,_outs,_cb=tw.vectorize(c); lo=tw.interval_boundaries(c)[args.start]
    guides=[vals[g['out']] for g in c['gates'][lo:] if g['op']!='AND']
    if len(guides)!=24: raise AssertionError(('expected 24 tail linears',len(guides)))
    if len(set(guides))!=len(guides): raise AssertionError('tail guide functions not unique')
    drop_n=len(guides)-args.keep
    if drop_n<0: raise ValueError(args.keep)

    t0=time.time(); tested=0; best=None; best_drop=None; best_meta=None
    for dropped in itertools.combinations(range(len(guides)),drop_n):
        tested+=1; ds=set(dropped); selected=[v for i,v in enumerate(guides) if i not in ds]
        _full,meta=close_subset(c,args.start,selected,False)
        residual=((ras.extract_skeleton(c)['n_and']-args.start)-meta['released_ands'],
                  meta['missing_outputs'],meta['remaining_guides'])
        if best is None or residual<best:
            best=residual; best_drop=list(dropped); best_meta=dict(meta)
        if not meta['success']: continue
        full,meta2=close_subset(c,args.start,selected,True)
        (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
        summary={'status':'found','start':args.start,'keep':args.keep,'drop_n':drop_n,
                 'tested_subsets':tested,'dropped_indices':list(dropped),
                 'candidate_gates':len(full['gates']),'verified_all_256':True,
                 'gate_counts':{op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')},
                 **meta2,'elapsed_s':round(time.time()-t0,3)}
        (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        print(json.dumps(summary,sort_keys=True)); return

    summary={'status':'exhausted','start':args.start,'keep':args.keep,'drop_n':drop_n,
             'tested_subsets':tested,'best_residual':best,'best_drop_indices':best_drop,
             'best_meta':best_meta,'elapsed_s':round(time.time()-t0,3),
             'family_scope':'retain 21 of original 24 late linear functions; arbitrary rewiring/rescheduling across final four fixed AND releases'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
