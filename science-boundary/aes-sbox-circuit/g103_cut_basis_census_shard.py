#!/usr/bin/env python3
"""Sharded driver for g103_cut_basis_census.py."""
from __future__ import annotations
import argparse,json,pathlib
import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf
import g103_cut_basis_census as cb


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--shard',type=int,required=True);ap.add_argument('--shards',type=int,default=8)
    ap.add_argument('--seeds',type=int,default=6);ap.add_argument('--max-gates',type=int,default=22)
    ap.add_argument('--max-support',type=int,default=10);ap.add_argument('--elite',type=int,default=24)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    last,prefix,suffix,boundary=suf.split(c)
    m,C,vals,aff_targets,qtargets,orig_guide=suf.formal_suffix(suffix,boundary,c['outputs'])
    extras=['t47','t48','t49'];extra_idx=[boundary.index(w) for w in extras]
    qvals={w:1<<i for i,w in enumerate(boundary)};guide=[]
    for g in suffix:
        q=qvals[g['a']]^qvals[g['b']];qvals[g['out']]=q;guide.append(q)
    rows=[]
    mats=list(cb.gl3());assert len(mats)==168
    for mi,mat in enumerate(mats):
        if mi%args.shards!=args.shard:continue
        cmap=cb.coeff_map(mat)
        ts=[cb.transform_mask(t,extra_idx,cmap) for t in qtargets]
        gs={cb.transform_mask(g,extra_idx,cmap) for g in guide}
        best=None;best_cfg=None;best_dist=None
        for policy in ('classic','hard','guide'):
            for seed in range(1,args.seeds+1):
                cost,dist=cb.rnbp_cost(ts,gs,seed,policy,args.max_gates,args.max_support,args.elite)
                if cost is not None and (best is None or cost<best):
                    best=cost;best_cfg={'policy':policy,'seed':seed}
                if best_dist is None or sum(dist)<sum(best_dist):best_dist=list(dist)
        row={'matrix_index':mi,'matrix_rows':list(mat),'coeff_map':[cmap[i] for i in range(8)],
             'identity':list(mat)==[1,2,4],'initial_supports':[t.bit_count() for t in ts],
             'initial_bp_sum':sum(t.bit_count()-1 for t in ts),'best_suffix_gates':best,
             'best_config':best_cfg,'best_residual_sum':sum(best_dist),'best_residual':best_dist}
        rows.append(row);print(json.dumps(row,sort_keys=True),flush=True)
    rows.sort(key=lambda r:(999 if r['best_suffix_gates'] is None else r['best_suffix_gates'],r['initial_bp_sum'],r['matrix_rows']))
    summary={'shard':args.shard,'shards':args.shards,'matrices':len(rows),'seeds':args.seeds,
             'max_gates':args.max_gates,'found_le_19':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=19 for r in rows),
             'found_le_20':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=20 for r in rows),
             'found_le_21':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=21 for r in rows),
             'found_le_22':sum(r['best_suffix_gates'] is not None and r['best_suffix_gates']<=22 for r in rows),'rows':rows}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__':main()
