#!/usr/bin/env python3
"""Exact focused two-new-helper search around the shared G103 suffix weak core.

Across all three cheap 49-linear cut bases, the exhaustive 20-gate one-new-helper
search has the same best deleted original-guide core: indices {0,5,8}.  This
script asks the next falsifiable question: if that common weak core is fixed as
deleted, can two genuinely new linear functions replace it (and additional old
guides as required by the gate budget)?

For target K, retain K-2 of the 22 transformed original suffix guide functions
and use exactly two new helpers h1,h2.  Hence K=19 deletes five old guides and is
a direct 49-prefix + 19-suffix = 100-gate route; K=20 deletes four and becomes a
100-gate route if a 48-linear nonlinear prefix is found independently.

Exactness within this focused family:
* enumerate every deletion set containing the required core;
* maximally close retained old guides before h1;
* enumerate every h1 computable by one XOR from that closure;
* maximally close retained guides again;
* h2 is either a required dropped output, or must directly unlock at least one
  remaining retained guide (there is no third new gate, so otherwise h2 is dead);
* enumerate every such computable h2 and close again.

Thus a miss excludes the represented two-new-function family for the required
deletion core.  It is not a global lower bound and says nothing about different
old-guide deletion cores or three-plus-new-function architectures.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez
import g103_explicit_cut_basis as xp
import g103_suffix_guide_subset as gs


def close_from(S, remaining, order, parents):
    S=set(S); rem=set(remaining); order=list(order); parents=dict(parents)
    while rem:
        ready=[]
        for v in sorted(rem):
            ab=gs.pair_witness(S,v)
            if ab is not None: ready.append((v,ab))
        if not ready: break
        for v,ab in ready:
            if v not in rem: continue
            parents[v]=ab; order.append(v); S.add(v); rem.remove(v)
    return S,rem,order,parents


def pair_map(S):
    xs=sorted(S); out={}
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            v=a^b
            if v and v not in S: out.setdefault(v,(a,b))
    return out


def parse_ints(s):
    return tuple(int(x) for x in s.split(',') if x!='')


def search(c, rows, gates, required_drop):
    m,C,boundary,extras,guide,target_q,affine_targets=gs.ordered_guide_vectors(c,rows)
    assert len(guide)==22 and len(set(guide))==22
    by_value={v:i for i,v in enumerate(guide)}
    target_indices={by_value[q] for q in target_q}
    required=set(required_drop)
    if not required <= set(range(22)): raise ValueError(required_drop)

    retain_n=gates-2
    drop_n=22-retain_n
    if drop_n < len(required):
        return None,{'status':'invalid_bound','gates':gates,'drop_n':drop_n,
                     'required_drop':sorted(required)}
    choose_from=[i for i in range(22) if i not in required]
    add_drop=drop_n-len(required)

    tested_drop=0; tested_h1=0; tested_h2=0
    best=None; best_record=None
    S0={1<<i for i in range(m)}

    for extra_drop in itertools.combinations(choose_from,add_drop):
        dropped=tuple(sorted(required|set(extra_drop)))
        dropped_targets=[guide[i] for i in dropped if i in target_indices]
        if len(dropped_targets)>2: continue
        tested_drop+=1
        dset=set(dropped)
        selected=[v for i,v in enumerate(guide) if i not in dset]
        S,rem,order,parents=close_from(S0,selected,[],{})
        P1=pair_map(S)
        for h1,ab1 in P1.items():
            if h1 in selected: continue
            # A dropped output can only be materialized by h1 or h2.
            if len(dropped_targets)==2 and h1 not in dropped_targets:
                # Then h2 could match only one of the two, so this h1 is useless.
                continue
            tested_h1+=1
            S1=set(S); S1.add(h1)
            order1=list(order)+[h1]; parents1=dict(parents); parents1[h1]=ab1
            S1,rem1,order1,parents1=close_from(S1,rem,order1,parents1)

            missing_dropped=[q for q in dropped_targets if q not in S1]
            if len(missing_dropped)>1: continue
            P2=pair_map(S1)
            if missing_dropped:
                h2c=[missing_dropped[0]] if missing_dropped[0] in P2 else []
            elif rem1:
                # With h2 the final new gate, it must directly make at least one
                # remaining retained guide reachable.  Generate exactly those
                # useful values and intersect with one-gate-computable values.
                cand=set()
                for v in rem1:
                    for a in S1:
                        h=v^a
                        if h in P2: cand.add(h)
                h2c=sorted(cand)
            else:
                # All retained guides and outputs are already ready after h1;
                # accept the shorter realization rather than add a dead gate.
                if all(q in S1 for q in target_q):
                    net=gs.build_net(m,C,order1,parents1,target_q,affine_targets)
                    return net,{'status':'found','gates':len(net['gates']),
                               'target_bound':gates,'dropped_indices':list(dropped),
                               'h1':h1,'h2':None,'tested_drop_sets':tested_drop,
                               'tested_h1':tested_h1,'tested_h2':tested_h2,
                               'required_drop':sorted(required)}
                h2c=[]

            for h2 in h2c:
                if h2 in S1 or h2 in selected: continue
                tested_h2+=1
                S2=set(S1); S2.add(h2)
                order2=list(order1)+[h2]; parents2=dict(parents1); parents2[h2]=P2[h2]
                S2,rem2,order2,parents2=close_from(S2,rem1,order2,parents2)
                missing=[q for q in target_q if q not in S2]
                score=(len(missing),len(rem2))
                if best is None or score<best:
                    best=score
                    best_record={'dropped_indices':list(dropped),'h1':h1,'h2':h2,
                                 'missing_outputs':len(missing),
                                 'remaining_guides':len(rem2)}
                if rem2 or missing: continue
                if len(order2)>gates: raise AssertionError((len(order2),gates))
                net=gs.build_net(m,C,order2,parents2,target_q,affine_targets)
                return net,{'status':'found','gates':len(net['gates']),
                           'target_bound':gates,'dropped_indices':list(dropped),
                           'h1':h1,'h2':h2,'tested_drop_sets':tested_drop,
                           'tested_h1':tested_h1,'tested_h2':tested_h2,
                           'required_drop':sorted(required)}

    return None,{'status':'exhausted','gates':gates,'required_drop':sorted(required),
                 'tested_drop_sets':tested_drop,'tested_h1':tested_h1,
                 'tested_h2':tested_h2,'best_residual':best,
                 'best_record':best_record,
                 'family_scope':'two new helpers; every deleted-guide set contains required core'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=ez.parse_rows,default=(1,2,4))
    ap.add_argument('--gates',type=int,choices=[19,20],required=True)
    ap.add_argument('--required-drop',type=parse_ints,default=(0,5,8))
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    t0=time.time(); net,meta=search(c,args.basis_rows,args.gates,args.required_drop)
    print(json.dumps(meta,sort_keys=True),flush=True)
    prec,pmeta=xp.synthesize_at_cut(c,args.basis_rows)
    summary={'basis_rows':list(args.basis_rows),'search':meta,'prefix':pmeta,
             'elapsed_s':round(time.time()-t0,3)}
    if net is not None:
        (out/'suffix.json').write_text(json.dumps(net,indent=2)+'\n')
        if prec is not None:
            full=xp.attach_suffix(c,prec,net)
            if not ras.independent_check(full)[0]:
                raise AssertionError('reattached focused two-new suffix failed AES')
            (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
            summary['full_gates']=len(full['gates'])
            summary['verified_all_256']=True
            summary['gate_counts']={op:sum(g['op']==op for g in full['gates'])
                                    for op in ('AND','XOR','XNOR')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('search','prefix')},sort_keys=True),flush=True)

if __name__=='__main__': main()
