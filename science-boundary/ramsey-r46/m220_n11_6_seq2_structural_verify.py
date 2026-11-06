#!/usr/bin/env python3
"""Sound post-audit necessary filters for m220,n11=6,seq2.
Not a complete exclusion. Requires the separately certified universal
R=22/24 low graph boundary, d12 S<=147 and McKay's complete B88 layer.
"""
import hashlib,itertools,json
from collections import Counter
B88=(
 'U?`@?bGKdWSWRELSWk?fGtHUMVEuH@VP`}HA[Ui?',
 'U?`D@`gFCkIWwcbK\\CPVOdQWu[Cqsadm@ddCRPM?',
 'U?`@?bGpDcCY[PCyTahjgxobZG@tbAxIaMYGRY`?',
)
SHA='cdb6bbe20c73cd578590d57d896a343fceed76f5216d2a8524ccd1afd9559fb8'
def decode(code):
 n=ord(code[0])-63
 bits=((ord(c)-63>>s)&1 for c in code[1:] for s in (5,4,3,2,1,0))
 a=[0]*n
 for j in range(1,n):
  for i in range(j):
   if next(bits):a[i]|=1<<j;a[j]|=1<<i
 return a
def b88_scan():
 assert hashlib.sha256(('\n'.join(B88)+'\n').encode()).hexdigest()==SHA
 out={}
 for bi,code in enumerate(B88):
  a=decode(code)
  assert len(a)==22 and sum(x.bit_count() for x in a)==176
  for R,profile in ((22,(3,3,4,4,4,4)),(24,(4,4,4,4,4,4))):
   best=-1;count=0
   for S in itertools.combinations(range(22),6):
    mask=sum(1<<v for v in S)
    if tuple(sorted((a[v]&mask).bit_count() for v in S))!=profile:continue
    count+=1
    anti=sum(1 for q in range(22) if not(mask>>q&1) and not(a[q]&mask))
    best=max(best,anti)
   out[f'{bi}:{R}']={'sixset_candidates':count,'max_anticomplete':best}
 assert [out[f'{i}:22']['max_anticomplete'] for i in range(3)]==[3,2,2]
 assert all(out[f'{i}:24']['max_anticomplete']==-1 for i in range(3))
 return out
def matrices():
 rows=[]
 for R in (22,24):
  lm=66-R
  for x in range(67):  # e13_13
   for y in range(13): # e13_14
    b=14-y;a=156-2*x-y;rem=204-lm-a-b
    if a<0 or rem<0 or rem%2:continue
    p=rem//2
    sm=11*lm+24*p+13*a+14*b
    sh=12*a+26*x+14*y
    sj=12*b+13*y
    if not(132*17<=sm<=147*17 and 143*12<=sh<=164*12 and 154<=sj<=178):continue
    rows.append(dict(R=R,e13_13=x,e13_14=y,e12_12=p,
       e12_13=a,e12_14=b,S12=sm,S13=sh,S14=sj,
       D13=1968-sh,D12=2499-sm))
 assert len(rows)==137 and Counter(r['R'] for r in rows)=={22:74,24:63}
 return rows
def main():
 scan=b88_scan();rows=matrices()
 # A hypothetical S=164 d13 vertex v sees no degree-11 vertices.
 # S(v)=156+h13+2*k=164, k in {0,1}. Its B88 contains
 # 12-h13-k=4+k other high nonneighbors, all anticomplete to
 # the six low vertices: impossible since max anticomplete is 3.
 filtered=[r for r in rows if r['D13']>=12]
 assert len(filtered)==18
 # The high 13-vertex graph has alpha<=3 because the low graph
 # contains an independent pair and is anticomplete to highs.
 # N_H(v14) is triangle-free by K4-freeness; R(3,4)=9 => y<=8.
 surviving=[r for r in filtered if r['e13_14']<=8]
 assert len(surviving)==8 and Counter(r['R'] for r in surviving)=={22:6,24:2}
 assert {r['D13'] for r in surviving}=={12,14}
 # Let m be degree 12, l=#low neighbors, a=#d13 neighbors,
 # b=#d14 neighbors. S(m)=144+a+2b-l<=147.
 # If l<=2, >=4 low nonneighbors contain an independent pair.
 # Thus its high nonneighbors must have alpha<=2 and, by
 # R(4,3)=9, number at most 8 => a+b>=5. So l>=2;
 # l=2 forces a=5,b=0 and S(m)=147.
 # Sum low-middle edges =66-R, so >=R-15 middles have l=2.
 assert all(r['D12']<=3 for r in surviving)
 result={'campaign':'m220-n11-6-seq2-structural-post-audit',
   'degree_sequence':{'11':6,'12':17,'13':12,'14':1},
   'B88_member_sha256':SHA,'B88_low_anti_scan':scan,
   'class_matrices_initial':len(rows),
   'after_no_extreme_degree13':len(filtered),
   'after_high_degree14_neighborhood':len(surviving),
   'surviving_matrices':surviving,
   'degree12_lemma':{'min_low_neighbors':2,
     'if_exactly_two':{'degree13_neighbors':5,'degree14_neighbors':0,'S':147},
     'minimum_count_exactly_two':{'R22':7,'R24':9}},
   'status':'NECESSARY_ONLY_NOT_EXCLUDED',
   'soundness':'Exact class handshakes; complete B88 member; certified low graph boundary; classical R(3,4)=9; no row CSP.'}
 print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__':main()
