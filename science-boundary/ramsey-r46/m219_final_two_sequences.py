#!/usr/bin/env python3
"""Solver-free endpoint proof for the two final m=219 degree sequences.

This recomputes the exact degree-class integer relaxation used in the durable
workspace, and combines it with the self-contained binary-row CSP result.
"""
from math import comb
import json,argparse
from pathlib import Path
SEQS=[{11:7,12:16,13:13},{11:8,12:14,13:14}]
A_MIN={11:8,12:11,13:15};A_MAX={11:26,12:29,13:32}
B_MIN={11:116,12:101,13:88};B_MAX={11:132,12:122,13:114}
def s_interval(d,m=219): return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])
def ex_k4(n):
 q,r=divmod(n,3);p=[q+(i<r) for i in range(3)];return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))
def distributions(total,limits,p=()):
 if len(limits)==1:
  if 0<=total<=limits[0]: yield p+(total,)
  return
 lo=max(0,total-sum(limits[1:]));hi=min(limits[0],total)
 for x in range(lo,hi+1): yield from distributions(total-x,limits[1:],p+(x,))
def solve_seq(seq):
 ds=sorted(seq);k=len(ds);M=[[0]*k for _ in ds];cap=[[0]*k for _ in ds];vals=[]
 for i,d in enumerate(ds):
  for j in range(i,k):cap[i][j]=min(comb(seq[d],2),ex_k4(seq[d])) if i==j else seq[d]*seq[ds[j]]
 def check(i):
  d=ds[i];ss=2*d*M[i][i]+sum(e*M[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i);lo,hi=s_interval(d)
  if d==12:hi=min(hi,146)
  return lo*seq[d]<=ss<=hi*seq[d]
 def rec(i,rem):
  if i==k-1:
   if rem[i]<0 or rem[i]%2:return
   z=rem[i]//2
   if z>cap[i][i]:return
   M[i][i]=z
   if check(i):
    i11=ds.index(11);R=2*M[i11][i11]-sum((d-12)*M[min(i11,j)][max(i11,j)] for j,d in enumerate(ds) if d>=13);vals.append(R)
   return
  for eii in range(min(cap[i][i],rem[i]//2)+1):
   need=rem[i]-2*eii;js=list(range(i+1,k));lims=[min(cap[i][j],rem[j]) for j in js]
   if need<0 or need>sum(lims):continue
   M[i][i]=eii
   for xs in distributions(need,lims):
    nr=rem[:]
    for j,x in zip(js,xs):M[i][j]=x;nr[j]-=x
    if min(nr)>=0 and check(i):rec(i+1,nr)
 rec(0,[d*seq[d] for d in ds]);return vals
def prove(csp_path):
 csp=json.load(open(csp_path));assert csp['all_unsat'] and csp['total_pairs']==252
 if 'families' in csp:
  assert csp['families']['r3_A26_B116']['pairs']==18 and csp['families']['r3_A26_B116']['status']=='UNSAT'
  assert csp['families']['r4_A25_B116']['pairs']==54 and csp['families']['r4_A25_B116']['status']=='UNSAT'
  assert csp['families']['r4_A26_B117']['pairs']==180 and csp['families']['r4_A26_B117']['status']=='UNSAT'
 else:
  fam={}
  for r in csp['rows']:fam.setdefault(r['family'],[]).append(r)
  assert len(fam['r3_A26_B116'])==18 and all(x['status']=='UNSAT' for x in fam['r3_A26_B116'])
  assert len(fam['r4_A25_B116'])==54 and all(x['status']=='UNSAT' for x in fam['r4_A25_B116'])
  assert len(fam['r4_A26_B117'])==180 and all(x['status']=='UNSAT' for x in fam['r4_A26_B117'])
 rows=[]
 for i,s in enumerate(SEQS):
  vals=solve_seq(s);assert vals;maxR=max(vals);n=s[11]
  if i==0:
   simple_upper=2*ex_k4(n);assert simple_upper==32 and 5*n>simple_upper
  else:
   simple_upper=None;assert maxR==32 and 5*n>maxR
  rows.append({'degree_sequence':{str(k):v for k,v in s.items()},'class_relaxation_count':len(vals),'max_sum_r':maxR,'simple_turan_sum_r_upper':simple_upper,'r3_excluded_by_binary_csp':True,'r4_forced':True,'r4_excluded_by_binary_csp':True,'status':'UNSAT'})
 assert [r['max_sum_r'] for r in rows]==[31,32]
 return {'campaign':'m219-final-two-sequences','edges':219,'rows':rows,'all_unsat':True,'logic':{'r3':'r=3 implies A26/B116; all 18 fixed pairs are UNSAT in a relaxed binary row CSP','r4':'r=4 implies A25/B116 or A26/B117; all 234 fixed pairs are UNSAT in the same relaxed binary row CSP','forcing':'after r=3 is excluded, 11^7 12^16 13^13 forces r=4 by Turan on the seven low vertices; 11^8 12^14 13^14 forces r=4 by the exact degree-class relaxation max sum r=32','dependency':'the second degree-class relaxation uses the already-certified no-lucky-d12 consequence S<=146 at m=219'}}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--csp',type=Path,default=Path(__file__).resolve().parent/'results/m219-r34-binary-csp.json');ap.add_argument('--output',type=Path);a=ap.parse_args();out=prove(a.csp);text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(text,end='')
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
if __name__=='__main__':main()
