#!/usr/bin/env python3
"""Constructive 10D >134753 search: full 5D isometries of 41 auxiliary 367 codes.

For each port orientation PH/PV, any 367-point independent X disjoint from
D=N[PH]∩N[PV] produces a verifier-checkable 10D certificate with 367²+t²
points (t=9:134770; t=10:134789). Iterate ALL 120*32 signed-permutations
and ALL 16807 shifts, using exact-rounded FFT and integer zero replay.
"""
import argparse,base64,hashlib,itertools,json,struct,sys,time
from pathlib import Path
import numpy as np
Q=7;U=16807;P=(1,7,49,343,2401)
DIG=np.array([[v//p%7 for p in P] for v in range(U)],dtype=np.int8)
STEPS=list(itertools.product((-1,0,1),repeat=5))
def read_seed(path):
    x=json.loads(path.read_text());raw=base64.b64decode(x["data"])
    assert len(raw)==734 and hashlib.sha256(raw).hexdigest()==x["sha256_decoded_bytes"]
    return list(struct.unpack("<367H",raw))
def neigh(v):
    d=DIG[v]
    return [sum((int(d[k])+e[k])%7*P[k] for k in range(5)) for e in STEPS]
def clash(a,b):
    return all((int(x)-int(y))%7 in (0,1,6) for x,y in zip(DIG[a],DIG[b]))
def check(S):
    return len(S)==367 and len(set(S))==367 and all(not clash(x,y) for i,x in enumerate(S) for y in S[i+1:])
def priv(I):
    hit=np.zeros(U,dtype=np.int16);last=np.full(U,-1,dtype=np.int32)
    for v in I:
        n=neigh(v);hit[n]+=1;last[n]=v
    owners={}
    Iset=set(I)
    for z in np.flatnonzero(hit==1):
        if int(z) not in Iset:owners.setdefault(int(last[z]),[]).append(int(z))
    return owners
def ports(G,t):
    out=[];own=sorted(G)
    def dfs(i,H,V,pairs):
        if len(pairs)==t:out.append((pairs,H,V));return
        if i==len(own) or len(pairs)+len(own)-i<t:return
        a=own[i]
        for b in G[a]:
            for h,v in ((a,b),(b,a)):
                if all(not clash(h,x) for x in H) and all(not clash(v,y) for y in V):
                    dfs(i+1,H+[h],V+[v],pairs+[(a,b)])
        dfs(i+1,H,V,pairs)
    dfs(0,[],[],[])
    return out
def forbidden(H,V):
    a=np.zeros(U,dtype=np.bool_);b=np.zeros(U,dtype=np.bool_)
    for v in H:a[neigh(v)]=True
    for v in V:b[neigh(v)]=True
    return a&b
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tandon",type=Path);ap.add_argument("family",type=Path)
    ap.add_argument("parents",type=Path);ap.add_argument("out",type=Path)
    ap.add_argument("--shard",type=int,required=True);ap.add_argument("--shards",type=int,default=9)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    A=[int(x) for x in (a.parents/"port12a.ids").read_text().split()]
    B=[int(x) for x in (a.parents/"port12b.ids").read_text().split()]
    assert check(A) and check(B)
    tandon=json.loads((a.tandon/"data/base_c7.json").read_text())
    family=json.loads((a.family/"data/family-f.json").read_text())
    circular=read_seed(Path(__file__).resolve().parents[1]/"data/circular-phase-367-2026-11-04.json")
    library=[("port12a",A),("port12b",B),("circle",circular),("I0",tandon["I0"]),("X",tandon["X"])]
    library += [(f"F{i}",v) for i,v in enumerate(family["states"])]
    assert len(library)==41 and all(check(v) for _,v in library)
    G=priv(A);settings=[]
    for t,indices in ((9,(63,273,3)),(10,(9,))):
        collection=ports(G,t)
        assert len(collection)==(672 if t==9 else 48),(t,len(collection))
        for oi in indices:
            pairs,H,V=collection[oi];mask=forbidden(H,V)
            grid=np.zeros((7,)*5,dtype=float);grid[tuple(DIG[np.flatnonzero(mask)].T)]=1.0
            settings.append((t,oi,pairs,H,V,mask,np.fft.fftn(grid)))
    stats=[];best=None;winner=None;start=time.monotonic()
    for si,(name,S) in enumerate(library):
        if si%a.shards!=a.shard:continue
        src=DIG[S];entry={"name":name,"isometries":0,"minimum_hits":999}
        for t,oi,pairs,H,V,mask,FM in settings:
            for perm in itertools.permutations(range(5)):
                selected=src[:,perm]
                for sign in itertools.product((-1,1),repeat=5):
                    transformed=np.remainder(selected*np.asarray(sign,dtype=np.int8),7)
                    arr=np.zeros((7,)*5,dtype=float);arr[tuple(transformed.T)]=1.0
                    c=np.rint(np.fft.ifftn(np.conj(np.fft.fftn(arr))*FM).real).astype(np.int16)
                    hits=int(c.min());entry["isometries"]+=1
                    if hits<entry["minimum_hits"]:
                        shift=list(map(int,np.unravel_index(int(c.argmin()),c.shape)))
                        words={sum((int(transformed[j,k])+shift[k])%7*P[k] for k in range(5))
                               for j in range(len(transformed))}
                        assert len(words)==367 and int(mask[list(words)].sum())==hits
                        entry["minimum_hits"]=hits
                        entry["best"]={"aux":name,"t":t,"orientation":oi,"hits":hits,
                                       "perm":list(perm),"sign":list(sign),"shift":shift,
                                       "forbidden_size":int(mask.sum())}
                        if best is None or hits<best["hits"]:
                            best=entry["best"]
                            print("BEST",json.dumps(best,sort_keys=True),flush=True)
                        if hits==0:
                            winner=(entry["best"],words,pairs,H,V);break
                if winner:break
            if winner:break
        stats.append(entry)
        print("SEED",name,entry["minimum_hits"],"elapsed",round(time.monotonic()-start,3),flush=True)
        if winner:break
    if winner:
        desc,X,pairs,H,V=winner
        sys.path.insert(0,str(a.tandon.resolve()))
        from shannon.certificates import Ring
        import bpz_t9_aux_translation_fft as bpz
        points,partition=bpz.build(sum(1<<v for v in A),sum(1<<v for v in X),
                                   pairs,H,V,Ring(5))
        expected=367**2+desc["t"]**2
        assert expected>134753 and len(points)==expected and len(set(points))==expected
        (a.out/"certificate.json").write_text(json.dumps({"points":points},separators=(",",":"))+"\n")
        desc["score"]=expected;desc["partition"]=partition
    report={"method":"constructive-full-isometry-nine-ten-port","shard":a.shard,
            "source_count":len(stats),"settings":[[t,oi] for t,oi,*_ in settings],
            "best":best,"winner":winner[0] if winner else None,
            "elapsed":time.monotonic()-start,"records":stats}
    (a.out/"status.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps({k:v for k,v in report.items() if k!="records"},sort_keys=True),flush=True)
if __name__=="__main__":main()
