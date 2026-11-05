#!/usr/bin/env python3
"""Fresh independent old lMAts source-run parent audit, distinct from archive roots.
Corpus is labeled historically native lMAts, NOT recent GPU-MTS frontier.
"""
import argparse,collections,concurrent.futures,csv,hashlib,json,os,pathlib,re,subprocess,time
REFERENCE={46:131,47:135,50:153,59:205,60:218}
def energy(s):
 a=[1 if c=='+' else -1 for c in s];n=len(s)
 return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def orbit(s):
 b=s.replace('+','1').replace('-','0')
 flip=lambda x:''.join('0' if q=='1' else '1' for q in x)
 alt=lambda x:''.join(q if i%2==0 else ('0' if q=='1' else '1') for i,q in enumerate(x))
 return min(t for x in (b,b[::-1]) for y in (x,alt(x)) for t in (y,flip(y)))
def solve(q):
 exe,n,seed,seconds=q
 t=time.monotonic()
 try:
  p=subprocess.run([str(exe),str(n),str(seed),str(seconds),'1','0'],capture_output=True,text=True,timeout=seconds+35)
 except subprocess.TimeoutExpired:
  return {'n':n,'seed':seed,'error':'timeout'}
 m=list(re.finditer(r'(?<![+-])([+-]{%d})\s+(\d+)\s+([\d.]+)'%n,p.stdout))
 if p.returncode or not m:return {'n':n,'seed':seed,'error':'invalid_code_or_no_sequence','tail':p.stdout[-300:]}
 b=m[-1].group(1);e=int(m[-1].group(2));true=energy(b)
 if e!=true:return {'n':n,'seed':seed,'error':'independent_exact_score_mismatch','e':e,'true':true}
 can=orbit(b)
 return {'n':n,'seed':seed,'E':e,'bits':b.replace('+','1').replace('-','0'),'canonical':can,
  'relative_gap':round((e-REFERENCE[n])/REFERENCE[n],5),
  'duration_s':seconds,'external_elapsed_s':round(time.monotonic()-t,3),'output_sha256':hashlib.sha256(p.stdout.encode()).hexdigest()}
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--solver',type=pathlib.Path,required=True)
 parser.add_argument('--out',type=pathlib.Path,required=True)
 parser.add_argument('--reps',type=int,default=8)
 parser.add_argument('--seconds',type=int,default=20)
 parser.add_argument('--workers',type=int,default=4)
 args=parser.parse_args()
 exe=args.solver.resolve();args.out.mkdir(parents=True,exist_ok=True)
 jobs=[(exe,n,918110+n*1103+rep*31157,args.seconds) for n in REFERENCE for rep in range(args.reps)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex: rows=list(ex.map(solve,jobs))
 errors=[r for r in rows if 'error' in r]
 allfile=args.out/'native_source_runs.tsv'
 with allfile.open('w') as f:
  w=csv.DictWriter(f,fieldnames=['n','seed','E','bits','canonical','relative_gap','duration_s','external_elapsed_s','output_sha256','error'],delimiter='\t',extrasaction='ignore')
  w.writeheader();w.writerows(rows)
 # Use certified independently seeded real source trajectories, never perturb another elite.
 elite=collections.defaultdict(dict)
 for r in rows:
  if 'E' not in r or r['E']>REFERENCE[r['n']]*1.2:continue
  n=r['n'];key=r['canonical']
  old=elite[n].get(key)
  if old is None or r['E']<old['E']:elite[n][key]=r
 outfile=args.out/'independent_highquality_orbits.tsv'
 with outfile.open('w') as f:
  f.write('id\tn\tE\tbits\tcanonical\tsource\tlineage\tsource_row\tnear\tbest_known\n')
  for n,items in elite.items():
   for j,z in enumerate(sorted(items.values(),key=lambda a:(a['E'],a['canonical']))):
    f.write(f"native_{n}_{j}\t{n}\t{z['E']}\t{z['bits']}\t{z['canonical']}\tpublished_2009_native_lMAts\tindependent_seed_{z['seed']}\t{z['seed']}\t-1\t{REFERENCE[n]}\n")
 meta={'source_pin':'borkob/git_labs/solvers/lMAts-lRRts/src at 1aa123407636e48630174e0bf122037e369c1d68',
  'solver':'2009 historical unrestricted lMAts, NOT 2025 GPU-MTS',
  'planned_runs':len(jobs),'valid_runs':len(rows)-len(errors),'errors':errors,
  'full_verified_orbits':{str(n):len({r['canonical'] for r in rows if r['n']==n and 'canonical' in r}) for n in REFERENCE},
  'highquality_energy_gate':'at most 1.20 * exact old optimum, no synthetic perturbations',
  'highquality_independent_source_orbits':{str(n):len(elite[n]) for n in REFERENCE},
  'count_distinct_native_parent_orbits':sum(len(z) for z in elite.values()),
  'quality_observation':'multiple seeds may reach same orbit, only one retained per canonical orbit',
  'all_rows_sha256':hashlib.sha256(allfile.read_bytes()).hexdigest()}
 (args.out/'independent_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(json.dumps(meta,indent=2))
 if errors:raise RuntimeError('some independent source runs failed')
if __name__=='__main__':main()
