#!/usr/bin/env python3
"""Independent exact integer rescoring of all progressive/reversible LABS
donor-backbone relinking endpoints; source-pair clustering, no offspring IID.
"""
import argparse,csv,collections,json,pathlib,hashlib
import numpy as np

ARMS={0:'single_elite_short_ILS',1:'monotone_locked_B_path',
      2:'half_B_fixed_backbone',3:'half_B_exactE_lock_exchange',
      4:'half_B_random_lock_exchange',5:'half_B_exact_lag_lock_exchange',
      6:'half_B_permuted_lag_placebo',7:'half_virtual_B_exactE_exchange'}
PAIRS={46:['c46_0-c46_1'],47:['c47_0-c47_2'],50:['c50_0-c50_1'],
       59:['c59_0-c59_2'],60:['c60_1-c60_4','c60_0-c60_3','c60_2-c60_5'],
       92:['c92_0-c92_1'],99:['c99_0-c99_1']}
def read(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def score(w):
 s=[2*int(c)-1 for c in w];n=len(s)
 return sum(sum(s[i]*s[i+k] for i in range(n-k))**2 for k in range(1,n))
def variants(w):
 invert=lambda t:''.join('1' if c=='0' else '0' for c in t)
 alt=lambda t:''.join(c if i%2==0 else invert(c) for i,c in enumerate(t))
 return sorted({z for b in (w,w[::-1]) for t in (b,alt(b)) for z in (t,invert(t))})
def minhd(a,b):return min(sum(x!=y for x,y in zip(a,t)) for t in variants(b))
def clusterboot(x,seed=20261105):
 if not x:return None
 a=np.asarray(x,float);rng=np.random.default_rng(seed)
 return list(map(float,np.quantile(a[rng.integers(len(a),size=(10000,len(a)))].mean(axis=1),[.025,.975])))
def main():
 p=argparse.ArgumentParser()
 for x in ('parents','sessions','certificates','out'):
  p.add_argument('--'+x,required=True,type=pathlib.Path)
 a=p.parse_args()
 parents=read(a.parents);runs=read(a.sessions);saved=read(a.certificates)
 byid={x['id']:x for x in parents}
 source=collections.defaultdict(set);ref={}
 for x in parents:
  n=int(x['n']);assert score(x['bits'])==int(x['E'])
  assert variants(x['bits'])[0]==x['canonical']
  source[n].add(x['canonical']);ref[n]=min(ref.get(n,10**8),int(x['best_known']))
 contexts=collections.defaultdict(dict)
 for z in runs:
  n=int(z['N']);pair=z['pair'];arm=int(z['arm']);rep=int(z['rep'])
  assert pair in PAIRS[n] and arm in ARMS
  aa,bb=pair.split('-')
  assert z['A_id']==aa and z['B_id']==bb
  assert aa in byid and bb in byid
  assert len(z['bestBits'])==n and score(z['bestBits'])==int(z['bestE'])
  assert variants(z['bestBits'])[0]==z['bestCanon']
  d=min(minhd(z['bestBits'],byid[aa]['bits']),minhd(z['bestBits'],byid[bb]['bits']))
  assert d==int(z['bestDist'])
  assert int(z['offspring'])>0 and int(z['trajectory_count'])>0
  assert int(z['offspring'])==(int(z['trajectory_count']) if arm==0 else 4*int(z['trajectory_count']))
  assert (0<=int(z['nov5'])<=int(z['nov10'])<=int(z['nov15'])<=int(z['nov20'])<=int(z['offspring']))
  assert float(z['elapsedMs'])>=400
  assert float(z['modelMs'])+float(z['pathMs'])+float(z['protectedMs'])+float(z['finalRepairMs'])<=float(z['elapsedMs'])+.1
  key=(n,pair,rep)
  assert arm not in contexts[key]
  contexts[key][arm]=z
 assert len(contexts)==9*len({int(z['rep']) for z in runs})
 assert all(set(z)==set(ARMS) for z in contexts.values())
 assert len(runs)==len(contexts)*len(ARMS)
 cert=collections.defaultdict(dict)
 unique=collections.defaultdict(dict)
 for z in saved:
  n=int(z['N']);pair=z['pair'];rep=int(z['rep']);arm=int(z['arm'])
  assert (n,pair,rep) in contexts and arm in ARMS
  raw=z['preBits'];word=z['bits'];e=int(z['E']);can=variants(word)[0]
  assert len(raw)==len(word)==n and score(raw)==int(z['preE'])
  assert score(word)==e and can==z['canonical'] and can not in source[n]
  assert e<=ref[n]*1.2
  aa,bb=pair.split('-')
  assert min(minhd(word,byid[aa]['bits']),minhd(word,byid[bb]['bits']))==int(z['closestParentDist'])
  st=int(z['stage']);lock=int(z['lockedCount'])
  if arm==0:assert st==-1 and lock==0
  else:assert 0<=st<4 and lock>0
  k=(n,pair,rep,arm)
  assert can not in cert[k], 'same orbit counted twice in one session'
  cert[k][can]=e
  unique[n,arm][can]=e
 for z in runs:
  n=int(z['N']);pair=z['pair'];rep=int(z['rep']);arm=int(z['arm'])
  v=cert[n,pair,rep,arm]
  for cutoff,mul in [(5,1.05),(10,1.1),(15,1.15),(20,1.2)]:
   assert sum(e<=ref[n]*mul for e in v.values())==int(z['nov'+str(cutoff)])
 report={'status':'independently verified','source_parents_sha256':hashlib.sha256(a.parents.read_bytes()).hexdigest(),
         'sessions':len(runs),'pair_seed_contexts':len(contexts),
         'source_pair_contexts':9,'new_certificate_rows':len(saved),
         'arms':ARMS,'by_length':{},'comparisons':{},
         'limits':['Mature path-relinking general principle, new experimental conditional-backbone variant only',
           'No known third-target used in algorithm','All end-to-end budgets 400 ms historical CPU source scoring not modern GPU MTS',
           'Source pairs overlap discovery lineages; 9 clusters and N92/N99 one cluster each',
           'Near-elite certificate events per session are not independent first-ever discoveries']}
 byN=collections.defaultdict(list)
 for k,v in contexts.items():byN[k[0]].append(v)
 for n,arr in sorted(byN.items()):
  r={'parent_pair_contexts':len(PAIRS[n]),'seed_sessions_per_arm':len(arr),'reference_E':ref[n],'methods':{}}
  for arm,name in ARMS.items():
   cells=[v[arm] for v in arr];elapsed=sum(float(z['elapsedMs']) for z in cells)/1000
   r['methods'][name]={
    'avg_best_repaired_E':float(np.mean([int(z['bestE']) for z in cells])),
    'avg_all_repaired_E':float(np.mean([float(z['meanAllRepairedE']) for z in cells])),
    'best_observed_E':min(int(z['bestE']) for z in cells),
    'near5_events':sum(int(z['nov5']) for z in cells),
    'near10_events':sum(int(z['nov10']) for z in cells),
    'near20_events':sum(int(z['nov20']) for z in cells),
    'distinct_near10_orbits':sum(e<=ref[n]*1.1 for e in unique[n,arm].values()),
    'sessions_with_near10':sum(int(z['nov10'])>0 for z in cells),
    'parent_collapse_rate':float(np.mean([z['bestCanon'] in source[n] for z in cells])),
    'total_repaired_offspring':sum(int(z['offspring']) for z in cells),
    'novel10_orbit_events_per_second':sum(int(z['nov10']) for z in cells)/elapsed}
  report['by_length'][str(n)]=r
 for c,b,name in [(3,2,'exact_exchange_vs_fixed_half_backbone'),
                  (3,1,'exact_exchange_vs_monotone_backbone'),
                  (3,4,'exact_exchange_vs_random_lock_exchange'),
                  (5,6,'exact_spectrum_vs_permuted_spectrum'),
                  (3,7,'realB_exchange_vs_virtualB'),
                  (3,0,'realB_exchange_vs_single_ILS')]:
  C=collections.defaultdict(list);N=collections.defaultdict(list)
  for (n,pair,rep),z in contexts.items():
   C[n,pair].append((int(z[b]['bestE'])-int(z[c]['bestE']))/ref[n])
   N[n,pair].append(int(z[c]['nov10'])-int(z[b]['nov10']))
  vals=[float(np.mean(v)) for v in C.values()]
  nov=[float(np.mean(v)) for v in N.values()]
  report['comparisons'][name]={'mean_Eopt_normalized_bestE_advantage':float(np.mean(vals)),
        'pair_bootstrap95_exploratory':clusterboot(vals,seed=22311+c*173),
        'mean_new10_events_per_session_advantage':float(np.mean(nov)),
        'pair_bootstrap_new10_exploratory':clusterboot(nov,seed=22311+c*199),
        'pair_contexts_better':sum(v>0 for v in vals),
        'pair_contexts_worse':sum(v<0 for v in vals)}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,indent=2)+'\n')
 print('VERIFIED',len(runs),'complete source-pair sessions and',len(saved),'new exact certificates')
 for n,z in report['by_length'].items():
  print('N',n,'near10',{q:v['near10_events'] for q,v in z['methods'].items()},
    'means',{q:round(v['avg_best_repaired_E'],2) for q,v in z['methods'].items()},flush=True)
 print('PAIR CLUSTER COMPARISONS',report['comparisons'])
if __name__=='__main__':main()
