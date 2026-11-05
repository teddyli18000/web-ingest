#!/usr/bin/env python3
"""Exact known-target oracle analysis of the inherent *target exclusion* bias
created when a progressive elite A->B path irreversibly locks B alleles.

Does NOT score any learned or deployed policy. Exhaustively enumerate all
orientations of every known N46/47/50 third optimum; compare compatibility
with the nearest-Hamming B alignment and with all possible B orientations.
For a fixed third target C and a uniform m-subset of d A/B differences,
probability locks agree with C is C(d-u,m)/C(d,m), where
u = # {i:A_i!=B_i and B_i!=C_i}.
"""
import argparse,csv,collections,itertools,json,math,pathlib
from fractions import Fraction

def variants(s):
 def invert(x):return ''.join('1' if c=='0' else '0' for c in x)
 def alt(x):return ''.join(c if i%2==0 else invert(c) for i,c in enumerate(x))
 return sorted({z for b in (s,s[::-1]) for t in (b,alt(b)) for z in (t,invert(t))})
def hd(a,b):return sum(x!=y for x,y in zip(a,b))
def exactE(b):
 x=[2*int(a)-1 for a in b];n=len(b)
 return sum(sum(x[i]*x[i+k] for i in range(n-k))**2 for k in range(1,n))
def probability(d,u,m):
 return Fraction(math.comb(d-u,m),math.comb(d,m)) if m<=d-u else Fraction(0)
def geometry(A,B,C):
 dsite=[i for i in range(len(A)) if A[i]!=B[i]]
 u=sum(B[i]!=C[i] for i in dsite)
 return len(dsite),u
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parents',type=pathlib.Path,required=True)
 ap.add_argument('--out',type=pathlib.Path,required=True)
 a=ap.parse_args()
 with a.parents.open() as f:p=list(csv.DictReader(f,delimiter='\t'))
 groups=collections.defaultdict(list)
 for z in p:
  n=int(z['n'])
  if n in (46,47,50):
   assert exactE(z['bits'])==int(z['E'])
   groups[n].append(z)
 result={'scope':'exact known-optimum triple oracle; no hidden target information available to an actual operator',
         'meaning':'probability that uniformly chosen locked B source-difference positions do not disagree with a target C representation',
         'triples':[], 'by_length':{}}
 for n,pool in sorted(groups.items()):
  for i,j in itertools.combinations(range(len(pool)),2):
   A,B=pool[i],pool[j]; aa=A['bits']
   nearest=min(variants(B['bits']),key=lambda b:(hd(aa,b),b))
   da=hd(aa,nearest)
   for k,C in enumerate(pool):
    if k in (i,j):continue
    cvars=variants(C['bits'])
    best=min((geometry(aa,nearest,c)[1],c) for c in cvars)
    u=best[0]
    stage_counts=[(da*z+3)//4 for z in (1,2,3,4)]
    probabilities=[float(probability(da,u,m)) for m in stage_counts]
    # Jointly choose any B and C orientation at each stage; an *oracle*
    # optimistic upper bound, not an available adaptive action.
    optimistic=[]
    for stage in (1,2,3,4):
     maximum=Fraction(0)
     for b in variants(B['bits']):
      d=hd(aa,b);m=(d*stage+3)//4
      for c in cvars:
       _,v=geometry(aa,b,c)
       maximum=max(maximum,probability(d,v,m))
     optimistic.append(float(maximum))
    result['triples'].append(dict(N=n,A=A['id'],B=B['id'],target=C['id'],
      nearest_B_distance=da,minimum_B_conflict_sites=u,
      stage_locked_sites=stage_counts,nearest_stage_target_compatibility=probabilities,
      fully_locked_target_inaccessible=(u>0),
      symmetry_optimistic_target_compatibility=optimistic))
  sub=[z for z in result['triples'] if z['N']==n]
  for t in sub:assert all(0<=v<=1 for v in t['nearest_stage_target_compatibility'])
  result['by_length'][str(n)]={
   'known_third_optimum_triples':len(sub),
   'nearest_B_conflicts_min':min(z['minimum_B_conflict_sites'] for z in sub),
   'nearest_B_conflicts_median':sorted(z['minimum_B_conflict_sites'] for z in sub)[len(sub)//2],
   'nearest_B_conflicts_max':max(z['minimum_B_conflict_sites'] for z in sub),
   'all_B_locked_excludes_known_C':sum(z['fully_locked_target_inaccessible'] for z in sub),
   'median_maximally_C_aligned_halfway_compatibility':
       sorted(z['nearest_stage_target_compatibility'][1] for z in sub)[len(sub)//2],
   'mean_maximally_C_aligned_halfway_compatibility':
       sum(z['nearest_stage_target_compatibility'][1] for z in sub)/len(sub),
   'median_oracle_BC_aligned_halfway_compatibility':
       sorted(z['symmetry_optimistic_target_compatibility'][1] for z in sub)[len(sub)//2]}
 assert len(result['triples'])==66
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result['by_length'],indent=2))
 print('PASS exact 66 triple-orbit hypergeometric locked-donor compatibility certificates')
if __name__=='__main__':main()
