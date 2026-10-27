#!/usr/bin/env python3
import argparse,itertools,json
from pathlib import Path
Q=7;D=5;U=Q**D;N=367;TARGET=134770

def dec5(v):
 a=[0]*D
 for i in range(D-1,-1,-1):a[i],v=v%Q,v//Q
 return tuple(a)
def dec10(v):
 a=["0"]*(2*D)
 for i in range(2*D-1,-1,-1):a[i],v=str(v%Q),v//Q
 return "".join(a)
def conf(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("result",type=Path);ap.add_argument("output",type=Path);ap.add_argument("status",type=Path);z=ap.parse_args();r=json.loads(z.result.read_text())
 if r.get("kind")!="translate-found":
  s={"candidate":False,"search":r};z.status.write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s));return
 d=tuple(dec5(v) for v in range(U));I=list(map(int,r["independent_set"]));X=list(map(int,r["companion_set"]));P=r["ports"]
 for S,n in ((I,"I"),(X,"X")):
  if len(S)!=N or len(set(S))!=N:raise ValueError(f"bad {n} size")
  for a,b in itertools.combinations(S,2):
   if conf(a,b,d):raise ValueError(f"{n} not independent")
 ins=set(I);cent=[];ph=[];pv=[]
 for p in P:
  c,a,s=int(p["center"]),int(p["alt"]),int(p["side"])
  if c not in ins or a in ins or s not in (0,1):raise ValueError("bad port")
  if [q for q in I if conf(a,q,d)]!=[c]:raise ValueError("not private")
  cent.append(c);ph.append((c,a)[s]);pv.append((c,a)[1-s])
 if len(P)!=9 or len(set(cent))!=9:raise ValueError("not 9 ports")
 for T,n in ((ph,"PH"),(pv,"PV")):
  for a,b in itertools.combinations(T,2):
   if conf(a,b,d):raise ValueError(f"{n} not independent")
 A={i for i,x in enumerate(X) if any(conf(x,p,d) for p in pv)};Ds={i for i,x in enumerate(X) if any(conf(x,p,d) for p in ph)}
 if A&Ds:raise ValueError("footprint overlap")
 B=[q for q in I if q not in set(cent)];cand={a*U+b for a in B for b in B}
 for i,x in enumerate(X):
  for p in P:
   c,a,s=int(p["center"]),int(p["alt"]),int(p["side"]);ep=(c,a);hi=int((s==0 and i in A)or(s==1 and i in Ds));vi=int((s==0 and i in Ds)or(s==1 and i in A));cand.add(x*U+ep[hi]);cand.add(ep[vi]*U+x)
 if len(cand)!=TARGET:raise ValueError(len(cand))
 z.output.parent.mkdir(parents=True,exist_ok=True);z.output.write_text(json.dumps({"points":[dec10(v) for v in sorted(cand)]},separators=(",",":"))+"\n")
 s={"candidate":True,"score":len(cand),"method":"exact-companion-translation","depth":r.get("depth"),"translation":r.get("translation"),"footprint_A":len(A),"footprint_D":len(Ds),"ports":P};z.status.write_text(json.dumps(s,indent=2,sort_keys=True)+"\n");print(json.dumps(s,sort_keys=True))
if __name__=="__main__":main()
