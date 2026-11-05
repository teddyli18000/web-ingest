#!/usr/bin/env python3
"""Exact all-eightfold-symmetry *third-optimum recombinability* certificate.

For each ordered pair {A,B} of distinct known LABS optimum source orbits
and an archive-listed third C, compute
 min_{a∈orbit(A),b∈orbit(B),c∈orbit(C)}
   |{i:a_i=b_i != c_i}|.
This is the minimum number of *non-inherited* allele changes required
by any direct site-wise AB recombination to reach an orientation of C.
No local descent or other innovation can be silently identified as crossover.
"""
import argparse,csv,collections,itertools,json,pathlib
def variants(s):
 def inv(t):return ''.join('1' if c=='0' else '0' for c in t)
 def alt(t):return ''.join(c if i%2==0 else ('1' if c=='0' else '0') for i,c in enumerate(t))
 return sorted({u for r in (s,s[::-1]) for t in (r,alt(r)) for u in (t,inv(t))})
def E(s):
 a=[int(c)*2-1 for c in s];n=len(a)
 return sum(sum(a[i]*a[i+k] for i in range(n-k))**2 for k in range(1,n))
def compute(parents):
 data=collections.defaultdict(list)
 for r in parents:
  n=int(r['n']);s=r['bits']
  assert len(s)==n and E(s)==int(r['E']) and variants(s)[0]==r['canonical']
  data[n].append(r)
 results={'by_length':{},'triples':[],
 'interpretation':'positive min consensus disagreements excludes EXACT listed third orbit by pure allele mixing in any of the eight LABS symmetry orientations; not an exclusion of mutation/local descent or an unlisted near optimum'}
 for n,group in sorted(data.items()):
  if len(group)<3:continue
  scores=[]
  for i,j in itertools.combinations(range(len(group)),2):
   A,B=group[i],group[j]
   for k,C in enumerate(group):
    if k==i or k==j:continue
    best=n;witness=None
    for a in variants(A['bits']):
     for b in variants(B['bits']):
      same=[p for p in range(n) if a[p]==b[p]]
      for c in variants(C['bits']):
       conflicts=[p for p in same if c[p]!=a[p]]
       if len(conflicts)<best:
        best=len(conflicts);witness={'agreement_positions':len(same),'necessary_nondonor_positions':conflicts}
    assert witness is not None
    scores.append(best)
    results['triples'].append({'N':n,'A':A['id'],'B':B['id'],'C':C['id'],
                              'C_E':int(C['E']),'min_uninheritable':best,**witness})
  vals=sorted(scores)
  results['by_length'][str(n)]={'n_triples':len(vals),'min_uninheritable':vals[0],
    'median_uninheritable':vals[len(vals)//2],'max_uninheritable':vals[-1],
    'direct_recombinable_known_thirds':sum(z==0 for z in vals),
    'triples_requiring_at_most_four_extra_bit_edits':sum(z<=4 for z in vals)}
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args()
 with a.parents.open() as f:pool=list(csv.DictReader(f,delimiter='\t'))
 r=compute(pool)
 for n,expected in [(46,3),(47,60),(50,3)]:
  assert r['by_length'][str(n)]['n_triples']==expected
  assert r['by_length'][str(n)]['direct_recombinable_known_thirds']==0
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r['by_length'],indent=2))
 print('CERTIFIED all symmetry-triplet consensus incompatibility conditions')
