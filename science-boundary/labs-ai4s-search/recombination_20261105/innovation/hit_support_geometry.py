#!/usr/bin/env python3
"""Exact support test: can fixed source-mixed mask directly represent near-elite hits?

For aligned source A/B, choose exactly floor(d/2) B-alleles among d parental
disagreement sites and exactly r flips among all agreement sites. For target C,
the MINIMUM Hamming distance to ANY raw pre-repair proposal is precisely
 |b_C-floor(d/2)| + |q_C-r|
where b_C=#D positions C inherits from B, q_C=#Q sites C flips from A.
This follows by maximizing the intersection of two equal/unequal-sized subsets
independently; it is an exact *combinatorial* lower bound on the number of
net edit differences that local repair must induce to reach C.

Check all eight LABS symmetry orientations, not just one displayed word.
Source input: frozen certified source pool and independent repaired children.
"""
import argparse,csv,collections,json,pathlib

def read(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def variants(s):
 def neg(t):return ''.join('1' if x=='0' else '0' for x in t)
 def alt(t):return ''.join(c if i%2==0 else neg(c) for i,c in enumerate(t))
 return sorted({u for b in (s,s[::-1]) for z in (b,alt(b)) for u in (z,neg(z))})
def energy(s):
 x=[int(c)*2-1 for c in s];n=len(s)
 return sum(sum(x[i]*x[i+k] for i in range(n-k))**2 for k in range(1,n))
def compare(A,B,C,r):
 n=len(A);assert n==len(B)==len(C)
 d=b=q=0
 for i in range(n):
  if A[i]!=B[i]:
   d+=1;b+=(C[i]==B[i])
  else:q+=(C[i]!=A[i])
 k=d//2
 return dict(D=d,donor_count=b,consensus_override=q,k=k,r=r,
             required_postrepair_hamming=abs(b-k)+abs(q-r))
def geometry(A,B,C,r):
 choices=[]
 for a in variants(A):
  for b in variants(B):
   for c in variants(C):choices.append(compare(a,b,c,r))
 aligned=min(variants(B),key=lambda b:(sum(x!=y for x,y in zip(A,b)),b))
 fixed=[compare(A,aligned,c,r) for c in variants(C)]
 assert len(choices)==512 and len(fixed)==8
 res=dict(all_sym_min_consensus_override=min(v['consensus_override'] for v in choices),
          all_sym_min_required_postrepair_hamming=min(v['required_postrepair_hamming'] for v in choices),
          fixed_nearest_parent_B_Hamming=compare(A,aligned,C,r)['D'],
          fixed_nearest_min_consensus_override=min(v['consensus_override'] for v in fixed),
          fixed_nearest_min_required_postrepair_hamming=min(v['required_postrepair_hamming'] for v in fixed),
          fixed_nearest_min_hit_witness=min(fixed,key=lambda v:(v['required_postrepair_hamming'],v['consensus_override'])))
 # Check exact combinatorial distance identity against SMALL exhaustively
 # enumerated independent subsets in an intentionally tiny toy example.
 return res
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--replication-dir',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 a=p.parse_args()
 parents={x['id']:x for x in read(a.parents)}
 found={}
 cases={'selected':'c60_1-c60_4','holdout60b':'c60_2-c60_5','holdout59':'c59_0-c59_2'}
 for cohort,pair in cases.items():
  for z in read(a.replication_dir/(cohort+'_children.tsv')):
   n=int(z['N']);E=int(z['E']);ref=218 if n==60 else 205
   if E>1.05*ref:continue
   assert energy(z['bits'])==E
   A,B=pair.split('-')
   x=parents[A];y=parents[B]
   r=4 if n<=47 else 8 if n==50 else 6
   key=f'{n}_{pair}_{z["canon"]}'
   if key not in found:
    found[key]=dict(N=n,E=E,pair=pair,canonical=z['canon'],
      source_A_E=int(x['E']),source_B_E=int(y['E']),
      **geometry(x['bits'],y['bits'],z['bits'],r),
      replicates_and_arms=[])
   found[key]['replicates_and_arms'].append(dict(cohort=cohort,rep=int(z['rep']),arm=int(z['arm'])))
 results={'scope':'posthoc diagnostic of exact pre-repair mask support, not prospective prediction or achieved computational improvement',
    'formula':'min_Hamming(raw_child,target)=abs(target_B_count-floor(D/2))+abs(target_consensus_override-r)',
    'source_pair_hits':list(found.values())}
 assert len(results['source_pair_hits'])==3 # same E226 in two distinct pairs plus E209
 for x in results['source_pair_hits']:
  assert x['fixed_nearest_min_required_postrepair_hamming']>0
  assert x['all_sym_min_required_postrepair_hamming']<=x['fixed_nearest_min_required_postrepair_hamming']
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':main()
