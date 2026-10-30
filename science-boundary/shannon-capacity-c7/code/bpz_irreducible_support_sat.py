#!/usr/bin/env python3
"""Exact SAT for outside-only positive BPZ support defects.

For the pinned BPZ/Tan core B (|B|=359), every five-dimensional candidate z
has support S(z)=N[z] cap B.  This model simultaneously chooses at most k owners
and at least k+1 pairwise nonconfusable candidates outside B, requiring every
chosen candidate's full nonempty support to be contained in the selected owner
set.  Thus SAT is exactly an outside-only positive support defect with support
union <= k; UNSAT excludes the whole family without enumerating owner subsets.

The k=7,target=8 instance is a self-check: prior exact census found 12 genuine
outside-only irreducible 7->8 defects.  The active frontier is k=8,target=9.
"""
from __future__ import annotations
import argparse,itertools,json,time,sys
from pathlib import Path

OFFSETS=tuple(itertools.product((-1,0,1),repeat=5))

def dec(v:int):
    d=[0]*5
    for i in range(4,-1,-1): d[i]=v%7;v//=7
    return d

def enc(d):
    z=0
    for x in d:z=7*z+x
    return z

def conflict5(a:int,b:int)->bool:
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def load_geometry(root:Path,k:int):
    root=root.resolve();sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({x:y for x,y in ax.items() if not y})
    ring=base.ring;I=set(map(int,raw['I0']));R={int(x) for x,_ in raw['private_pairs']};B=I-R
    if len(B)!=359:raise RuntimeError(('B',len(B)))
    owners=sorted(B);oid={v:i for i,v in enumerate(owners)}
    candidates=[];supports=[]
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if not S or len(S)>k:continue
        candidates.append(z);supports.append(tuple(oid[x] for x in S))
    return ring,raw,B,owners,candidates,supports

def build(root:Path,k:int,cnf_path:Path,meta_path:Path):
    from pysat.card import CardEnc,EncType
    from pysat.formula import CNF
    ring,raw,B,owners,cands,supp=load_geometry(root,k);n=len(cands);m=len(owners)
    xvar={v:i+1 for i,v in enumerate(cands)};y0=n+1
    cnf=CNF();edges=0;impl=0
    cset=set(cands)
    # Exact induced conflict graph using the 3^5 closed neighborhood.
    for v in cands:
        iv=xvar[v];d=dec(v)
        for off in OFFSETS:
            if all(q==0 for q in off):continue
            w=enc(tuple((d[i]+off[i])%7 for i in range(5)))
            iw=xvar.get(w)
            if iw is not None and iw>iv:
                cnf.append([-iv,-iw]);edges+=1
    for i,S in enumerate(supp):
        xv=i+1
        for oi in S:
            cnf.append([-xv,y0+oi]);impl+=1
    top=y0+m-1
    atmost=CardEnc.atmost(lits=list(range(y0,y0+m)),bound=k,top_id=top,encoding=EncType.cardnetwrk)
    cnf.extend(atmost.clauses);top=max(top,atmost.nv)
    atleast=CardEnc.atleast(lits=list(range(1,n+1)),bound=k+1,top_id=top,encoding=EncType.cardnetwrk)
    cnf.extend(atleast.clauses)
    cnf.to_file(cnf_path)
    meta={'method':'exact-outside-only-support-defect-sat','k':k,'target':k+1,'B_size':len(B),'candidate_count':n,'conflict_edges':edges,'support_implications':impl,'cnf_vars':cnf.nv,'cnf_clauses':len(cnf.clauses),'owners':owners,'candidates':cands,'supports':[list(s) for s in supp],'private_pairs':raw['private_pairs']}
    meta_path.parent.mkdir(parents=True,exist_ok=True);meta_path.write_text(json.dumps(meta,separators=(',',':'))+'\n')
    print(json.dumps({q:v for q,v in meta.items() if q not in ('owners','candidates','supports','private_pairs')},sort_keys=True))

def worker(cnf_path:Path,solver:str,out:Path):
    from pysat.formula import CNF
    from pysat.solvers import Solver
    t=time.time();f=CNF(from_file=cnf_path)
    try:
        with Solver(name=solver,bootstrap_with=f.clauses) as s:
            sat=s.solve();model=s.get_model() if sat else None
        r={'status':'sat' if sat else 'unsat','solver':solver,'seconds':time.time()-t}
        if sat:r['model_positive']=[x for x in model if x>0]
    except Exception as e:
        r={'status':'error','solver':solver,'seconds':time.time()-t,'error':repr(e)}
        out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');raise
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='model_positive'},sort_keys=True),flush=True)

def replay(meta_path:Path,res_path:Path,out_path:Path):
    d=json.loads(meta_path.read_text());r=json.loads(res_path.read_text());k=int(d['k']);n=len(d['candidates'])
    out={'method':'exact-outside-only-support-defect-replay','k':k,'target':k+1,'solver':r.get('solver'),'solver_status':r.get('status')}
    if r.get('status')=='unsat':
        out.update(candidate=False);out_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));return
    if r.get('status')!='sat':raise RuntimeError(r)
    pos=set(map(int,r['model_positive']));chosen=[int(d['candidates'][i]) for i in range(n) if i+1 in pos]
    # Solver may select more than target; retain all and replay exactly.
    if len(chosen)<k+1:raise RuntimeError(('cardinality',len(chosen)))
    for i,a in enumerate(chosen):
        for b in chosen[i+1:]:
            if conflict5(a,b):raise RuntimeError(('conflict',a,b))
    B=set(map(int,d['owners']));
    if any(x in B for x in chosen):raise RuntimeError('owner reused')
    supp_union=set()
    for i in range(n):
        if i+1 in pos:supp_union.update(int(x) for x in d['supports'][i])
    if len(supp_union)>k:raise RuntimeError(('support-union',len(supp_union)))
    owner_words=[int(d['owners'][i]) for i in sorted(supp_union)]
    out.update(candidate=True,witness=sorted(chosen),owners=owner_words,support_union_size=len(supp_union),witness_size=len(chosen))
    out_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build');b.add_argument('tan_root',type=Path);b.add_argument('k',type=int);b.add_argument('cnf',type=Path);b.add_argument('meta',type=Path)
    w=sub.add_parser('worker');w.add_argument('cnf',type=Path);w.add_argument('solver');w.add_argument('output',type=Path)
    r=sub.add_parser('replay');r.add_argument('meta',type=Path);r.add_argument('result',type=Path);r.add_argument('output',type=Path)
    a=ap.parse_args()
    if a.mode=='build':build(a.tan_root,a.k,a.cnf,a.meta)
    elif a.mode=='worker':worker(a.cnf,a.solver,a.output)
    else:replay(a.meta,a.result,a.output)
if __name__=='__main__':main()
