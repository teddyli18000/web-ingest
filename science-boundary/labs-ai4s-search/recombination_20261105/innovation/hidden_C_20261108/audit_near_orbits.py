#!/usr/bin/env python3
"""Independent exact quality/diversity reanalysis of C-blind full search archives.

Only called after all frozen sources and target C vaults exist; never feeds a
C target, a parent library orbit or a label back to the solver/model.
"""
import argparse,csv,gzip,json,hashlib,pathlib,collections,statistics,math
from verify_hidden import E,canon,orbit_hd,validate_inputs

def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for x in iter(lambda:f.read(1<<20),b''):h.update(x)
    return h.hexdigest()

def read(p):
    with open(p,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def score_archive(name,path,scenarios,all_known):
    states={}
    counters=collections.Counter()
    for sid in scenarios:
        for arm in range(6):
            states[(sid,arm)]={'all5':set(),'all10':set(),'after5':set(),'after10':set(),
              'all_global5':set(),'all_global10':set(),'after_global5':set(),
              'after_global10':set(),'all_diverse5':set(),'all_diverse10':set(),
              'after_diverse5':set(),'after_diverse10':set(),
              'initial5':set(),'initial10':set(),'first5ms':None,'first10ms':None,
              'best_other_E':None,'full_repairs':0,'min_other_certificate':None}
    with gzip.open(path,'rt',newline='') as f:
        reader=csv.DictReader(f,delimiter='\t')
        assert all(z in reader.fieldnames for z in ('id','arm','postE','postBits','postCanon','iteration','t_ms','rawE','rawBits'))
        for z in reader:
            sid=z['id'];arm=int(z['arm']);sc=scenarios[sid];key=(sid,arm)
            a=states[key];a['full_repairs']+=1
            n=int(sc['n']);e=int(z['postE']);co=z['postCanon'];it=int(z['iteration'])
            assert int(z['n'])==n
            if it==0:assert a['full_repairs']==1
            else:assert it==a['full_repairs']-1
            if co in (sc['A_orbit'],sc['B_orbit']):continue
            if a['best_other_E'] is None or e<a['best_other_E']:
                a['best_other_E']=e
                a['min_other_certificate']={'E':e,'bits':z['postBits'],'orbit':co}
            opt={46:131,47:135,50:153}[n]
            if e>math.floor(1.10*opt):continue
            # Independent exact scorer of EVERY near-frontier retained child.
            assert E(z['postBits'])==e and canon(z['postBits'])==co
            # The entire frozen source registry is read ONLY in this posthoc script.
            is_global=co not in all_known[n]
            orbitdist=min(orbit_hd(z['postBits'],sc['A']),orbit_hd(z['postBits'],sc['B']))
            diverse=orbitdist>=math.ceil(n/5)
            if co not in a['all10'] and a['first10ms'] is None and it>0:
                a['first10ms']=float(z['t_ms'])
            a['all10'].add(co)
            if it>0:a['after10'].add(co)
            else:a['initial10'].add(co)
            if is_global:
                a['all_global10'].add(co)
                if it>0:a['after_global10'].add(co)
            if diverse:
                a['all_diverse10'].add(co)
                if it>0:a['after_diverse10'].add(co)
            if e<=math.floor(1.05*opt):
                if co not in a['all5'] and a['first5ms'] is None and it>0:
                    a['first5ms']=float(z['t_ms'])
                a['all5'].add(co)
                if it>0:a['after5'].add(co)
                else:a['initial5'].add(co)
                if is_global:
                    a['all_global5'].add(co)
                    if it>0:a['after_global5'].add(co)
                if diverse:
                    a['all_diverse5'].add(co)
                    if it>0:a['after_diverse5'].add(co)
    assert all(v['full_repairs']>0 for v in states.values())
    return states

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True);p.add_argument('--vault',required=True)
    p.add_argument('--parents',required=True)
    p.add_argument('--run',nargs='+',required=True,help='tag=path/to/events.tsv.gz')
    p.add_argument('--out',required=True)
    a=p.parse_args()
    scenarios,h=validate_inputs(a.input,a.vault)
    n=int(next(iter(scenarios.values()))['n'])
    assert len({int(z['n']) for z in scenarios.values()})==1 and n in (46,47,50)
    parents=read(a.parents)
    all_known=collections.defaultdict(set)
    for z in parents:
        k=int(z['n']);w=z['bits']
        assert E(w)==int(z['E']) and canon(w)==z['canonical']
        all_known[k].add(z['canonical'])
    names={};outputs={}
    for kv in a.run:
        tag,path=kv.split('=',1);assert tag not in names
        names[tag]=path
        outputs[tag]=score_archive(tag,path,scenarios,all_known)
    assert {'control','alternating_X'}.issubset(names)
    keys=set(outputs['control'])
    assert all(set(v)==keys and len(v)==len(scenarios)*6 for v in outputs.values())
    methods={}
    for tag,records in outputs.items():
        methods[tag]={}
        for mode in ('AB_blind','C_shell'):
            methods[tag][mode]={}
            for arm in range(6):
                cases=[(sid,v) for (sid,a2),v in records.items()
                       if a2==arm and scenarios[sid]['mode']==mode]
                assert len(cases)==len(scenarios)//2
                details={}
                for endpoint in ('5','10','global5','global10','diverse5','diverse10'):
                    fullfield='all'+endpoint;postfield='after'+endpoint
                    # Do not count shared baseline target as incremental.
                    filtered=[(sid,v) for sid,v in cases if not v['initial'+endpoint]]
                    if endpoint not in ('5','10'):filtered=cases
                    details[endpoint]={
                        'cases_with_any_near':sum(bool(v[fullfield]) for sid,v in cases),
                        'cases_with_new_after_first':sum(bool(v[postfield]-v['initial'+endpoint]) if endpoint in ('5','10')
                                                       else bool(v[postfield]) for sid,v in cases),
                        'unique_orbits_all_sessions':len(set().union(*(v[fullfield] for sid,v in cases))),
                        'mean_distinct_orbits_per_case':statistics.mean(len(v[fullfield]) for sid,v in cases)}
                methods[tag][mode][str(arm)]={
                    'states':len(cases),'target_source_orbits':len({h[sid]['C_id'] for sid,v in cases}),
                    'reported':details,
                    'mean_full_repairs':statistics.mean(v['full_repairs'] for sid,v in cases),
                    'mean_best_nonAB_E':statistics.mean(v['best_other_E'] for sid,v in cases if v['best_other_E'] is not None)
                                         if any(v['best_other_E'] is not None for sid,v in cases) else None}
    paired={}
    for tag in names:
        if tag=='control':continue
        paired[tag]={}
        for mode in ('AB_blind','C_shell'):
            paired[tag][mode]={}
            for arm in range(6):
                z={}
                for endpoint in ('5','10','diverse5','diverse10','global5','global10'):
                    start='all'+endpoint
                    diffs=[int(bool(outputs[tag][(sid,arm)][start]))-
                           int(bool(outputs['control'][(sid,arm)][start]))
                           for sid in scenarios if scenarios[sid]['mode']==mode]
                    z[endpoint]={'wins':diffs.count(1),'ties':diffs.count(0),'losses':diffs.count(-1)}
                paired[tag][mode][str(arm)]=z
    report={'N':n,'states':len(scenarios),'methods':list(names),
      'verified_archive_event_hashes':{name:sha(v) for name,v in names.items()},
      'complete_source_orbit_registry_count':len(all_known[n]),
      'diversity_cutoff_min_parent_orbit_hamming':math.ceil(n/5),
      'thresholds':{'near5':'E <= floor(1.05*known_optimum)',
                    'near10':'E <= floor(1.10*known_optimum)'},
      'outcomes':methods,'paired_vs_control':paired,
      'limitations':[
         'Full original events were independently exact-scored by verify_hidden.py; retained near-frontier descendants were rescored again by independent bitcount.',
         'AB_blind X uses only A/B and random seed. C_shell X was constructed from hidden C and must never be treated as genuine A/B blind discovery.',
         'Distinct near frontier symmetry orbits are only proxy for different energy basins; parent-distance cutoff excludes very near clones.',
         'Known-source registry contains C but was loaded solely after complete C-blind search.',
         'Only 3 or 6 distinct target C orbit identities per length; repeat seeds are conditionally dependent.'
      ]}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'N':n,'states':len(scenarios),'summary':
      {tag:{mode:{arm:{'near5':v['reported']['5']['cases_with_any_near'],
        'near10':v['reported']['10']['cases_with_any_near'],
        'global5':v['reported']['global5']['cases_with_any_near'],
        'global10':v['reported']['global10']['cases_with_any_near'],
        'diverse5':v['reported']['diverse5']['cases_with_any_near'],
        'diverse10':v['reported']['diverse10']['cases_with_any_near']}
        for arm,v in modes.items()} for mode,modes in tiers.items()}
        for tag,tiers in methods.items()}},indent=2))
if __name__=='__main__':main()
