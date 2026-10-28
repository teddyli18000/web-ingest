#!/usr/bin/env python3
"""Search private-swap components of U1, U2, and FunSearch 367-sets for t>=11.

These public seeds are distinct from the already exhausted 522-state
BPZ/Family-F component.  Each private swap preserves size 367 and independence.
We traverse their union of components exactly up to a configurable cap, stopping
immediately if any state has at least 11 distinct private owners.
"""
import argparse,json,runpy,sys
from collections import deque
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10
from bpz_t9_funsearch_fft import funsearch_seed


def extract_367(ns,digits):
    found=[]
    for name,v in ns.items():
        if name.startswith('__'): continue
        try:
            if len(v)!=367: continue
        except Exception:
            continue
        try:
            words=[]
            for w in v:
                if not isinstance(w,(tuple,list)) or len(w)!=5: raise ValueError
                q=tuple(int(x) for x in w)
                if any(not 0<=x<7 for x in q): raise ValueError
                words.append(t10.enc(q))
            S=frozenset(words)
            if len(S)==367 and t10.independent(S,digits): found.append((name,S))
        except Exception:
            pass
    uniq={S:name for name,S in found}
    if not uniq: raise RuntimeError('no 367 independent witness found in verifier namespace')
    return [(name,S) for S,name in uniq.items()]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--max-states',type=int,default=100000);args=ap.parse_args()
    digits=tuple(t10.dec(v) for v in range(t10.U))
    # Closed neighborhoods, represented as bit masks over ambient vertices.
    nb=[]
    for v in range(t10.U):
        w=digits[v];m=0
        for d0 in (-1,0,1):
          for d1 in (-1,0,1):
           for d2 in (-1,0,1):
            for d3 in (-1,0,1):
             for d4 in (-1,0,1):
              u=t10.enc(((w[0]+d0)%7,(w[1]+d1)%7,(w[2]+d2)%7,(w[3]+d3)%7,(w[4]+d4)%7));m|=1<<u
        nb.append(m)
    seeds=[]
    for fn,label in [('u1.py','u1'),('u2.py','u2')]:
        ns=runpy.run_path(str(args.c7five_root/'verify'/fn))
        xs=extract_367(ns,digits)
        for var,S in xs: seeds.append((f'{label}:{var}',set(S)))
    fs=funsearch_seed(digits);seeds.append(('funsearch',set(fs)))
    # Deduplicate exact seed sets while keeping provenance.
    dseed={frozenset(S):name for name,S in seeds};seeds=[(name,set(S)) for S,name in dseed.items()]
    print('SEEDS',json.dumps({'count':len(seeds),'names':[n for n,S in seeds]},sort_keys=True),flush=True)
    seen=set();q=deque();origin={}
    for name,S in seeds:
        if len(S)!=367 or not t10.independent(S,digits): raise RuntimeError(f'invalid seed {name}')
        b=sum(1<<z for z in S)
        if b not in seen: seen.add(b);q.append((b,0));origin[b]=name
    expanded=trans=0;bestowners=-1;bestpairs=-1;best=None;found=None;hist={};maxdepth=0
    while q and expanded<args.max_states:
        bits,depth=q.popleft();expanded+=1;maxdepth=max(maxdepth,depth)
        pp=t10.private(bits,nb);owners={a for a,x in pp};no=len(owners);npair=len(pp);hist[str(no)]=hist.get(str(no),0)+1
        if no>bestowners or (no==bestowners and npair>bestpairs):
            bestowners=no;bestpairs=npair;best=(bits,depth,origin.get(bits),pp)
            print('NEW_BEST',json.dumps({'expanded':expanded,'seen':len(seen),'depth':depth,'origin':origin.get(bits),'private_owners':no,'private_pairs':npair},sort_keys=True),flush=True)
        if no>=11: found=(bits,depth,pp);break
        for a,x in pp:
            c=bits^(1<<a)^(1<<x);trans+=1
            if c in seen: continue
            S=set(t10.values(c))
            if len(S)!=367 or not t10.independent(S,digits): raise RuntimeError('private swap replay failed')
            seen.add(c);q.append((c,depth+1));origin[c]=origin.get(bits)
    complete=not q and found is None
    status={'method':'u1-u2-funsearch-private-swap-component-hunt','seed_count':len(seeds),'seed_names':[n for n,S in seeds],'max_states':args.max_states,'states_expanded':expanded,'states_seen':len(seen),'frontier_remaining':len(q),'complete_without_t11':complete,'found_t11_parent':found is not None,'max_private_owners':bestowners,'max_private_pairs':bestpairs,'max_depth_expanded':maxdepth,'transitions_examined':trans,'owner_histogram':hist,'c7five_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5','funsearch_source_commit':'b02fdbfeb1e138ff3fd74592439e645a3a11de69'}
    if best:
        bb,bd,bo,bpp=best;status['best']={'depth':bd,'origin':bo,'private_owners':len({a for a,x in bpp}),'private_pairs':len(bpp),'points':list(t10.values(bb))}
    if found:
        fb,fd,fpp=found;status['t11_parent']={'depth':fd,'origin':origin.get(fb),'private_owners':len({a for a,x in fpp}),'private_pairs':len(fpp),'points':list(t10.values(fb)),'private_pairs_list':[list(z) for z in fpp]}
    args.status.parent.mkdir(parents=True,exist_ok=True);args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(('FOUND' if found else 'DONE' if complete else 'CAPPED'),json.dumps({k:v for k,v in status.items() if k not in ('best','t11_parent','owner_histogram')},sort_keys=True),flush=True)

if __name__=='__main__':main()
