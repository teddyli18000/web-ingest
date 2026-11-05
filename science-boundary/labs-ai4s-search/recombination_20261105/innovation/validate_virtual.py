#!/usr/bin/env python3
"""Independent exact LABS + 8-symmetry verification of true vs virtual donor.

The only counterfactual difference is parental information. Repaired endpoints
are scored independently; archive-wide novelty is not confused with per-pair
third known-optimum restoration.
"""
import argparse,csv,collections,json,hashlib,pathlib
import numpy as np
NAMES={0:'copy_A',1:'trueB_uniform',2:'virtualB_uniform',
       3:'trueB_prequench',4:'virtualB_prequench',
       5:'trueB_exactE_coupled',6:'virtualB_exactE_coupled',
       7:'trueB_spectral_coupled',8:'virtualB_spectral_coupled',
       9:'A_only_free_mask_swap'}
PAIRS=[(1,2,'uniform'),(3,4,'prequench'),(5,6,'exact_E_coupled'),
       (7,8,'spectral_coupled'),(5,9,'trueB_vs_A_free_mask')]
def read(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def energy(s):
 x=[2*int(c)-1 for c in s];n=len(s)
 return sum(sum(x[i]*x[i+k] for i in range(n-k))**2 for k in range(1,n))
def variants(s):
 def neg(t):return ''.join('1' if q=='0' else '0' for q in t)
 def alt(t):return ''.join(q if i%2==0 else neg(q) for i,q in enumerate(t))
 return sorted({z for a in (s,s[::-1]) for b in (a,alt(a)) for z in (b,neg(b))})
def h(a,b):return sum(x!=y for x,y in zip(a,b))
def boot(v,seed=20261105):
 if not v:return [None,None]
 rng=np.random.default_rng(seed)
 x=np.asarray(v,float)
 z=x[rng.integers(len(x),size=(5000,len(x)))].mean(axis=1)
 return list(map(float,np.quantile(z,[.025,.975])))
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--sessions',type=pathlib.Path,required=True)
 p.add_argument('--novel',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args()
 parents=read(a.parents)
 ids={x['id']:x for x in parents}
 byN=collections.defaultdict(set);refs={}
 for x in parents:
  n=int(x['n'])
  assert energy(x['bits'])==int(x['E']) and variants(x['bits'])[0]==x['canonical']
  byN[n].add(x['canonical'])
  refs[n]=min(refs.get(n,100000),int(x['best_known']))
 rows=read(a.sessions);nov=read(a.novel)
 groups=collections.defaultdict(dict)
 for r in rows:
  n=int(r['N']);arm=int(r['arm']);seed=int(r['rep'])
  assert arm in NAMES
  A=ids[r['A_id']];B=ids[r['B_id']]
  assert r['pair']==A['id']+'-'+B['id']
  assert int(A['n'])==int(B['n'])==n and int(r['AE'])==int(A['E']) and int(r['BE'])==int(B['E'])
  assert len(r['bestBits'])==n and energy(r['bestBits'])==int(r['bestE'])
  assert variants(r['bestBits'])[0]==r['bestCanon']
  dist=min(h(r['bestBits'],v) for z in [A,B] for v in variants(z['bits']))
  assert int(r['bestDistSource'])==dist
  d=min(h(A['bits'],z) for z in variants(B['bits']))
  assert int(r['D'])==d and int(r['m'])==d//2+(4 if n<=47 else 8 if n==50 else 6)
  assert int(r['generation_count'])>0
  assert float(r['elapsed_ms'])>=120
  assert float(r['generation_ms'])+float(r['repair_ms'])<=float(r['elapsed_ms'])+.001
  assert int(r['new5'])<=int(r['new10'])<=int(r['new15'])<=int(r['new20'])<=int(r['generation_count'])
  gen=int(r['generation_count'])
  assert int(r['proposals'])==({0:0,3:4,4:4}.get(arm,24))*gen
  assert int(r['prequench_calls'])==(4*gen if arm in (3,4) else 0)
  key=(n,r['pair'],seed)
  assert arm not in groups[key]
  groups[key][arm]=r
 assert all(set(z)==set(NAMES) for z in groups.values())
 seen=collections.defaultdict(list)
 for z in nov:
  n=int(z['N']);key=(n,z['pair'],int(z['rep']));arm=int(z['arm'])
  assert key in groups and arm in groups[key]
  r=groups[key][arm];A=ids[r['A_id']];B=ids[r['B_id']]
  s=z['bits'];e=int(z['E']);can=variants(s)[0]
  assert energy(s)==e and can==z['canon'] and can not in byN[n]
  assert len(s)==n and e<=refs[n]*1.2+1e-8
  dist=min(h(s,v) for p0 in (A,B) for v in variants(p0['bits']))
  assert int(z['nearest_parent_orbit_distance'])==dist
  for val,mult in [('threshold5',1.05),('threshold10',1.10),('threshold15',1.15),('threshold20',1.20)]:
   assert int(z[val])==int(e<=refs[n]*mult+1e-8)
  seen[(n,z['pair'],int(z['rep']),arm)].append((can,e))
 for r in rows:
  n=int(r['N']);key=(n,r['pair'],int(r['rep']),int(r['arm']))
  items=seen[key]
  assert len({z[0] for z in items})==len(items)
  for name,mult in [('new5',1.05),('new10',1.1),('new15',1.15),('new20',1.2)]:
   assert int(r[name])==sum(e<=refs[n]*mult+1e-8 for ca,e in items)
 summary={'scope':'independently exact integer-scored whole 120ms repair runs; second-parent information trueB vs matched virtualB',
          'rows':len(rows),'source_seed_pair_units':len(groups),'new_20percent_child_records':len(nov),
          'methods':NAMES,'pairwise':{},'one_source_warning':'random virtual B sampled independently for each offspring and carries no true parent info',
          'limits':['Same parent-pair seeds do NOT make separate independent source lineages',
                    'Unseen source-pair testing but N46/47/50 included for mechanism',
                    'Historical small solver, not modern GPU MTS or tuned GOMEA',
                    'Outcome is source-novel, not first-ever LABS discovery or improvement of published optimum',
                    'The full source library includes historical archived parent orbits; never use third hidden optimum as generator input']}
 for n,pair in sorted({(k[0],k[1]) for k in groups}):
  sessions=[v for k,v in groups.items() if k[:2]==(n,pair)]
  res={'N':n,'pair':pair,'seed_repetitions':len(sessions),'by_arm':{},'comparisons':{}}
  for arm,name in NAMES.items():
   rr=[r[arm] for r in sessions]
   res['by_arm'][name]={
    'mean_postrepair_best_E':float(np.mean([int(z['bestE']) for z in rr])),
    'mean_all_postrepair_E':float(np.mean([float(z['mean_all_postrepair_E']) for z in rr])),
    'best_E':min(int(z['bestE']) for z in rr),
    'near5_events':sum(int(z['new5']) for z in rr),'near10_events':sum(int(z['new10']) for z in rr),
    'near20_events':sum(int(z['new20']) for z in rr),
    'distinct_new_near10_orbits':len({ca for seed in sessions for ca,e in seen[(n,pair,int(seed[0]['rep']),arm)] if e<=1.1*refs[n]+1e-8}),
    'new_near10_sessions':sum(int(z['new10'])>0 for z in rr),
    'source_orbit_best_frac':float(np.mean([z['bestCanon'] in byN[n] for z in rr])),
    'repaired_total':sum(int(z['generation_count']) for z in rr)}
  for tr,vl,name in PAIRS:
   improvement=[int(ss[vl]['bestE'])-int(ss[tr]['bestE']) for ss in sessions]
   novelty=[int(ss[tr]['new10'])-int(ss[vl]['new10']) for ss in sessions]
   res['comparisons'][name]={'trueB_best_E_gain_over_virtualB':float(np.mean(improvement)),
      'CI95_seed_bootstrap_NOT_source_independent':boot(improvement,seed=20261105+n+tr),
      'mean_near10_event_gain':float(np.mean(novelty)),
      'win_tie_loss':[sum(x>0 for x in improvement),sum(x==0 for x in improvement),sum(x<0 for x in improvement)]}
  summary['pairwise'][pair]=res
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(summary,indent=2)+'\n')
 print('PASS',len(rows),'full source-pair costed treatments',len(nov),'independently exact-verified novel child records')
 for p,v in summary['pairwise'].items():
  print(p,'n',v['N'],'true-vs-virtual E gain',
        {k:round(z['trueB_best_E_gain_over_virtualB'],2) for k,z in v['comparisons'].items()},
        'new10',{k:z['near10_events'] for k,z in v['by_arm'].items()})
if __name__=='__main__':main()
