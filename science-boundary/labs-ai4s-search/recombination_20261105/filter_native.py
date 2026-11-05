#!/usr/bin/env python3
"""Make an explicitly independent-run, 10%-near-optimum parent source cohort.
No historical archive sequence used as a parent in this cohort.
"""
import argparse,collections,csv,hashlib,json,pathlib
LIMIT={46:131,47:135,50:153,59:205,60:218}
def energy(s):
 a=[2*int(q)-1 for q in s];n=len(a)
 return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def orb(s):
 neg=lambda a:''.join('0' if x=='1' else '1' for x in a)
 alt=lambda a:''.join(c if i%2==0 else ('0' if c=='1' else '1') for i,c in enumerate(a))
 return min(t for x in (s,s[::-1]) for y in (x,alt(x)) for t in (y,neg(y)))
def main():
 p=argparse.ArgumentParser();p.add_argument('src',type=pathlib.Path);p.add_argument('out',type=pathlib.Path)
 a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.src.open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
 dst=[];groups=collections.defaultdict(list);seen=set()
 for r in rows:
  n=int(r['n']);e=int(r['E'])
  assert r['source']=='published_2009_native_lMAts' and r['lineage'].startswith('independent_seed_')
  assert orb(r['bits'])==r['canonical'] and energy(r['bits'])==e
  if e>LIMIT[n]*1.1:continue
  key=(n,r['canonical'])
  assert key not in seen
  seen.add(key);dst.append(r);groups[n].append(r)
 assert {n:len(x) for n,x in groups.items()}=={46:3,47:4,50:3,59:4,60:5}
 assert len({r['lineage'] for r in dst})==len(dst), 'every selected distinct orbit must have a different source seed'
 with a.out.open('w') as f:
  writer=csv.DictWriter(f,fieldnames=['id','n','E','bits','canonical','source','lineage','source_row','near','best_known'],delimiter='\t')
  writer.writeheader();writer.writerows(dst)
 manifest={'parent_count':len(dst),'selected_from_40_independent_seed_runs':True,
   'max_relative_E_gap':0.10,'no_original_archive_parent_inputs':True,
   'source_data_sha256':hashlib.sha256(a.src.read_bytes()).hexdigest(),
   'parent_data_sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),
   'by_length':{n:{'orbits':len(v),'E':[int(r['E']) for r in v],
                   'distinct_original_runs':len({r['lineage'] for r in v})} for n,v in groups.items()},
   'caution':'Different seeded native searches can still share an upstream algorithm and correlated search distribution; one run per selected orbit is independently seeded, not independence of algorithm design.'}
 a.out.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
