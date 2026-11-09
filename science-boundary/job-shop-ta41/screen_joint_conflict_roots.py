#!/usr/bin/env python3
"""Oracle-blind root screening by counterfactual precompletion conflict burden.

For each near-critical (source-only) machine adjacent precedence root:
  1) compute mincut cycle closure and successive deadline-path closure;
  2) one 0.2-second fully constrained CP assumption-core probe;
  3) record local core size, closure cardinality and conditional feasibility.

Never read the hidden reference machine orders. Held-out audit may later
compare selected roots to a known improved certificate, but the root
candidate generator must not use that information.
"""
import argparse,json,random,time
from pathlib import Path
from counterfactual_joint_cut import (
    immutable_and_resource,choose_roots,counterfactual_closure,
    hard_completion)
from partial_resource_pair_repair import parse_case

def main(a):
    orders,pos,dur,score=parse_case(a.start)
    mutable=immutable_and_resource(orders,pos)
    roots,slacks=choose_roots(dur,mutable,orders,a.seed,a.pool)
    elapsed=time.monotonic();res=[]
    for idx,root in enumerate(roots):
        closure,info=counterfactual_closure(dur,mutable,root,score-1,a.max_released)
        r=dict(root=root,machine=mutable[root][2],
            baseline_slack=slacks[root],
            closure_cardinality=(len(closure[0]) if closure else None),
            closure_optimistic_makespan=(closure[1]['lb'] if closure else None),
            initial_reason=info.get('reason'))
        if closure:
            decision,cert,core=hard_completion(
                dur,mutable,orders,pos,closure[0],root,score-1,
                a.cp_seconds,a.seed*101+root)
            r.update(CP_status=decision['status'],
                CP_seconds=decision['wall_seconds'],
                CP_core_count=(len(core) if core is not None else None),
                CP_branch_count=decision['branches'])
            if cert is not None:r['found_score']=decision['independent_makespan']
        res.append(r)
        if idx%20==0:print('ROOT-SCREEN',idx,'of',len(roots),flush=True)
    # Rank truly source-only by cheap predictors; as each is uncalibrated,
    # save several rankings to compare against downstream constructive cost.
    ids={k:sorted(res,key=key) for k,key in {
        'fewest_releases':lambda z:(z['closure_cardinality'] is None,z['closure_cardinality'] or 999,z['baseline_slack'],z['root']),
        'largest_core_first':lambda z:(z['CP_core_count'] is None,-(z['CP_core_count'] or 0),z['closure_cardinality'] or 999,z['root']),
        'smallest_core_first':lambda z:(z['CP_core_count'] is None,z['CP_core_count'] or 999,z['closure_cardinality'] or 999,z['root']),
    }.items()}
    report=dict(instance=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
        incumbent=score,target=score-1,
        source_only_root_generation=True,
        scoring_cost_seconds=round(time.monotonic()-elapsed,3),
        roots_evaluated=len(res),
        raw=res,
        proposed_rankings={k:[o['root'] for o in arr] for k,arr in ids.items()})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k not in ('raw','proposed_rankings')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--seed',type=int,default=333)
    p.add_argument('--pool',type=int,default=100)
    p.add_argument('--cp-seconds',type=float,default=0.30)
    p.add_argument('--max-released',type=int,default=120)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
