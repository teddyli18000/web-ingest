#!/usr/bin/env python3
"""Construct the exact care-neutral FS101 variant found after PR #31.

At gate index 53 (zero-based in the normalized merged certificate), the second
AND operand g52 may be replaced by g50 because the two functions agree on all
states where the other AND operand is 1. This preserves 101 gates but changes
the dependency graph and is therefore a distinct structural seed for later
full-circuit search.
"""
import argparse, hashlib, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census


def canonical_json_hash(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); args=ap.parse_args()
    c=ras.load_circuit('fs-101')
    assert len(c['gates'])==101
    g=c['gates'][53]
    assert g['op']=='AND' and g['b']=='g52', g
    vals=census.input_tables(False)
    for q in c['gates']:
        vals[q['out']]=census.op_eval(q['op'],vals[q['a']],vals[q['b']])
    old=g['b']; new='g50'; care=vals[g['a']]
    assert ((vals[old]^vals[new]) & care)==0
    c['gates'][53]['b']=new
    c=ras.prune(c)
    assert len(c['gates'])==101
    assert ras.independent_check(c)[0]
    p=pathlib.Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps({'gates':len(c['gates']),'and_index':53,'old':old,'new':new,'care_bits':care.bit_count(),
                      'verified_all_256':True,'structural_sha256':canonical_json_hash(c)}))

if __name__=='__main__': main()
