#!/usr/bin/env python3
"""Prepare and verify published GPX2 crossover over diverse 100K parent tours.

Input parents were independently scored by the upstream p010 verifier in the
LKH population workflow. This script does *not* trust LKH or GPX2 costs.
It reconstructs and validates every resulting Hamiltonian tour.
"""
import argparse,importlib.util,json,os
from pathlib import Path

def ed(a,b):return (a,b) if a<b else (b,a)
def edges(t):return {ed(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def upstream():
    module=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('verify',module)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['prepare','check'])
    for k in ('baseline','input-root','workdir'):p.add_argument('--'+k,required=True)
    args=p.parse_args()
    base=json.loads(Path(args.baseline).read_text())['tour']
    n=len(base);assert n==100000
    v=upstream()
    assert v.tour_length(base)==5757191
    out=Path(args.workdir);out.mkdir(parents=True,exist_ok=True)
    if args.mode=='prepare':
        sources=[('baseline',base)]
        for file in sorted(Path(args.input_root).glob('monalisa-lkh-parent-*/certificate.json')):
            t=json.loads(file.read_text())['tour']
            assert len(t)==n and len(set(t))==n
            score=v.tour_length(t)
            verdict=v.verify_bytes(json.dumps({'tour':t},separators=(',',':')).encode(),v.load_config())
            assert verdict['valid'] and int(verdict['score'])==score
            sources.append((file.parent.name,t))
        hashes=set();parents=[]
        for name,t in sources:
            h=frozenset(edges(t))
            if h in hashes:continue
            hashes.add(h)
            path=out/f'parent-{len(parents)}.raw'
            path.write_text(''.join(f'{city-1}\n' for city in t))
            parents.append({'name':name,'file':str(path),'score':v.tour_length(t),
                            'changed_edges_from_baseline':len(edges(t)^edges(base))//2})
        assert parents
        data={'upstream_scored_parents':parents,'parent_count':len(parents)}
        (out/'parents.json').write_text(json.dumps(data,indent=2)+'\n')
        print(json.dumps({'stage':'prepared','parents':parents}),flush=True)
        return
    parents=json.loads((out/'parents.json').read_text())['upstream_scored_parents']
    offspring=sorted(out.glob('child-*.raw'))
    report=[];best=5757191;best_blob=None
    for file in offspring:
        t=[int(x) for x in file.read_text().split()]
        assert len(t)==n and len(set(t))==n and min(t)==1 and max(t)==n
        b=json.dumps({'tour':t},separators=(',',':')).encode()
        verdict=v.verify_bytes(b,v.load_config())
        assert verdict['valid'],(file,verdict)
        score=int(verdict['score'])
        entry={'source':file.name,'score':score,'gain':5757191-score,
               'changed_edges_from_baseline':len(edges(t)^edges(base))//2,
               'canonical_hash':verdict['canonical_hash']}
        report.append(entry)
        if score<best:
            best=score;best_blob=b
    if best_blob:
        (out/'certificate.json').write_bytes(best_blob)
    summary={'parents':parents,'offspring_count':len(offspring),
             'offspring':report,'best_score':best,
             'breakthrough':best<5757191}
    (out/'report.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'stage':'independent_gpx2_scoring',
           'parent_count':len(parents),'offspring_count':len(offspring),
           'best_score':best,'breakthrough':best<5757191}),flush=True)
if __name__=='__main__':main()
