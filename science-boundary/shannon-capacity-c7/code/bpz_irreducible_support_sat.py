#!/usr/bin/env python3
"""Exact SAT for outside-only positive BPZ support defects.

For the pinned BPZ/Tan core B (|B|=359), every five-dimensional candidate z
has support S(z)=N[z] intersect B. For integer k this model selects at least
k+1 pairwise nonconfusable candidates outside B and requires their exact support
union to contain exactly k owners.

Optional killer controls use the eight pinned BPZ private-pair colors. A point
kills color j when it conflicts with both endpoints of private pair j.
--killer-free filters all killer points. --max-killer-colors h keeps all points
but constrains the union of killed colors to size at most h.
"""
from __future__ import annotations
import argparse,itertools,json,time,sys
from pathlib import Path

OFFSETS=tuple(itertools.product((-1,0,1),repeat=5))

def dec(v:int):
    d=[0]*5
    for i in range(4,-1,-1):d[i]=v%7;v//=7
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

def killer_mask(z:int,pairs)->int:
    m=0
    for i,p in enumerate(pairs):
        a,b=int(p[0]),int(p[1])
        if conflict5(z,a) and conflict5(z,b):m|=1<<i
    return m

def load_geometry(root:Path,k:int,killer_free:bool):
    root=root.resolve();sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({x:y for x,y in ax.items() if not y})
    ring=base.ring;I=set(map(int,raw['I0']));R={int(x) for x,_ in raw['private_pairs']};B=I-R
    if len(B)!=359:raise RuntimeError(('B',len(B)))
    owners=sorted(B);oid={v:i for i,v in enumerate(owners)}
    candidates=[];supports=[];kmasks=[]
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if not S or len(S)>k:continue
        km=killer_mask(z,raw['private_pairs'])
        if killer_free and km:continue
        candidates.append(z);supports.append(tuple(oid[x] for x in S));kmasks.append(km)
    return ring,raw,B,owners,candidates,supports,kmasks

def build(root:Path,k:int,cnf_path:Path,meta_path:Path,killer_free:bool=False,max_killer_colors:int|None=None):
    from pysat.card import CardEnc,EncType
    from pysat.formula import CNF
    if killer_free and max_killer_colors not in (None,0):raise ValueError('killer-free conflicts with positive max-killer-colors')
    if max_killer_colors is not None and not 0<=max_killer_colors<=8:raise ValueError(max_killer_colors)
    ring,raw,B,owners,cands,supp,kmasks=load_geometry(root,k,killer_free);n=len(cands);m=len(owners);nc=len(raw['private_pairs'])
    xvar={v:i+1 for i,v in enumerate(cands)};y0=n+1;c0=y0+m
    cnf=CNF();edges=0;impl=0;reverse=0;kimpl=0
    for v in cands:
        iv=xvar[v];d=dec(v)
        for off in OFFSETS:
            if all(q==0 for q in off):continue
            w=enc(tuple((d[i]+off[i])%7 for i in range(5)))
            iw=xvar.get(w)
            if iw is not None and iw>iv:
                cnf.append([-iv,-iw]);edges+=1
    incident=[[] for _ in range(m)]
    for i,S in enumerate(supp):
        xv=i+1
        for oi in S:
            cnf.append([-xv,y0+oi]);impl+=1;incident[oi].append(xv)
        if max_killer_colors is not None:
            km=kmasks[i]
            for j in range(nc):
                if km>>j&1:cnf.append([-xv,c0+j]);kimpl+=1
    for oi,xs in enumerate(incident):
        cnf.append([-(y0+oi),*xs] if xs else [-(y0+oi)]);reverse+=1
    top=c0+nc-1 if max_killer_colors is not None else y0+m-1
    exact=CardEnc.equals(lits=list(range(y0,y0+m)),bound=k,top_id=top,encoding=EncType.cardnetwrk)
    cnf.extend(exact.clauses);top=max(top,exact.nv)
    atleast=CardEnc.atleast(lits=list(range(1,n+1)),bound=k+1,top_id=top,encoding=EncType.cardnetwrk)
    cnf.extend(atleast.clauses);top=max(top,atleast.nv)
    if max_killer_colors is not None:
        kc=CardEnc.atmost(lits=list(range(c0,c0+nc)),bound=max_killer_colors,top_id=top,encoding=EncType.cardnetwrk)
        cnf.extend(kc.clauses)
    cnf.to_file(cnf_path)
    meta={'method':'exact-outside-only-exact-support-defect-sat','k':k,'target':k+1,'killer_free':killer_free,'max_killer_colors':max_killer_colors,'B_size':len(B),'candidate_count':n,'conflict_edges':edges,'support_implications':impl,'support_reverse_clauses':reverse,'killer_implications':kimpl,'cnf_vars':cnf.nv,'cnf_clauses':len(cnf.clauses),'owners':owners,'candidates':cands,'supports':[list(s) for s in supp],'killer_masks':kmasks,'private_pairs':raw['private_pairs']}
    meta_path.parent.mkdir(parents=True,exist_ok=True);meta_path.write_text(json.dumps(meta,separators=(',',':'))+'\n')
    print(json.dumps({q:v for q,v in meta.items() if q not in ('owners','candidates','supports','killer_masks','private_pairs')},sort_keys=True))

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
    out={'method':'exact-outside-only-exact-support-defect-replay','k':k,'target':k+1,'killer_free':bool(d.get('killer_free')),'max_killer_colors':d.get('max_killer_colors'),'solver':r.get('solver'),'solver_status':r.get('status')}
    if r.get('status')=='unsat':
        out.update(candidate=False);out_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));return
    if r.get('status')!='sat':raise RuntimeError(r)
    pos=set(map(int,r['model_positive']));chosen_idx=[i for i in range(n) if i+1 in pos];chosen=[int(d['candidates'][i]) for i in chosen_idx]
    if len(chosen)<k+1:raise RuntimeError(('cardinality',len(chosen)))
    for i,a in enumerate(chosen):
        for b in chosen[i+1:]:
            if conflict5(a,b):raise RuntimeError(('conflict',a,b))
    B=set(map(int,d['owners']))
    if any(x in B for x in chosen):raise RuntimeError('owner reused')
    supp_union=set();killer_union=0
    for i in chosen_idx:
        supp_union.update(int(x) for x in d['supports'][i]);killer_union|=int(d['killer_masks'][i])
    if len(supp_union)!=k:raise RuntimeError(('support-union',len(supp_union),k))
    kc=killer_union.bit_count();mk=d.get('max_killer_colors')
    if d.get('killer_free') and killer_union:raise RuntimeError(('killer-free-violation',killer_union))
    if mk is not None and kc>int(mk):raise RuntimeError(('killer-bound',kc,mk))
    owner_words=[int(d['owners'][i]) for i in sorted(supp_union)]
    killed=[i for i in range(len(d['private_pairs'])) if killer_union>>i&1]
    out.update(candidate=True,witness=sorted(chosen),owners=owner_words,support_union_size=len(supp_union),witness_size=len(chosen),killed_private_pair_colors=killed,killed_private_pair_count=kc)
    out_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='mode',required=True)
    b=sub.add_parser('build');b.add_argument('tan_root',type=Path);b.add_argument('k',type=int);b.add_argument('cnf',type=Path);b.add_argument('meta',type=Path);b.add_argument('--killer-free',action='store_true');b.add_argument('--max-killer-colors',type=int)
    w=sub.add_parser('worker');w.add_argument('cnf',type=Path);w.add_argument('solver');w.add_argument('output',type=Path)
    r=sub.add_parser('replay');r.add_argument('meta',type=Path);r.add_argument('result',type=Path);r.add_argument('output',type=Path)
    a=ap.parse_args()
    if a.mode=='build':build(a.tan_root,a.k,a.cnf,a.meta,a.killer_free,a.max_killer_colors)
    elif a.mode=='worker':worker(a.cnf,a.solver,a.output)
    else:replay(a.meta,a.result,a.output)
if __name__=='__main__':main()
