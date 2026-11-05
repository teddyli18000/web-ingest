#!/usr/bin/env python3
"""Actual upstream CWI discrete GOMEA LABS baseline (not hand-rolled FOS).

This is a FULL evolutionary optimizer from random population, not a warm-start
elite-pair recombination experiment. Use exact black-box E, document Python
callback overhead, compare univariate vs learned MI linkage on same hardware.
"""
import argparse,csv,hashlib,json,pathlib,time,traceback
import gomea
import numpy as np
OPT={46:131,47:135,50:153,59:205,60:218,92:490,99:553}
def exact(bits):
 s=[1 if q=='1' else -1 for q in bits];n=len(s)
 return sum(sum(s[i]*s[i+k] for i in range(n-k))**2 for k in range(1,n))
def variants(s):
 neg=lambda t:''.join('1' if c=='0' else '0' for c in t)
 alt=lambda t:''.join(c if i%2==0 else neg(c) for i,c in enumerate(t))
 return sorted({u for z in (s,s[::-1]) for w in (z,alt(z)) for u in (w,neg(w))})
class LABS(gomea.fitness.BBOFitnessFunctionDiscrete):
 def __new__(cls,n,target,**kwargs):
  obj=super().__new__(cls,n,alphabet_size=2,value_to_reach=-target,**kwargs)
  obj.n=n;obj.Ebest=10**9;obj.best='';obj.evals=0;obj.improvements=[]
  return obj
 def objective_function(self,objective_index,variables):
  bitstring=''.join(str(int(a)) for a in variables)
  val=exact(bitstring)
  self.evals+=1
  if val<self.Ebest:
   self.Ebest=val;self.best=bitstring;self.improvements.append((self.evals,val))
  return -float(val)

def one(n,seed,mode,budget):
 t=time.monotonic()
 fit=LABS(n,target=OPT[n])
 lm=gomea.linkage.Univariate() if mode=='univariate' else gomea.linkage.LinkageTree(similarity_measure='MI',filtered=True)
 try:
  solver=gomea.DiscreteGOMEA(fitness=fit,linkage_model=lm,
    random_seed=seed,max_number_of_seconds=budget,
    max_number_of_populations=12,base_population_size=2,
    verbose=False,generational_statistics=False,generational_solution=False)
  statistics=solver.run().getFinalStatistics()
  err=None
 except Exception as ex:
  statistics={};err=repr(ex)
 elapsed=time.monotonic()-t
 if not fit.best:raise RuntimeError(f'no LABS objective evaluations after solver: {err}')
 if exact(fit.best)!=fit.Ebest:raise RuntimeError('tracked E contradiction')
 if err:raise RuntimeError(f'GOMEA solver run failed {mode} {n} {seed}: {err}')
 return dict(N=n,seed=seed,mode=mode,target=OPT[n],actual_wall_s=round(elapsed,4),
   objective_evaluations=fit.evals,bestE=fit.Ebest,best_bits=fit.best,canonical=variants(fit.best)[0],
   near10=int(fit.Ebest<=1.10*OPT[n]),target_attained=int(fit.Ebest<=OPT[n]),
   source='official CWI-EvolutionaryIntelligence gomea 1.1.0 discrete GOMEA black-box',
   best_improvement_trace=json.dumps(fit.improvements),
   final_stats=json.dumps(statistics,default=str))
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--out',type=pathlib.Path,required=True)
 p.add_argument('--lengths',default='46,47,50,59,60,92,99')
 p.add_argument('--reps',type=int,default=4)
 p.add_argument('--seconds',type=float,default=2.0)
 p.add_argument('--seed-offset',type=int,default=34000)
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 Ns=[int(z) for z in a.lengths.split(',')]
 assert all(n in OPT for n in Ns)
 rows=[];total=len(Ns)*a.reps*2;num=0
 for n in Ns:
  for rep in range(a.reps):
   for mode in ('univariate','MI_filtered_linkage_tree'):
    seed=a.seed_offset+n*1009+rep*17011
    result=one(n,seed,mode,a.seconds);rows.append(result)
    num+=1
    print('GOMEA',num,'/',total,'N',n,'rep',rep,'mode',mode,
      'best E',result['bestE'],'evaluations',result['objective_evaluations'],
      'wall_s',result['actual_wall_s'],flush=True)
 with a.out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t')
  w.writeheader();w.writerows(rows)
 meta=dict(library='PyPI gomea==1.1.0; official full CWI discrete GOMEA (not GOMEA style approximation)',
   problem='unrestricted LABS exact integer E',objective='maximize -E',
   source='random initial population (no elite seeds supported in this interface)',
   comparisons=['univariate full GOMEA','filtered MI linkage-tree full GOMEA'],
   bias='Python O(N^2) callback overhead, not hardware-normalized C++ native solver',
   parameters=dict(vars(a),out=str(a.out)),completed=len(rows),exact_verified_best=len(rows),
   file_sha256=hashlib.sha256(a.out.read_bytes()).hexdigest())
 a.out.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(json.dumps({k:v for k,v in meta.items() if k!='parameters'},indent=2))
if __name__=='__main__':main()
