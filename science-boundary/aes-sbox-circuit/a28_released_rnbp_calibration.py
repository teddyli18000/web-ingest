#!/usr/bin/env python3
"""Cheap architecture-reset calibration on public NIST A28/G124.

A28/G124 (28 AND + 96 linear) is structurally far from G103 and the current
101-gate record.  Before spending serious compute on this niche, test whether the
existing released-AND true-support RNBP can at least reconstruct a complete A28
AES circuit within its known 96-linear budget from the nonlinear skeleton alone.

This wrapper deliberately does not modify the shared released_and_skeleton source
registry.  It independently downloads/parses the public NIST seed, prunes it,
checks all 256 AES inputs, then calls the existing fast released-AND synthesizer.
If the heuristic cannot reproduce anything near 96 linear gates, that is evidence
only about this heuristic and is a reason not to scale it on A28.  A successful
candidate is again independently checked on all 256 inputs.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import seed_family_census as census
import released_and_skeleton as ras
import released_rnbp_support_fast as rf

URL='https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'


def load_a28():
    text=census.get(URL)
    c,_=census.normalize_nist(census.parse_nist(text))
    c=ras.prune(c)
    ok=ras.independent_check(c)
    if not ok[0]: raise AssertionError(('public A28 failed AES check',ok))
    na=sum(g['op']=='AND' for g in c['gates'])
    if (len(c['gates']),na)!=(124,28): raise AssertionError((len(c['gates']),na))
    return c


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--max-linear',type=int,default=96)
    ap.add_argument('--max-support',type=int,default=8)
    ap.add_argument('--elite',type=int,default=8)
    ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    base=load_a28(); t0=time.time()
    cand,s=rf.synthesize(base,a.seed,a.max_linear,a.max_support,a.elite)
    s.update({'family':'nist-a28-g124','source_gates':124,'source_and':28,'source_linear':96,
              'max_linear':a.max_linear,'max_support':a.max_support,'elite':a.elite,
              'elapsed_s':round(time.time()-t0,3)})
    if cand is not None:
        ok=ras.independent_check(cand)
        if not ok[0]: raise AssertionError(('A28 candidate failed AES',ok))
        (out/'candidate.json').write_text(json.dumps(cand,indent=2)+'\n')
        s['verified_all_256']=True
    (out/'summary.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in s.items() if k!='trace_tail'},sort_keys=True),flush=True)

if __name__=='__main__': main()
