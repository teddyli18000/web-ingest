#!/usr/bin/env python3
"""Search 32-AND hybrid skeletons across the full near-frontier NIST family.

Pool exact AND functions and distinct affine factorizations from A32/G103,G104,
G105,G109 and A33/G105,G108.  Rather than enumerate every 32-subset of the
union, exhaust all one- and two-atom swaps around each existing 32-AND source
set.  A candidate is kept only if its atoms can be topologically generated from
known pooled factorizations and its affine span contains every AES output.

The result is a covered local architecture family, not a global lower bound.
"""
from __future__ import annotations
import argparse,itertools,json,pathlib
import seed_family_census as census
import seed_family_census_extended as ext
import released_and_skeleton as ras
import hybrid_and_pool as hp

NAMES=['nist-a32-g103','nist-a32-g104','nist-a32-g105','nist-a32-g109','nist-a33-g105','nist-a33-g108']

def load_url(url):
    text=census.get(url)
    if text.lstrip().startswith('{'): c=json.loads(text)
    else: c,_=census.normalize_nist(census.parse_nist(text))
    c=ras.prune(c); assert ras.independent_check(c)[0]; return c

def data(name):
    c=load_url(ext.URLS[name]);sk=ras.extract_skeleton(c)
    vals=census.input_tables(False); af=[]
    for g in c['gates']:
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
        if g['op']=='AND':af.append(vals[g['out']])
    return c,sk,af,[vals[o] for o in c['outputs']]

def build_pool():
    raw={n:data(n) for n in NAMES};funcs=[];gid={}
    for n in NAMES:
        for f in raw[n][2]:
            if f not in gid:gid[f]=len(funcs);funcs.append(f)
    ng=len(funcs);decomp=[[] for _ in funcs];source_sets={}
    for n in NAMES:
        c,sk,afs,outs=raw[n];mp=[gid[f] for f in afs];source_sets[n]=set(mp)
        for li,g in enumerate(mp):
            a=hp.affine_global(sk['ands'][li]['a'],mp,ng,sk['const_bit'])
            b=hp.affine_global(sk['ands'][li]['b'],mp,ng,sk['const_bit'])
            # Deduplicate real factor pairs; retain provenance separately.
            key=tuple(sorted((a,b)))
            hit=None
            for j,(aa,bb,prov) in enumerate(decomp[g]):
                if tuple(sorted((aa,bb)))==key:hit=j;break
            if hit is None:decomp[g].append((a,b,[(n,li)]))
            else:decomp[g][hit][2].append((n,li))
    return raw,funcs,decomp,source_sets

def topo(selected,decomp,ng):
    selected=set(selected);done=set();order=[];choice={}
    while len(done)<len(selected):
        opts=[]
        for g in selected-done:
            for a,b,prov in decomp[g]:
                deps=hp.dep_atoms(a,ng)|hp.dep_atoms(b,ng)
                if deps<=done:
                    cost=((a & ((1<<(8+ng))-1)).bit_count()+(b & ((1<<(8+ng))-1)).bit_count(),g)
                    opts.append((cost,g,(a,b,prov)));break
        if not opts:return None
        _,g,ch=min(opts);done.add(g);order.append(g);choice[g]=ch
    return order,choice

def output_forms(selected,funcs,outputs):
    sel=sorted(selected);basis=[census.input_tables(False)[f'x{i}'] for i in range(8)]+[funcs[g] for g in sel]+[(1<<256)-1]
    coeff=[]
    for t in outputs:
        p=hp.gf2_span_coeff(t,basis)
        if p is None:return None
        coeff.append(p)
    return coeff

def candidate_sets(source_sets,ng,max_swaps):
    universe=set(range(ng));seen=set()
    for name,S in source_sets.items():
        if len(S)!=32:continue
        outside=sorted(universe-S);inside=sorted(S)
        for r in range(0,max_swaps+1):
            if r==0:
                key=tuple(sorted(S));
                if key not in seen:seen.add(key);yield key
                continue
            for rem in itertools.combinations(inside,r):
                for add in itertools.combinations(outside,r):
                    T=(S-set(rem))|set(add);key=tuple(sorted(T))
                    if key not in seen:seen.add(key);yield key

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--max-swaps',type=int,default=2);ap.add_argument('--out',required=True);args=ap.parse_args()
    raw,funcs,decomp,source_sets=build_pool();ng=len(funcs);outputs=raw[NAMES[0]][3]
    distinct_alt=sum(len(ds)>1 for ds in decomp);total_decomps=sum(len(ds) for ds in decomp)
    feasible=[];tested=0
    for selected in candidate_sets(source_sets,ng,args.max_swaps):
        tested+=1;t=topo(selected,decomp,ng)
        if t is None:continue
        of=output_forms(selected,funcs,outputs)
        if of is None:continue
        order,choice=t
        # Build proxy using a compatibility shim to hp.proxy's choice format.
        compat={g:(choice[g][0],choice[g][1],choice[g][2][0][0],choice[g][2][0][1]) for g in order}
        m=hp.proxy(order,compat,of,sorted(selected),ng)
        dist={n:len(set(selected)^S) for n,S in source_sets.items() if len(S)==32}
        feasible.append({'selected':list(selected),'proxy':m,'distance':dist,
                         'choice_provenance':{str(g):choice[g][2] for g in order}})
    feasible.sort(key=lambda x:(min(x['distance'].values()),x['proxy']['unique_naive_cost'],x['proxy']['support_sum']))
    originals={tuple(sorted(S)) for S in source_sets.values() if len(S)==32}
    novel=[x for x in feasible if tuple(x['selected']) not in originals]
    out={'sources':NAMES,'union_and_functions':ng,'distinct_atoms_with_multiple_factor_pairs':distinct_alt,
         'total_distinct_factor_pairs':total_decomps,'tested_local_32sets':tested,'feasible_count':len(feasible),
         'novel_feasible_count':len(novel),'novel_top':novel[:100],'all_top':feasible[:100]}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('union_and_functions','distinct_atoms_with_multiple_factor_pairs','total_distinct_factor_pairs','tested_local_32sets','feasible_count','novel_feasible_count')},sort_keys=True))
    for x in novel[:10]:print(json.dumps({'distance':x['distance'],'proxy':x['proxy'],'selected':x['selected']},sort_keys=True))
if __name__=='__main__':main()
