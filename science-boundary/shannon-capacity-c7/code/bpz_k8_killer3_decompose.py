#!/usr/bin/env python3
"""Exact decomposition of the k8 positive-defect search by allowed killer colors.

A solution using at most three of the eight BPZ private-pair killer colors is
contained in at least one 3-color allowed set.  Therefore it is sufficient and
complete to solve the 56 triples of colors.  The input CNF is the unrestricted
exact-k8 support-union model; each triple is imposed only through assumptions
forbidding candidate variables whose exact killer mask is not a subset of the
allowed triple.  Each worker reuses one incremental SAT instance across its
assigned triples.
"""
from __future__ import annotations
import argparse,itertools,json,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path

TRIPLES=list(itertools.combinations(range(8),3))

def solve_shard(cnf_path:str,meta_path:str,shard:int,shards:int,solver_name:str):
    from pysat.formula import CNF
    from pysat.solvers import Solver
    meta=json.loads(Path(meta_path).read_text());masks=list(map(int,meta['killer_masks']));n=len(masks)
    f=CNF(from_file=cnf_path);rows=[];t0=time.time()
    with Solver(name=solver_name,bootstrap_with=f.clauses) as s:
        for ti,T in enumerate(TRIPLES):
            if ti%shards!=shard:continue
            allowed=sum(1<<j for j in T)
            assumptions=[-(i+1) for i,km in enumerate(masks) if km & ~allowed]
            ts=time.time();sat=s.solve(assumptions=assumptions);model=s.get_model() if sat else None
            row={'triple_index':ti,'colors':list(T),'allowed_mask':allowed,'status':'sat' if sat else 'unsat','seconds':time.time()-ts,'forbidden_candidates':len(assumptions)}
            if sat:row['model_positive']=[z for z in model if z>0]
            rows.append(row)
            if sat:break
    return {'shard':shard,'shards':shards,'solver':solver_name,'seconds':time.time()-t0,'rows':rows}

def replay(meta,row):
    k=int(meta['k']);n=len(meta['candidates']);pos=set(map(int,row['model_positive']))
    chosen_idx=[i for i in range(n) if i+1 in pos];chosen=[int(meta['candidates'][i]) for i in chosen_idx]
    supp=set();km=0
    for i in chosen_idx:supp.update(map(int,meta['supports'][i]));km|=int(meta['killer_masks'][i])
    allowed=int(row['allowed_mask'])
    if len(chosen)<k+1 or len(supp)!=k or km&~allowed or km.bit_count()>3:raise RuntimeError(('replay',len(chosen),len(supp),km,allowed))
    return {'candidate':True,'colors':row['colors'],'allowed_mask':allowed,'witness':sorted(chosen),'owners':[int(meta['owners'][i]) for i in sorted(supp)],'support_union_size':len(supp),'witness_size':len(chosen),'killer_mask':km,'killer_colors':[j for j in range(8) if km>>j&1],'killer_count':km.bit_count()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('cnf',type=Path);ap.add_argument('meta',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--solver',default='cadical195');a=ap.parse_args()
    meta=json.loads(a.meta.read_text());workers=max(1,min(a.workers,4,len(TRIPLES)));parts=[]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        fs=[ex.submit(solve_shard,str(a.cnf),str(a.meta),i,workers,a.solver) for i in range(workers)]
        for f in as_completed(fs):parts.append(f.result())
    rows=sorted((r for p in parts for r in p['rows']),key=lambda x:x['triple_index']);satrows=[r for r in rows if r['status']=='sat']
    if satrows:
        wit=replay(meta,satrows[0]);status='sat'
    else:
        if len(rows)!=len(TRIPLES) or any(r['status']!='unsat' for r in rows):raise RuntimeError(('incomplete',len(rows)))
        wit=None;status='unsat'
    out={'method':'exact-k8-killer3-color-triple-decomposition','status':status,'triples_total':len(TRIPLES),'triples_completed':len(rows),'workers':workers,'solver':a.solver,'witness':wit,'parts':parts}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='parts'},sort_keys=True))
if __name__=='__main__':main()
