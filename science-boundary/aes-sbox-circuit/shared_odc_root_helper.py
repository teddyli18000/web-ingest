#!/usr/bin/env python3
"""Direct-100 shared one-gate ODC helper across arbitrary FS101 roots.

Choose two circuit gate roots i<j.  Insert one new legal two-input helper before
i, computed from wires already available there, and replace *both* root wires by
the helper everywhere downstream.  Delete the two old root gates.  The raw gate
count is therefore 101 + 1 - 2 = 100.

To make the search tractable while staying scientifically clean, require the
helper to be individually valid for each root under that root's exact original
full-circuit observability mask.  Candidate helpers are arbitrary AND/XOR/XNOR
of distinct earlier wires.  Truth-equivalent helpers use one witness because the
new wire has the same placement and downstream role.  Functions already present
as earlier wires are skipped: if such a wire individually resubstitutes a root,
ordinary strict alias resubstitution already covers the cheaper case.

Every simultaneous replacement that passes the individual-care filters is
materialized, pruned, and independently checked on all 256 AES inputs.  The
simultaneous check is necessary because two individually ODC-valid rewrites need
not compose.  Exhaustion is exact only for this 'one new helper individually
ODC-valid for both roots' family, not for arbitrary coordinated ODC changes.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,pathlib,time
import released_and_skeleton as ras
import exact_strict_resub as esr
import seed_family_census as census

OPS=('AND','XOR','XNOR')

def sig(c): return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def helper_functions(earlier,vals):
    existing={vals[w] for w in earlier};out={};tests=0
    for ia,a in enumerate(earlier):
        va=vals[a]
        for b in earlier[ia+1:]:
            vb=vals[b]
            for op in OPS:
                tests+=1;v=census.op_eval(op,va,vb)
                if v in existing:continue
                out.setdefault(v,(op,a,b))
    return out,tests

def materialize(base,i,j,wit):
    ri=base['gates'][i]['out'];rj=base['gates'][j]['out'];op,a,b=wit;hn='__shared_odc__'
    gates=[]
    for k,g in enumerate(base['gates']):
        if k==i:gates.append({'op':op,'a':a,'b':b,'out':hn})
        if k in (i,j):continue
        ng=dict(g);ng['a']=hn if ng['a'] in (ri,rj) else ng['a'];ng['b']=hn if ng['b'] in (ri,rj) else ng['b']
        if ng['a']==ng['b']:return None
        gates.append(ng)
    outs=[hn if w in (ri,rj) else w for w in base['outputs']]
    return ras.prune({'gates':gates,'outputs':outs})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);ap.add_argument('--out',required=True);args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit('fs-101');assert len(base['gates'])==101 and ras.independent_check(base)[0]
    vals,base_out=esr.eval_all(base);n=len(base['gates']);cares=[];proj=[]
    for idx,g in enumerate(base['gates']):
        c=esr.care_mask(base,idx,base_out);cares.append(c);proj.append(vals[g['out']]&c)
    stats=collections.Counter();seen=set();best=None;path=None;t0=time.time()
    for i in range(n-1):
        if i%args.shards!=args.shard:continue
        stats['first_roots']+=1
        earlier=[f'x{k}' for k in range(8)]+[g['out'] for g in base['gates'][:i]]
        helpers,tests=helper_functions(earlier,vals);stats['helper_expr_tests']+=tests;stats['helper_functions']+=len(helpers)
        ci=cares[i];pi=proj[i]
        valid_i=[(v,w) for v,w in helpers.items() if (v&ci)==pi]
        stats['helpers_valid_first']+=len(valid_i)
        if not valid_i:continue
        for j in range(i+1,n):
            cj=cares[j];pj=proj[j]
            for v,wit in valid_i:
                stats['pair_helper_tests']+=1
                if (v&cj)!=pj:continue
                stats['pair_helper_matches']+=1
                nc=materialize(base,i,j,wit)
                if nc is None:stats['duplicate_operand_reject']+=1;continue
                h=sig(nc)
                if h in seen:continue
                seen.add(h);stats['materialized']+=1
                ok=ras.independent_check(nc)
                if not ok[0]:stats['noncomposing']+=1;continue
                stats['verified_composing']+=1
                rec={'root_i':i,'root_j':j,'root_i_out':base['gates'][i]['out'],'root_j_out':base['gates'][j]['out'],'helper':{'op':wit[0],'a':wit[1],'b':wit[2]},'care_i_bits':ci.bit_count(),'care_j_bits':cj.bit_count(),'candidate_gates':len(nc['gates'])}
                if best is None or len(nc['gates'])<len(best['gates']):best=nc;path=rec
                if len(nc['gates'])<=100:break
            if best is not None and len(best['gates'])<=100:break
        if best is not None and len(best['gates'])<=100:break
    summary={'status':'found' if best is not None and len(best['gates'])<=100 else 'exhausted','shard':args.shard,'shards':args.shards,'source_gates':101,'best_gates':None if best is None else len(best['gates']),'best_path':path,'stats':dict(stats),'distinct_materialized':len(seen),'elapsed_s':round(time.time()-t0,3),'family_scope':'one new AND/XOR/XNOR helper before root i, individually ODC-valid for roots i and j, replacing/deleting both roots'}
    if best is not None:
        (out/'best.json').write_text(json.dumps(best,indent=2)+'\n')
        if len(best['gates'])<=100:(out/'candidate.json').write_text(json.dumps(best,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':main()
