#!/usr/bin/env python3
"""Independent endpoint and exact-correlation certificate audit of constrained
recombination. Primary inference = source-pair (not offspring) comparisons.
"""
import argparse,csv,json,math,pathlib,collections,hashlib
import numpy as np

NAMES={0:'copy_source',1:'random_balanced_inheritance',2:'circular_segment_inheritance',
       3:'MI_FOS_GOM_style_balanced',4:'exact_pair_epistasis_FOS_GOM_style_balanced',
       5:'uniform_Johnson_mask_walk',6:'true_E_mask_swap_hillclimb',
       7:'exact_autocorrelation_envelope_corridor',
       8:'shuffled_autocorrelation_envelope_placebo'}
def read(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def E(bs):
 a=[1 if q=='1' else -1 for q in bs];n=len(a)
 return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def orbit(s):
 def neg(s):return ''.join('1' if q=='0' else '0' for q in s)
 def alt(s):return ''.join(q if i%2==0 else ('1' if q=='0' else '0') for i,q in enumerate(s))
 return {z for b in (s,s[::-1]) for t in (b,alt(b)) for z in (t,neg(t))}
def boot(x,seed=905,B=10000):
 rng=np.random.default_rng(seed);v=np.asarray(x,float)
 if len(v)==0:return None
 return [float(y) for y in np.quantile(v[rng.integers(len(v),size=(B,len(v)))].mean(axis=1),[.025,.975])]
def summarize(rows,parents):
 pmap={p['id']:p for p in parents}
 group=collections.defaultdict(list)
 allorbit=collections.defaultdict(set)
 known={}
 for p in parents:
  n=int(p['n'])
  assert len(p['bits'])==n and E(p['bits'])==int(p['E'])
  assert min(orbit(p['bits']))==p['canonical']
  group[n].append(p);allorbit[n].add(p['canonical']);known[n]=min(known.get(n,10**8),int(p['best_known']))
 expectedPairs=sum(len(g)*(len(g)-1)//2 for g in group.values())
 groups=collections.defaultdict(dict)
 for r in rows:
  n=int(r['N']);pair=r['pair'];rep=int(r['rep']);arm=int(r['arm'])
  assert arm in NAMES
  assert r['A_id'] in pmap and r['B_id'] in pmap
  a,b=pmap[r['A_id']],pmap[r['B_id']]
  assert int(a['n'])==int(b['n'])==n and int(r['AE'])==int(a['E']) and int(r['BE'])==int(b['E'])
  assert pair==a['id']+'-'+b['id']
  assert int(r['bestE'])==E(r['bestBits'])
  assert min(orbit(r['bestBits']))==r['bestCanon']
  dist=min(sum(x!=y for x,y in zip(r['bestBits'],z)) for q in (a['bits'],b['bits']) for z in orbit(q))
  assert dist==int(r['bestParentDist'])
  assert int(r['near10_unique'])<=int(r['near15_unique'])<=int(r['near20_unique'])
  assert int(r['near20_unique'])<=int(r['generations'])
  assert int(r['pre_mix_valid'])==(0 if arm==0 else int(r['generations']))
  assert float(r['elapsed_ms'])>=100  # 120ms nominal, permit small rounding?
  assert float(r['model_ms'])+float(r['generation_ms'])+float(r['repair_ms'])<=float(r['elapsed_ms'])+0.001
  if arm in (0,1,2):assert int(r['mask_evals'])==0
  if arm in (5,6,7,8):assert int(r['mask_evals'])==24*int(r['generations'])
  key=(n,pair,rep)
  assert arm not in groups[key]
  groups[key][arm]=r
 assert len(groups)==expectedPairs*len(set(int(z['rep']) for z in rows))
 assert all(set(v)==set(NAMES) for v in groups.values())
 return groups,allorbit,known,expectedPairs
def main():
 p=argparse.ArgumentParser();p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--sessions',type=pathlib.Path,required=True)
 p.add_argument('--certificates',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args()
 parents=read(a.parents);rows=read(a.sessions);cert=read(a.certificates)
 groups,origins,reference,pairs=summarize(rows,parents)
 by=collections.defaultdict(list)
 for k,v in groups.items():by[k[0]].append((k,v))
 seen=collections.defaultdict(set)
 for z in cert:
  n=int(z['N']);key=(n,z['pair'],int(z['rep']),int(z['arm']))
  assert key[:3] in groups and key[3] in groups[key[:3]]
  assert z['bits'] and len(z['bits'])==n
  e=int(z['E']);assert E(z['bits'])==e
  c=min(orbit(z['bits']));assert c==z['canon'] and c not in origins[n]
  assert e<=reference[n]*1.2+1e-9
  parentids=groups[key[:3]][key[3]]
  aa=next(x for x in parents if x['id']==parentids['A_id'])
  bb=next(x for x in parents if x['id']==parentids['B_id'])
  d=min(sum(c!=v for c,v in zip(z['bits'],t)) for parent in (aa,bb) for t in orbit(parent['bits']))
  assert d==int(z['parentDist'])
  assert key not in seen[c]
  seen[c].add(key)
 for r in rows:
  n=int(r['N']);key=(n,r['pair'],int(r['rep']),int(r['arm']))
  counted10=counted15=counted20=0
  for c,ks in seen.items():
   if key in ks:
    e=E(c)
    counted20+=1
    if e<=reference[n]*1.15:counted15+=1
    if e<=reference[n]*1.10:counted10+=1
  assert (counted10,counted15,counted20)==(int(r['near10_unique']),int(r['near15_unique']),int(r['near20_unique'])),(key,counted10,counted15,counted20)
 report={'status':'verified','rows':len(rows),'source_parent_orbits':len(parents),'distinct_pair_contexts':pairs,
  'complete_pair_replicate_contexts':len(groups),'certificates':len(cert),
  'methods':NAMES,'lengths':{},'caveat':[
    'Each pair-rep is one budgeted source run; many repaired children are correlated.',
    'Mixed archive records are distinct orbits, but some discovery lineages unknown.',
    'N92/N99 each have only a single same-length pair of elite source orbits.',
    'This study uses a source-identical repair kernel, not full modern GPU MTS / full GOMEA.',
    'Retrospective best post-repair E and novel orbit count, not candidate pre-repair energy, are primary.',
    'A single run over a source family is not enough to infer general transferable learned structure.']}
 for n,arr in by.items():
  entry={'pairs':len({k[1] for k,_ in arr}),'sessions_per_arm':len(arr),'best_reference_E':reference[n],'arms':{},'paired':{}}
  for arm,name in NAMES.items():
   values=[v[arm] for _,v in arr]
   best=np.array([int(v['bestE']) for v in values])
   n10=np.array([int(v['near10_unique']) for v in values])
   n15=np.array([int(v['near15_unique']) for v in values])
   n20=np.array([int(v['near20_unique']) for v in values])
   elapsed=np.array([float(v['elapsed_ms']) for v in values])/1000
   entry['arms'][name]={'mean_best_postrepair_E':float(best.mean()),
    'mean_all_offspring_postrepair_E':float(np.mean([float(v['avg_childE']) for v in values])),
    'best_observed_E':int(best.min()),
    'source_parent_orbit_best_fraction':float(np.mean([v['bestCanon'] in origins[n] for v in values])),
    'new_near10_orbit_events':int(n10.sum()),'new_near15_orbit_events':int(n15.sum()),
    'new_near20_orbit_events':int(n20.sum()),
    'sessions_with_new_near10':int((n10>0).sum()),'total_repaired_offspring':int(sum(int(v['generations']) for v in values)),
    'near10_orbit_event_rate_per_CPU_second':float(n10.sum()/elapsed.sum()),
    'cost_seconds':float(elapsed.sum()),
    'avg_cumulative_model_ms':float(np.mean([float(v['model_ms']) for v in values]))}
  for x,y,label in [(7,8,'exact_envelope_vs_permuted_control'),(7,6,'exact_envelope_vs_true_energy'),
                    (6,5,'true_energy_vs_uniform_random_walk'),(4,3,'epistasis_tree_vs_MI_tree'),
                    (7,1,'exact_envelope_vs_balanced_random'),(7,2,'exact_envelope_vs_segment')]:
   diffs=[int(v[y]['bestE'])-int(v[x]['bestE']) for _,v in arr]
   novelty=[int(v[x]['near10_unique'])-int(v[y]['near10_unique']) for _,v in arr]
   entry['paired'][label]={'mean_best_E_advantage':float(np.mean(diffs)),
    'mean_near10_advantage':float(np.mean(novelty)),
    'bootstrap_CI95_by_pair_rep_NOT_source_independent':boot(diffs,seed=20261105+n*12+x),
    'win_tie_loss':[int(sum(i>0 for i in diffs)),int(sum(i==0 for i in diffs)),int(sum(i<0 for i in diffs))]}
  report['lengths'][str(n)]=entry
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 print('VERIFIED',len(rows),'independent integer-scored budgeted sessions',len(cert),'new low-E records')
 for n,v in report['lengths'].items():
  print('N',n,'pairs',v['pairs'],'near10',[v['arms'][k]['new_near10_orbit_events'] for k in NAMES.values()],
  'corridor-vs-placebo',v['paired']['exact_envelope_vs_permuted_control']['mean_best_E_advantage'])
if __name__=='__main__':main()
