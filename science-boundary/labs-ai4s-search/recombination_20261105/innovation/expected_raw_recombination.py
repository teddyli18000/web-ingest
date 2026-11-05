#!/usr/bin/env python3
"""Exact expected raw LABS E for fixed-cardinality two-parent inheritance masks.

This is NOT a neural model nor a prediction of repaired success. It computes
E_mask[sum_lag C_lag^2] analytically for UNIFORMLY sampled donor and consensus
masks, retaining all correlations between sites caused by fixed mask weights.
Used only as an inexpensive principled cross-parent ALIGNMENT representation
that potentially distinguishes eightfold symmetry words where parent spectra
alone cannot.

For m distinct sites in a population N with exactly K uniformly selected
flips, E[prod_i X_i] = sum_{h=0}^m binom(m,h)(-2)^h
 (K)_h/(N)_h. In the correlation squared expansion, each pair of lag edges
produces up to four distinct odd-degree vertex factors. D and Q group
expectations multiply because the two fixed-size masks are independent.
"""
import argparse,csv,itertools,json,math,pathlib
from collections import defaultdict

def load(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def variants(s):
 neg=lambda t:''.join('0' if z=='1' else '1' for z in t)
 alt=lambda t:''.join(z if i%2==0 else neg(z) for i,z in enumerate(t))
 return sorted({u for b in (s,s[::-1]) for c in (b,alt(b)) for u in (c,neg(c))})
def exact_energy(s):
 a=[int(x)*2-1 for x in s]
 return sum(sum(a[i]*a[i+k] for i in range(len(a)-k))**2 for k in range(1,len(a)))
def moments(n,k):
 assert 0<=k<=n
 z=[1.]
 for m in range(1,5):
  if m>n:
   z.append(0.)
   continue
  t=0.
  for h in range(m+1):
   if h>k:continue
   p=1.
   for j in range(h):p*=(k-j)/(n-j)
   t+=math.comb(m,h)*(-2.)**h*p
  z.append(t)
 return z
def expected_raw_E(A,D,k,r):
 n=len(A);q=n-len(D)
 assert len(D)>=k and q>=r
 a=[int(x)*2-1 for x in A]
 dmask=sum(1<<i for i in D)
 mD,mQ=moments(len(D),k),moments(q,r)
 result=0.
 for lag in range(1,n):
  edges=[((1<<i)|(1<<(i+lag)),a[i]*a[i+lag]) for i in range(n-lag)]
  result+=len(edges) # self term, always (A_i A_i+lag)^2=1
  for j,(u,x) in enumerate(edges):
   for v,y in edges[j+1:]:
    bits=u^v # sites of odd degree survive: X^2=1
    ds=(bits&dmask).bit_count();qs=bits.bit_count()-ds
    result+=2*x*y*mD[ds]*mQ[qs]
 return result
def brute_expected(A,D,k,r):
 n=len(A);Q=[i for i in range(n) if i not in D];result=0;count=0
 for don in itertools.combinations(D,k):
  for inn in itertools.combinations(Q,r):
   x=list(A)
   for pos in don+inn:x[pos]='0' if x[pos]=='1' else '1'
   result+=exact_energy(''.join(x));count+=1
 return result/count
def selftest():
 for A,B in [('01001010','10110100'),('1011000111','0100110110')]:
  D=[i for i,(x,y) in enumerate(zip(A,B)) if x!=y]
  k=len(D)//2;r=1
  brute=brute_expected(A,D,k,r)
  calc=expected_raw_E(A,D,k,r)
  assert abs(brute-calc)<1e-8,(A,brute,calc)
 print('PASS independently enumerated all masks against analytic E[LABS] moment formula')
def analyze(parents,pairs):
 byid={p['id']:p for p in parents}
 out={'scope':'exact expected raw E over all fixed-count donor/consensus mask choices; no final repair, NO claim of prospective search advantage',
       'identity':'E(prod X_i)=sum binom(m,h)(-2)^h*(K)_h/(N)_h with symmetry difference of every pair of lag-edges',
       'pairs':[]}
 for ids in pairs:
  i,j=ids.split('-');A=byid[i]['bits'];B=byid[j]['bits']
  assert len(A)==len(B) and exact_energy(A)==int(byid[i]['E']) and exact_energy(B)==int(byid[j]['E'])
  n=len(A);representations=variants(B)
  dmin=min(sum(c!=u for c,u in zip(A,b)) for b in representations)
  k=dmin//2;r=4 if n<=47 else 8 if n==50 else 6
  stats=[]
  for b in representations:
   D=[z for z in range(n) if A[z]!=b[z]]
   est=expected_raw_E(A,D,k,r)
   stats.append(dict(B_oriented=b,parent_Hamming=len(D),
        expected_raw_E=est,selected_donor_count=k,selected_consensus_count=r))
  hmin=min(stats,key=lambda z:(z['parent_Hamming'],z['B_oriented']))
  ebest=min(stats,key=lambda z:(z['expected_raw_E'],z['parent_Hamming'],z['B_oriented']))
  out['pairs'].append({'source_pair':ids,'N':n,'A_E':int(byid[i]['E']),'B_E':int(byid[j]['E']),
     'minHD_B_expected_rawE':hmin['expected_raw_E'],
     'bestExpected_B_rawE':ebest['expected_raw_E'],
     'improvement_in_raw_expectedE':hmin['expected_raw_E']-ebest['expected_raw_E'],
     'change_of_representation':hmin['B_oriented']!=ebest['B_oriented'],
     'fixed_child_Hamming':k+r,'orientations':stats})
 return out
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--parents',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 p.add_argument('--pairs',default='c60_1-c60_4,c60_0-c60_3,c60_2-c60_5,c59_0-c59_2,c46_0-c46_1,c47_0-c47_2,c50_0-c50_1,c92_0-c92_1,c99_0-c99_1')
 a=p.parse_args()
 selftest()
 result=analyze(load(a.parents),a.pairs.split(','))
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps([{k:v for k,v in z.items() if k!='orientations'} for z in result['pairs']],indent=2))
if __name__=='__main__':main()
