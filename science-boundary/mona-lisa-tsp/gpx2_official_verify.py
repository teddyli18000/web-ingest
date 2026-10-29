#!/usr/bin/env python3
"""Independently score and audit GPX2 results (never trust GPX2 float score).

Read a plain 1-based one-city-per-line output from a foreign GPL GPX2 binary,
check 100k permutation and score with the Few Shots p010 verifier, compare
against original parent tours and inspect actual offspring-only edges.
A winning certificate is emitted only after authoritative verification.
"""
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
N=100000
def ek(a,b):return (min(a,b),max(a,b))
def edges(t):return {ek(t[i],t[(i+1)%N]) for i in range(N)}
def parse_tour(path):
    a=[]
    with open(path) as f:
        for line in f:
            for z in line.split():
                a.append(int(z))
    assert len(a)==N and min(a)==1 and max(a)==N and len(set(a))==N
    return a
def main():
    p=argparse.ArgumentParser()
    for arg in ('child','parentA','parentB','out'):p.add_argument('--'+arg,required=True)
    p.add_argument('--tag',default='unspecified')
    args=p.parse_args()
    spec=importlib.util.spec_from_file_location('official',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    child=parse_tour(args.child)
    def read_parent(path):
        content=Path(path).read_text()
        if content.lstrip().startswith('{'):
            t=json.loads(content)['tour']
        else:
            sect=content.index('TOUR_SECTION')+len('TOUR_SECTION')
            t=[]
            for z in content[sect:].split():
                if z=='-1' or z=='EOF':break
                t.append(int(z))
        assert len(t)==N and len(set(t))==N
        return t
    a=read_parent(args.parentA);b=read_parent(args.parentB)
    scores=[v.tour_length(t) for t in (a,b,child)]
    assert scores[0]>=5757191 and scores[1]>=5757191
    assert scores[2]<=min(scores[:2]),('GPX2 recombination monotonicity violated',scores)
    blob=json.dumps({'tour':child},separators=(',',':')).encode()
    verdict=v.verify_bytes(blob,v.load_config())
    assert verdict['valid'] and int(verdict['score'])==scores[2], verdict
    ea,eb,ec=edges(a),edges(b),edges(child)
    novel=ec-(ea|eb)
    result={'tag':args.tag,'parent_scores':scores[:2],'child_score':scores[2],
        'child_better_than_best_parent':scores[2]<min(scores[:2]),
        'child_better_than_nagata':scores[2]<5757191,
        'child_edges_outside_parent_union':len(novel),
        'differing_edges_parentA_child':len(ec-ea),
        'differing_edges_parentB_child':len(ec-eb),
        'official_verified':True,'official_hash':verdict['canonical_hash'],
        'sha256_child_order':hashlib.sha256(blob).hexdigest()}
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'offspring.json').write_bytes(blob)
    if scores[2]<5757191:(out/'certificate.json').write_bytes(blob)
    print(json.dumps({'stage':'verified_gpx2',**result}),flush=True)

if __name__=='__main__':main()
