#!/usr/bin/env python3
import argparse
import itertools
import json
from pathlib import Path

Q=7;D=5;U=Q**D;N=367;TARGET=134770
DELTAS=list(itertools.product((-1,0,1),repeat=D))

def enc(w):
 v=0
 for x in w:v=v*Q+x
 return v

def dec(v):
 a=[0]*D
 for i in range(D-1,-1,-1):a[i],v=v%Q,v//Q
 return tuple(a)
DIG=tuple(dec(v) for v in range(U))
def conflict(a,b):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(DIG[a],DIG[b]))
def neighbors(v):
 d=DIG[v]
 return [enc(tuple((d[i]+z[i])%Q for i in range(D))) for z in DELTAS]
NB={}
def nb(v):
 if v not in NB:NB[v]=neighbors(v)
 return NB[v]
def load_r(path):
 r=[enc(tuple(map(int,l.split()))) for l in path.read_text().splitlines() if l.strip()]
 if len(r)!=N or len(set(r))!=N:raise ValueError('bad R')
 return r
def make_x(r):
 x=[]
 for rid in r:
  w=DIG[rid];x.append(enc(((2-w[1])%Q,w[3],w[0],(2-w[2])%Q,w[4])))
 x[267]=enc((1,5,6,3,5));return x
def analyze(state):
 inside=set(state);cnt=[0]*U;own=[-1]*U
 for z in state:
  for q in nb(z):
   cnt[q]+=1
   if cnt[q]==1:own[q]=z
   else:own[q]=-2
 return [(own[q],q) for q in range(U) if q not in inside and cnt[q]==1]
def footprint(v,x):
 m=0
 for i,z in enumerate(x):
  if conflict(v,z):m|=1<<i
 return m
def translate_id(v,t):return enc(tuple((a+b)%Q for a,b in zip(DIG[v],DIG[t])))
def diff_id(f,x):return enc(tuple((a-b)%Q for a,b in zip(DIG[f],DIG[x])))
def dec10(v):
 a=['0']*(2*D)
 for i in range(2*D-1,-1,-1):a[i],v=str(v%Q),v//Q
 return ''.join(a)

def independent(vals):
 return all(not conflict(a,b) for a,b in itertools.combinations(vals,2))

def try_ports(state,pairs,x):
 by={}
 for c,a in pairs:by.setdefault(c,[]).append(a)
 centers=list(by)
 if len(centers)<9:return None
 # One-swap states observed here have 9 private centers; still handle alternatives exactly.
 for csel in itertools.combinations(centers,9):
  alt_lists=[by[c] for c in csel]
  for alts in itertools.product(*alt_lists):
   pair=list(zip(csel,alts))
   fp={v:footprint(v,x) for p in pair for v in p}
   nbs={v:set(nb(v)) for p in pair for v in p}
   for bits in range(1<<9):
    ph=[];pv=[];hu=vu=0
    ok=True
    for j,(c,a) in enumerate(pair):
     s=(bits>>j)&1;h=(c,a)[s];v=(c,a)[1-s]
     if any(conflict(h,z) for z in ph) or any(conflict(v,z) for z in pv):ok=False;break
     ph.append(h);pv.append(v);hu|=fp[h];vu|=fp[v]
    if not ok:continue
    overlap=(hu&vu).bit_count()
    if overlap>1:continue
    H=set().union(*(nbs[z] for z in ph));V=set().union(*(nbs[z] for z in pv));F=H&V
    blocked=set()
    for f in F:
     for q in x:
      blocked.add(diff_id(f,q))
      if len(blocked)==U:break
     if len(blocked)==U:break
    if len(blocked)==U:continue
    t=next(v for v in range(U) if v not in blocked)
    xp=[translate_id(q,t) for q in x]
    if len(set(xp))!=N or not independent(xp):raise RuntimeError('translation broke independence')
    if any(any(conflict(z,h) for h in ph) and any(conflict(z,v) for v in pv) for z in xp):raise RuntimeError('translation check mismatch')
    ports=[{'center':c,'alt':a,'side':(bits>>j)&1} for j,(c,a) in enumerate(pair)]
    return ports,xp,overlap,len(F),t
 return None

def build(state,xp,ports):
 centers={p['center'] for p in ports};B=[z for z in state if z not in centers]
 ph=[(p['center'],p['alt'])[p['side']] for p in ports];pv=[(p['center'],p['alt'])[1-p['side']] for p in ports]
 A={i for i,z in enumerate(xp) if any(conflict(z,p) for p in pv)};Ds={i for i,z in enumerate(xp) if any(conflict(z,p) for p in ph)}
 if A&Ds:raise RuntimeError('overlap at build')
 cand={a*U+b for a in B for b in B}
 for i,z in enumerate(xp):
  for p in ports:
   ep=(p['center'],p['alt']);s=p['side'];hi=int((s==0 and i in A)or(s==1 and i in Ds));vi=int((s==0 and i in Ds)or(s==1 and i in A));cand.add(z*U+ep[hi]);cand.add(ep[vi]*U+z)
 if len(cand)!=TARGET:raise RuntimeError(f'wrong score {len(cand)}')
 return cand,len(A),len(Ds)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);a=ap.parse_args();r=load_r(a.r367);x=make_x(r);p0=analyze(r);print('root private',len(p0),len({c for c,q in p0}),flush=True)
 seen={tuple(sorted(r))};checked=0;best=999
 for c,q in p0:
  s=r.copy();s[s.index(c)]=q;k=tuple(sorted(s))
  if k in seen:continue
  seen.add(k);pairs=analyze(s);checked+=1;print('state',checked,'private',len(pairs),'centers',len({cc for cc,aa in pairs}),flush=True)
  res=try_ports(s,pairs,x)
  if res is None:continue
  ports,xp,ov,fs,t=res;best=min(best,ov);cand,fa,fd=build(s,xp,ports);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'points':[dec10(v) for v in sorted(cand)]},separators=(',',':'))+'\n');st={'candidate':True,'score':len(cand),'method':'one-swap-nine-port-companion-translation','state':checked,'original_overlap':ov,'forbidden_5d_size':fs,'translation':t,'footprint_A':fa,'footprint_D':fd,'ports':ports};a.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(st,sort_keys=True),flush=True);return
 st={'candidate':False,'score':134753,'method':'one-swap-nine-port-companion-translation','states_checked':checked,'best_overlap_considered':None if best==999 else best};a.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(st,sort_keys=True),flush=True)
if __name__=='__main__':main()
