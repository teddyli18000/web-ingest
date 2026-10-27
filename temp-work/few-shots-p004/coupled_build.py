#!/usr/bin/env python3
import argparse
import itertools
import json
from pathlib import Path

Q=7; D=5; U=Q**D; N=367; TARGET=134_770

def dec5(v):
    out=[0]*D
    for i in range(D-1,-1,-1):out[i],v=v%Q,v//Q
    return tuple(out)

def dec10(v):
    out=["0"]*(2*D)
    for i in range(2*D-1,-1,-1):out[i],v=str(v%Q),v//Q
    return "".join(out)

def conflict(a,b,d):
    return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("result",type=Path);ap.add_argument("output",type=Path);ap.add_argument("status",type=Path);args=ap.parse_args()
    r=json.loads(args.result.read_text())
    if r.get("kind")!="coupled-found":
        s={"candidate":False,"search":r};args.status.write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s));return
    digits=tuple(dec5(v) for v in range(U))
    I=[int(v) for v in r["independent_set"]];X=[int(v) for v in r["companion_set"]];ports=r["ports"]
    if len(I)!=N or len(set(I))!=N or len(X)!=N or len(set(X))!=N:raise ValueError("bad 5D set size")
    for S,name in ((I,"I"),(X,"X")):
        for a,b in itertools.combinations(S,2):
            if conflict(a,b,digits):raise ValueError(f"{name} not independent")
    iset=set(I)
    centers=[];ph=[];pv=[]
    for p in ports:
        c,a,s=int(p["center"]),int(p["alt"]),int(p["side"])
        if c not in iset or a in iset or s not in (0,1):raise ValueError("bad port")
        hits=[z for z in I if conflict(a,z,digits)]
        if hits!=[c]:raise ValueError("port not private")
        centers.append(c);ph.append((c,a)[s]);pv.append((c,a)[1-s])
    if len(ports)!=9 or len(set(centers))!=9:raise ValueError("need 9 distinct ports")
    for T,name in ((ph,"PH"),(pv,"PV")):
        for a,b in itertools.combinations(T,2):
            if conflict(a,b,digits):raise ValueError(f"{name} not independent")
    A={i for i,x in enumerate(X) if any(conflict(x,p,digits) for p in pv)}
    Dset={i for i,x in enumerate(X) if any(conflict(x,p,digits) for p in ph)}
    if A&Dset:raise ValueError("footprints overlap")
    B=[z for z in I if z not in set(centers)]
    cand={a*U+b for a in B for b in B}
    for xi,x in enumerate(X):
        for p in ports:
            c,a,s=int(p["center"]),int(p["alt"]),int(p["side"]);ep=(c,a)
            hidx=int((s==0 and xi in A) or (s==1 and xi in Dset))
            vidx=int((s==0 and xi in Dset) or (s==1 and xi in A))
            cand.add(x*U+ep[hidx]);cand.add(ep[vidx]*U+x)
    if len(cand)!=TARGET:raise ValueError(f"wrong score {len(cand)}")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"points":[dec10(v) for v in sorted(cand)]},separators=(",",":"))+"\n")
    s={"candidate":True,"score":len(cand),"method":"coupled-shallow-swap-x-repair","depth":r.get("depth"),"best_overlap_seen":r.get("best_overlap_seen"),"footprint_A":len(A),"footprint_D":len(Dset),"ports":ports}
    args.status.write_text(json.dumps(s,indent=2,sort_keys=True)+"\n");print(json.dumps(s,sort_keys=True))
if __name__=="__main__":main()
