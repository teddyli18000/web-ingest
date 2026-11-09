#!/usr/bin/env python3
"""Offline causal *representation* ablation, not a deployed repair policy.

Same X, exact full repair, A/B/fake donor supports and j=1..5 proposal rule.
Only the branch anchor differs: accepted greedy repair vs original X.
Hidden C vault used here solely for post hoc orbit-distance diagnostics.
"""
import argparse,csv,json,pathlib,statistics,collections
from verify_hidden import validate_inputs,orbit_hd,E,canon

def read(p):
 with open(p,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def main():
 q=argparse.ArgumentParser();q.add_argument('--input',required=True)
 q.add_argument('--vault',required=True);q.add_argument('--first',required=True)
 q.add_argument('--retained',required=True);q.add_argument('--raw-bank',required=True)
 q.add_argument('--out',required=True);a=q.parse_args()
 inputs,vault=validate_inputs(a.input,a.vault)
 x=read(a.first);y=read(a.retained);raw=read(a.raw_bank)
 assert len(x)==len(y)==len(inputs)*3
 grouped={}
 for rows,branch in [(x,0),(y,1)]:
  for r in rows:
   k=(r['id'],int(r['donor_method']))
   grouped.setdefault(k,{})[branch]=r
 assert len(grouped)==len(inputs)*3 and all(set(v)=={0,1} for v in grouped.values())
 roots=collections.defaultdict(dict)
 for r in raw:
  sid=r['id'];branch=int(r['branch']);method=int(r['donor_method']);j=int(r['j'])
  assert branch in (0,1) and method in (0,1,2) and 1<=j<=5
  key=(sid,branch,method);roots[key][j]=r
 assert all(set(v)==set(range(1,6)) for v in roots.values()) and len(roots)==len(inputs)*6
 rows=[]
 for (sid,method),v in grouped.items():
  z=v[0];t=v[1];h=vault[sid];s=inputs[sid]
  r0=roots[(sid,0,method)][1];r1=roots[(sid,1,method)][1]
  assert r0['starting_bits']!= '' and r1['starting_bits']!=''
  assert r0['baseline_post_bits']==r1['baseline_post_bits']
  assert r1['starting_bits']==s['X']
  assert E(r0['baseline_post_bits'])==int(r0['baseline_post_E'])
  assert int(z['baseline_C'])==int(t['baseline_C'])
  first_fail=not int(z['baseline_C'])
  d0=orbit_hd(r0['starting_bits'],h['C'])
  d1=orbit_hd(r1['starting_bits'],h['C'])
  db=orbit_hd(r0['baseline_post_bits'],h['C'])
  rows.append({'id':sid,'n':int(s['n']),'mode':s['mode'],'C_id':h['C_id'],
    'rep':int(s['rep']),'damage':int(s['damage']),'donor_method':method,
    'direct_repair_fails_C':int(first_fail),
    'branch0_changes_anchor':int(r0['starting_bits']!=r1['starting_bits']),
    'raw_X_orbit_dist_to_C':d1,'greedy_current_dist_to_C':d0,
    'raw_full_repair_dist_to_C':db,
    'accepted_greedy_branch_C_reachable':int(z['oracle_any_C']),
    'original_X_branch_C_reachable':int(t['oracle_any_C']),
    'new_C_from_original_X_only':int(bool(int(t['oracle_incremental_C'])) and not bool(int(z['oracle_incremental_C']))),
    'new_C_from_greedy_only':int(bool(int(z['oracle_incremental_C'])) and not bool(int(t['oracle_incremental_C']))),
    'greedy_only_any_new_optimum':int(z['oracle_any_nonA_optimum']),
    'original_X_any_new_optimum':int(t['oracle_any_nonA_optimum']),
    'greedy_min_E':int(z['min_actual_repairE']),
    'original_X_min_E':int(t['min_actual_repairE']),
    'greedy_history_selected_E':int(z['trained_history_actual_E']),
    'retained_history_selected_E':int(t['trained_history_actual_E']),
    'greedy_joint_selected_E':int(z['trained_joint_history_actual_E']),
    'retained_joint_selected_E':int(t['trained_joint_history_actual_E']),
    'greedy_history_hit_C':int(z['trained_history_hit_C']),
    'retained_history_hit_C':int(t['trained_history_hit_C']),
    'greedy_joint_hit_C':int(z['trained_joint_history_hit_C']),
    'retained_joint_hit_C':int(t['trained_joint_history_hit_C'])})
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with (out/'paired_branch_trials.tsv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');wr.writeheader();wr.writerows(rows)
 report={'exactness':'PASS: independent scorers already verified every parent, raw and repaired frame on both branches',
         'states':len(inputs),'paired_repair_branches':len(rows),'by_tier':{},'source_aware_limitations':[
           'N50 is already exposed to analysis; this branch comparison is exploratory.',
           'C-shell X was privileged generated from C and can contain target information via X.',
           'Retaining the alternative X branch changes the action interface, not simply the choice model.',
           'Oracle reachability requires all five repairs; not a costed practical online policy.',
           'Only 3 independent N50 optimum orbits; seeds conditional within shared parent triple.'
         ]}
 for tier in ('AB_blind','C_shell'):
  report['by_tier'][tier]={}
  for donor,name in [(0,'A_only'),(1,'true_B'),(2,'fake_B')]:
   z=[r for r in rows if r['mode']==tier and r['donor_method']==donor]
   failed=[r for r in z if r['direct_repair_fails_C']]
   def mean(k):return statistics.mean(r[k] for r in z)
   data={'states':len(z),'baseline_C_failures':len(failed),
        'changed_state_anchor_cases':sum(r['branch0_changes_anchor'] for r in z),
        'greedy_branch_anyC':sum(r['accepted_greedy_branch_C_reachable'] for r in z),
        'retained_X_branch_anyC':sum(r['original_X_branch_C_reachable'] for r in z),
        'retained_X_only_incremental_C':sum(r['new_C_from_original_X_only'] for r in failed),
        'greedy_only_incremental_C':sum(r['new_C_from_greedy_only'] for r in failed),
        'greedy_branch_nonA_optimum':sum(r['greedy_only_any_new_optimum'] for r in z),
        'retained_X_branch_nonA_optimum':sum(r['original_X_any_new_optimum'] for r in z),
        'mean_original_X_C_orbit_distance_for_baseline_failures':
           statistics.mean(r['raw_X_orbit_dist_to_C'] for r in failed) if failed else None,
        'mean_greedy_current_C_orbit_distance_for_baseline_failures':
           statistics.mean(r['greedy_current_dist_to_C'] for r in failed) if failed else None,
        'mean_greedy_bank_min_E':mean('greedy_min_E'),
        'mean_retained_bank_min_E':mean('original_X_min_E'),
        'mean_greedy_joint_selected_E':mean('greedy_joint_selected_E'),
        'mean_retained_joint_selected_E':mean('retained_joint_selected_E'),
        'mean_greedy_history_selected_E':mean('greedy_history_selected_E'),
        'mean_retained_history_selected_E':mean('retained_history_selected_E'),
        'retained_joint_C_hits_on_previously_failed':sum(r['retained_joint_hit_C'] for r in failed),
        'retained_history_C_hits_on_previously_failed':sum(r['retained_history_hit_C'] for r in failed)}
   report['by_tier'][tier][name]=data
 (out/'branch_causal_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
