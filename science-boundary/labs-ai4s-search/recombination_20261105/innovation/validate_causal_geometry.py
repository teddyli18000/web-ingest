#!/usr/bin/env python3
"""Independent exact direct LABS auditing and pair-clustered causal comparison.

Crossover here is a structured mutation mask; *only* the partner's spatial
disagreement mask can distinguish it from matched-radius one-parent mutation.
All LABS energies recomputed by separate Python O(N^2) loops, not C++ deltas.
"""
import argparse,collections,csv,json,pathlib
import numpy as np
NAMES={
 0:'parent_copy_common_repair',
 1:'single_parent_uniform_H_mutation',
 2:'real_second_parent_D_random_inheritance',
 3:'placebo_permuted_D_random_inheritance',
 4:'real_second_parent_D_trueE_joint_mask_hill',
 5:'placebo_permuted_D_trueE_joint_mask_hill',
 6:'single_parent_unrestricted_H_trueE_mask_hill',
 7:'single_parent_small_radius_random_2_4_8_12',
 8:'single_parent_small_radius_trueE_mask_hill',
 9:'real_second_parent_D_four_quenches',
 10:'single_parent_unrestricted_H_four_quenches'}
def load(path):
 with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def energy(t):
 s=[int(c)*2-1 for c in t]
 return sum(sum(s[i]*s[i+k] for i in range(len(s)-k))**2 for k in range(1,len(s)))
def variants(s):
 def neg(t):return ''.join('1' if c=='0' else '0' for c in t)
 def alt(t):return ''.join(neg(c) if i%2 else c for i,c in enumerate(t))
 return sorted({u for x in (s,s[::-1]) for y in (x,alt(x)) for u in (y,neg(y))})
def hd(a,b):return sum(x!=y for x,y in zip(a,b))
def bootstrap(pairvals,seed=315901):
 a=np.array(pairvals,float)
 if not len(a):return [None,None]
 rng=np.random.default_rng(seed)
 samples=a[rng.integers(len(a),size=(4000,len(a)))].mean(axis=1)
 return list(map(float,np.quantile(samples,[.025,.975])))
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--sessions',type=pathlib.Path,required=True)
 p.add_argument('--novel',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 args=p.parse_args()
 ps=load(args.parents);raw=load(args.sessions);nov=load(args.novel)
 parent={z['id']:z for z in ps}
 byN=collections.defaultdict(list)
 for z in ps:
  assert energy(z['bits'])==int(z['E']) and variants(z['bits'])[0]==z['canonical']
  byN[int(z['n'])].append(z)
 source={n:{z['canonical'] for z in a} for n,a in byN.items()}
 bestknown={n:min(int(z['best_known']) for z in a) for n,a in byN.items()}
 known_pairs=sum(len(v)*(len(v)-1)//2 for v in byN.values())
 trials=collections.defaultdict(dict)
 for x in raw:
  n=int(x['N']);arm=int(x['arm']);rep=int(x['rep'])
  assert arm in NAMES
  A=parent[x['A_id']];B=parent[x['B_id']]
  assert n==int(A['n'])==int(B['n'])
  assert int(x['AE'])==int(A['E']) and int(x['BE'])==int(B['E'])
  assert x['pair']==A['id']+'-'+B['id']
  base=parent[x['baseId']]
  assert x['baseId'] in (A['id'],B['id'])
  bestbits=x['bestBits'];prebits=x['bestPreBits'];E=int(x['bestE'])
  assert len(bestbits)==len(prebits)==n
  assert energy(bestbits)==E
  assert energy(prebits)==int(x['bestPreE'])
  assert variants(bestbits)[0]==x['bestCanon']
  d=min(hd(bestbits,t) for q in (A,B) for t in variants(q['bits']))
  assert d==int(x['bestParentDist'])
  r=int(x['r']);D=int(x['D']);Q=int(x['Q']);h=int(x['h']);H=int(x['H'])
  assert D+Q==n and h==D//2 and H==h+r
  assert r==(4 if n<=47 else 8 if n==50 else 6)
  pre_d=hd(prebits,base['bits'])
  assert pre_d==int(x['bestPreDistanceFromBase'])
  if arm==0:assert pre_d==0
  elif arm in (7,8):assert pre_d in (2,4,8,12)
  else:assert pre_d==H
  assert int(x['generations'])>0 and float(x['elapsedMs'])>=120
  assert 0<=int(x['new5'])<=int(x['new10'])<=int(x['new15'])<=int(x['new20'])<=int(x['generations'])
  assert float(x['modelMs'])+float(x['generationMs'])+float(x['repairMs'])<=float(x['elapsedMs'])+.2
  if arm in (4,5,6,8):assert int(x['proposals'])==24*int(x['generations'])
  if arm in (9,10):assert int(x['quenches'])==int(x['proposals'])==4*int(x['generations'])
  else:assert int(x['quenches'])==0
  if arm in (0,1,2,3,7):assert int(x['proposals'])==0
  key=(n,x['pair'],rep)
  assert arm not in trials[key]
  trials[key][arm]=x
 assert len({(x[0],x[1]) for x in trials})==known_pairs
 assert len(raw)==known_pairs*5*len(NAMES),len(raw)
 assert all(set(v)==set(NAMES) for v in trials.values())
 events=collections.defaultdict(list)
 globalnear=collections.defaultdict(set)
 for x in nov:
  n=int(x['N']);key=(n,x['pair'],int(x['rep']))
  arm=int(x['arm'])
  assert key in trials and arm in trials[key]
  source_row=trials[key][arm];A=parent[source_row['A_id']];B=parent[source_row['B_id']]
  base=parent[source_row['baseId']]
  e=int(x['E']);s=x['bits'];pre=x['preBits'];can=x['canonical']
  assert len(s)==len(pre)==n and energy(s)==e and energy(pre)==int(x['preE'])
  assert can==variants(s)[0] and can not in source[n]
  assert e<=bestknown[n]*1.2+1e-8
  assert int(x['parentDist'])==min(hd(s,t) for q in (A,B) for t in variants(q['bits']))
  assert hd(pre,base['bits'])==int(x['preDistanceBase'])
  events[(n,x['pair'],int(x['rep']),arm)].append((can,e))
  for cut in (5,10,15,20):
   if e<=bestknown[n]*(1+cut/100)+1e-8:globalnear[cut].add((n,can))
 for x in raw:
  n=int(x['N']);key=(n,x['pair'],int(x['rep']),int(x['arm']))
  cert=events[key]
  assert len(cert)==len({ca for ca,e in cert})
  for cut in (5,10,15,20):
   count=sum(e<=bestknown[n]*(1+cut/100)+1e-8 for ca,e in cert)
   assert count==int(x[f'new{cut}']),(key,cut,count,x[f'new{cut}'])
 out={'status':'independent direct score and all eight LABS symmetries verified',
  'source_orbits':len(ps),'source_parent_pairs':known_pairs,'sessions':len(raw),
  'new_orbit_certificate_events':len(nov),
  'globally_distinct_new_orbits_at_threshold':{str(cut):len(globalnear[cut]) for cut in (5,10,15,20)},
  'methods':NAMES,'by_length':{},'study_limits':[
   'Only actual archived high-quality source orbits are parents; single-parent perturbations are NULL controls, never independent second parents',
   'All arms share same wall-clock budget and common repaired endpoint; no modern full GPU-MTS or full optimized GOMEA',
   'Source pair/rep IDs are paired but repeated offspring from one source parent pair are not independent source lineages',
   'Each N92,99 has only one true elite pair; uncertainty there is descriptive only',
   'The true-parent disagreement geometry is the sole source of extra binary information beyond parent A and Hamming radius',
   'New library orbit is not necessarily an unprecedented historical record']}
 group=collections.defaultdict(list)
 for k,v in trials.items():group[k[0]].append((k,v))
 comparisons=[
 (2,3,'realD_random_vs_shuffledD_random'),
 (2,1,'realD_random_vs_singleparent_H_random'),
 (4,5,'realD_hill_vs_shuffledD_hill'),
 (4,6,'realD_hill_vs_singleparent_H_hill'),
 (9,10,'realD_prequench_vs_singleparent_H_prequench'),
 (4,8,'realD_hill_vs_small_radius_hill'),
 (9,7,'realD_prequench_vs_small_radius_random')]
 for n,rs in sorted(group.items()):
  result={'pairs':len({k[1] for k,v in rs}),'source_orbits':len(byN[n]),
      'paired_reps_per_arm':len(rs),'known_bestE':bestknown[n],
      'methods':{},'comparisons':{}}
  for arm,name in NAMES.items():
   t=[v[arm] for k,v in rs]
   sec=sum(float(x['elapsedMs']) for x in t)/1000
   new5=sum(int(x['new5']) for x in t)
   new10=sum(int(x['new10']) for x in t)
   result['methods'][name]={
    'mean_session_bestE':float(np.mean([int(x['bestE']) for x in t])),
    'mean_generated_initialE':float(np.mean([float(x['avg_initial_E']) for x in t])),
    'mean_postrepair_offspring_E':float(np.mean([float(x['avg_repaired_E']) for x in t])),
    'new5_orbit_events':new5,'new10_orbit_events':new10,
    'new15_orbit_events':sum(int(x['new15']) for x in t),
    'new20_orbit_events':sum(int(x['new20']) for x in t),
    'near10_events_per_full_cpu_second':new10/sec,
    'near5_events_per_full_cpu_second':new5/sec,
    'total_repaired_offspring':sum(int(x['generations']) for x in t),
    'best_session_returns_to_source_fraction':float(np.mean([x['bestCanon'] in source[n] for x in t])),
    'cost_full_seconds':sec}
  for a,b,name in comparisons:
   delta=[int(v[b]['bestE'])-int(v[a]['bestE']) for k,v in rs]
   nov=[int(v[a]['new10'])-int(v[b]['new10']) for k,v in rs]
   bypair=collections.defaultdict(list)
   for (key,arms),d in zip(rs,delta):bypair[key[1]].append(d)
   result['comparisons'][name]={
     'bestE_advantage_positive_means_realD_better':float(np.mean(delta)),
     'mean_new10_event_advantage':float(np.mean(nov)),
     'bootstrap95_by_parent_pair_NOT_independent_lineages':bootstrap(
        [float(np.mean(q)) for q in bypair.values()],seed=20261105+n*11+a*19+b),
     'wins_ties_losses':[sum(d>0 for d in delta),sum(d==0 for d in delta),sum(d<0 for d in delta)]}
  out['by_length'][str(n)]=result
 args.out.write_text(json.dumps(out,indent=2)+'\n')
 print('PASS',len(raw),'fair budget sessions,',len(nov),'independently scored novel orbit records')
 for n,v in out['by_length'].items():
  print('N',n,'pairs',v['pairs'],
   'new5',[(a,term['new5_orbit_events']) for a,term in enumerate(v['methods'].values())],
   'new10',[(a,term['new10_orbit_events']) for a,term in enumerate(v['methods'].values())],
   'realD_vs_randomD',round(v['comparisons']['realD_random_vs_shuffledD_random']['bestE_advantage_positive_means_realD_better'],3))
if __name__=='__main__':main()
