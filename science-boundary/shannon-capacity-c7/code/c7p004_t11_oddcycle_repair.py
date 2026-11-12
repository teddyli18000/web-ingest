#!/usr/bin/env python3
"""Constructive odd-cycle-targeted 2/3-for-2/3 C7^5 parent rewiring.

The 14-private-owner C7^5 seed has only ten *orientable* private pairs.
A valid 11-port BPZ/Gao gadget requires jointly changing private-neighbor
conflict graph, not adding more raw private owners. Release selected original
owner points near the unselected endpoints of a t=10 orientation and replace
them by mutually nonconfusable outside vertices with support fully inside the
released owner set. Re-evaluate the true t11 orientation and immediately
search 365+ D-free auxiliaries on success.
"""
import argparse,collections,itertools,json,random,time
from pathlib import Path
from c7p004_orientable_t11_construct import (
    load_code,profiles,orient,conf,scan,build,closed_neighborhood
)
from c7p5_port_aware_block_walk import PortGeometry
from c7p5_two_layer_repair import independent

def support_pool(S):
    observed={}
    for a in S:
        for z in closed_neighborhood(a):
            if z not in S:observed.setdefault(z,set()).add(a)
    groups=collections.defaultdict(list)
    for z,owners in observed.items():
        if 1<=len(owners)<=3:
            groups[tuple(sorted(owners))].append(z)
    return groups

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('frozen',type=Path);ap.add_argument('tandon',type=Path)
    ap.add_argument('family',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--state',type=int,required=True)
    ap.add_argument('--mode',choices=('double','triple','quad','quint'),required=True)
    ap.add_argument('--max-cases',type=int,default=8000)
    ap.add_argument('--seed',type=int,default=202611121)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    raw=json.loads(a.frozen.read_text())
    name=raw['parents'][a.state]['name'];S=load_code(raw['parents'][a.state])
    assert len(S)==367 and independent(sorted(S))
    g=PortGeometry(S);initial=profiles(g)
    ref=orient(initial,10)
    assert ref is not None and orient(initial,11) is None
    omitted=set(initial)-{x for x,y,c in ref}
    supports=support_pool(S)
    rng=random.Random(a.seed)
    if a.mode=='double':
        release=set(k for k in supports if len(k)==2)
        one_owners=[k[0] for k in supports if len(k)==1]
        release.update(itertools.combinations(one_owners,2))
    elif a.mode=='triple':
        release=set(k for k in supports if len(k)==3)
        for pair in (k for k in supports if len(k)==2):
            for third in omitted:
                if third not in pair:release.add(tuple(sorted((*pair,third))))
    else:
        cardinality=4 if a.mode=='quad' else 5
        release=set(itertools.combinations(sorted(initial),cardinality))
    # Target odd-cycle repair by releasing owners responsible for private-neighbor
    # clash edges, not merely by replacing randomly chosen parent words.
    edges=[]
    for a0,va in initial.items():
        for b0,vb in initial.items():
            if b0>a0 and any(conf(x,y) for x in va for y in vb):
                edges.append((a0,b0))
    def rank(k):
        K=set(k)
        covered=sum(a0 in K or b0 in K for a0,b0 in edges)
        return (-covered,-len(K&omitted),rng.random())
    release=sorted(release,key=rank)
    src=json.loads((a.tandon/'data/base_c7.json').read_text())
    fam=json.loads((a.family/'data/family-f.json').read_text())
    auxiliaries=[('I0',set(src['I0'])),('X',set(src['X']))]
    auxiliaries += [(f'F{i}',set(v)) for i,v in enumerate(fam['states'])]
    auxiliaries.append(('parent',S))
    tests=0;orient11=0;best_owner=len(initial);besthits=367;best=None
    seen=set();start=time.monotonic()
    for released in release:
        if tests>=a.max_cases:break
        L=list(released);pool=[]
        for r in range(1,len(L)+1):
            for part in itertools.combinations(L,r):
                pool.extend(supports.get(part,[]))
        pool=sorted(set(pool))
        if len(pool)<len(L):continue
        options=list(itertools.combinations(pool,len(L)))
        rng.shuffle(options)
        for additions in options:
            if tests>=a.max_cases:break
            if any(conf(x,y) for i,x in enumerate(additions) for y in additions[i+1:]):
                continue
            k=tuple(sorted(additions))
            key=(released,k)
            if key in seen:continue
            seen.add(key)
            Y=(S-set(released))|set(additions)
            assert len(Y)==367 and independent(sorted(Y))
            g.move(Y)
            owners=profiles(g);best_owner=max(best_owner,len(owners))
            tests+=1
            wit=orient(owners,11)
            if wit:
                orient11+=1
                (hits,aux_name,shift,aux),ds=scan(Y,wit,auxiliaries+[('current',Y)])
                if hits<besthits:
                    besthits=hits
                    best={'points':sorted(Y),'pairs':[[u,v,c] for u,v,c in wit],
                          'deleted':list(released),'added':list(additions),
                          'obstruction_size':ds,'auxiliary':aux_name,'translation':shift,
                          'minimum_hits':hits}
                    (a.output/'best_parent.json').write_text(json.dumps(best,indent=2)+'\n')
                    print('T11_WITNESS',json.dumps({'tests':tests,'hits':hits,'obstruction_size':ds}),flush=True)
                if hits<=2:
                    PH={q if c else u for u,q,c in wit};PV={u if c else q for u,q,c in wit}
                    NH=set().union(*(set(closed_neighborhood(x)) for x in PH))
                    NV=set().union(*(set(closed_neighborhood(x)) for x in PV))
                    X=aux-(NH&NV)
                    assert len(X)>=365
                    words=build(Y,X,wit)
                    (a.output/'certificate.json').write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
                    print('FOUND_P004',len(words),'tested',tests,flush=True)
                    break
            g.move(S)
        if (a.output/'certificate.json').exists():break
        if tests and tests%500==0:
            print('PROGRESS',json.dumps({'tested':tests,'best_owners':best_owner,
                't11_parents':orient11,'best_auxiliary_hits':besthits}),flush=True)
    result={'method':'odd-cycle-targeted-2-3-neutral-parent-rewiring',
            'seed':name,'mode':a.mode,'tried_states':tests,'t11_parents':orient11,
            'best_private_owners':best_owner,
            'best_forbidden_hits':besthits if orient11 else None,
            'has_candidate':(a.output/'certificate.json').exists(),
            'seconds':round(time.monotonic()-start,2)}
    (a.output/'status.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps(result,sort_keys=True),flush=True)

if __name__=='__main__':main()
