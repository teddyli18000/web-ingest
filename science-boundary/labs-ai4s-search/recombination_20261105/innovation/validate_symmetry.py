#!/usr/bin/env python3
"""Audit exact terminal scores and new orbit certificates from source-B alignment search."""
import argparse,csv,collections,json,pathlib
import numpy as np
ARM={0:'nearest_Hamming_B',1:'nearest_signed_C_B',2:'farthest_signed_C_B',
     3:'random_B_orientation',4:'farthest_Hamming_B',
     5:'best_two_raw_E_probes_per_orientation',
     6:'matched_fake_B',7:'copy_A',8:'best_one_steepest_probe_per_orientation'}
def read(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def energy(s):
 x=[int(z)*2-1 for z in s]
 return sum(sum(x[i]*x[i+k] for i in range(len(x)-k))**2 for k in range(1,len(x)))
def variants(s):
 def neg(t):return ''.join('0' if z=='1' else '1' for z in t)
 def alt(t):return ''.join(z if i%2==0 else neg(z) for i,z in enumerate(t))
 return sorted({y for b in (s,s[::-1]) for t in (b,alt(b)) for y in (t,neg(t))})
def hd(s,t):return sum(a!=b for a,b in zip(s,t))
def boot(a,seed):
 rng=np.random.default_rng(seed);v=np.asarray(a,float)
 x=v[rng.integers(len(v),size=(5000,len(v)))].mean(axis=1)
 return list(map(float,np.quantile(x,[.025,.975])))
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--sessions',type=pathlib.Path,required=True)
 p.add_argument('--certificates',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args()
 parents=read(a.parents);idx={z['id']:z for z in parents}
 reg=collections.defaultdict(set);refs={}
 for z in parents:
  n=int(z['n']);assert energy(z['bits'])==int(z['E']) and variants(z['bits'])[0]==z['canonical']
  reg[n].add(z['canonical']);refs[n]=min(refs.get(n,100000),int(z['best_known']))
 rows=read(a.sessions);cert=read(a.certificates)
 keys=collections.defaultdict(dict);byarm=collections.defaultdict(list)
 for z in rows:
  n=int(z['N']);r=int(z['rep']);m=int(z['arm']);a0=idx[z['A_id']];b0=idx[z['B_id']]
  assert m in ARM
  assert z['pair']==a0['id']+'-'+b0['id']
  assert int(a0['n'])==int(b0['n'])==n and int(z['AE'])==int(a0['E']) and int(z['BE'])==int(b0['E'])
  assert int(z['bestE'])==energy(z['bestBits'])
  assert variants(z['bestBits'])[0]==z['bestCanon']
  assert int(z['bestSymDistance'])==min(hd(z['bestBits'],o) for p0 in (a0,b0) for o in variants(p0['bits']))
  d=min(hd(a0['bits'],o) for o in variants(b0['bits']))
  expectedM=d//2+(4 if n<=47 else 8 if n==50 else 6)
  assert int(z['D0'])==d and int(z['fixed_mask_hamming'])==expectedM
  assert int(z['generations'])>=1 and float(z['elapsed_ms'])>=120
  assert float(z['generation_ms'])+float(z['model_ms'])+float(z['repair_ms'])<=float(z['elapsed_ms'])+.01
  assert int(z['mask_proposals'])==(0 if m==7 else 24*int(z['generations']))
  if m in (5,8):assert int(z['scouts'])>0
  else:assert int(z['scouts'])==0
  assert int(z['new5'])<=int(z['new10'])<=int(z['new20'])<=int(z['generations'])
  key=(n,z['pair'],r)
  assert m not in keys[key]
  keys[key][m]=z;byarm[m].append(z)
 assert all(set(z)==set(ARM) for z in keys.values())
 seen=collections.defaultdict(list)
 for z in cert:
  n=int(z['N']);rep=int(z['rep']);arm=int(z['arm']);key=(n,z['pair'],rep)
  assert key in keys and arm in keys[key]
  source=keys[key][arm];x=z['bits'];e=int(z['E'])
  assert len(x)==n and energy(x)==e and variants(x)[0]==z['canon'] and z['canon'] not in reg[n]
  assert e<=1.2*refs[n]+1e-8
  aa,bb=idx[source['A_id']],idx[source['B_id']]
  assert int(z['nearest_source_distance'])==min(hd(x,w) for q in (aa,bb) for w in variants(q['bits']))
  assert int(z['threshold5'])==int(e<=1.05*refs[n]+1e-8)
  assert int(z['threshold10'])==int(e<=1.10*refs[n]+1e-8)
  assert int(z['threshold20'])==1
  seen[(n,z['pair'],rep,arm)].append((z['canon'],e))
 for z in rows:
  n=int(z['N']);key=(n,z['pair'],int(z['rep']),int(z['arm']))
  w=seen[key];assert len({x for x,e in w})==len(w)
  for t,mult in [('new5',1.05),('new10',1.10),('new20',1.2)]:
   assert int(z[t])==sum(e<=refs[n]*mult+1e-8 for c,e in w)
 pair=next(iter(keys))[1];N=next(iter(keys))[0]
 assert {z[1] for z in keys}=={pair} and {z[0] for z in keys}=={N}
 samples=[z for k,z in sorted(keys.items())]
 summary={'N':N,'pair':pair,'repeats':len(keys),'verified_sessions':len(rows),
          'verified_new_orbit_certificates':len(cert),'methods':{},'paired':{},
          'limits':['Independent run seeds share one fixed elite pair; no source-population inference',
                    'Oracle known third optimum not used in selection',
                    'All model alignment and 64-step native-inspired repair counted in same 120ms',
                    'All arms 0..6 and 8 share fixed true physical Hamming radius before repair',
                    'This is not a modern GPU MTS or official seeded GOMEA solver']}
 for m,name in ARM.items():
  vals=[z[m] for z in samples]
  summary['methods'][name]={
   'mean_session_best_E':float(np.mean([int(z['bestE']) for z in vals])),
   'mean_all_repaired_E':float(np.mean([float(z['avg_repaired_E']) for z in vals])),
   'best_observed_E':min(int(z['bestE']) for z in vals),
   'new5_events':sum(int(z['new5']) for z in vals),
   'new10_events':sum(int(z['new10']) for z in vals),
   'distinct_new10_orbits':len({c for z in vals for c,e in seen[(N,pair,int(z['rep']),m)] if e<=1.1*refs[N]+1e-8}),
   'new20_events':sum(int(z['new20']) for z in vals),
   'source_orbit_best_fraction':float(np.mean([z['bestCanon'] in reg[N] for z in vals])),
   'n_repaired_children':sum(int(z['generations']) for z in vals),
   'mean_scout_count':float(np.mean([int(z['scouts']) for z in vals]))}
 for m,name in ARM.items():
  if m==0:continue
  deltas=[int(z[0]['bestE'])-int(z[m]['bestE']) for z in samples]
  summary['paired'][name]={'mean_best_E_gain_vs_min_hamming':float(np.mean(deltas)),
         'CI95_seed_bootstrap_NOT_source_independent':boot(deltas,seed=4311+m+N),
         'win_tie_loss':[sum(v>0 for v in deltas),sum(v==0 for v in deltas),sum(v<0 for v in deltas)]}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(summary,indent=2)+'\n')
 print('PASS',pair,len(rows),'exact score+eightfold audited full 120ms repairs and',len(cert),'source-novel records')
 print(json.dumps({'meanE':{m:z['mean_session_best_E'] for m,z in summary['methods'].items()},
                   'near10':{m:z['new10_events'] for m,z in summary['methods'].items()}},indent=2))
if __name__=='__main__':main()
