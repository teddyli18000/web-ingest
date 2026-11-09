#!/usr/bin/env python3
"""Independent, AFTER-THE-FACT hidden-optimum C scoring, no C-informed search.

Critical: this verifier is the ONLY code that opens target-vault.tsv. The
C-blind native C++ solver sees scenario-input.tsv and optionally frozen models.
"""
import argparse,collections,csv,hashlib,json,pathlib,random,statistics

def rows(path):
    with open(path,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def neg(s):return ''.join('1' if x=='0' else '0' for x in s)
def alt(s):return ''.join(neg(x) if i%2 else x for i,x in enumerate(s))
def orb(s):return sorted(set(t for z in (s,s[::-1]) for t in (z,neg(z),alt(z),neg(alt(z)))))
def canon(s):return orb(s)[0]
def hd(s,t):return sum(a!=b for a,b in zip(s,t))
def orbit_hd(s,t):return min(hd(s,q) for q in orb(t))
def E(s):
    # Independent exact integer aperiodic LABS scorer using XOR/popcount, not
    # the C++ solver's delta formula. O(N) native bit_count operations.
    assert set(s)<={'0','1'} and s
    n=len(s);v=int(s,2);energy=0
    for k in range(1,n):
        mismatch=((v ^ (v>>k)) & ((1<<(n-k))-1)).bit_count()
        corr=n-k-2*mismatch
        energy+=corr*corr
    return energy
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def validate_inputs(inputs,vault):
    xs=rows(inputs);hidden=rows(vault)
    head=pathlib.Path(inputs).read_text().splitlines()[0]
    assert 'C_orbit' not in head and '\tC\t' not in head and 'C_id' not in head
    assert len(xs)==len(hidden)>0
    h={r['id']:r for r in hidden}
    assert set(h)=={r['id'] for r in xs}
    optimum={46:131,47:135,50:153}
    for row in xs:
        r=h[row['id']];n=int(row['n'])
        assert n in optimum and int(r['n'])==n
        assert len(row['A'])==len(row['B'])==len(row['X'])==len(r['C'])==n
        assert E(row['A'])==E(row['B'])==E(r['C'])==optimum[n]
        assert E(row['X'])==int(row['EX'])
        assert len({canon(row['A']),canon(row['B']),canon(r['C'])})==3
        assert canon(row['A'])==row['A_orbit'] and canon(row['B'])==row['B_orbit']
        assert canon(r['C'])==r['C_orbit']
        assert canon(row['X'])!=r['C_orbit']
        assert int(row['dA'])==orbit_hd(row['X'],row['A'])
        assert int(row['dB'])==orbit_hd(row['X'],row['B'])
        assert int(r['dC'])==orbit_hd(row['X'],r['C'])
        if row['mode']=='C_shell':assert int(r['dC'])<=int(row['damage'])
    return {r['id']:r for r in xs},h

def validate_harvest(inputs,vault,harvest,output):
    x,h=validate_inputs(inputs,vault)
    rr=rows(harvest)
    assert rr
    n=int(next(iter(x.values()))['n'])
    assert {int(r['n']) for r in rr}=={n}
    group=collections.defaultdict(dict);stats=collections.Counter()
    for r in rr:
        sid=r['id'];assert sid in x
        key=(sid,int(r['round']))
        j=int(r['proposal_index'])
        assert j not in group[key];group[key][j]=r
        assert int(r['repairSteps'])==64
        assert E(r['repairBits'])==int(r['repairE'])
        assert canon(r['repairBits'])==r['repairCanon']
        assert int(r['rawE'])>0 and int(r['currentE'])>0
        stats[(r['mode'],'examples')]+=1
        if r['repairCanon']==h[sid]['C_orbit']:stats[(r['mode'],'C_hit')]+=1
        if int(r['repairE'])==({46:131,47:135,50:153}[n]) and r['repairCanon']!=x[sid]['A_orbit']:
            stats[(r['mode'],'any_nonA_optimum')]+=1
    assert all(set(g)==set(range(6)) for g in group.values())
    assert len(set(k[0] for k in group))==len(x)
    out={'status':'PASS independently exact-scored all non-oracle harvest episodes',
         'N':n,'cases':len(x),'candidate_rows':len(rr),'banks':len(group),
         'by_tier':{mode:{k:stats[(mode,k)] for k in ('examples','C_hit','any_nonA_optimum')}
                    for mode in ('AB_blind','C_shell')},
         'sha256':{'scenario_input':sha(inputs),'oracle_vault':sha(vault),'harvest':sha(harvest)},
         'warning':'Oracle C labels computed only after harvest and not used to train either model.'}
    pathlib.Path(output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

def score_deployment(inputs,vault,events,summary,output):
    x,h=validate_inputs(inputs,vault);rr=rows(events);ss=rows(summary)
    assert rr and ss
    run_ev=collections.defaultdict(list)
    for e in rr:
        sid=e['id'];assert sid in x
        n=int(e['n']);assert int(x[sid]['n'])==n
        assert int(e['rep'])==int(x[sid]['rep']) and e['mode']==x[sid]['mode']
        assert int(e['damage'])==int(x[sid]['damage'])
        raw=e['rawBits'];post=e['postBits']
        assert len(raw)==len(post)==n
        assert E(raw)==int(e['rawE']) and E(post)==int(e['postE'])
        assert canon(post)==e['postCanon']
        if 'proposal_origin_bits' in e:
            origin=e['proposal_origin_bits']
            assert len(origin)==n and E(origin)==int(e['proposal_origin_E'])
            assert e['retention_active'] in ('0','1')
            it=int(e['iteration'])
            delta=sum(q!=z for q,z in zip(origin,raw))
            if it==0:
                assert origin==x[sid]['X'] and delta==0
            else:
                assert delta in (2,4,6,8,10),(sid,it,delta)
                if e['retention_active']=='1' and it%2==1:
                    assert origin==x[sid]['X'],(sid,it)
        run_ev[(sid,int(e['arm']))].append(e)
    assert set(run_ev)=={(sid,i) for sid in x for i in range(6)}
    run_sum={}
    for s in ss:
        key=(s['id'],int(s['arm']))
        assert key not in run_sum and key in run_ev
        seq=run_ev[key];n=int(s['n'])
        assert len(seq)==int(s['full_repair_calls'])
        assert int(s['steps'])==len(seq)-1 and int(seq[0]['iteration'])==0
        assert all(int(z['iteration'])==j for j,z in enumerate(seq))
        assert all(float(seq[j]['t_ms'])<=float(seq[j+1]['t_ms']) for j in range(len(seq)-1))
        assert float(s['wall_ms'])>=float(s['budget_ms']) or int(s['steps'])==0
        en=[int(z['postE']) for z in seq]
        assert min(en)==int(s['bestE'])
        assert E(s['bestBits'])==int(s['bestE']) and canon(s['bestBits'])==s['bestCanon']
        other=[z for z in seq if z['postCanon']!=x[s['id']]['A_orbit']]
        if other:
            assert min(int(z['postE']) for z in other)==int(s['bestNonA_E'])
            assert E(s['bestNonA_Bits'])==int(s['bestNonA_E'])
            assert canon(s['bestNonA_Bits'])==s['bestNonA_Canon']
        else:
            assert int(s['bestNonA_E'])==-1 and not s['bestNonA_Bits']
        assert sum(z['postCanon']==x[s['id']]['A_orbit'] for z in seq)==int(s['source_returns'])
        run_sum[key]=s
    assert len(run_sum)==len(x)*6
    # Important: original unperturbed X receives exact identical initial native
    # Tabu repair for every arm, independently of any parent/model.
    for sid in x:
        firsts={run_ev[(sid,a)][0]['postBits'] for a in range(6)}
        assert len(firsts)==1,(sid,firsts)
    opt={46:131,47:135,50:153}
    trial=[];hit_details=[]
    for (sid,arm),evs in run_ev.items():
        st=x[sid];vaultrow=h[sid]
        c=vaultrow['C_orbit'];a=st['A_orbit'];b=st['B_orbit'];n=int(st['n'])
        first=evs[0]
        first_hit=int(first['postCanon']==c)
        hits=[z for z in evs if z['postCanon']==c]
        otherhits=[z for z in evs if int(z['postE'])==opt[n] and z['postCanon']!=a]
        novel_orbits={z['postCanon'] for z in evs if z['postCanon'] not in (a,b,c)}
        ctime=float(hits[0]['t_ms']) if hits else None
        xdist=orbit_hd(st['X'],vaultrow['C'])
        if hits:
            firstc=hits[0]
            hit_details.append({'id':sid,'n':n,'mode':st['mode'],'arm':arm,'first_hit_t_ms':ctime,
                'C_before_orbit_distance':xdist,
                'selected_raw_to_C':orbit_hd(firstc['rawBits'],vaultrow['C']),
                'repaired_to_C':orbit_hd(firstc['postBits'],vaultrow['C']),
                'sourceA_to_C_orbit':orbit_hd(st['A'],vaultrow['C']),
                'sourceB_to_C_orbit':orbit_hd(st['B'],vaultrow['C']),
                'raw_E':int(firstc['rawE']),'repaired_E':int(firstc['postE']),
                'first_hit_iteration':int(firstc['iteration'])})
        trial.append({'id':sid,'n':n,'mode':st['mode'],'damage':int(st['damage']),
            'A_id':st['A_id'],'B_id':st['B_id'],'C_id':vaultrow['C_id'],
            'rep':int(st['rep']),'arm':arm,'startE':int(st['EX']),
            'dA':int(st['dA']),'dB':int(st['dB']),'dC':xdist,
            'initial_direct_repair_C':first_hit,
            'hit_C':int(bool(hits)),
            'incremental_C_after_initial_failure':int(bool(hits) and not first_hit),
            'hit_nonA_optimum':int(bool(otherhits)),
            'bestE':int(run_sum[(sid,arm)]['bestE']),
            'bestNonA_E':int(run_sum[(sid,arm)]['bestNonA_E']),
            'first_C_ms':ctime,'repaired_calls':int(run_sum[(sid,arm)]['full_repair_calls']),
            'wall_ms':float(run_sum[(sid,arm)]['wall_ms']),
            'model_ms':float(run_sum[(sid,arm)]['model_cost_ms']),
            'distinct_non_source_orbits':len(novel_orbits)})
    output=pathlib.Path(output);output.mkdir(parents=True,exist_ok=True)
    with (output/'verified_trials.tsv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trial[0]),delimiter='\t');w.writeheader();w.writerows(trial)
    if hit_details:
        with (output/'hidden_C_first_recovery_diagnostics.tsv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(hit_details[0]),delimiter='\t');w.writeheader();w.writerows(hit_details)
    # Explicitly do not treat 6 strategies × repeated seeds as independent optima.
    bytier={}
    for mode in ('AB_blind','C_shell'):
        pool=[r for r in trial if r['mode']==mode]
        if not pool:continue
        details={}
        for arm in range(6):
            g=[z for z in pool if z['arm']==arm]
            details[str(arm)]={'cases':len(g),
                 'C_success':sum(r['hit_C'] for r in g),
                 'nonA_optimum_success':sum(r['hit_nonA_optimum'] for r in g),
                 'initial_direct_hit_C':sum(r['initial_direct_repair_C'] for r in g),
                 'incremental_new_C_from_baseline_failure':sum(r['incremental_C_after_initial_failure'] for r in g),
                 'mean_best_nonA_E_excluding_minus1':statistics.mean([r['bestNonA_E'] for r in g if r['bestNonA_E']>=0]) if any(r['bestNonA_E']>=0 for r in g) else None,
                 'mean_full_repair_calls':statistics.mean(r['repaired_calls'] for r in g),
                 'mean_wall_ms':statistics.mean(r['wall_ms'] for r in g),
                 'distinct_C_orbit_ids':len({r['C_id'] for r in g})}
        bytier[mode]=details
    # A paired conditional C-hit difference: actual unique X is the unit, with
    # A,B,C orbit family as the source-level cluster. Strict test has only 3.
    groups=collections.defaultdict(dict)
    for r in trial:groups[(r['mode'],r['id'])][r['arm']]=r
    paired={}
    for tier in bytier:
        paired[tier]={}
        for other in (0,1,2,4,5):
            deltas=[]
            for (mode,sid),arms in groups.items():
                if mode==tier:
                    assert set(arms)==set(range(6))
                    deltas.append(arms[3]['hit_C']-arms[other]['hit_C'])
            paired[tier][f'learned_full_minus_{other}']={
                'paired_delta_C_rate':statistics.mean(deltas),'wins':sum(z>0 for z in deltas),
                'ties':sum(z==0 for z in deltas),'losses':sum(z<0 for z in deltas)}
    result={'status':'PASS independently verified every pre/post exact LABS integer E and eightfold hidden C orbit',
        'n':sorted({int(r['n']) for r in trial}),'states':len(x),'run_rows':len(ss),
        'events':len(rr),'first_hidden_C_hits':len(hit_details),
        'tier_outcomes':bytier,'paired_C_recovery':paired,
        'hashes':{'input':sha(inputs),'vault':sha(vault),
                  'events':sha(events),'sessions':sha(summary)},
        'policy_arms':{'0':'A_only_exact_energy_pool','1':'true_B_exact_energy_pool',
        '2':'fake_B_exact_energy_pool','3':'learned_history_joint_full',
        '4':'learned_energy_history_base','5':'single_ILS'},
        'critical_qualifications':[
          'C-shell X originates from hidden C and is only a privileged denoising control',
          'AB-blind X uses A and B only and is the primary cross-basin search experiment',
          'The first direct repair(X) event is identical for all policies and does not establish incremental policy merit',
          'Repeated seeds within the same C orbit are not independent optimum identities',
          'Outcome labels computed after model freeze and search; never given to candidate generator',
          'The trained model predicts postrepair E, not target C identity'
        ]}
    (output/'verdict.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='cmd',required=True)
    for mode in ('harvest','deploy'):
        q=sub.add_parser(mode)
        q.add_argument('--input',required=True);q.add_argument('--vault',required=True)
        q.add_argument('--output',required=True)
        if mode=='harvest':q.add_argument('--data',required=True)
        else:
            q.add_argument('--events',required=True)
            q.add_argument('--sessions',required=True)
    a=p.parse_args()
    if a.cmd=='harvest':validate_harvest(a.input,a.vault,a.data,a.output)
    else:score_deployment(a.input,a.vault,a.events,a.sessions,a.output)
if __name__=='__main__':main()
