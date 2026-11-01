#!/usr/bin/env python3
"""Exact direct-100 one-new-helper search on late tails of the FS101 record.

FS101 has 33 AND + 68 linear gates.  Fix a cut immediately before AND atom
`start`, keep the exact ordered nonlinear atom functions, and consider every
linear function appearing after that cut as an old guide.  Drop any two old
guides and add exactly one genuinely new XOR/XNOR helper.  All retained guides
may be regenerated in arbitrary order from currently available signals and may
move across old AND boundaries subject only to exact temporal legality.

The local linear cost is therefore reduced by one.  Any completed witness is a
<=100-gate full AES circuit after pruning.  The unique new helper can be delayed
until maximal closure of retained old guides without loss of generality; at that
point it must directly unlock a blocked retained guide, the next AND operand, or
a final output.  Enumerating those pair-computable helpers therefore exhausts
this represented one-new-helper family.
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
import g103_tail_one_new as one


def reconstruct(c,live,events,outputs,start):
    lo=tw.interval_boundaries(c)[start]
    gates=[dict(g) for g in c['gates'][:lo]]
    names={v:w for w,v in live}
    for ev in events:
        if ev[0]=='AND':
            _,gi,a,b,atom=ev
            out=f'__fston_{len(gates)}'
            gates.append({'op':'AND','a':names[a],'b':names[b],'out':out})
            names[atom]=out
        else:
            _,v,op,a,b=ev
            out=f'__fston_{len(gates)}'
            gates.append({'op':op,'a':names[a],'b':names[b],'out':out})
            names[v]=out
    full=ras.prune({'gates':gates,'outputs':[names[v] for v in outputs]})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('FS101 tail witness failed AES',ok))
    return full


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--start',type=int,required=True)
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)

    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c); assert sk['n_and']==33
    if not (0 <= args.start < sk['n_and']): raise ValueError(args.start)
    C=1<<sk['const_bit']; vals,_o,_cb=tw.vectorize(c)
    lo=tw.interval_boundaries(c)[args.start]
    live=tc.live_sources(c,vals,lo); S0={v for _w,v in live}
    guides=[vals[g['out']] for g in c['gates'][lo:] if g['op']!='AND']
    assert len(guides)==len(set(guides)),('duplicate guide vectors',args.start,len(guides),len(set(guides)))

    tested_sets=0; tested_helpers=0; serial=0; best=None; best_rec=None; t0=time.time()
    for dropped in itertools.combinations(range(len(guides)),2):
        if serial % args.shards != args.shard:
            serial+=1; continue
        serial+=1; tested_sets+=1
        ds=set(dropped); selected=[v for i,v in enumerate(guides) if i not in ds]
        S,rem,ai,events=one.close_state(sk,C,S0,selected,args.start,[])
        missing_out=[v for v in sk['outputs'] if v not in S]
        if ai==sk['n_and'] and not rem and not missing_out:
            full=reconstruct(c,live,events,sk['outputs'],args.start)
            summary={'status':'found_without_new','start':args.start,'dropped_indices':list(dropped),
                     'candidate_gates':len(full['gates']),'tested_sets':tested_sets,'tested_helpers':tested_helpers,
                     'verified_all_256':True,'elapsed_s':round(time.time()-t0,3)}
            (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
            (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
            print(json.dumps(summary,sort_keys=True)); return

        req=set(rem)|set(missing_out)
        if ai<sk['n_and']:
            req.add(sk['ands'][ai]['a']); req.add(sk['ands'][ai]['b'])
        WD=one.pair_map(S,C)
        for h in one.useful_helpers(WD,S,req,C):
            tested_helpers+=1
            op,a,b=WD[h]
            S1=set(S); S1.add(h); ev1=list(events)+[('LIN',h,op,a,b)]
            S2,rem2,ai2,ev2=one.close_state(sk,C,S1,rem,ai,ev1)
            miss2=[v for v in sk['outputs'] if v not in S2]
            residual=(sk['n_and']-ai2,len(miss2),len(rem2))
            if best is None or residual<best:
                best=residual; best_rec={'dropped_indices':list(dropped),'helper':h,'residual':residual}
            if ai2==sk['n_and'] and not rem2 and not miss2:
                full=reconstruct(c,live,ev2,sk['outputs'],args.start)
                if len(full['gates'])>100: raise AssertionError(('expected <=100',len(full['gates'])))
                summary={'status':'found','start':args.start,'dropped_indices':list(dropped),'helper':h,
                         'candidate_gates':len(full['gates']),'tested_sets':tested_sets,'tested_helpers':tested_helpers,
                         'verified_all_256':True,'gate_counts':{x:sum(g['op']==x for g in full['gates']) for x in ('AND','XOR','XNOR')},
                         'elapsed_s':round(time.time()-t0,3)}
                (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
                (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
                print(json.dumps(summary,sort_keys=True)); return

    summary={'status':'exhausted','start':args.start,'shard':args.shard,'shards':args.shards,
             'tail_guides':len(guides),'tail_ands':sk['n_and']-args.start,'live_sources':len(live),
             'tested_sets':tested_sets,'tested_helpers':tested_helpers,'best_residual':best,'best_record':best_rec,
             'elapsed_s':round(time.time()-t0,3),
             'family_scope':'drop any two old FS101 tail linear functions and add one new helper; retained guides arbitrarily rewired/rescheduled across fixed released ANDs'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
