#!/usr/bin/env python3
"""Independent post-search exact scorer for paper-inspired isolated 4-spin LABS.

The C target and whole source registry are accessible ONLY after all costed
C-blind ISO search sessions are complete. Every emitted record and final
certificate is independently exact-scored and canonicalized.
"""
import argparse, collections, csv, hashlib, json, math, pathlib, statistics
from verify_hidden import validate_inputs, E, canon, orbit_hd

OPT={46:131,47:135,50:153}
def read(p):
    with open(p,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def report(inputs,vault,parents,events,sessions,output):
    x,h=validate_inputs(inputs,vault)
    nset={int(z['n']) for z in x.values()};assert len(nset)==1
    n=nset.pop();known=collections.defaultdict(set)
    for r in read(parents):
        N=int(r['n'])
        if N not in OPT:continue
        if N==n:
            assert E(r['bits'])==int(r['E'])
            assert canon(r['bits'])==r['canonical']
            known[n].add(r['canonical'])
    assert len(known[n])=={46:3,47:6,50:4}[n]
    ev=read(events);ss=read(sessions);assert len(ss)==len(x)*6
    groups=collections.defaultdict(list)
    for row in ev:
        sid=row['id'];assert sid in x
        assert int(row['n'])==n and int(row['damage'])==int(x[sid]['damage'])
        assert int(row['rep'])==int(x[sid]['rep']) and row['mode']==x[sid]['mode']
        arm=int(row['arm']);assert 0<=arm<6
        word=row['bits'];assert len(word)==n and E(word)==int(row['E'])
        assert row['canonical']==canon(word)
        assert float(row['t_ms'])>=0
        assert int(row['near10_novel']) in (0,1)
        groups[(sid,arm)].append(row)
    assert set(groups)=={(sid,arm) for sid in x for arm in range(6)}
    trial=[];full_index={}
    for r in ss:
        key=(r['id'],int(r['arm']))
        assert key in groups and key not in full_index
        sid,arm=key
        assert int(r['n'])==n and r['mode']==x[sid]['mode']
        assert int(r['rep'])==int(x[sid]['rep']) and int(r['damage'])==int(x[sid]['damage'])
        assert int(r['budget_ms'])==150 and float(r['wall_ms'])>=150
        assert int(r['global_energy_evaluations'])>=0
        assert int(r['subsystem_proposals'])>=0
        assert int(r['kicks'])>=0 and int(r['restarts'])>=0
        assert int(r['steps'])>0
        assert int(r['bestE'])>=OPT[n]
        assert E(r['bestBits'])==int(r['bestE'])
        assert canon(r['bestBits'])==r['bestCanon']
        if int(r['bestNonAB_E'])>=0:
            assert E(r['bestNonAB_Bits'])==int(r['bestNonAB_E'])
            assert canon(r['bestNonAB_Bits'])==r['bestNonAB_Canon']
            assert r['bestNonAB_Canon'] not in (x[sid]['A_orbit'],x[sid]['B_orbit'])
        else:assert r['bestNonAB_Bits']==r['bestNonAB_Canon']==''
        if arm in (0,1,2):assert int(r['global_energy_evaluations'])<=2*int(r['subsystem_proposals'])
        first=groups[key][0]
        assert first['kind']=='initial_repair' and int(first['iteration'])==0
        assert int(first['E'])==int(r['first_repair_E'])
        assert all(int(row['iteration'])>=int(first['iteration']) for row in groups[key])
        assert all(float(q['t_ms'])<=float(v['t_ms']) for q,v in zip(groups[key],groups[key][1:]))
        assert min(int(row['E']) for row in groups[key])==int(r['bestE'])
        if int(r['bestNonAB_E'])>=0:
            assert min(int(v['E']) for v in groups[key] if v['canonical'] not in (x[sid]['A_orbit'],x[sid]['B_orbit']))==int(r['bestNonAB_E'])
        seen={x[sid]['A_orbit'],x[sid]['B_orbit']}
        source5=set();source10=set();global5=set();global10=set()
        novel5=set();novel10=set();seenInitial=set()
        first_C=False;any_C=False;any_B=False;any_non_AB_opt=False
        after_C=False;all_non_AB=set()
        for row in groups[key]:
            orbit=row['canonical'];score=int(row['E']);it=int(row['iteration'])
            new=score<=math.floor(OPT[n]*1.1) and orbit not in seen
            assert int(row['near10_novel'])==int(new),(key,row['iteration'])
            if new:seen.add(orbit)
            if orbit==h[sid]['C_orbit']:
                any_C=True
                if it==0:first_C=True
                else:after_C=True
            if orbit==x[sid]['B_orbit']:any_B=True
            if score==OPT[n] and orbit not in (x[sid]['A_orbit'],x[sid]['B_orbit']):
                any_non_AB_opt=True
            if orbit in (x[sid]['A_orbit'],x[sid]['B_orbit']):continue
            if score<=math.floor(OPT[n]*1.1):
                if it==0:seenInitial.add(orbit)
                if it>0:
                    source10.add(orbit);all_non_AB.add(orbit)
                    if score<=math.floor(OPT[n]*1.05):source5.add(orbit)
                    if orbit not in known[n]:
                        global10.add(orbit)
                        if score<=math.floor(OPT[n]*1.05):global5.add(orbit)
                    if min(orbit_hd(word,x[sid]['A']) for word in [row['bits']])>=math.ceil(n/5) and orbit_hd(row['bits'],x[sid]['B'])>=math.ceil(n/5):
                        novel10.add(orbit)
                        if score<=math.floor(OPT[n]*1.05):novel5.add(orbit)
        # Initial successes are shared across all six isolated methods.
        inc_C=int(any_C and not first_C)
        assert int(r['dynamic_new_near10'])==sum(int(q['near10_novel']) for q in groups[key] if q['canonical'] not in (x[sid]['A_orbit'],x[sid]['B_orbit']))
        assert int(r['initial_near10'])==sum(int(q['near10_novel']) for q in groups[key] if int(q['iteration'])==0 and q['canonical'] not in (x[sid]['A_orbit'],x[sid]['B_orbit']))
        trial.append({'id':sid,'N':n,'mode':x[sid]['mode'],'damage':int(x[sid]['damage']),
                      'rep':int(x[sid]['rep']),'C_id':h[sid]['C_id'],'arm':arm,
                      'first_C':int(first_C),'C_any':int(any_C),'C_incremental':inc_C,
                      'B_any':int(any_B),'any_other_optimum':int(any_non_AB_opt),
                      'near5_other_post':int(bool(source5-seenInitial)),
                      'near10_other_post':int(bool(source10-seenInitial)),
                      'corpus_new5_post':int(bool(global5)),
                      'corpus_new10_post':int(bool(global10)),
                      'diverse5_post':int(bool(novel5)),
                      'diverse10_post':int(bool(novel10)),
                      'num_corpus_new10_orbits':len(global10),
                      'num_nonparent_near10_orbits':len(source10),
                      'bestE':int(r['bestE']),
                      'bestNonAB_E':int(r['bestNonAB_E']),
                      'subsystems':int(r['subsystem_proposals']),
                      'full_E_calls':int(r['global_energy_evaluations']),
                      'kicks':int(r['kicks']),'restarts':int(r['restarts']),
                      'wall_ms':float(r['wall_ms'])})
        full_index[key]=r
    assert len(trial)==len(x)*6
    for sid in x:
        initial={groups[(sid,arm)][0]['bits'] for arm in range(6)}
        assert len(initial)==1
    out=pathlib.Path(output);out.mkdir(parents=True,exist_ok=True)
    with (out/'verified_scenario_treatments.tsv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(trial[0]),delimiter='\t')
        writer.writeheader();writer.writerows(trial)
    result={'status':'PASS: independent XOR-popcount exact E and full 8-fold orbit for every saved change and session result',
            'n':n,'cases':len(x),'sessions':len(trial),'record_events':len(ev),
            'method_arms':{
             '0':'KD80 starting from common repaired incumbent',
             '1':'KD80 from original X',
             '2':'KD80 from original X; stalls reset to X instead of accepting isolated kick',
             '3':'MS90/Y50 tracked choose from common repaired incumbent',
             '4':'MS90/Y50 tracked choose from original X',
             '5':'MS90/Y50 tracked choose from original X; stalls reset to X instead of kick'
            },
            'known_corpus_orbits_at_length':len(known[n]),
            'by_tier':{},'hashes':{'input':sha(inputs),'target_vault':sha(vault),'events':sha(events),'summary':sha(sessions)},
            'critical':'Exact paper-inspired small-subsystem method, not authors code or their time-to-solution scaling. C-shell is privileged denoising. N46 and N47 orbits already seen during model design; N50 orbit exposed after first sealed experiment.'}
    for mode in ('AB_blind','C_shell'):
        result['by_tier'][mode]={}
        for arm in range(6):
            w=[z for z in trial if z['mode']==mode and z['arm']==arm]
            assert len(w)==len(x)//2
            result['by_tier'][mode][str(arm)]={
                'n':len(w),'first_C_shared':sum(z['first_C'] for z in w),
                'C_incremental':sum(z['C_incremental'] for z in w),
                'B_recovered':sum(z['B_any'] for z in w),
                'other_optimum':sum(z['any_other_optimum'] for z in w),
                'near5_post':sum(z['near5_other_post'] for z in w),
                'near10_post':sum(z['near10_other_post'] for z in w),
                'corpus_new5_post':sum(z['corpus_new5_post'] for z in w),
                'corpus_new10_post':sum(z['corpus_new10_post'] for z in w),
                'diverse10_post':sum(z['diverse10_post'] for z in w),
                'mean_best_E':statistics.mean(z['bestE'] for z in w),
                'mean_subsystems':statistics.mean(z['subsystems'] for z in w),
                'mean_full_E_calls':statistics.mean(z['full_E_calls'] for z in w),
                'median_wall_ms':statistics.median(z['wall_ms'] for z in w),
                'by_target_orbit':{c:{
                    'states':sum(z['C_id']==c for z in w),
                    'C_incremental':sum(z['C_incremental'] for z in w if z['C_id']==c),
                    'corpus_new10_post':sum(z['corpus_new10_post'] for z in w if z['C_id']==c)}
                    for c in sorted({z['C_id'] for z in w})}
            }
    (out/'four_spin_verified.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'n':n,'cases':len(x),'sessions':len(trial),
       'by_tier':{tier:{arm:{k:v[k] for k in ('C_incremental','corpus_new5_post','corpus_new10_post','mean_best_E')}
                             for arm,v in arms.items()} for tier,arms in result['by_tier'].items()}},indent=2))
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True);p.add_argument('--vault',required=True)
    p.add_argument('--parents',required=True);p.add_argument('--events',required=True)
    p.add_argument('--sessions',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    report(a.input,a.vault,a.parents,a.events,a.sessions,a.output)
if __name__=='__main__':main()
