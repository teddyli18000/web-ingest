#!/usr/bin/env python3
"""Signed-component audit for the 12 smallest BB-coupled huge terminal block pairs.

The exact prize model has candidate variables x and deletion variables y.
Candidate->blocker implication edges require the same graph-cut orientation;
candidate-conflict edges require opposite orientation.  A connected signed
component is graph-cut representable iff these parity constraints are balanced.
This audit uses parity DSU to measure the actual unbalanced core size before
choosing between min-cut, branching, or componentwise MaxSAT.
"""
from __future__ import annotations
import argparse,json,sys
from collections import Counter,defaultdict
from pathlib import Path
LABELS=("B","N","A","D","O","H","V")
RECORD_CODE=(("B","B"),("N","O"),("A","H"),("D","V"),("O","N"),("H","D"),("V","A"))
TARGET=(('BN','AA'),('NB','AA'),('NN','AA'),('BN','AD'),('BN','DA'),('NB','AD'),('NB','DA'),('NN','AD'),('NN','DA'),('BN','DD'),('NB','DD'),('NN','DD'))
class PDSU:
 def __init__(self,n):self.p=list(range(n));self.sz=[1]*n;self.x=[0]*n;self.bad=[False]*n;self.edges=[0]*n
 def find(self,a):
  if self.p[a]!=a:
   q=self.p[a];r,px=self.find(q);self.x[a]^=px;self.p[a]=r
  return self.p[a],self.x[a]
 def add(self,a,b,w):
  ra,xa=self.find(a);rb,xb=self.find(b)
  if ra==rb:
   self.edges[ra]+=1
   if (xa^xb)!=w:self.bad[ra]=True
   return
  if self.sz[ra]<self.sz[rb]:ra,rb=rb,ra;xa,xb=xb,xa
  self.p[rb]=ra;self.x[rb]=xa^xb^w;self.sz[ra]+=self.sz[rb];self.bad[ra]=self.bad[ra] or self.bad[rb];self.edges[ra]+=self.edges[rb]+1

def main():
 ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
 base,_t,_e,ax=load_base(root/'data'/'base_c7.json');
 if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
 ring=base.ring;fam={'B':set(base.B.elements),'N':set(base.X0.elements),'A':set(base.XV.elements),'D':set(base.XH.elements),'O':set(base.R.elements),'H':set(base.PH.elements),'V':set(base.PV.elements)}
 owner={};op=[]
 for x,y in RECORD_CODE:
  for u in sorted(fam[x]):
   for v in sorted(fam[y]):owner[(u,v)]=len(op);op.append((u,v))
 baseline=set(owner)
 nbm={lab:[None]*ring.n for lab in LABELS}
 for lab in LABELS:
  F=fam[lab]
  for z in range(ring.n):nbm[lab][z]=tuple(q for q in ring.NB[z] if q in F)
 def block(word):
  x,y=word;return {(u,v) for u in fam[x] for v in fam[y] if (u,v) not in baseline}
 def blockers(p):
  u,v=p;out=[]
  for x,y in RECORD_CODE:
   for q in nbm[x][u]:
    for r in nbm[y][v]:out.append(owner[(q,r)])
  return tuple(out)
 rows=[]
 for w1,w2 in TARGET:
  P=block(w1);Q=block(w2);U=sorted(P|Q);uid={p:i for i,p in enumerate(U)};bs={};allb=set()
  for p in U:bs[p]=blockers(p);allb.update(bs[p])
  bsorted=sorted(allb);bid={b:len(U)+i for i,b in enumerate(bsorted)};D=PDSU(len(U)+len(bsorted));impl=0
  for p in U:
   u=uid[p]
   for b in bs[p]:D.add(u,bid[b],0);impl+=1
  # Cross conflicts; each source block is independent, so membership-index Q.
  qm=defaultdict(int)
  for x,y in Q:qm[x]|=1<<y
  conf=set()
  for p in P:
   x,y=p;u=uid[p]
   for z in ring.NB[x]:
    m=qm.get(z,0)&ring.BITS[y]
    while m:
     bb=m&-m;m-=bb;t=bb.bit_length()-1;q=(z,t)
     if q==p or q not in uid:continue
     v=uid[q]
     if u>v:u0,v0=v,u
     else:u0,v0=u,v
     conf.add((u0,v0))
  for u,v in conf:D.add(u,v,1)
  comps={}
  for i in range(len(D.p)):
   r,_=D.find(i)
   if r not in comps:comps[r]={'nodes':0,'candidates':0,'blockers':0,'bad':D.bad[r],'edges':D.edges[r]}
   c=comps[r];c['nodes']+=1
   if i<len(U):c['candidates']+=1
   else:c['blockers']+=1
  vals=sorted(comps.values(),key=lambda c:(c['bad'],c['nodes']),reverse=True);bad=[c for c in vals if c['bad']]
  rows.append({'word1':w1,'word2':w2,'candidates':len(U),'candidate_overlap':len(P&Q),'blockers':len(bsorted),'implication_edges':impl,'cross_conflicts':len(conf),'components':len(vals),'unbalanced_components':len(bad),'largest_component':max(c['nodes'] for c in vals),'largest_unbalanced':max((c['nodes'] for c in bad),default=0),'unbalanced_candidate_total':sum(c['candidates'] for c in bad),'unbalanced_blocker_total':sum(c['blockers'] for c in bad),'top_components':vals[:20]})
  print(json.dumps(rows[-1],sort_keys=True))
 out={'method':'exact-signed-component-audit-huge-terminal-prize','pairs':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
