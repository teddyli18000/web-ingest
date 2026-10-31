#!/usr/bin/env python3
"""Exact two-new-helper G103 late-tail search while retaining all 8 output functions.

The best 21-of-24 retained-guide solution saved three gates only by deleting the
entire original output-6 chain [7,10,23], leaving output bit 6 at affine support
size five.  Rather than trying to rebuild that deleted output with too few gates,
this family keeps all eight original output functions as retained terminal gates.

There are 16 non-output linear functions in the final-four-AND tail.  Drop any
five of them, retain the other 19 original linear functions (including all 8
outputs), and introduce exactly two genuinely new XOR/XNOR helpers.  Net local
linear cost is 19+2=21, hence any success is a 100-gate complete AES circuit.
Retained functions may be regenerated from arbitrary currently available signals
and may move across the old AND-release boundaries subject only to exact temporal
legality.

The search is exact for this represented family.  Before the first new helper,
maximally close every retained old function and fixed ordered AND that is already
legal.  In any two-new-helper completion, the first new helper h1 must be relevant
to a currently blocked requirement:

* for a hard requirement (next AND operand or final output), h1 must equal it or
  be one gate away from it using an existing signal;
* for a retained linear function, h1 may additionally be two gates away, because
  the second new helper can be the other operand of that retained gate.  If that
  second helper depended on h1, the XOR/XNOR algebra collapses to an existing
  signal, so no additional case is lost.

After h1 and maximal closure, the final helper must be directly useful (the same
one-new-helper necessity used by `g103_tail_one_new.py`).  Every hit is rebuilt
as a full circuit and checked on all 256 AES inputs.
"""
from __future__ import annotations

import argparse,itertools,json,pathlib,time
import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc
import g103_tail_one_new as one

START=28

def first_helpers_two_new(WD,S,rem,hard,C):
    P=set(WD); S=set(S); cand=set()
    # Cases where h1 is itself directly useful / one gate away.
    cand.update(one.useful_helpers(WD,S,set(rem)|set(hard),C))
    # A retained old function t may legally use both new helpers as its operands.
    # The second helper must then be a one-gate pair value from the old closure;
    # include every h1 whose XOR/XNOR complement against t is such a value.
    for t in rem:
        for r in P:
            h=t^r
            if h in P:cand.add(h)
            hc=t^r^C
            if hc in P:cand.add(hc)
    return sorted(cand)

def requirements(sk,S,rem,ai):
    hard={v for v in sk['outputs'] if v not in S}
    if ai<sk['n_and']:
        hard.add(sk['ands'][ai]['a']);hard.add(sk['ands'][ai]['b'])
    return hard

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--out',required=True);args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c);C=1<<sk['const_bit'];vals,_o,_cb=tw.vectorize(c)
    lo=tw.interval_boundaries(c)[START];live=tc.live_sources(c,vals,lo);S0={v for _w,v in live}
    tail_lin=[g for g in c['gates'][lo:] if g['op']!='AND'];guides=[vals[g['out']] for g in tail_lin]
    assert len(guides)==24 and len(set(guides))==24
    output_idx={i for i,v in enumerate(guides) if v in set(sk['outputs'])}
    assert len(output_idx)==8,output_idx
    internal=[i for i in range(24) if i not in output_idx];assert len(internal)==16

    serial=0;tested_sets=0;tested_h1=0;tested_h2=0;best=None;best_rec=None;t0=time.time()
    for dropped in itertools.combinations(internal,5):
        if serial%args.shards!=args.shard:
            serial+=1;continue
        serial+=1;tested_sets+=1;ds=set(dropped);selected=[v for i,v in enumerate(guides) if i not in ds]
        S,rem,ai,events=one.close_state(sk,C,S0,selected,START,[])
        hard=requirements(sk,S,rem,ai)
        if ai==sk['n_and'] and not rem and not hard:
            full=one.reconstruct(c,live,events,sk['outputs'])
            summary={'status':'found_without_new','dropped_indices':list(dropped),'candidate_gates':len(full['gates']),
                     'tested_sets':tested_sets,'tested_h1':tested_h1,'tested_h2':tested_h2,'verified_all_256':True,'elapsed_s':round(time.time()-t0,3)}
            (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True));return
        WD=one.pair_map(S,C);h1s=first_helpers_two_new(WD,S,rem,hard,C)
        for h1 in h1s:
            tested_h1+=1;op1,a1,b1=WD[h1]
            S1=set(S);S1.add(h1);ev1=list(events)+[('LIN',h1,op1,a1,b1)]
            S1,rem1,ai1,ev1=one.close_state(sk,C,S1,rem,ai,ev1)
            hard1=requirements(sk,S1,rem1,ai1)
            if ai1==sk['n_and'] and not rem1 and not hard1:
                full=one.reconstruct(c,live,ev1,sk['outputs'])
                if len(full['gates'])>100:raise AssertionError(len(full['gates']))
                summary={'status':'found_one_new','dropped_indices':list(dropped),'h1':h1,'candidate_gates':len(full['gates']),
                         'tested_sets':tested_sets,'tested_h1':tested_h1,'tested_h2':tested_h2,'verified_all_256':True,'elapsed_s':round(time.time()-t0,3)}
                (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True));return
            WD2=one.pair_map(S1,C);h2s=one.useful_helpers(WD2,S1,set(rem1)|set(hard1),C)
            for h2 in h2s:
                if h2==h1:continue
                tested_h2+=1;op2,a2,b2=WD2[h2]
                S2=set(S1);S2.add(h2);ev2=list(ev1)+[('LIN',h2,op2,a2,b2)]
                S2,rem2,ai2,ev2=one.close_state(sk,C,S2,rem1,ai1,ev2)
                hard2=requirements(sk,S2,rem2,ai2)
                residual=(sk['n_and']-ai2,len(hard2),len(rem2))
                if best is None or residual<best:
                    best=residual;best_rec={'dropped_indices':list(dropped),'h1':h1,'h2':h2,'residual':residual}
                if ai2==sk['n_and'] and not rem2 and not hard2:
                    full=one.reconstruct(c,live,ev2,sk['outputs'])
                    if len(full['gates'])>100:raise AssertionError(('expected <=100',len(full['gates'])))
                    summary={'status':'found','dropped_indices':list(dropped),'h1':h1,'h2':h2,'candidate_gates':len(full['gates']),
                             'tested_sets':tested_sets,'tested_h1':tested_h1,'tested_h2':tested_h2,'verified_all_256':True,
                             'gate_counts':{x:sum(g['op']==x for g in full['gates']) for x in ('AND','XOR','XNOR')},
                             'elapsed_s':round(time.time()-t0,3)}
                    (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True));return
    summary={'status':'exhausted','shard':args.shard,'shards':args.shards,'output_indices':sorted(output_idx),
             'tested_sets':tested_sets,'tested_h1':tested_h1,'tested_h2':tested_h2,'best_residual':best,'best_record':best_rec,
             'elapsed_s':round(time.time()-t0,3),
             'family_scope':'retain all 8 original output functions; retain 11 of 16 internal late guides; add exactly two new helpers; arbitrary rewiring/rescheduling across final four fixed AND releases'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
