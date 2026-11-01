#!/usr/bin/env python3
"""Diagnose the repeated [0,1,0] residual in direct-100 FS101 tail search."""
from __future__ import annotations

import itertools
import json

import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc
import g103_tail_one_new as one

CASES = [
    (24, [0,13], 4429185024),
    (27, [0,13], 34896609280),
    (30, [0,9], 249644974080),
    (32, [0,1], 249678528512),
]


def support_mod_const(S, target, C, maxk=5):
    xs=sorted(S)
    for k in range(1,maxk+1):
        for comb in itertools.combinations(xs,k):
            v=0
            for x in comb: v ^= x
            if v == target:
                return {'support':list(comb),'size':k,'polarity':'XOR'}
            if v ^ C == target:
                return {'support':list(comb),'size':k,'polarity':'XNOR'}
    return None


def main():
    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c); C=1<<sk['const_bit']; vals,_o,_cb=tw.vectorize(c)
    outs=list(sk['outputs'])
    rows=[]
    for start,dropped,helper in CASES:
        lo=tw.interval_boundaries(c)[start]
        live=tc.live_sources(c,vals,lo); S0={v for _w,v in live}
        tail_lin=[g for g in c['gates'][lo:] if g['op']!='AND']
        guides=[vals[g['out']] for g in tail_lin]
        selected=[v for i,v in enumerate(guides) if i not in set(dropped)]
        S,rem,ai,events=one.close_state(sk,C,S0,selected,start,[])
        WD=one.pair_map(S,C)
        if helper not in WD: raise AssertionError((start,'helper not computable',helper))
        op,a,b=WD[helper]
        S.add(helper); events.append(('LIN',helper,op,a,b))
        S,rem,ai,events=one.close_state(sk,C,S,rem,ai,events)
        missing=[(oi,v) for oi,v in enumerate(outs) if v not in S]
        if len(missing)!=1 or ai!=sk['n_and'] or rem:
            raise AssertionError((start,ai,len(rem),missing))
        oi,t=missing[0]
        guide_rows=[]
        for i,g in enumerate(tail_lin):
            v=guides[i]
            guide_rows.append({'index':i,'wire':g['out'],'op':g['op'],'a':g['a'],'b':g['b'],
                               'vector':v,'is_output':[j for j,x in enumerate(outs) if x==v]})
        rows.append({
            'start':start,'lo_gate':lo,'tail_ands':sk['n_and']-start,'tail_guides':len(guides),
            'dropped':dropped,'dropped_rows':[guide_rows[i] for i in dropped],
            'helper':helper,'helper_event':[op,a,b],
            'helper_matches_old_guides':[i for i,v in enumerate(guides) if v==helper],
            'missing_output_index':oi,'missing_output_vector':t,
            'missing_output_old_guide_indices':[i for i,v in enumerate(guides) if v==t],
            'available_count':len(S),'support_mod_const':support_mod_const(S,t,C,5),
            'guide_rows':guide_rows,
        })
    print(json.dumps({'cases':rows},indent=2,sort_keys=True))

if __name__=='__main__': main()
