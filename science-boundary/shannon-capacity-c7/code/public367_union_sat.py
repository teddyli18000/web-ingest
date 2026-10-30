#!/usr/bin/env python3
"""Exact SAT search for a 368-set inside the union of validated public C7^5 367-sets.

The corpus JSON is produced by public367_corpus.py.  This script deliberately
forgets which seed a vertex came from: the candidate universe is the complete
union of all validated public 367-sets.  It builds the exact induced C7^5
conflict graph and asks whether it contains an independent set of size >= 368.

Modes:
  build CORPUS CNF META
  worker CNF SOLVER RESULT
  replay RESULT OUT5 OUT10 STATUS

A SAT witness is independently replayed under the exact conflict rule.  The
10-dimensional output is the Cartesian square of the 5-dimensional witness.
An UNSAT answer, together with any known 367 member of the corpus, proves the
union-induced graph has independence number exactly 367.
"""
from __future__ import annotations
import itertools,json,sys,time
from pathlib import Path

U=7**5
TARGET=368
OFFSETS=tuple(itertools.product((-1,0,1),repeat=5))


def dec(v:int):
    d=[0]*5
    for i in range(4,-1,-1): d[i]=v%7; v//=7
    return d

def enc(d):
    v=0
    for x in d: v=7*v+x
    return v

def word5(v:int)->str:
    d=dec(v); return ''.join(map(str,d))

def conflict(a:int,b:int)->bool:
    if a==b:return True
    da,db=dec(a),dec(b)
    return all(((x-y)%7) in (0,1,6) for x,y in zip(da,db))

def independent(S):
    ss=set(S)
    for v in S:
        d=dec(v)
        for off in OFFSETS:
            if all(x==0 for x in off): continue
            w=enc(tuple((d[i]+off[i])%7 for i in range(5)))
            if w in ss and w>v:return False
    return True

def build(corpus_path,cnf_path,meta_path):
    from pysat.card import CardEnc,EncType
    from pysat.formula import CNF
    corpus=json.load(open(corpus_path))
    rows=corpus['sets']
    if not rows:raise RuntimeError('empty corpus')
    for r in rows:
        pts=list(map(int,r['points']))
        if len(pts)!=367 or len(set(pts))!=367 or not independent(pts):raise RuntimeError(('bad seed',r.get('sources')))
    universe=sorted(set().union(*(set(map(int,r['points'])) for r in rows)))
    idx={v:i+1 for i,v in enumerate(universe)}
    clauses=[]; edges=0
    for v in universe:
        iv=idx[v]; d=dec(v)
        for off in OFFSETS:
            if all(x==0 for x in off):continue
            w=enc(tuple((d[i]+off[i])%7 for i in range(5)))
            iw=idx.get(w)
            if iw is not None and iw>iv:
                clauses.append([-iv,-iw]);edges+=1
    card=CardEnc.atleast(lits=list(range(1,len(universe)+1)),bound=TARGET,top_id=len(universe),encoding=EncType.cardnetwrk)
    cnf=CNF();cnf.extend(clauses);cnf.extend(card.clauses)
    cnf.to_file(cnf_path)
    meta={'method':'public367-union-exact-sat','distinct_seed_sets':len(rows),'union_vertices':len(universe),'conflict_edges':edges,'target':TARGET,'cnf_vars':cnf.nv,'cnf_clauses':len(cnf.clauses),'vertices':universe}
    Path(meta_path).write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in meta.items() if k!='vertices'},sort_keys=True))

def worker(cnf_path,solver_name,result_path):
    from pysat.formula import CNF
    from pysat.solvers import Solver
    t=time.time();cnf=CNF(from_file=cnf_path)
    try:
        with Solver(name=solver_name,bootstrap_with=cnf.clauses) as s:
            sat=s.solve(); model=s.get_model() if sat else None
    except Exception as e:
        Path(result_path).write_text(json.dumps({'status':'error','solver':solver_name,'error':repr(e),'seconds':time.time()-t},indent=2)+'\n')
        raise
    out={'status':'sat' if sat else 'unsat','solver':solver_name,'seconds':time.time()-t}
    if sat:out['model_positive']=[x for x in model if x>0]
    Path(result_path).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='model_positive'},sort_keys=True),flush=True)

def replay(meta_path,result_path,out5,out10,status_path):
    meta=json.load(open(meta_path));r=json.load(open(result_path));status={'method':'public367-union-exact-sat-replay','solver':r.get('solver'),'solver_status':r.get('status'),'union_vertices':meta['union_vertices'],'target':TARGET}
    if r.get('status')=='unsat':
        status.update(candidate_368=False,exact_union_alpha=367)
        Path(status_path).write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(json.dumps(status,sort_keys=True));return
    if r.get('status')!='sat':raise RuntimeError(r)
    verts=meta['vertices'];chosen=[verts[i-1] for i in r['model_positive'] if 1<=i<=len(verts)]
    chosen=sorted(set(chosen))
    if len(chosen)<TARGET or not independent(chosen):raise RuntimeError(('bad witness',len(chosen)))
    Path(out5).write_text(json.dumps({'points':[word5(v) for v in chosen]},separators=(',',':'))+'\n')
    w5=[word5(v) for v in chosen]
    pts10=[a+b for a in w5 for b in w5]
    Path(out10).write_text(json.dumps({'points':sorted(pts10)},separators=(',',':'))+'\n')
    status.update(candidate_368=True,size5=len(chosen),score10=len(pts10))
    Path(status_path).write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(json.dumps(status,sort_keys=True))

def main():
    if len(sys.argv)<2:raise SystemExit(__doc__)
    mode=sys.argv[1]
    if mode=='build' and len(sys.argv)==5:build(*sys.argv[2:])
    elif mode=='worker' and len(sys.argv)==5:worker(*sys.argv[2:])
    elif mode=='replay' and len(sys.argv)==7:replay(*sys.argv[2:])
    else:raise SystemExit(__doc__)
if __name__=='__main__':main()
