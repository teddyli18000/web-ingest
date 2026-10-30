#!/usr/bin/env python3
"""Enumerate joint affine refactorizations of every nonlinear AND atom.

This deliberately relaxes a boundary left fixed by earlier searches.  For an
AND root y=u&v, both operands may change simultaneously.  Each replacement
factor is either an existing earlier wire (cost 0) or one new XOR/XNOR of two
earlier wires (cost 1).  The new product only has to agree with the old root on
that root's exact full-circuit observability mask; accepted complete circuits
are independently checked on all 256 AES inputs.

The search strictly contains the previous one-operand care-alias family and the
known G103/G104 factor-transfer family, while allowing new affine
factorizations not present in either source circuit.  Results at base+1 are
retained because a structurally different 102 seed can be more useful than a
locally exhausted 101 incumbent.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1


def eval_all(c, flip_idx=None):
    vals=census.input_tables(False)
    for i,g in enumerate(c['gates']):
        v=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
        if i==flip_idx:v^=MASK
        vals[g['out']]=v
    return vals,[vals[o] for o in c['outputs']]


def care_mask(c,idx,base_out):
    _,alt=eval_all(c,idx)
    care=0
    for a,b in zip(base_out,alt):care|=a^b
    return care


def signature(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def candidate_factors(earlier,vals,care,max_reps):
    """Projected truth -> low-cost realizations.  Keep several reps because
    identical helper functions can have different pruning consequences."""
    by=collections.defaultdict(list)
    seen_expr=set()
    def add(tv,expr):
        key=tv&care
        ekey=json.dumps(expr,sort_keys=True,separators=(',',':'))
        if (key,ekey) in seen_expr:return
        seen_expr.add((key,ekey))
        bucket=by[key]
        # Existing wires dominate helper realizations for the same function,
        # but keep helper alternatives as they can kill different old wires.
        if len(bucket)<max_reps:bucket.append(expr)
    for w in earlier:add(vals[w],{'cost':0,'wire':w})
    for i,a in enumerate(earlier):
        va=vals[a]
        for b in earlier[i+1:]:
            x=va^vals[b]
            add(x,{'cost':1,'op':'XOR','a':a,'b':b})
            add(x^MASK,{'cost':1,'op':'XNOR','a':a,'b':b})
    return by


def materialize(base,idx,ep,eq):
    nc={'gates':[dict(g) for g in base['gates']],'outputs':list(base['outputs'])}
    inserts=[]
    def wire(expr,k):
        if expr['cost']==0:return expr['wire']
        name=f'__joint_factor_{k}__'
        inserts.append({'op':expr['op'],'a':expr['a'],'b':expr['b'],'out':name})
        return name
    wp=wire(ep,0); wq=wire(eq,1)
    nc['gates'][idx:idx]=inserts
    root=nc['gates'][idx+len(inserts)]
    root['a']=wp;root['b']=wq
    return ras.prune(nc)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed-family',choices=sorted(ras.SOURCES),required=True)
    ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--out',required=True)
    ap.add_argument('--max-reps',type=int,default=3)
    ap.add_argument('--max-kept',type=int,default=200)
    ap.add_argument('--keep-delta',type=int,default=1)
    args=ap.parse_args()
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.seed_family);assert ras.independent_check(base)[0]
    vals,base_out=eval_all(base);base_n=len(base['gates'])
    seen={signature(base)}; kept=[]; best=base
    stats={'and_roots':0,'factor_functions':0,'cover_functions':0,'truth_factor_pairs':0,
           'expression_pairs':0,'verified_candidates':0,'rejected_too_large':0}
    for idx,g in enumerate(base['gates']):
        if g['op']!='AND' or (idx%args.shards)!=args.shard:continue
        stats['and_roots']+=1
        care=care_mask(base,idx,base_out)
        root=vals[g['out']]&care
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in base['gates'][:idx]]
        factors=candidate_factors(earlier,vals,care,args.max_reps)
        stats['factor_functions']+=len(factors)
        cover=[]
        for pv,reps in factors.items():
            # Any factor must be 1 wherever the desired AND output is 1.
            if root & (~pv & care):continue
            cover.append((pv,reps))
        stats['cover_functions']+=len(cover)
        # The AND is commutative, so enumerate unordered projected-factor pairs.
        for i,(pv,preps) in enumerate(cover):
            for qv,qreps in cover[i:]:
                if (pv&qv&care)!=root:continue
                stats['truth_factor_pairs']+=1
                for ep in preps:
                    for eq in qreps:
                        stats['expression_pairs']+=1
                        # Skip exact original operand pair when both are direct wires.
                        if ep['cost']==eq['cost']==0 and {ep['wire'],eq['wire']}=={g['a'],g['b']}:
                            continue
                        nc=materialize(base,idx,ep,eq)
                        if len(nc['gates'])>base_n+args.keep_delta:
                            stats['rejected_too_large']+=1;continue
                        h=signature(nc)
                        if h in seen:continue
                        seen.add(h)
                        ok=ras.independent_check(nc)
                        if not ok[0]:
                            raise AssertionError(('care refactor failed independent check',idx,care.bit_count(),ep,eq,ok))
                        stats['verified_candidates']+=1
                        rec={'and_index':idx,'care_bits':care.bit_count(),'gates':len(nc['gates']),
                             'p':ep,'q':eq,'hash':h}
                        kept.append((len(nc['gates']),h,rec,nc))
                        if len(nc['gates'])<len(best['gates']):best=nc
    kept.sort(key=lambda z:(z[0],z[1]))
    # Persist a bounded architecture archive, preferring smaller then unique hashes.
    archive=[]
    for rank,(n,h,rec,nc) in enumerate(kept[:args.max_kept]):
        name=f'candidate-{rank:03d}-g{n}-{h[:12]}.json'
        (outdir/name).write_text(json.dumps(nc,indent=2)+'\n')
        archive.append({**rec,'file':name})
    (outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={'seed_family':args.seed_family,'shard':args.shard,'shards':args.shards,
             'base_gates':base_n,'best_gates':len(best['gates']),'kept_total':len(kept),
             'kept_by_size':dict(sorted(collections.Counter(n for n,_,_,_ in kept).items())),
             'stats':stats,'archive':archive,'verified_best':ras.independent_check(best)[0]}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
