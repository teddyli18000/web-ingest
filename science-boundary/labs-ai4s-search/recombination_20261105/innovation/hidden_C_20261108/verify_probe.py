#!/usr/bin/env python3
"""Independent post hoc diagnostic of ONE C-free candidate bank per scenario.

No oracle in proposal generation or trained models. C is loaded only here.
Labels are never fed back to deploy, selection or retraining.
"""
import argparse,collections,csv,json,hashlib,pathlib,statistics
from verify_hidden import E,canon,validate_inputs,orbit_hd

def read(p):
    with open(p,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    p.add_argument('--vault',required=True);p.add_argument('--bank',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    xs,h=validate_inputs(a.input,a.vault)
    rows=read(a.bank)
    bank=collections.defaultdict(dict)
    for r in rows:
        sid=r['id'];assert sid in xs
        n=int(r['n']);assert n==int(xs[sid]['n'])
        method=int(r['donor_method']);j=int(r['j'])
        assert method in (0,1,2) and 1<=j<=5
        key=(sid,method);assert j not in bank[key]
        bank[key][j]=r
        for k,bits in [('raw_E','raw_bits'),('post_E','post_bits')]:
            assert len(r[bits])==n and E(r[bits])==int(r[k]),(sid,method,j,k)
        assert canon(r['post_bits'])==r['post_canon']
        assert E(r['baseline_post_bits'])==int(r['baseline_post_E'])
        assert E(r['starting_bits'])==int(r['starting_E'])
        assert int(r['initial_current_E'])==int(xs[sid]['EX'])
        assert sum(a!=b for a,b in zip(r['raw_bits'],r['starting_bits']))==j*2
        assert r['starting_bits']!=r['raw_bits']
        assert float(r['candidate_repair_ms'])>0
        assert r['mode']==xs[sid]['mode']
        assert int(r['damage'])==int(xs[sid]['damage'])
    assert len(rows)==15*len(xs) and len(bank)==3*len(xs)
    assert all(set(rr)==set(range(1,6)) for rr in bank.values())
    records=[];witnesses=[]
    for sid,scenario in xs.items():
        target=h[sid]['C_orbit']
        n=int(scenario['n']);opt={46:131,47:135,50:153}[n]
        for method in range(3):
            z=[bank[(sid,method)][j] for j in range(1,6)]
            assert len({r['baseline_post_bits'] for r in z})==1
            assert len({r['starting_bits'] for r in z})==1
            baseline=canon(z[0]['baseline_post_bits'])
            c_baseline=int(baseline==target)
            any_c=any(r['post_canon']==target for r in z)
            any_nonA=any(int(r['post_E'])==opt and r['post_canon']!=scenario['A_orbit'] for r in z)
            bestRaw=min(z,key=lambda v:(int(v['raw_E']),int(v['j'])))
            bestPredBase=min(z,key=lambda v:(float(v['pred_base']),int(v['j'])))
            bestPredFull=min(z,key=lambda v:(float(v['pred_full']),int(v['j'])))
            bestOracle=min(z,key=lambda v:(int(v['post_E']),int(v['j'])))
            methods={'raw_E':bestRaw,'trained_history':bestPredBase,
                     'trained_joint_history':bestPredFull,'unavailable_repair_oracle':bestOracle}
            rec={'id':sid,'n':n,'C_orbit_id':h[sid]['C_id'],'mode':scenario['mode'],
                 'rep':int(scenario['rep']),'damage':int(scenario['damage']),
                 'donor_method':method,'baseline_C':c_baseline,
                 'oracle_any_C':int(any_c),'oracle_incremental_C':int(any_c and not c_baseline),
                 'oracle_any_nonA_optimum':int(any_nonA),
                 'min_actual_repairE':min(int(v['post_E']) for v in z),
                 'best_raw_energy':int(bestRaw['raw_E']),
                 'num_distinct_repaired_orbits':len(set(v['post_canon'] for v in z)),
                 'mean_native_repair_ms':statistics.mean(float(v['candidate_repair_ms']) for v in z)}
            for name,r in methods.items():
                rec[name+'_choice']=int(r['j'])
                rec[name+'_actual_E']=int(r['post_E'])
                rec[name+'_hit_C']=int(r['post_canon']==target)
            records.append(rec)
            if any_c and not c_baseline:
                for r in z:
                    if r['post_canon']==target:
                        witnesses.append({'id':sid,'method':method,'j':int(r['j']),
                            'n':n,'mode':scenario['mode'],'C_id':h[sid]['C_id'],
                            'start_orbit_distance_to_C':orbit_hd(r['starting_bits'],h[sid]['C']),
                            'raw_orbit_distance_to_C':orbit_hd(r['raw_bits'],h[sid]['C']),
                            'post_E':int(r['post_E'])})
    assert len(records)==3*len(xs)
    out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with (out/'bank_verified_trials.tsv').open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(records[0]),delimiter='\t')
        wr.writeheader();wr.writerows(records)
    if witnesses:
        with (out/'bank_incremental_C_witnesses.tsv').open('w',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(witnesses[0]),delimiter='\t')
            wr.writeheader();wr.writerows(witnesses)
    report={'status':'PASS C-free true/fake/A donor bank scored only post hoc',
            'state_count':len(xs),'candidate_repairs':len(rows),
            'by_tier':{},'sha256':{k:hashlib.sha256(pathlib.Path(v).read_bytes()).hexdigest()
                          for k,v in [('input',a.input),('vault',a.vault),('bank',a.bank)]}}
    for tier in ('AB_blind','C_shell'):
        q=[r for r in records if r['mode']==tier]
        summary={}
        for donor,desc in [(0,'A_only'),(1,'true_B'),(2,'fake_B')]:
            z=[r for r in q if r['donor_method']==donor]
            assert len(z)==len(xs)//2
            filtered=[r for r in z if not r['baseline_C']]
            sel={}
            for name in ('raw_E','trained_history','trained_joint_history','unavailable_repair_oracle'):
                sel[name]={
                    'mean_actual_selected_E':statistics.mean(r[name+'_actual_E'] for r in z),
                    'incremental_C_recovered':sum(r[name+'_hit_C'] for r in filtered),
                    'any_C_chosen_total':sum(r[name+'_hit_C'] for r in z)}
            summary[desc]={
                'all_states':len(z),'initial_nonC':len(filtered),
                'oracle_any_C':sum(r['oracle_any_C'] for r in z),
                'oracle_incremental_C':sum(r['oracle_incremental_C'] for r in z),
                'oracle_nonA_optimum':sum(r['oracle_any_nonA_optimum'] for r in z),
                'mean_best_actual_repair_E':statistics.mean(r['min_actual_repairE'] for r in z),
                'candidate_rankers':sel}
        report['by_tier'][tier]=summary
    report['interpretation']=[
        'This is a one-step 5-proposal bank reachability diagnostic, not a deployable C-informed policy.',
        'All 3 donor branches share the same exact initial repaired X and fully charged 64-step Tabu repair semantics.',
        'The target C vault is opened only in this independent offline exact verifier.',
        'The unachievable repair oracle can use future repair scores; do not compare it as equal-cost algorithm.',
        'N50 target orbit population already exposed in first test; forced experiment is posthoc exploratory.'
    ]
    (out/'bank_reachability.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
