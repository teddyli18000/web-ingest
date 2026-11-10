#!/usr/bin/env python3
"""Post-hoc exact source-orbit C recovery causal witness audit.

Reads C after C-blind search already ended and full event logs were archived.
Cannot influence action generation or models.
"""
import argparse,csv,gzip,json,hashlib,pathlib,collections,statistics
from verify_hidden import validate_inputs, E, canon, orbit_hd

def scan(file,scenarios,vault,label):
    out={}; hit_count=collections.Counter()
    with gzip.open(file,'rt',newline='') as f:
        rdr=csv.DictReader(f,delimiter='\t')
        assert 'proposal_origin_bits' in rdr.fieldnames
        for q in rdr:
            sid=q['id'];arm=int(q['arm']);z=(sid,arm)
            assert sid in scenarios
            if z not in out:
                out[z]={'initial_C':False,'first_C':None,'first_B':None,'initial_E':None,'nEvents':0}
            d=out[z];d['nEvents']+=1
            it=int(q['iteration'])
            current=q['postCanon'];target=vault[sid]['C_orbit']
            assert int(q['n'])==int(scenarios[sid]['n'])
            assert E(q['postBits'])==int(q['postE'])
            assert canon(q['postBits'])==current
            if it==0:
                assert d['nEvents']==1 and q['proposal_origin_bits']==scenarios[sid]['X']
                d['initial_E']=int(q['postE'])
                d['initial_C']=current==target
            if current==target and d['first_C'] is None:
                origin=q['proposal_origin_bits']
                assert E(origin)==int(q['proposal_origin_E'])
                raw=q['rawBits'];assert E(raw)==int(q['rawE'])
                d['first_C']={'iteration':it,'time_ms':float(q['t_ms']),
                    'from_original_X':origin==scenarios[sid]['X'],
                    'origin_E':int(q['proposal_origin_E']),
                    'origin_to_C_orbit_dist':orbit_hd(origin,vault[sid]['C']),
                    'raw_to_C_orbit_dist':orbit_hd(raw,vault[sid]['C']),
                    'X_to_C_dist':int(vault[sid]['dC']),
                    'A_to_C_orbit_dist':orbit_hd(scenarios[sid]['A'],vault[sid]['C']),
                    'B_to_C_orbit_dist':orbit_hd(scenarios[sid]['B'],vault[sid]['C']),
                    'postE':int(q['postE']),
                    'source_C_orbit':vault[sid]['C_id'],
                    'damage':int(scenarios[sid]['damage']),
                    'mode':scenarios[sid]['mode'],'arm':arm,'sid':sid,
                    'selected_rawE':int(q['rawE']),
                    'start_orbit_dist_to_B':orbit_hd(origin,scenarios[sid]['B'])}
            if current==scenarios[sid]['B_orbit'] and d['first_B'] is None:
                d['first_B']={'iteration':it,'time_ms':float(q['t_ms'])}
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True);p.add_argument('--vault',required=True)
    p.add_argument('--control',required=True);p.add_argument('--retained',required=True)
    p.add_argument('--out',required=True)
    a=p.parse_args();xs,h=validate_inputs(a.input,a.vault)
    c=scan(a.control,xs,h,'control');r=scan(a.retained,xs,h,'retained')
    assert set(c)==set(r)=={(sid,arm) for sid in xs for arm in range(6)}
    all_witness=[]
    groups=collections.defaultdict(list)
    for key in sorted(c):
        ctrl=c[key];keep=r[key];sid,arm=key
        assert ctrl['initial_C']==keep['initial_C']
        for method,o in (('control',ctrl),('retained_X',keep)):
            if o['first_C'] and not o['initial_C']:
                zz=dict(method=method,**o['first_C'])
                all_witness.append(zz)
                groups[(zz['mode'],zz['arm'],method)].append(zz)
    info={'states':len(xs),'source_N':sorted({int(v['n']) for v in xs.values()}),
          'pair_arm_runs':len(c),'events_control':sum(q['nEvents'] for q in c.values()),
          'events_retained':sum(q['nEvents'] for q in r.values()),
          'additional_C_hits_by_tier_arm':{},'AB_blind_post_first_witnesses':[],
          'sha256':{'control':hashlib.sha256(pathlib.Path(a.control).read_bytes()).hexdigest(),
                     'retained':hashlib.sha256(pathlib.Path(a.retained).read_bytes()).hexdigest()},
          'note':'All C labels used exclusively in offline forensic audit after both costed C-blind searches completed.'}
    for mode in ('AB_blind','C_shell'):
        info['additional_C_hits_by_tier_arm'][mode]={}
        for arm in range(6):
            zc=groups[(mode,arm,'control')];zr=groups[(mode,arm,'retained_X')]
            info['additional_C_hits_by_tier_arm'][mode][str(arm)]={
                'control_success':len(zc),'retained_success':len(zr),
                'retained_first_C_from_original_X':sum(v['from_original_X'] for v in zr),
                'retained_first_C_from_updated_incumbent':sum(not v['from_original_X'] for v in zr),
                'retained_median_first_C_time_ms':statistics.median([v['time_ms'] for v in zr]) if zr else None,
                'target_orbit_ids':sorted({v['source_C_orbit'] for v in zr}),
                'retained_by_damage':{str(d):sum(v['damage']==d for v in zr) for d in (4,8,12)}
            }
            if mode=='AB_blind':info['AB_blind_post_first_witnesses']+=zr
    output=pathlib.Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))
if __name__=='__main__':main()
