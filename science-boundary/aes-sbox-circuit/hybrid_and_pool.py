#!/usr/bin/env python3
"""Construct hybrid 32-AND AES skeletons from multiple high-quality NIST seeds.

Rather than treating complete circuits as isolated seeds, align AND outputs by
exact 256-bit Boolean function.  A shared nonlinear atom may have different
affine operand factorizations in different circuits.  We pool those choices,
then enumerate 32-atom subsets that (a) can be topologically generated using a
pooled factorization and (b) linearly span every AES output together with the
primary inputs and constant.

This searches a qualitatively different architecture family.  It does not
claim that a feasible nonlinear skeleton has a good linear gate realization;
we rank feasible candidates by affine-interface support only for follow-up.
"""
from __future__ import annotations
import argparse, collections, itertools, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census

SOURCES={
 'g103':'nist-g103',
 'g104':'nist-g104',
}
MASK=(1<<256)-1


def circuit_data(name):
    c=ras.load_circuit(SOURCES[name]); sk=ras.extract_skeleton(c)
    vals=census.input_tables(False); and_funcs=[]
    for g in c['gates']:
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
        if g['op']=='AND': and_funcs.append(vals[g['out']])
    assert len(and_funcs)==sk['n_and']
    outs=[vals[o] for o in c['outputs']]
    return c,sk,and_funcs,outs


def affine_global(local_v, local_to_gid, nglobal, local_const_bit):
    gc=8+nglobal; out=(1<<gc) if ((local_v>>local_const_bit)&1) else 0
    for i in range(8):
        if (local_v>>i)&1:out^=1<<i
    for li,gid in enumerate(local_to_gid):
        if (local_v>>(8+li))&1:out^=1<<(8+gid)
    return out


def dep_atoms(v,nglobal):
    return {i for i in range(nglobal) if (v>>(8+i))&1}


def eval_affine_mask(mask, atom_truths):
    z=MASK if ((mask>>(8+len(atom_truths)))&1) else 0
    for i,t in enumerate(census.input_tables(False).values()):
        if (mask>>i)&1:z^=t
    for i,t in enumerate(atom_truths):
        if (mask>>(8+i))&1:z^=t
    return z


def gf2_span_coeff(target,basis):
    """Return subset mask over basis whose XOR is target, or None."""
    rows={}  # pivot -> (value, provenance)
    for i,v in enumerate(basis):
        x=v; p=1<<i
        while x:
            b=x.bit_length()-1
            if b not in rows:
                rows[b]=(x,p);break
            x^=rows[b][0];p^=rows[b][1]
    x=target;p=0
    while x:
        b=x.bit_length()-1
        if b not in rows:return None
        x^=rows[b][0];p^=rows[b][1]
    return p


def build_pool(names):
    raw={n:circuit_data(n) for n in names}
    funcs=[]; gid={}
    for n in names:
        for f in raw[n][2]:
            if f not in gid:gid[f]=len(funcs);funcs.append(f)
    ng=len(funcs);decomp=[[] for _ in funcs]; origins=[set() for _ in funcs]
    source_sets={}
    for n in names:
        c,sk,afs,outs=raw[n]; mp=[gid[f] for f in afs]; source_sets[n]=set(mp)
        for li,g in enumerate(mp):
            a=affine_global(sk['ands'][li]['a'],mp,ng,sk['const_bit'])
            b=affine_global(sk['ands'][li]['b'],mp,ng,sk['const_bit'])
            pair=(a,b,n,li)
            if pair not in decomp[g]:decomp[g].append(pair)
            origins[g].add(n)
    return raw,funcs,decomp,origins,source_sets


def topological_realization(selected,decomp,ng):
    selected=set(selected);done=set();order=[];choice={}
    while len(done)<len(selected):
        avail=[]
        for g in selected-done:
            for a,b,src,li in decomp[g]:
                deps=(dep_atoms(a,ng)|dep_atoms(b,ng))
                if deps<=done:
                    # Rank choices by direct support first; preserve source diversity second.
                    cost=((a & ((1<<(8+ng))-1)).bit_count() + (b & ((1<<(8+ng))-1)).bit_count(),src,li)
                    avail.append((cost,g,(a,b,src,li)));break
        if not avail:return None
        _,g,ch=min(avail);done.add(g);order.append(g);choice[g]=ch
    return order,choice


def output_forms(selected, funcs, outputs):
    selected=list(selected)
    basis=[census.input_tables(False)[f'x{i}'] for i in range(8)]+[funcs[g] for g in selected]+[MASK]
    coeff=[]
    for t in outputs:
        p=gf2_span_coeff(t,basis)
        if p is None:return None
        coeff.append(p)
    return coeff


def remap_form(global_v, order, ng):
    """Global affine mask -> local released-order mask for support metrics."""
    pos={g:i for i,g in enumerate(order)}; lc=8+len(order); gc=8+ng
    v=(1<<lc) if ((global_v>>gc)&1) else 0
    for i in range(8):
        if (global_v>>i)&1:v^=1<<i
    for g in order:
        if (global_v>>(8+g))&1:v^=1<<(8+pos[g])
    return v


def proxy(order,choice,out_coeff,selected,ng):
    forms=[]
    for g in order:
        a,b,_,_=choice[g];forms.extend((remap_form(a,order,ng),remap_form(b,order,ng)))
    # output coeff are over [x0..x7, selected-in-sorted-order, const]; translate.
    sorted_sel=list(selected);lc=8+len(order);pos={g:i for i,g in enumerate(order)}
    for p in out_coeff:
        v=(1<<lc) if ((p>>(8+len(sorted_sel)))&1) else 0
        for i in range(8):
            if (p>>i)&1:v^=1<<i
        for j,g in enumerate(sorted_sel):
            if (p>>(8+j))&1:v^=1<<(8+pos[g])
        forms.append(v)
    uniq=set(forms); linear_mask=(1<<lc)-1
    support_sum=sum((v&linear_mask).bit_count() for v in uniq)
    naive=sum(max(0,(v&linear_mask).bit_count()-1) + (2 if ((v>>lc)&1 and (v&linear_mask).bit_count()==1) else 0) for v in uniq)
    return {'unique_forms':len(uniq),'support_sum':support_sum,'unique_naive_cost':naive}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sources',default='g103,g104');ap.add_argument('--and-count',type=int,default=32);ap.add_argument('--out',required=True)
    args=ap.parse_args();names=args.sources.split(',')
    raw,funcs,decomp,origins,source_sets=build_pool(names);ng=len(funcs)
    # AES outputs are identical across every verified source.
    outputs=raw[names[0]][3]
    feasible=[];tested=0
    for selected in itertools.combinations(range(ng),args.and_count):
        tested+=1
        topo=topological_realization(selected,decomp,ng)
        if topo is None:continue
        of=output_forms(selected,funcs,outputs)
        if of is None:continue
        order,choice=topo;m=proxy(order,choice,of,selected,ng)
        srcdist={n:len(set(selected)^source_sets[n]) for n in names}
        feasible.append({'selected':list(selected),'order':order,'choices':{str(g):{'src':choice[g][2],'local_index':choice[g][3]} for g in order},
                         'proxy':m,'symmetric_difference_to_source':srcdist})
    feasible.sort(key=lambda x:(x['proxy']['unique_naive_cost'],x['proxy']['support_sum'],min(x['symmetric_difference_to_source'].values())))
    out={'sources':names,'union_and_functions':ng,'target_and_count':args.and_count,'tested_subsets':tested,'feasible_count':len(feasible),
         'source_sets':{n:sorted(v) for n,v in source_sets.items()},
         'shared_atoms':sum(len(origins[g])>1 for g in range(ng)),'multi_factorization_atoms':sum(len(decomp[g])>1 for g in range(ng)),
         'top':feasible[:100]}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('sources','union_and_functions','target_and_count','tested_subsets','feasible_count','shared_atoms','multi_factorization_atoms')},sort_keys=True))
    for x in feasible[:10]:print(json.dumps({'proxy':x['proxy'],'dist':x['symmetric_difference_to_source'],'selected':x['selected']},sort_keys=True))

if __name__=='__main__':main()
