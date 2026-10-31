#!/usr/bin/env python3
"""Exact one-new-helper 21-linear tail search across the final four G103 ANDs.

Target a 100-gate circuit by using exactly 21 local linear gates from start=28:
20 retained functions from the original 24 late linear gates plus one genuinely
new XOR/XNOR helper.  Retained functions may be regenerated in any order from
any currently available values, and the final four fixed G103 AND atoms are
released as soon as their exact affine operands become available.

For each 20-of-24 retained set, first take the complete monotone closure without
the new helper.  Delaying the unique new helper until this closure is exhausted
is without loss of generality.  At that point a useful helper must either itself
be a blocked required value, or combine with one existing value to materialize a
blocked retained guide / next AND operand / final output.  We therefore generate
exactly those pair-computable helper values, insert each one, and close again.

This exhausts the represented one-new-helper family.  A success is reconstructed
and checked on all 256 AES inputs.  A miss does not exclude tails with two or
more genuinely new linear functions.
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
import g103_tail_guide_subset as gs


def close_state(sk,C,S,rem,ai,events):
    S=set(S); rem=set(rem); events=list(events)
    while True:
        progress=False
        while ai<sk['n_and']:
            ab=sk['ands'][ai]
            if ab['a'] not in S or ab['b'] not in S: break
            atom=1<<(8+ai)
            if atom not in S:
                S.add(atom); events.append(('AND',ai,ab['a'],ab['b'],atom)); progress=True
            ai+=1
        ready=[]
        for v in sorted(rem):
            hit=gs.pair_witness(S,v,C)
            if hit is not None: ready.append((v,hit))
        for v,hit in ready:
            if v not in rem: continue
            S.add(v); rem.remove(v); events.append(('LIN',v,*hit)); progress=True
        if not progress: break
    return S,rem,ai,events


def pair_map(S,C):
    xs=sorted(S); out={}
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            v=a^b
            if v not in S: out.setdefault(v,('XOR',a,b))
            vn=v^C
            if vn not in S: out.setdefault(vn,('XNOR',a,b))
    return out


def useful_helpers(WD,S,requirements,C):
    cand=set(); S=list(S)
    for t in requirements:
        if t in WD: cand.add(t)
        for a in S:
            h=t^a
            if h in WD: cand.add(h)
            hn=t^a^C
            if hn in WD: cand.add(hn)
    return sorted(cand)


def reconstruct(c,live,events,outputs):
    lo_prefix=[]
    # Prefix is everything before the first generated event's fixed tail, passed
    # separately through the caller by deriving the same start=28 boundary.
    vals,_o,_cb=tw.vectorize(c); lo=tw.interval_boundaries(c)[28]
    gates=[dict(g) for g in c['gates'][:lo]]
    names={v:w for w,v in live}
    for ev in events:
        if ev[0]=='AND':
            _,gi,a,b,atom=ev; out=f'__ton_{len(gates)}'
            gates.append({'op':'AND','a':names[a],'b':names[b],'out':out}); names[atom]=out
        else:
            _,v,op,a,b=ev; out=f'__ton_{len(gates)}'
            gates.append({'op':op,'a':names[a],'b':names[b],'out':out}); names[v]=out
    full=ras.prune({'gates':gates,'outputs':[names[v] for v in outputs]})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('one-new tail witness failed AES',ok))
    return full


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--shard',type=int,default=0); ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--out',required=True); args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c); C=1<<sk['const_bit']; vals,_o,_cb=tw.vectorize(c); start=28
    lo=tw.interval_boundaries(c)[start]; live=tc.live_sources(c,vals,lo); S0={v for _w,v in live}
    guides=[vals[g['out']] for g in c['gates'][lo:] if g['op']!='AND']
    assert len(guides)==24 and len(set(guides))==24

    tested_sets=0; tested_helpers=0; best=None; best_rec=None; serial=0; t0=time.time()
    for dropped in itertools.combinations(range(24),4):
        if serial%args.shards!=args.shard:
            serial+=1; continue
        serial+=1; tested_sets+=1; ds=set(dropped); selected=[v for i,v in enumerate(guides) if i not in ds]
        S,rem,ai,events=close_state(sk,C,S0,selected,start,[])
        missing_out=[v for v in sk['outputs'] if v not in S]
        if ai==sk['n_and'] and not rem and not missing_out:
            # Already <=20 old gates; reconstruct even though no new helper is needed.
            full=reconstruct(c,live,events,sk['outputs'])
            summary={'status':'found_without_new','dropped_indices':list(dropped),'candidate_gates':len(full['gates']),
                     'tested_sets':tested_sets,'tested_helpers':tested_helpers,'verified_all_256':True,'elapsed_s':round(time.time()-t0,3)}
            (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n'); (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,sort_keys=True)); return

        requirements=set(rem)|set(missing_out)
        if ai<sk['n_and']:
            requirements.add(sk['ands'][ai]['a']); requirements.add(sk['ands'][ai]['b'])
        WD=pair_map(S,C); candidates=useful_helpers(WD,S,requirements,C)
        for h in candidates:
            tested_helpers+=1; op,a,b=WD[h]
            S1=set(S); S1.add(h); ev1=list(events)+[('LIN',h,op,a,b)]
            S2,rem2,ai2,ev2=close_state(sk,C,S1,rem,ai,ev1)
            miss2=[v for v in sk['outputs'] if v not in S2]
            residual=(sk['n_and']-ai2,len(miss2),len(rem2))
            if best is None or residual<best:
                best=residual; best_rec={'dropped_indices':list(dropped),'helper':h,'residual':residual}
            if ai2==sk['n_and'] and not rem2 and not miss2:
                full=reconstruct(c,live,ev2,sk['outputs'])
                if len(full['gates'])>100: raise AssertionError(('expected <=100',len(full['gates'])))
                summary={'status':'found','dropped_indices':list(dropped),'helper':h,'candidate_gates':len(full['gates']),
                         'tested_sets':tested_sets,'tested_helpers':tested_helpers,'verified_all_256':True,
                         'gate_counts':{x:sum(g['op']==x for g in full['gates']) for x in ('AND','XOR','XNOR')},
                         'elapsed_s':round(time.time()-t0,3)}
                (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n'); (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,sort_keys=True)); return

    summary={'status':'exhausted','shard':args.shard,'shards':args.shards,'tested_sets':tested_sets,
             'tested_helpers':tested_helpers,'best_residual':best,'best_record':best_rec,
             'elapsed_s':round(time.time()-t0,3),
             'family_scope':'20 original late linear functions + one new helper, arbitrary rewiring/rescheduling across final four fixed AND releases'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
