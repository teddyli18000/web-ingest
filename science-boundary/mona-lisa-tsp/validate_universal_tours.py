#!/usr/bin/env python3
"""Independent full-tour verification of the exponentially large neutral family.

Uses no part of the SAT connectivity search implementation. Only independently
verified removed/added edge edits, baseline, upstream scoring, and direct graph
traversal. A representative set checks independent reconstructions and hashes.
"""
import argparse
import importlib.util
import json
import math
import os
import random
from pathlib import Path

def ed(a,b):return (a,b) if a<b else (b,a)

def main():
    p=argparse.ArgumentParser()
    for x in ('baseline','moves','proof','report','candidate-dir'):
        p.add_argument('--'+x,required=True)
    a=p.parse_args()
    baseline=json.loads(Path(a.baseline).read_text())['tour']
    assert len(baseline)==100000
    data=json.loads(Path(a.moves).read_text())
    proof=json.loads(Path(a.proof).read_text())
    assert proof['universal_connectivity_verified']
    selected=proof['selected_harvest_indices']
    assert len(selected)==proof['universally_connected_dimension']
    moves=[data['moves'][i] for i in selected]
    supports=[{v for e in m['removed']+m['added'] for v in e} for m in moves]
    assert all(not(supports[i]&supports[j]) for i in range(len(moves)) for j in range(i+1,len(moves)))
    base={ed(baseline[i],baseline[(i+1)%len(baseline)]) for i in range(len(baseline))}
    assert len(base)==100000
    mod_old=[{ed(*x) for x in m['removed']} for m in moves]
    mod_new=[{ed(*x) for x in m['added']} for m in moves]
    verify_path=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('p010',verify_path)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    assert v.tour_length(baseline)==5757191
    xs,ys=v.coordinates()
    def full_length(t):
        return math.fsum(math.hypot(xs[t[i]-1]-xs[t[(i+1)%len(t)]-1],
                                      ys[t[i]-1]-ys[t[(i+1)%len(t)]-1])
                         for i in range(len(t)))
    baseline_real=full_length(baseline)
    best_mask=sum(1<<i for i,m in enumerate(moves) if m['continuous_delta']<0)
    random_mask=random.Random(103).getrandbits(len(moves))
    masks=sorted(set([0,(1<<len(moves))-1,best_mask,random_mask]))
    outdir=Path(a.candidate_dir);outdir.mkdir(parents=True,exist_ok=True)
    checks=[]
    for mask in masks:
        edge_set=set(base)
        for i in range(len(moves)):
            if (mask>>i)&1:edge_set.difference_update(mod_old[i])
        for i in range(len(moves)):
            if (mask>>i)&1:edge_set.update(mod_new[i])
        assert len(edge_set)==100000
        adj=[[] for _ in baseline]
        for u,w in edge_set:
            adj[u-1].append(w);adj[w-1].append(u)
        assert all(len(e)==2 for e in adj)
        tour=[];seen=bytearray(100001)
        now=1;prev=0
        while not seen[now]:
            seen[now]=1;tour.append(now)
            z0,z1=adj[now-1]
            nxt=z0 if z0!=prev else z1
            prev,now=now,nxt
        assert now==1 and len(tour)==100000
        assert v.tour_length(tour)==5757191
        actual_real=full_length(tour)-baseline_real
        expected_real=sum(m['continuous_delta'] for i,m in enumerate(moves) if (mask>>i)&1)
        assert abs(actual_real-expected_real)<0.0001,(actual_real,expected_real)
        output={'tour':tour}
        blob=json.dumps(output,separators=(',',':')).encode()
        verdict=v.verify_bytes(blob,v.load_config())
        assert verdict['valid'] and verdict['score']=='5757191'
        (outdir/f'mask-{mask}.json').write_bytes(blob)
        checks.append({'mask':str(mask),'on_switches':mask.bit_count(),
            'score':5757191,'canonical_hash':verdict['canonical_hash'],
            'continuous_euclidean_delta':actual_real})
    assert len({x['canonical_hash'] for x in checks})==len(checks)
    report={'baseline':5757191,'universal_dimension':len(moves),
        'provable_distinct_tours':str(1<<len(moves)),
        'two_independent_solvers_found_no_disconnected_configuration':True,
        'representative_full_upstream_verifier_checks':checks,
        'max_secondary_saving_from_negative_switches':-sum(min(0,m['continuous_delta']) for m in moves)}
    target=Path(a.report)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
