#!/usr/bin/env python3
"""Full costed classical all-X restart, C offline only; compare exact prior two-arm record."""
import csv,gzip,json,pathlib,collections,statistics,argparse
from verify_hidden import validate_inputs

def read(path):
    with open(path,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    a=argparse.ArgumentParser()
    a.add_argument('--input',required=True);a.add_argument('--vault',required=True)
    a.add_argument('--new',required=True);a.add_argument('--old',required=True)
    a.add_argument('--out',required=True);z=a.parse_args()
    xs,h=validate_inputs(z.input,z.vault)
    fresh=read(pathlib.Path(z.new)/'verified_trials.tsv')
    prior=read(pathlib.Path(z.old)/'retention_paired_trials.tsv')
    assert len(xs)==144 and len(fresh)==len(prior)==864
    n={int(q['n']) for q in xs.values()};assert n=={50}
    previous={(t['id'],int(t['arm'])):t for t in prior}
    new={(t['id'],int(t['arm'])):t for t in fresh}
    assert set(previous)==set(new)
    # Input B orbit checked only postsearch; scorer already certified the C orbit.
    b_hits=set()
    with gzip.open(pathlib.Path(z.new)/'events.tsv.gz','rt',newline='') as f:
        rdr=csv.DictReader(f,delimiter='\t')
        assert 'always_original' in rdr.fieldnames
        for e in rdr:
            sid=e['id']; arm=int(e['arm'])
            assert e['always_original']=='1'
            assert e['proposal_origin_bits']==xs[sid]['X']
            if e['postCanon']==xs[sid]['B_orbit']:b_hits.add((sid,arm))
    out={'states':len(xs),'paired_strategy_sessions':len(fresh),
       'identical_N50_source_orbit_population_already_exposed':True,
       'by_tier':{},'critical_scope':'costed classical fixed-X multistart, not novel neural structure'}
    comparisons=[]
    for key in sorted(new):
        now=new[key];old=previous[key];sid,arm=key;source=xs[sid]
        assert now['mode']==old['mode']==source['mode']
        assert int(now['initial_direct_repair_C'])==int(old['baseline_C'])
        comparisons.append({'id':sid,'mode':source['mode'],'damage':int(source['damage']),
            'C_orbit':h[sid]['C_id'],'arm':arm,
            'original_greedy_C_incremental':int(old['control_incremental_C']),
            'alternating_X_C_incremental':int(old['retained_incremental_C']),
            'always_X_C_incremental':int(now['incremental_C_after_initial_failure']),
            'always_X_B_hit':int(key in b_hits),
            'greedy_best_E':int(old['control_best_E']),
            'alternating_best_E':int(old['retained_best_E']),
            'always_X_best_E':int(now['bestE']),
            'greedy_full_repairs':int(old['control_repair_calls']),
            'alternating_full_repairs':int(old['retained_repair_calls']),
            'always_X_full_repairs':int(now['repaired_calls']),
            'always_X_wall_ms':float(now['wall_ms'])})
    for tier in ('AB_blind','C_shell'):
        out['by_tier'][tier]={}
        for arm in range(6):
            zz=[v for v in comparisons if v['mode']==tier and v['arm']==arm]
            assert len(zz)==72
            out['by_tier'][tier][str(arm)]={
                'states':len(zz),'shared_optimum_orbits':len({t['C_orbit'] for t in zz}),
                'greedy_additional_C':sum(t['original_greedy_C_incremental'] for t in zz),
                'alternating_X_additional_C':sum(t['alternating_X_C_incremental'] for t in zz),
                'always_X_additional_C':sum(t['always_X_C_incremental'] for t in zz),
                'always_X_B_hits':sum(t['always_X_B_hit'] for t in zz),
                'mean_greedy_best_E':statistics.mean(t['greedy_best_E'] for t in zz),
                'mean_alternating_best_E':statistics.mean(t['alternating_best_E'] for t in zz),
                'mean_always_X_best_E':statistics.mean(t['always_X_best_E'] for t in zz),
                'mean_always_X_full_repairs':statistics.mean(t['always_X_full_repairs'] for t in zz),
                'mean_always_X_wall_ms':statistics.mean(t['always_X_wall_ms'] for t in zz),
                'alternating_X_but_not_always_X':sum(t['alternating_X_C_incremental'] and not t['always_X_C_incremental'] for t in zz),
                'always_X_but_not_alternating_X':sum(t['always_X_C_incremental'] and not t['alternating_X_C_incremental'] for t in zz),
                'by_target_orbit':{target:{
                  'states':sum(t['C_orbit']==target for t in zz),
                  'alternating_X_C_hits':sum(t['alternating_X_C_incremental'] for t in zz if t['C_orbit']==target),
                  'always_X_C_hits':sum(t['always_X_C_incremental'] for t in zz if t['C_orbit']==target)}
                  for target in sorted({t['C_orbit'] for t in zz})}
            }
    p=pathlib.Path(z.out);p.parent.mkdir(parents=True,exist_ok=True)
    (p/'all_X_vs_alternating_verdict.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
