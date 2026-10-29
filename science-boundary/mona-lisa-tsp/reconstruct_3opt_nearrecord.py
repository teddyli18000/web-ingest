#!/usr/bin/env python3
"""Reconstruct an exact valid full 100K GPX parent from two-cycle+3opt patch.

Without this, 2026 dynamic repair found 5,757,195 but only saved its hash,
not the full non-record tour. This replay independently restores it from
the original Nagata certificate plus the saved factor and exactly three
old/new exchange edges, then scores by official Few Shots p010 oracle.
"""
import argparse,importlib.util,json,os
from pathlib import Path
N=100000
def E(a,b):return (min(a,b),max(a,b))
def main():
 p=argparse.ArgumentParser()
 for key in ('baseline','factor','patch','out'):p.add_argument('--'+key,required=True)
 a=p.parse_args()
 spec=importlib.util.spec_from_file_location('official',Path(os.environ['FEWSHOTS_ROOT'])/
   'problems/p010-mona-lisa-tsp/verify/verify.py')
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 raw=json.loads(Path(a.baseline).read_text())['tour']
 assert len(raw)==N and v.tour_length(raw)==5757191
 base={E(raw[i]-1,raw[(i+1)%N]-1) for i in range(N)}
 factor=json.loads(Path(a.factor).read_text())
 old={tuple(e) for e in factor['removed_baseline_edges']}
 new={tuple(e) for e in factor['added_nonbaseline_edges']}
 assert old<=base and not new&base
 edges=(base-old)|new
 assert len(edges)==N
 patch=json.loads(Path(a.patch).read_text())
 assert patch['factor_score']==factor['factor_score'] and patch['best_3opt_delta']==6
 r={tuple(e) for e in patch['removed_edges']}
 t={tuple(e) for e in patch['added_edges']}
 assert len(r)==len(t)==3 and r<=edges and not(t&edges)
 es=(edges-r)|t
 assert len(es)==N
 adj=[[] for _ in range(N)]
 for u,w in es:adj[u].append(w);adj[w].append(u)
 assert all(len(x)==2 for x in adj)
 route=[];seen=bytearray(N);previous=-1;cur=0
 while not seen[cur]:
    seen[cur]=1;route.append(cur+1)
    x,y=adj[cur];nxt=x if x!=previous else y
    previous,cur=cur,nxt
 assert cur==0 and len(route)==N
 blob=json.dumps({'tour':route},separators=(',',':')).encode()
 verdict=v.verify_bytes(blob,v.load_config())
 assert verdict['valid'] and int(verdict['score'])==5757195
 assert verdict['canonical_hash']==patch['official_verified_hash']
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_bytes(blob)
 (out.parent/'seed-report.json').write_text(json.dumps({
     'score':int(verdict['score']),'official_hash':verdict['canonical_hash'],
     'distance_to_Nagata_by_edges':len(es-base),
     'recovered_exact_3opt_provenance':True},indent=2)+'\n')
 print(json.dumps({'stage':'reconstructed_seed','score':int(verdict['score']),
     'official_hash':verdict['canonical_hash'],'different_edges':len(es-base)}),flush=True)
if __name__=='__main__':main()
