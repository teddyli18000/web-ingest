#!/usr/bin/env python3
"""Independent integer-LABS scoring, symmetry-aware novelty and paired evaluation
of the *consensus innovation* action space. Final repair, not immediate E, counts.
"""
import argparse,collections,csv,json,pathlib
import numpy as np
NAMES={0:'donor_only_exactE_swap',1:'random_donor_plus_consensus',2:'donor_swap_innovations_fixed',
       3:'innovation_swap_donor_fixed',4:'alternating_independent_swaps_true_E',
       5:'joint_4bit_swaps_true_E',6:'joint_4bit_exact_spectrum_envelope',
       7:'joint_4bit_shuffled_envelope_placebo',8:'local_descent_aware_random_innovation',
       9:'source_copy_common_repair'}
def read(path):
 with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def E(s):
 n=len(s);v=[1 if c=='1' else -1 for c in s]
 return sum(sum(v[i]*v[i+k] for i in range(n-k))**2 for k in range(1,n))
def variants(s):
 def neg(t):return ''.join('1' if c=='0' else '0' for c in t)
 def alt(t):return ''.join(c if i%2==0 else ('1' if c=='0' else '0') for i,c in enumerate(t))
 return sorted({z for b in (s,s[::-1]) for t in (b,alt(b)) for z in (t,neg(t))})
def boot_cluster(vals,seed=20261105):
 vals=np.asarray(vals,float)
 if not len(vals):return None
 rng=np.random.default_rng(seed)
 B=10000
 return list(map(float,np.quantile(vals[rng.integers(len(vals),size=(B,len(vals)))].mean(axis=1),[.025,.975])))
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--sessions',type=pathlib.Path,required=True)
 p.add_argument('--certificates',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 args=p.parse_args()
 parents=read(args.parents);rows=read(args.sessions);cert=read(args.certificates)
 lookup={p['id']:p for p in parents};byN=collections.defaultdict(list)
 for p in parents:
  assert E(p['bits'])==int(p['E']) and variants(p['bits'])[0]==p['canonical']
  byN[int(p['n'])].append(p)
 corpus={n:set(p['canonical'] for p in ps) for n,ps in byN.items()}
 known={n:min(int(p['best_known']) for p in ps) for n,ps in byN.items()}
 groups=collections.defaultdict(dict)
 for r in rows:
  n=int(r['N']);a=lookup[r['A_id']];b=lookup[r['B_id']];arm=int(r['arm']);rep=int(r['rep'])
  assert n==int(a['n'])==int(b['n']) and arm in NAMES
  assert int(r['AE'])==int(a['E']) and int(r['BE'])==int(b['E'])
  assert r['pair']==a['id']+'-'+b['id']
  assert E(r['bestBits'])==int(r['bestE']) and variants(r['bestBits'])[0]==r['bestCanon']
  d=min(sum(x!=y for x,y in zip(r['bestBits'],v)) for q in (a,b) for v in variants(q['bits']))
  assert d==int(r['bestDistSource'])
  assert int(r['generation_count'])>=1
  assert float(r['elapsed_ms'])>=100
  assert (int(r['new5'])<=int(r['new10'])<=int(r['new15'])<=int(r['new20'])<=int(r['generation_count']))
  assert float(r['model_ms'])+float(r['generation_ms'])+float(r['repair_ms'])<=float(r['elapsed_ms'])+.01
  expectedR=4 if n<=47 else 8 if n==50 else 6
  assert int(r['consensus_r'])==expectedR
  assert int(r['D'])+int(r['Q'])==n and int(r['Q'])>=expectedR
  if arm not in (8,9):assert int(r['proposals'])==24*int(r['generation_count'])
  if arm==8:assert int(r['prequench_calls'])==4*int(r['generation_count'])
  else:assert int(r['prequench_calls'])==0
  key=(n,r['pair'],rep)
  assert arm not in groups[key]
  groups[key][arm]=r
 assert all(set(v)==set(NAMES) for v in groups.values())
 expected_pairs=sum(len(g)*(len(g)-1)//2 for g in byN.values())
 assert len({(key[0],key[1]) for key in groups})==expected_pairs
 saved=collections.defaultdict(list)
 for row in cert:
  n=int(row['N']);pair=row['pair'];rep=int(row['rep']);arm=int(row['arm'])
  assert (n,pair,rep) in groups and arm in groups[(n,pair,rep)]
  r=groups[(n,pair,rep)][arm];a=lookup[r['A_id']];b=lookup[r['B_id']]
  s=row['bits'];e=int(row['E']);can=variants(s)[0]
  assert len(s)==n and E(s)==e and can==row['canon'] and can not in corpus[n]
  assert e<=known[n]*1.2+1e-8
  d=min(sum(x!=y for x,y in zip(s,z)) for x in (a,b) for z in variants(x['bits']))
  assert int(row['nearest_parent_orbit_distance'])==d
  for key,threshold in [('threshold5',1.05),('threshold10',1.10),('threshold15',1.15),('threshold20',1.20)]:
   assert int(row[key])==int(e<=known[n]*threshold+1e-8)
  saved[(n,pair,rep,arm)].append((can,e))
 for r in rows:
  n=int(r['N']);i=(n,r['pair'],int(r['rep']),int(r['arm']))
  z=saved[i];assert len({c for c,e in z})==len(z)
  for name,threshold in [('new5',1.05),('new10',1.10),('new15',1.15),('new20',1.20)]:
   count=sum(e<=known[n]*threshold+1e-8 for c,e in z)
   assert count==int(r[name]),(i,name,count,r[name])
 summary={'status':'exact-verified','sessions':len(rows),'source_pairs':expected_pairs,
   'source_orbits':len(parents),'new_certificate_rows':len(cert),
   'method_mapping':NAMES,'strata':{},
   'warnings':['Parent-pair replications share source orbits and are not independent parent families',
   'N92/99 each have only one source-elite pair; no cross-source inferential claim',
   'Modern published GPU MTS and full GOMEA not directly benchmarked',
   'Source library defines an orbit, not guaranteed first discovery',
   'Consensus innovation is a classical exact score method, no neural architecture is tested']}
 byStrata=collections.defaultdict(list)
 for key,v in groups.items():byStrata[key[0]].append((key,v))
 for n,arr in sorted(byStrata.items()):
  x={'parent_orbits':len(byN[n]),'pairs':len({key[1] for key,v in arr}),
     'source_reference_E':known[n],'per_arm':{},'paired':{}}
  for arm,name in NAMES.items():
   v=[z[arm] for key,z in arr]
   sec=np.array([float(a['elapsed_ms']) for a in v])/1000
   ne=np.array([int(a['new10']) for a in v])
   x['per_arm'][name]={'avg_session_best_E':float(np.mean([int(a['bestE']) for a in v])),
    'avg_all_repaired_E':float(np.mean([float(a['mean_all_postrepair_E']) for a in v])),
    'best_observed_E':min(int(a['bestE']) for a in v),
    'new_within5_events':sum(int(a['new5']) for a in v),
    'new_within10_events':int(ne.sum()),
    'new_within15_events':sum(int(a['new15']) for a in v),
    'new_within20_events':sum(int(a['new20']) for a in v),
    'source_parent_best_frac':float(np.mean([a['bestCanon'] in corpus[n] for a in v])),
    'sessions_with_novel10':int(np.sum(ne>0)),
    'source_pair_third_best_count':sum(a['bestCanon'] in corpus[n] and a['bestCanon'] not in
      (lookup[a['A_id']]['canonical'],lookup[a['B_id']]['canonical']) for a in v),
    'repaired_offspring_count':sum(int(a['generation_count']) for a in v),
    'novel10_events_per_seconds':float(ne.sum()/sec.sum()),
    'avg_prequench_calls':float(np.mean([int(a['prequench_calls']) for a in v]))}
  for arm,reference,name in [(4,0,'alternating_vs_donor_only'),
    (5,0,'joint4_vs_donor_only'),(5,4,'joint4_vs_separate_swaps'),
    (6,7,'exact_corridor_vs_permuted_corridor'),
    (6,5,'exact_corridor_vs_trueE'),(8,1,'descent_aware_vs_random_innovation'),
    (5,1,'joint4_vs_random_innovation')]:
   vals=[int(v[reference]['bestE'])-int(v[arm]['bestE']) for _,v in arr]
   nov=[int(v[arm]['new10'])-int(v[reference]['new10']) for _,v in arr]
   # Aggregate replicates by (source pair); bootstrap over distinct pairs only.
   bypair=collections.defaultdict(list)
   for (k,v),value in zip(arr,vals):bypair[k[1]].append(value)
   means=[float(np.mean(s)) for s in bypair.values()]
   x['paired'][name]={'mean_bestE_advantage':float(np.mean(vals)),
     'mean_new10_event_advantage':float(np.mean(nov)),
     'pair_cluster_bootstrap95_not_independent_lineages':boot_cluster(means,seed=2220+n+arm),
     'paired_session_win_tie_loss':[sum(z>0 for z in vals),sum(z==0 for z in vals),sum(z<0 for z in vals)]}
  summary['strata'][str(n)]=x
 args.out.parent.mkdir(parents=True,exist_ok=True)
 args.out.write_text(json.dumps(summary,indent=2)+'\n')
 print('VERIFIED',len(rows),'repaired parent-pair sessions',len(cert),'new-source ≤20% certificates')
 for n,r in summary['strata'].items():
  print('N',n,'pairs',r['pairs'],
    'new10',[r['per_arm'][v]['new_within10_events'] for v in NAMES.values()],
    'joint4vsdonor',r['paired']['joint4_vs_donor_only']['mean_bestE_advantage'],
    'corridor-vs-permuted',r['paired']['exact_corridor_vs_permuted_corridor']['mean_bestE_advantage'])
if __name__=='__main__':main()
