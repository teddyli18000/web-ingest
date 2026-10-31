#!/usr/bin/env python3
"""Export/replay the validated public-367 union graph for exact MIS decision solvers."""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from public367_union_cpsat import graph_from_corpus, independent, word5

TARGET=368

def export(corpus:Path,graph:Path,meta:Path):
    rows,seeds,universe,edges=graph_from_corpus(corpus)
    graph.parent.mkdir(parents=True,exist_ok=True)
    with graph.open('w') as f:
        f.write(f'{len(universe)} {len(edges)} {TARGET}\n')
        for u,v in edges:f.write(f'{u} {v}\n')
    d={'method':'validated-public367-union-graph','distinct_seed_sets':len(rows),'union_vertices':len(universe),'conflict_edges':len(edges),'target':TARGET,'universe':universe}
    meta.parent.mkdir(parents=True,exist_ok=True);meta.write_text(json.dumps(d,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in d.items() if k!='universe'},sort_keys=True))

def replay(corpus:Path,result:Path,witness5:Path,cert10:Path,status:Path):
    rows,seeds,universe,edges=graph_from_corpus(corpus);r=json.loads(result.read_text());st=r.get('status')
    out={'method':'exact-public367-union-clique-replay','solver_status':st,'target':TARGET,'candidate_368':False}
    if st=='SAT':
        idx=list(map(int,r.get('witness_indices',[])))
        if len(idx)<TARGET or len(set(idx))!=len(idx) or any(i<0 or i>=len(universe) for i in idx):raise RuntimeError(('bad indices',len(idx)))
        chosen=sorted(universe[i] for i in idx[:TARGET])
        if not independent(chosen):raise RuntimeError('solver witness not independent')
        w=[word5(v) for v in chosen];pts10=sorted(a+b for a in w for b in w)
        if len(pts10)!=TARGET*TARGET:raise RuntimeError('square size drift')
        witness5.parent.mkdir(parents=True,exist_ok=True);witness5.write_text(json.dumps({'points':w},separators=(',',':'))+'\n')
        cert10.parent.mkdir(parents=True,exist_ok=True);cert10.write_text(json.dumps({'points':pts10},separators=(',',':'))+'\n')
        out.update(candidate_368=True,size5=TARGET,score10=TARGET*TARGET)
    elif st=='UNSAT':out['exact_union_alpha']=367
    elif st!='UNKNOWN':raise RuntimeError(('unknown solver status',st))
    status.parent.mkdir(parents=True,exist_ok=True);status.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='mode',required=True)
    e=sp.add_parser('export');e.add_argument('corpus',type=Path);e.add_argument('graph',type=Path);e.add_argument('meta',type=Path)
    r=sp.add_parser('replay');r.add_argument('corpus',type=Path);r.add_argument('result',type=Path);r.add_argument('witness5',type=Path);r.add_argument('cert10',type=Path);r.add_argument('status',type=Path)
    a=ap.parse_args()
    if a.mode=='export':export(a.corpus,a.graph,a.meta)
    else:replay(a.corpus,a.result,a.witness5,a.cert10,a.status)
if __name__=='__main__':main()
