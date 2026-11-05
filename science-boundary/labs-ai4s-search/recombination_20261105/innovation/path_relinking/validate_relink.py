#!/usr/bin/env python3
"""Independent O(N^2) exact LABS + eightfold orbit audit of fully costed
protected-elite path relinking against classical PR and elite ILS controls.
"""
import argparse,csv,collections,hashlib,json,pathlib
import numpy as np

ARMS={0:'single_elite_short_radius_ILS',1:'elite_source_copy',
      2:'classic_greedy_path_relink',3:'classic_random_path_relink',
      4:'greedy_with_protected_tabu',5:'random_with_protected_tabu',
      6:'protected_trueE_consensus_corepair',
      7:'protected_exact_lag_envelope_corepair',
      8:'protected_shuffled_lag_envelope_placebo'}
FROZEN={46:['c46_0-c46_1'],47:['c47_0-c47_2'],50:['c50_0-c50_1'],
        59:['c59_0-c59_2'],
        60:['c60_1-c60_4','c60_0-c60_3','c60_2-c60_5'],
        92:['c92_0-c92_1'],99:['c99_0-c99_1']}
def read(path):
 with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def exact(word):
 x=[2*int(v)-1 for v in word];n=len(x)
 return sum(sum(x[i]*x[i+k] for i in range(n-k))**2 for k in range(1,n))
def orbit(word):
 invert=lambda s:''.join('1' if c=='0' else '0' for c in s)
 alt=lambda s:''.join(c if i%2==0 else invert(c) for i,c in enumerate(s))
 return sorted({t for b in (word,word[::-1]) for z in (b,alt(b)) for t in (z,invert(z))})
def min_hd(a,b):
 return min(sum(x!=y for x,y in zip(a,t)) for t in orbit(b))
def pair_boot(arr, seed):
 if not arr:return None
 r=np.random.default_rng(seed)
 x=np.asarray(arr)
 return list(map(float,np.quantile(x[r.integers(len(x),size=(20000,len(x)))].mean(axis=1),[.025,.975])))
def main():
 p=argparse.ArgumentParser()
 for flag in ('parents','sessions','certificates','out'):
  p.add_argument('--'+flag,required=True,type=pathlib.Path)
 a=p.parse_args()
 parents=read(a.parents);rows=read(a.sessions);cert=read(a.certificates)
 byid={p['id']:p for p in parents}
 byn=collections.defaultdict(set);refs={}
 for p in parents:
  n=int(p['n']);w=p['bits']
  assert len(w)==n and exact(w)==int(p['E']) and orbit(w)[0]==p['canonical']
  byn[n].add(p['canonical'])
  refs[n]=min(refs.get(n,10**9),int(p['best_known']))
 grouped=collections.defaultdict(dict)
 for z in rows:
  n=int(z['N']);pair=z['pair'];arm=int(z['arm']);rep=int(z['rep'])
  assert pair in FROZEN[n] and arm in ARMS
  pidA,pidB=pair.split('-')
  assert z['A_id']==pidA and z['B_id']==pidB and z['AE']==byid[pidA]['E'] and z['BE']==byid[pidB]['E']
  raw=z['bestBits']
  assert len(raw)==n and exact(raw)==int(z['bestE']) and orbit(raw)[0]==z['bestCanon']
  assert min(min_hd(raw,byid[pidA]['bits']),min_hd(raw,byid[pidB]['bits']))==int(z['bestDist'])
  assert int(z['trajectory_count'])>=1 and int(z['offspring'])>=int(z['trajectory_count'])
  if arm>=2:
   assert int(z['offspring'])==4*int(z['trajectory_count'])
   assert int(z['stageVisits'])==int(z['offspring'])
   if arm>=4:assert int(z['protectMoves'])>0
   else:assert int(z['protectMoves'])==0
  else:assert int(z['offspring'])==int(z['trajectory_count'])
  assert 0<=int(z['nov5'])<=int(z['nov10'])<=int(z['nov15'])<=int(z['nov20'])<=int(z['offspring'])
  assert float(z['elapsedMs'])>=400
  assert float(z['modelMs'])+float(z['pathMs'])+float(z['protectedMs'])+float(z['finalRepairMs'])<=float(z['elapsedMs'])+.10
  key=(n,pair,rep)
  assert arm not in grouped[key]
  grouped[key][arm]=z
 assert len(rows)==len(grouped)*len(ARMS)
 assert set((n,pair) for n,pair,r in grouped)==set((n,pair) for n,v in FROZEN.items() for pair in v)
 assert all(set(g)==set(ARMS) for g in grouped.values())
 collection=collections.defaultdict(list)
 byarmglobal=collections.defaultdict(dict)
 for z in cert:
  n=int(z['N']);pair=z['pair'];rep=int(z['rep']);arm=int(z['arm'])
  assert (n,pair,rep) in grouped and arm in ARMS
  e=int(z['E']);word=z['bits'];b=z['preBits'];c=orbit(word)[0]
  assert len(word)==n and len(b)==n
  assert e==exact(word) and int(z['preE'])==exact(b)
  assert c==z['canonical'] and c not in byn[n] and e<=refs[n]*1.20+1e-9
  aa,bb=pair.split('-')
  assert min(min_hd(word,byid[aa]['bits']),min_hd(word,byid[bb]['bits']))==int(z['closestParentDist'])
  stage=int(z['stage']);locknum=int(z['lockedCount'])
  if arm>=2:assert 0<=stage<=3 and locknum>0
  else:assert stage==-1 and locknum==0
  assert c not in collection[(n,pair,rep,arm)],'duplicates within session'
  collection[(n,pair,rep,arm)].append(c)
  byarmglobal[(n,arm)][c]=min(e,byarmglobal[(n,arm)].get(c,10**9))
 for key,g in grouped.items():
  n,pair,rep=key
  for arm,z in g.items():
   observed=collection[n,pair,rep,arm]
   for tag,r in [(5,1.05),(10,1.1),(15,1.15),(20,1.2)]:
    count=sum(byarmglobal[(n,arm)][c]<=refs[n]*r+1e-9 for c in observed)
    assert count==int(z['nov'+str(tag)]),(n,pair,rep,arm,tag,count,z['nov'+str(tag)])
 out={'status':'independently verified','source_sha256':hashlib.sha256(a.parents.read_bytes()).hexdigest(),
      'sessions':len(rows),'pair_seed_contexts':len(grouped),'source_pair_contexts':len(FROZEN[46])+len(FROZEN[47])+len(FROZEN[50])+len(FROZEN[59])+len(FROZEN[60])+len(FROZEN[92])+len(FROZEN[99]),
      'certificates':len(cert),'arms':ARMS,'by_length':{},'pair_cluster_primary':{},
      'limitations':['Established path-relinking family, not claimed novel',
        'No hidden third target enters any operator',
        'Historical archived/source distinct orbits are not independent modern GPU lineages',
        'N92/99 one source pair each; source-pair bootstraps are small exploratory samples',
        '400ms local repair common across arms, not modern 2025 GPU MTS/full tuned GOMEA',
        'Novel certificate records are source registry novel, but are not necessarily first-ever discoveries']}
 bylength=collections.defaultdict(list)
 for key,g in grouped.items():bylength[key[0]].append((key,g))
 for n,pairs in sorted(bylength.items()):
  row={'pairs':len(set(k[1] for k,g in pairs)),'seed_contexts':len(pairs),'Eopt':refs[n],'methods':{}}
  for arm,name in ARMS.items():
   gs=[g[arm] for _,g in pairs]
   total_seconds=sum(float(z['elapsedMs']) for z in gs)/1000
   certificates_per_method=byarmglobal[n,arm]
   num_events=sum(int(z['nov10']) for z in gs)
   row['methods'][name]={
    'mean_best_repaired_E':float(np.mean([int(z['bestE']) for z in gs])),
    'mean_all_repaired_E':float(np.mean([float(z['meanAllRepairedE']) for z in gs])),
    'mean_all_prepared_E':float(np.mean([float(z['meanAllPreE']) for z in gs])),
    'best_E':min(int(z['bestE']) for z in gs),
    'session_ave_novel10':float(np.mean([int(z['nov10']) for z in gs])),
    'novel5_events':sum(int(z['nov5']) for z in gs),
    'novel10_events':num_events,
    'novel20_events':sum(int(z['nov20']) for z in gs),
    'unique_novel10_source_orbits':sum(v<=refs[n]*1.1+1e-9 for v in certificates_per_method.values()),
    'near10_positive_sessions':sum(int(z['nov10'])>0 for z in gs),
    'best_return_to_parent_registry_fraction':float(np.mean([z['bestCanon'] in byn[n] for z in gs])),
    'total_repaired_offspring':sum(int(z['offspring']) for z in gs),
    'total_model_wall_seconds':total_seconds,
    'novel10_events_per_second':num_events/total_seconds}
  out['by_length'][str(n)]=row
 # Pair-cluster inference, including many explicit zero-event outcomes.
 for c,r,name in [(4,2,'protected_greedy_vs_greedy_classic'),
                  (6,4,'compensated_exactE_vs_protected'),
                  (7,8,'true_lag_envelope_vs_shuffled_placebo'),
                  (6,0,'compensated_path_vs_short_radius_ILS'),
                  (4,0,'protected_path_vs_short_radius_ILS'),
                  (2,3,'classic_greedy_vs_classic_random')]:
  clusters=collections.defaultdict(list)
  novelty=collections.defaultdict(list)
  for (n,pair,rep),g in grouped.items():
   clusters[(n,pair)].append((int(g[r]['bestE'])-int(g[c]['bestE']))/refs[n])
   novelty[(n,pair)].append(int(g[c]['nov10'])-int(g[r]['nov10']))
  vals=[np.mean(z) for z in clusters.values()]
  nor=[np.mean(z) for z in novelty.values()]
  out['pair_cluster_primary'][name]={
   'mean_Eopt_normalized_bestE_advantage':float(np.mean(vals)),
   'pair_cluster_bootstrap95_exploratory':pair_boot(vals,seed=20261105+c*41),
   'mean_novel10_event_advantage_per_session':float(np.mean(nor)),
   'pair_cluster_bootstrap_novel10_exploratory':pair_boot(nor,seed=20261105+c*73),
   'pair_contexts_with_improvement':sum(v>0 for v in vals),
   'pair_contexts_with_worse':sum(v<0 for v in vals)}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
 print('VERIFIED sessions',len(rows),'distinct frozen pair-contexts',out['source_pair_contexts'],
       'source-new terminal certificates',len(cert),flush=True)
 for n,row in out['by_length'].items():
  print('N',n,'new10_by_arm',[(arm,row['methods'][name]['novel10_events'])
   for arm,name in ARMS.items()],'postrepair_means',
        {a:round(row['methods'][n]['mean_best_repaired_E'],2) for a,n in ARMS.items()},flush=True)
 print('Primary cluster comparisons',out['pair_cluster_primary'],flush=True)
if __name__=='__main__':main()
