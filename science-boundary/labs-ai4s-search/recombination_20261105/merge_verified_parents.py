#!/usr/bin/env python3
"""Combine independent native solver outputs with genuinely archived elite orbits.

No synthetic sources, no repeated record perturbations, no identity conflation:
native seed labels retain distinct provenance. The combined orbit hash is the
same exact 8-element LABS symmetry group used in the prior experiment.
"""
import argparse,csv,hashlib,json,pathlib,collections
def load(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def score(b):
 a=[int(z)*2-1 for z in b];n=len(a)
 return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def can(s):
 rev=s[::-1]
 flip=lambda b:''.join('1' if x=='0' else '0' for x in b)
 alt=lambda b:''.join(x if i%2==0 else ('1' if x=='0' else '0') for i,x in enumerate(b))
 return min(z for x in (s,rev) for y in (x,alt(x)) for z in (y,flip(y)))
def main():
 p=argparse.ArgumentParser();p.add_argument('--archives',type=pathlib.Path,required=True)
 p.add_argument('--native',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 pool=collections.defaultdict(dict);counts=collections.defaultdict(lambda:collections.Counter())
 for source,filename in [('archive',a.archives),('independent_native',a.native)]:
  for row in load(filename):
   n=int(row['n']);E=int(row['E']);bs=row['bits'];c=can(bs)
   assert len(bs)==n and E==score(bs) and c==row['canonical']
   ref=int(row['best_known']);assert E>=ref
   assert E<=int(ref*1.20+1e-8)
   key=(n,c)
   counts[n][source]+=1
   if key not in pool[n]:
    pool[n][key]=dict(n=n,E=E,bits=bs,canonical=c,source=source,
      lineage=row['lineage'],source_row=row['source_row'],near=row['near'],
      best_known=ref,native_seed=row['source_row'] if source=='independent_native' else '')
   else:
    old=pool[n][key]
    assert old['E']==E
    old['source']+='+'+source
    if source=='independent_native':
     old['lineage']='independent_run_'+row['source_row']
     old['native_seed']=row['source_row']
 allp=[]
 for n,v in pool.items():
  for j,r in enumerate(sorted(v.values(),key=lambda x:(x['E'],x['canonical']))):
   r['id']=f'c{n}_{j}'
   allp.append(r)
 ref={n:min(z['best_known'] for z in v.values()) for n,v in pool.items()}
 def write(path,r):
  with path.open('w') as f:
   field=['id','n','E','bits','canonical','source','lineage','source_row','near','best_known']
   w=csv.DictWriter(f,fieldnames=field,delimiter='\t',extrasaction='ignore')
   w.writeheader();w.writerows(r)
 write(a.out/'combined20.tsv',allp)
 strong=[r for r in allp if r['E']<=ref[r['n']]*1.10+1e-9]
 write(a.out/'combined10.tsv',strong)
 out={'total20':len(allp),'total10':len(strong),
  'groups20':{str(n):{'count':len(v),'independently_discovered':sum(bool(x['native_seed']) for x in v.values()),
                       'energies':sorted(x['E'] for x in v.values())} for n,v in pool.items()},
  'groups10':{str(n):{'count':sum(z['n']==n for z in strong),
                       'native_independent':sum(z['n']==n and bool(z['native_seed']) for z in strong)} for n in pool},
  'quality_gate':'primary <= 1.10 * minimum exact known E; secondary <=1.20; known archive optimal parent and independent solver runs only',
  'caveat':'independent seeds establish independent native runs, not independent modern GPU strong solver lineages; merged archive bits may coincide with native runs',
  'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out.glob('*.tsv')}}
 (a.out/'combined_manifest.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
