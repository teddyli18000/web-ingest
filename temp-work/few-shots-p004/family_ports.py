#!/usr/bin/env python3
import argparse
import itertools
import json
from pathlib import Path

Q = 7
D = 5
U = Q**D
N = 367
TARGET = 134_770


def dec5(v):
    out=[0]*D
    for i in range(D-1,-1,-1): out[i],v=v%Q,v//Q
    return tuple(out)


def enc5(w):
    v=0
    for x in w:v=v*Q+x
    return v


def dec10(v):
    out=["0"]*(2*D)
    for i in range(2*D-1,-1,-1):out[i],v=str(v%Q),v//Q
    return "".join(out)


def conflict(a,b,digits):
    return all((x-y)%Q in (0,1,Q-1) for x,y in zip(digits[a],digits[b]))


def neighbors(v,digits):
    d=digits[v]
    for delta in itertools.product((-1,0,1),repeat=D):
        yield enc5(tuple((d[i]+delta[i])%Q for i in range(D)))


def load_r(path):
    r=[enc5(tuple(map(int,line.split()))) for line in path.read_text().splitlines() if line.strip()]
    if len(r)!=N:return (_ for _ in ()).throw(ValueError("bad R367"))
    return r


def make_x(r,digits):
    x=[]
    for rid in r:
        w=digits[rid];x.append(enc5(((2-w[1])%Q,w[3],w[0],(2-w[2])%Q,w[4])))
    x[267]=enc5((1,5,6,3,5))
    return x


def private_pairs(state,digits):
    inside=set(state)
    cnt=[0]*U
    for z in state:
        for v in neighbors(z,digits):cnt[v]+=1
    out=[]
    for q,c in enumerate(cnt):
        if c!=1 or q in inside:continue
        center=next(z for z in neighbors(q,digits) if z in inside)
        out.append((center,q))
    return out


def footprint(v,xset,digits):
    m=0
    for i,x in enumerate(xset):
        if conflict(v,x,digits):m|=1<<i
    return m


def find_ports(pairs,xset,digits,k=9):
    if len(pairs)<k:return None
    foot={}
    for c,a in pairs:
        foot.setdefault(c,footprint(c,xset,digits));foot.setdefault(a,footprint(a,xset,digits))
    order=list(range(len(pairs)))
    order.sort(key=lambda i:(foot[pairs[i][0]]|foot[pairs[i][1]]).bit_count())
    chosen=[];used=set();hs=[];vs=[]

    def dfs(pos,hu,vu):
        if len(chosen)==k:return chosen.copy()
        if pos>=len(order):return None
        rem={pairs[order[t]][0] for t in range(pos,len(order)) if pairs[order[t]][0] not in used}
        if len(chosen)+len(rem)<k:return None
        for kk in range(pos,len(order)):
            order[pos],order[kk]=order[kk],order[pos]
            c,a=pairs[order[pos]]
            if c not in used:
                for side in (0,1):
                    h=(c,a)[side];v=(c,a)[1-side]
                    hf=foot[h];vf=foot[v]
                    if hf&vu or vf&hu or hf&vf:continue
                    if any(conflict(h,z,digits) for z in hs):continue
                    if any(conflict(v,z,digits) for z in vs):continue
                    used.add(c);hs.append(h);vs.append(v);chosen.append((c,a,side))
                    ans=dfs(pos+1,hu|hf,vu|vf)
                    if ans is not None:return ans
                    chosen.pop();vs.pop();hs.pop();used.remove(c)
            order[pos],order[kk]=order[kk],order[pos]
        return None
    return dfs(0,0,0)


def build_candidate(state,ports,xset,digits):
    centers={c for c,a,s in ports}
    b=[z for z in state if z not in centers]
    ph=[(c,a)[s] for c,a,s in ports]
    pv=[(c,a)[1-s] for c,a,s in ports]
    A={i for i,x in enumerate(xset) if any(conflict(x,p,digits) for p in pv)}
    Dset={i for i,x in enumerate(xset) if any(conflict(x,p,digits) for p in ph)}
    if A&Dset:raise RuntimeError("footprints overlap")
    cand={a*U+c for a in b for c in b}
    for xi,x in enumerate(xset):
        for c,a,s in ports:
            ep=(c,a)
            hidx=int((s==0 and xi in A) or (s==1 and xi in Dset))
            vidx=int((s==0 and xi in Dset) or (s==1 and xi in A))
            cand.add(x*U+ep[hidx]);cand.add(ep[vidx]*U+x)
    return cand,A,Dset


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("family_json",type=Path)
    ap.add_argument("r367",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("status",type=Path)
    args=ap.parse_args()
    digits=tuple(dec5(v) for v in range(U))
    r=load_r(args.r367);xset=make_x(r,digits)
    states=json.loads(args.family_json.read_text())["states"]
    summary=[]
    for si,state in enumerate(states):
        if len(state)!=N or len(set(state))!=N:raise RuntimeError("bad family state")
        for i,a in enumerate(state):
            for b in state[i+1:]:
                if conflict(a,b,digits):raise RuntimeError("family state not independent")
        pairs=private_pairs(state,digits)
        centers=len({c for c,a in pairs})
        summary.append({"state":si,"private_pairs":len(pairs),"private_centers":centers})
        print("state",si,"private",len(pairs),"centers",centers,flush=True)
        ports=find_ports(pairs,xset,digits,9)
        if ports is None:continue
        cand,A,Dset=build_candidate(state,ports,xset,digits)
        if len(cand)!=TARGET:
            print("state",si,"ports-found-but-score",len(cand),flush=True)
            continue
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({"points":[dec10(v) for v in sorted(cand)]},separators=(",",":"))+"\n")
        status={"candidate":True,"score":len(cand),"method":"family-f-nine-ports","state":si,"private_pairs":len(pairs),"private_centers":centers,"footprint_A":len(A),"footprint_D":len(Dset),"ports":[{"center":c,"alt":a,"side":s} for c,a,s in ports],"states_summary":summary}
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
        print("FOUND",json.dumps(status,sort_keys=True),flush=True);return
    status={"candidate":False,"score":134753,"method":"family-f-nine-ports","states":len(states),"max_private_pairs":max(s["private_pairs"] for s in summary),"max_private_centers":max(s["private_centers"] for s in summary),"states_summary":summary}
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print("NONE",json.dumps(status,sort_keys=True),flush=True)

if __name__=="__main__":main()
