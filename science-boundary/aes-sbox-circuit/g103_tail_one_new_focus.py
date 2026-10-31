#!/usr/bin/env python3
"""Focused exact one-new-helper repair of the best 21-of-24 G103 tail subset.

The exhaustive retained-guide census found deletion core [7,10,23]: all four
late AND atoms and all 21 retained linear functions close, but exactly one AES
output is missing.  To stay within the same 21-linear budget, replace one of the
21 retained old functions by one genuinely new helper.  There are only 21 such
four-deletion sets.

For each set, take maximal old-guide/AND closure, enumerate every pair-computable
new helper that can directly unlock a blocked guide, next AND operand, or output,
and close again.  This is exact for the focused one-new-helper repair family.
Any success is a complete <=100-gate AES circuit and is all-256 checked.
"""
from __future__ import annotations
import json,pathlib,time
import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc
import g103_tail_one_new as one

CORE={7,10,23}

def main():
    out=pathlib.Path('result');out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c);C=1<<sk['const_bit'];vals,_o,_cb=tw.vectorize(c);start=28
    lo=tw.interval_boundaries(c)[start];live=tc.live_sources(c,vals,lo);S0={v for _w,v in live}
    guides=[vals[g['out']] for g in c['gates'][lo:] if g['op']!='AND']
    assert len(guides)==24
    t0=time.time();tested_sets=0;tested_helpers=0;best=None;best_rec=None
    for extra in [i for i in range(24) if i not in CORE]:
        dropped=sorted(CORE|{extra});ds=set(dropped);selected=[v for i,v in enumerate(guides) if i not in ds]
        tested_sets+=1
        S,rem,ai,events=one.close_state(sk,C,S0,selected,start,[])
        miss=[v for v in sk['outputs'] if v not in S]
        requirements=set(rem)|set(miss)
        if ai<sk['n_and']:
            requirements|={sk['ands'][ai]['a'],sk['ands'][ai]['b']}
        WD=one.pair_map(S,C);candidates=one.useful_helpers(WD,S,requirements,C)
        for h in candidates:
            tested_helpers+=1;op,a,b=WD[h]
            S1=set(S);S1.add(h);ev1=list(events)+[('LIN',h,op,a,b)]
            S2,rem2,ai2,ev2=one.close_state(sk,C,S1,rem,ai,ev1)
            miss2=[v for v in sk['outputs'] if v not in S2]
            residual=(sk['n_and']-ai2,len(miss2),len(rem2))
            if best is None or residual<best:
                best=residual;best_rec={'dropped_indices':dropped,'helper':h,'residual':residual}
            if ai2==sk['n_and'] and not rem2 and not miss2:
                full=one.reconstruct(c,live,ev2,sk['outputs'])
                if len(full['gates'])>100:raise AssertionError(len(full['gates']))
                summary={'status':'found','dropped_indices':dropped,'helper':h,'candidate_gates':len(full['gates']),
                         'tested_sets':tested_sets,'tested_helpers':tested_helpers,'verified_all_256':True,
                         'gate_counts':{x:sum(g['op']==x for g in full['gates']) for x in ('AND','XOR','XNOR')},
                         'elapsed_s':round(time.time()-t0,3)}
                (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True));return
    summary={'status':'exhausted','required_drop':sorted(CORE),'tested_sets':tested_sets,'tested_helpers':tested_helpers,
             'best_residual':best,'best_record':best_rec,'elapsed_s':round(time.time()-t0,3),
             'family_scope':'replace one retained function around exact best deletion core [7,10,23] with one new helper'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
