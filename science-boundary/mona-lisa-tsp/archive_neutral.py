#!/usr/bin/env python3
"""Freeze public neutral p010 tours as tiny exact edge-difference certificates."""
import argparse, importlib.util, json, os
from pathlib import Path

def e(a,b):return (a,b) if a<b else (b,a)
def edges(t):return {e(t[i],t[(i+1)%len(t)]) for i in range(len(t))}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True)
    p.add_argument('--artifacts-root',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    spec=importlib.util.spec_from_file_location('p010_verify',
        Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    baseline=json.loads(Path(args.baseline).read_text())['tour']
    assert len(baseline)==100000
    be=edges(baseline)
    assert v.tour_length(baseline)==5757191
    moves=[];hashes=set()
    for rank in [0,50,100,150,200,250]:
        folder=Path(args.artifacts_root)/f'monalisa-global-split-{rank}'
        cert=folder/'certificate.json'
        assert cert.is_file(),str(cert)
        verdict=v.verify_dir(folder,v.load_config())
        assert verdict['valid'] and verdict['score']=='5757191',verdict
        alt=json.loads(cert.read_text())['tour']
        ea=edges(alt)
        removed=sorted(be-ea)
        added=sorted(ea-be)
        assert 0<len(removed)==len(added)<=40
        # Independent reconstruction of the public candidate from its edge edit.
        adj=[[] for _ in baseline]
        for a,b in be:adj[a-1].append(b);adj[b-1].append(a)
        for a,b in removed:
            adj[a-1].remove(b);adj[b-1].remove(a)
        for a,b in added:
            adj[a-1].append(b);adj[b-1].append(a)
        assert all(len(q)==2 for q in adj)
        t=[];prev=0;now=1
        for _ in range(100000):
            t.append(now)
            x,y=adj[now-1]
            nxt=x if x!=prev else y
            prev,now=now,nxt
        assert now==1 and len(set(t))==100000
        assert edges(t)==ea and v.tour_length(t)==5757191
        assert verdict['canonical_hash'] not in hashes
        hashes.add(verdict['canonical_hash'])
        moves.append({'artifact_seed':rank,'source_run':40690889447,
            'canonical_hash':verdict['canonical_hash'],'score':5757191,
            'removed':removed,'added':added})
        print(json.dumps({'seed':rank,'removed_edges':len(removed),
                          'hash':verdict['canonical_hash']}),flush=True)
    out={'baseline_source':'few-shots/few-shots p010 baseline',
         'baseline_score':5757191,'source_run':40690889447,
         'note':'1-based city IDs; reconstruct cycle by deleting removed and adding added edges',
         'neutral_moves':moves}
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'distinct_equal_score_tours':len(moves),
                      'output':str(target)}))
if __name__=='__main__':
    main()
