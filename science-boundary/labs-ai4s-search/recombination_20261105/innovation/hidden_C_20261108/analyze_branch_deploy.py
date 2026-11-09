#!/usr/bin/env python3
"""Source-paired actually costed search: greedy single trajectory vs retained X.

This is EXPLORATORY after exposing N50 optimum population (not a new heldout
test). C vault loaded only after both separate 150ms campaigns finish.
"""
import argparse,csv,gzip,json,pathlib,collections,statistics,hashlib
from verify_hidden import validate_inputs
def csvread(p):
    with open(p,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def scan(path,scenarios,vault):
    state=collections.defaultdict(lambda:{'B_hits':0,'C_hits':0,'A_hits':0,
            'first_C_iteration':None,'first_B_iteration':None})
    with gzip.open(path,'rt',newline='') as f:
        reader=csv.DictReader(f,delimiter='\t')
        assert 'proposal_origin_bits' in reader.fieldnames
        for z in reader:
            key=(z['id'],int(z['arm']))
            q=state[key];bits=z['postCanon'];n=int(z['n'])
            assert n==50
            if bits==scenarios[z['id']]['A_orbit']:q['A_hits']+=1
            if bits==scenarios[z['id']]['B_orbit']:
                q['B_hits']+=1
                if q['first_B_iteration'] is None:q['first_B_iteration']=int(z['iteration'])
            if bits==vault[z['id']]['C_orbit']:
                q['C_hits']+=1
                if q['first_C_iteration'] is None:q['first_C_iteration']=int(z['iteration'])
    return state
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    p.add_argument('--vault',required=True)
    p.add_argument('--control',required=True);p.add_argument('--retained',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    scenarios,hidden=validate_inputs(a.input,a.vault)
    raw={}; scanres={}
    for method,root in [('control',pathlib.Path(a.control)),('retained_X',pathlib.Path(a.retained))]:
        rr=csvread(root/'verified_trials.tsv')
        assert len(rr)==len(scenarios)*6
        raw[method]={(z['id'],int(z['arm'])):z for z in rr}
        scanres[method]=scan(root/'events.tsv.gz',scenarios,hidden)
        assert set(raw[method])==set(scanres[method])
    keys=sorted(raw['control'])
    assert keys==sorted(raw['retained_X'])
    samples=[];summary={}
    for sid,arm in keys:
        ctrl=raw['control'][(sid,arm)]
        keep=raw['retained_X'][(sid,arm)]
        h=hidden[sid];x=scenarios[sid]
        for z in (ctrl,keep):
            assert z['mode']==x['mode']
        c=scanres['control'][(sid,arm)]
        r=scanres['retained_X'][(sid,arm)]
        assert int(ctrl['initial_direct_repair_C'])==int(keep['initial_direct_repair_C'])
        baseline=int(ctrl['initial_direct_repair_C'])
        samples.append(dict(id=sid,mode=x['mode'],arm=arm,damage=int(x['damage']),
           C_orbit_id=h['C_id'],rep=int(x['rep']),
           baseline_C=baseline,
           control_C=int(c['C_hits']>0),retained_C=int(r['C_hits']>0),
           control_incremental_C=int(c['C_hits']>0 and not baseline),
           retained_incremental_C=int(r['C_hits']>0 and not baseline),
           control_B=int(c['B_hits']>0),retained_B=int(r['B_hits']>0),
           control_best_E=int(ctrl['bestE']),retained_best_E=int(keep['bestE']),
           control_best_nonA_E=int(ctrl['bestNonA_E']),retained_best_nonA_E=int(keep['bestNonA_E']),
           control_repair_calls=int(ctrl['repaired_calls']),retained_repair_calls=int(keep['repaired_calls']),
           control_model_ms=float(ctrl['model_ms']),retained_model_ms=float(keep['model_ms']),
           control_wall_ms=float(ctrl['wall_ms']),retained_wall_ms=float(keep['wall_ms'])))
    out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with (out/'retention_paired_trials.tsv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(samples[0]),delimiter='\t')
        writer.writeheader();writer.writerows(samples)
    for tier in ('AB_blind','C_shell'):
        summary[tier]={}
        for arm in range(6):
            sub=[z for z in samples if z['mode']==tier and z['arm']==arm]
            assert len(sub)==72
            source_groups={c:[z for z in sub if z['C_orbit_id']==c] for c in set(z['C_orbit_id'] for z in sub)}
            summary[tier][str(arm)]={'cases':len(sub),'source_C_orbit_groups':len(source_groups),
              'baseline_C':sum(z['baseline_C'] for z in sub),
              'control_incremental_C':sum(z['control_incremental_C'] for z in sub),
              'retained_incremental_C':sum(z['retained_incremental_C'] for z in sub),
              'control_B':sum(z['control_B'] for z in sub),
              'retained_B':sum(z['retained_B'] for z in sub),
              'mean_control_best_E':statistics.mean(z['control_best_E'] for z in sub),
              'mean_retained_best_E':statistics.mean(z['retained_best_E'] for z in sub),
              'control_mean_repairs':statistics.mean(z['control_repair_calls'] for z in sub),
              'retained_mean_repairs':statistics.mean(z['retained_repair_calls'] for z in sub),
              'control_wall_ms':statistics.mean(z['control_wall_ms'] for z in sub),
              'retained_wall_ms':statistics.mean(z['retained_wall_ms'] for z in sub),
              'retained_C_wins_vs_control':sum(z['retained_incremental_C']>z['control_incremental_C'] for z in sub),
              'retained_C_losses_vs_control':sum(z['retained_incremental_C']<z['control_incremental_C'] for z in sub),
              'by_C_orbit':{k:{
                'n':len(g),
                'control_incremental_C':sum(z['control_incremental_C'] for z in g),
                'retained_incremental_C':sum(z['retained_incremental_C'] for z in g),
                'mean_best_E_gain_control_minus_retained':
                    statistics.mean(z['control_best_E']-z['retained_best_E'] for z in g)}
                for k,g in source_groups.items()},
              'by_damage':{str(d):{
                'n':sum(z['damage']==d for z in sub),
                'control_incremental_C':sum(z['control_incremental_C'] for z in sub if z['damage']==d),
                'retained_incremental_C':sum(z['retained_incremental_C'] for z in sub if z['damage']==d)}
                 for d in (4,8,12)}}
    report={'status':'PASS two costed source-identical N50 150ms deployments, all pre/post repaired events independently exact scored',
       'N':50,'states':len(scenarios),'paired_arm_runs':len(samples),
       'outcomes':summary,
       'sha256':{'control_verified_trials':hashlib.sha256((pathlib.Path(a.control)/'verified_trials.tsv').read_bytes()).hexdigest(),
                 'retained_verified_trials':hashlib.sha256((pathlib.Path(a.retained)/'verified_trials.tsv').read_bytes()).hexdigest()},
       'qualifications':[
         'This posthoc changed representation reuses N50 optimum orbits which were already exposed in earlier tests.',
         'X is generated from privileged C in C_shell; only AB_blind serves source-blind search.',
         'Same identical X and first direct repaired outcome, same model SHA and same total 150ms wall cap per arm.',
         'Counterfactual donor mask proposal enumeration was performed in separate retrospective bank experiments and is not a cost-free online oracle.',
         'Only three independent optimum orbit IDs at N50; 72 state seeds per tier are not 72 independent target structures.'
       ]}
    (out/'retention_search_verdict.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
