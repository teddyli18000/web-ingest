#!/usr/bin/env python3
"""Diagnose the exact one-output residual around the best G103 late-tail core.

The retained 21-of-24 tail census and the broad/focused one-new-helper searches
repeatedly reach the same state: all final four AND atoms and all retained guide
functions close, but exactly one AES output is absent.  This script makes that
state explicit for the best deletion core [7,10,23] and the best focused
one-new record [0,7,10,23] + helper 17188257792.

It reports guide indices/wires/functions, the missing output, its minimum support
size over the final available affine set, and exact low-support witnesses.  This
is intended to define a targeted two-new-helper search rather than blindly add
another helper dimension.
"""
from __future__ import annotations
import itertools,json
import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc
import g103_tail_one_new as one

START=28
CORE=[7,10,23]
FOCUS_DROP=[0,7,10,23]
FOCUS_HELPER=17188257792

def support_witness(S,target,C,maxk=5):
    xs=sorted(S)
    # XOR/XNOR polarity is represented by constant coordinate already, so this
    # is exact affine XOR support in the released-AND vector space.
    for k in range(1,maxk+1):
        for comb in itertools.combinations(xs,k):
            v=0
            for x in comb:v^=x
            if v==target:return list(comb)
    return None

def state(c,guides,dropped,helper=None):
    sk=ras.extract_skeleton(c);C=1<<sk['const_bit'];vals,_o,_cb=tw.vectorize(c)
    lo=tw.interval_boundaries(c)[START];live=tc.live_sources(c,vals,lo);S0={v for _w,v in live}
    selected=[v for i,v in enumerate(guides) if i not in set(dropped)]
    S,rem,ai,events=one.close_state(sk,C,S0,selected,START,[])
    helper_event=None
    if helper is not None:
        WD=one.pair_map(S,C)
        if helper not in WD: raise AssertionError(('focused helper not computable',helper))
        op,a,b=WD[helper];helper_event=(op,a,b)
        S.add(helper);events.append(('LIN',helper,op,a,b))
        S,rem,ai,events=one.close_state(sk,C,S,rem,ai,events)
    missing=[(oi,v) for oi,v in enumerate(sk['outputs']) if v not in S]
    return {'S':S,'rem':rem,'ai':ai,'events':events,'missing':missing,'helper_event':helper_event,'live':live}

def main():
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c);C=1<<sk['const_bit'];vals,_o,_cb=tw.vectorize(c)
    lo=tw.interval_boundaries(c)[START]
    tail=[g for g in c['gates'][lo:] if g['op']!='AND']
    guides=[vals[g['out']] for g in tail]
    assert len(guides)==24
    guide_rows=[{'index':i,'wire':g['out'],'op':g['op'],'a':g['a'],'b':g['b'],'vector':guides[i],
                 'is_output_function':[oi for oi,v in enumerate(sk['outputs']) if v==guides[i]]}
                for i,g in enumerate(tail)]
    cases=[]
    for label,dropped,helper in [('core21',CORE,None),('focus_one_new',FOCUS_DROP,FOCUS_HELPER)]:
        st=state(c,guides,dropped,helper)
        misses=[]
        for oi,v in st['missing']:
            wit=support_witness(st['S'],v,C,5)
            misses.append({'output_index':oi,'vector':v,'support_witness':wit,
                           'support_size':None if wit is None else len(wit),
                           'one_gate':wit is not None and len(wit)<=2})
        cases.append({'label':label,'dropped':dropped,'helper':helper,
                      'released_ands':st['ai']-START,'remaining_guides':len(st['rem']),
                      'available_count':len(st['S']),'missing_outputs':misses,
                      'helper_event':st['helper_event']})
    out={'start':START,'guide_rows':guide_rows,'cases':cases,
         'output_vectors':[{'output_index':i,'vector':v} for i,v in enumerate(sk['outputs'])]}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
