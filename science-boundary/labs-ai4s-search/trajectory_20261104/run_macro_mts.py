#!/usr/bin/env python3
"""Fair runtime-matched macro interventions inside original lMAts.

All proposal scoring/selection and later native Tabu repair are inside
unchanged solver wall-time cap. Capture source-best records and exact proof.
"""
import argparse,concurrent.futures,csv,hashlib,json,os,pathlib,re,subprocess,time
from collections import Counter

def energy(s):
 z=[1 if c=='+' else -1 for c in s];n=len(s)
 return sum(sum(z[i]*z[i+k] for i in range(n-k))**2 for k in range(1,n))
def canonical(s):
 def neg(x):return x.translate(str.maketrans('+-','-+'))
 def alt(x):return ''.join(c if i%2==0 else ('+' if c=='-' else '-') for i,c in enumerate(x))
 return min(z.replace('+','1').replace('-','0') for b in (s,s[::-1]) for z in (b,neg(b),alt(b),neg(alt(b))))
def near_skew(s):
 def skew(a):
  n=len(a);m=n//2
  return n%2==1 and all((a[m+j]==a[m-j])==(j%2==0) for j in range(1,m+1))
 return skew(s) if len(s)%2 else skew(s[:-1]) or skew(s[1:])
def parity(s):
 z=[1 if c=='+' else -1 for c in s];n=len(z);odd=even=0
 for k in range(1,n):
  C=sum(z[i]*z[i+k] for i in range(n-k))
  if k%2:odd+=C*C
  else:even+=C*C
 assert odd+even==energy(s)
 return odd,even
def run(t):
 exe,out,n,seed,arm,seconds=t
 label=f'n{n}-seed{seed}-arm{arm}'
 env=os.environ.copy();env['LABS_MACRO_ARM']=str(arm)
 clock=time.monotonic()
 try:
  p=subprocess.run([exe,str(n),str(seed),str(seconds),'1','0'],capture_output=True,text=True,
        env=env,timeout=seconds+35)
 except subprocess.TimeoutExpired:
  return {'n':n,'seed':seed,'arm':arm,'error':'wall-timeout'}
 elapsed=time.monotonic()-clock
 # Original solver prints exact final +-word, energy, MF; include all such words.
 hits=list(re.finditer(r'(?<![+-])([+-]{%d})\s+(\d+)\s+([0-9]+(?:\.[0-9]+)?)' % n,p.stdout))
 macro=list(re.finditer(r'MACRO arm=(\d+) gen=(\d+) sourceE=(\d+) proposedE=(\d+) k=(\d+) proposals=(\d+)',p.stdout))
 result={'n':n,'seed':seed,'arm':arm,'seconds':seconds,'actual_seconds':round(elapsed,5),
          'macro_proposals':len(macro),'macro_first_gen':int(macro[0].group(2)) if macro else None,
          'macro_avg_proposedE':(sum(int(m.group(4)) for m in macro)/len(macro)) if macro else None,
          'macro_avg_sourceE':(sum(int(m.group(3)) for m in macro)/len(macro)) if macro else None,
          'stdout_sha256':hashlib.sha256(p.stdout.encode()).hexdigest()}
 if p.returncode!=0 or not hits:
  result.update(error='solver_failure_or_unparsed',code=p.returncode,tail=p.stdout[-500:],stderr=p.stderr[-500:])
  return result
 last=hits[-1];bits=last.group(1);e=int(last.group(2))
 verified=energy(bits)
 if verified!=e:result.update(error='energy_mismatch',reported=e,verified=verified);return result
 if (arm==0 and macro) or (arm!=0 and any(int(m.group(1))!=arm for m in macro)):
  result.update(error='macro_arm_mismatch');return result
 odd,even=parity(bits)
 result.update(bestE=e,best_bits=bits.replace('+','1').replace('-','0'),
  orbit=canonical(bits),near_skew=int(near_skew(bits)),oddE=odd,evenE=even)
 return result
def main():
 a=argparse.ArgumentParser()
 a.add_argument('--exe',required=True)
 a.add_argument('--out',required=True)
 a.add_argument('--lengths',default='64,80,99,100')
 a.add_argument('--reps',type=int,default=4)
 a.add_argument('--seconds',type=int,default=14)
 a.add_argument('--workers',type=int,default=4)
 a.add_argument('--arms',default='0,1,2,3,4,5')
 opt=a.parse_args();dest=pathlib.Path(opt.out);dest.mkdir(parents=True,exist_ok=True)
 Ns=[int(t) for t in opt.lengths.split(',')];arms=[int(v) for v in opt.arms.split(',')]
 jobs=[(str(pathlib.Path(opt.exe).resolve()),str(dest),n,173911+n*553+rep*13121,arm,opt.seconds)
       for n in Ns for rep in range(opt.reps) for arm in arms]
 t0=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=opt.workers) as pool:
  rows=list(pool.map(run,jobs))
 keys=['n','seed','arm','seconds','actual_seconds','macro_proposals','macro_first_gen','macro_avg_proposedE','macro_avg_sourceE',
 'bestE','oddE','evenE','near_skew','orbit','best_bits','stdout_sha256','error']
 with (dest/'results.tsv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=keys,delimiter='\t',extrasaction='ignore')
  writer.writeheader();writer.writerows(rows)
 failures=[x for x in rows if 'error' in x]
 pair={}
 for n in Ns:
  rr=[x for x in rows if x['n']==n and 'bestE' in x]
  means={str(arm):round(sum(v['bestE'] for v in rr if v['arm']==arm)/opt.reps,3) for arm in arms}
  triggers={str(arm):sum(v['macro_proposals'] for v in rr if v['arm']==arm) for arm in arms}
  pair[str(n)]={'mean_E':means,'trigger_events':triggers}
 summary={'source':'borkob/git_labs lMAts original C solver, transient macro patch',
  'source_commit':'1aa123407636e48630174e0bf122037e369c1d68',
  'parameters':vars(opt),'job_count':len(jobs),'valid':len(rows)-len(failures),
  'failures':failures,'total_macro_events':sum(r['macro_proposals'] for r in rows),
  'by_length':pair,'runtime_wall_seconds':round(time.monotonic()-t0,2),
  'note':'GA-stagnation intervention; macro proposals plus native Tabu counted within total solver timer; compare entire independent runs'}
 (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2),flush=True)
 if failures:raise RuntimeError('some solver jobs invalid')
 # Declare arm triggers explicitly: without intervention, comparison has no statistical power.
 if any(arm!=0 and sum(z['macro_proposals'] for z in rows if z['arm']==arm)==0 for arm in arms):
  raise RuntimeError('no macro intervention occurred for at least one arm; need revise trigger')
if __name__=='__main__':main()
