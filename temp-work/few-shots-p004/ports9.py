#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Minisat22

Q = 7
D = 5
U = Q**D
N = 367
TARGET = 134_770

KNOWN_PAIRS = (
    ((1,3,4,4,6),(2,3,5,4,6)),
    ((3,4,0,3,5),(2,4,6,3,5)),
    ((5,3,1,3,4),(5,3,2,3,5)),
    ((4,4,6,1,6),(5,4,6,0,6)),
    ((6,0,6,4,5),(6,1,6,5,5)),
    ((0,3,5,6,5),(6,3,5,0,5)),
    ((6,4,3,4,0),(6,4,2,4,6)),
    ((6,4,5,3,2),(6,5,5,3,1)),
)
KNOWN_J0 = {0,5,6}


def enc(w):
    v=0
    for x in w: v=v*Q+x
    return v


def dec(v):
    a=[0]*D
    for i in range(D-1,-1,-1):
        a[i]=v%Q; v//=Q
    return tuple(a)


def dec10(v):
    a=["0"]*(2*D)
    for i in range(2*D-1,-1,-1):
        a[i]=str(v%Q); v//=Q
    return "".join(a)


def conf(a,b,digits):
    return all((x-y)%Q in (0,1,Q-1) for x,y in zip(digits[a],digits[b]))


def read_r(path):
    r=[enc(tuple(map(int,line.split()))) for line in path.read_text().splitlines() if line.strip()]
    if len(r)!=N or len(set(r))!=N: raise RuntimeError("bad R367")
    return r


def make_x(r,digits):
    x=[]
    for rid in r:
        w=digits[rid]
        x.append(enc(((2-w[1])%Q,w[3],w[0],(2-w[2])%Q,w[4])))
    x[267]=enc((1,5,6,3,5))
    if len(set(x))!=N: raise RuntimeError("X duplicates")
    for i,j in combinations(range(N),2):
        if conf(x[i],x[j],digits): raise RuntimeError("X not independent")
    return x


def audit_known(r,x,digits):
    ridx={v:i for i,v in enumerate(r)}
    ph=[]; pv=[]
    for j,(ra,qa) in enumerate(KNOWN_PAIRS):
        a,b=enc(ra),enc(qa)
        if a not in ridx: raise RuntimeError("known center absent from R")
        hits=[rv for rv in r if conf(b,rv,digits)]
        if hits != [a]: raise RuntimeError("known pair is not private")
        side=0 if j in KNOWN_J0 else 1
        ep=(a,b)
        ph.append(ep[side]); pv.append(ep[1-side])
    for p,q in combinations(ph,2):
        if conf(p,q,digits): raise RuntimeError("known PH not independent")
    for p,q in combinations(pv,2):
        if conf(p,q,digits): raise RuntimeError("known PV not independent")
    hit_h={i for i,z in enumerate(x) if any(conf(z,p,digits) for p in ph)}
    hit_v={i for i,z in enumerate(x) if any(conf(z,p,digits) for p in pv)}
    if hit_h & hit_v: raise RuntimeError("known footprints overlap")
    return {"ph_footprint":len(hit_h),"pv_footprint":len(hit_v),"eta":N-len(hit_h|hit_v)}


def build_private_candidates(r,digits):
    ridx={v:i for i,v in enumerate(r)}
    candidates=[]
    support_hist={}
    for q in range(U):
        hits=[]
        for i,rv in enumerate(r):
            if conf(q,rv,digits): hits.append(i)
        support_hist[len(hits)]=support_hist.get(len(hits),0)+1
        if len(hits)==1 and q not in ridx:
            candidates.append((hits[0],q))
    return candidates,support_hist


def solve_ports(candidates,r,x,digits,k):
    pool=IDPool()
    cnf=CNF()
    # Atom (candidate, side): selected pair and PH uses endpoint side.
    atoms={}
    for ci in range(len(candidates)):
        atoms[ci]=(pool.id((ci,0)),pool.id((ci,1)))
        cnf.append([-atoms[ci][0],-atoms[ci][1]])

    # At most one alternative for the same parent center.
    by_center={}
    for ci,(ri,q) in enumerate(candidates): by_center.setdefault(ri,[]).append(ci)
    for group in by_center.values():
        glits=[atoms[ci][s] for ci in group for s in (0,1)]
        if len(glits)>1:
            enc_atmost=CardEnc.atmost(glits,bound=1,vpool=pool,encoding=EncType.seqcounter)
            cnf.extend(enc_atmost.clauses)

    all_atoms=[atoms[ci][s] for ci in range(len(candidates)) for s in (0,1)]
    exact=CardEnc.equals(all_atoms,bound=k,vpool=pool,encoding=EncType.seqcounter)
    cnf.extend(exact.clauses)

    endpoints=[]
    for ri,q in candidates: endpoints.append((r[ri],q))

    # Pairwise phase-independence constraints.
    for ci in range(len(candidates)):
        for cj in range(ci+1,len(candidates)):
            if candidates[ci][0]==candidates[cj][0]: continue
            for si in (0,1):
                for sj in (0,1):
                    hi=endpoints[ci][si]; hj=endpoints[cj][sj]
                    vi=endpoints[ci][1-si]; vj=endpoints[cj][1-sj]
                    if conf(hi,hj,digits) or conf(vi,vj,digits):
                        cnf.append([-atoms[ci][si],-atoms[cj][sj]])

    # Footprint separation on X.  For every x, no selected PH endpoint and
    # selected PV endpoint may both conflict with x.
    for xv in x:
        h_atoms=[]; v_atoms=[]
        for ci in range(len(candidates)):
            for s in (0,1):
                lit=atoms[ci][s]
                if conf(xv,endpoints[ci][s],digits): h_atoms.append(lit)
                if conf(xv,endpoints[ci][1-s],digits): v_atoms.append(lit)
        hs=set(h_atoms); vs=set(v_atoms)
        for lit in hs & vs: cnf.append([-lit])
        for a in hs:
            for b in vs:
                if a!=b: cnf.append([-a,-b])

    with Minisat22(bootstrap_with=cnf.clauses) as solver:
        sat=solver.solve()
        if not sat:
            return None,{"candidates":len(candidates),"vars":pool.top,"clauses":len(cnf.clauses)}
        model=set(v for v in solver.get_model() if v>0)

    chosen=[]
    for ci in range(len(candidates)):
        for s in (0,1):
            if atoms[ci][s] in model:
                chosen.append((ci,s))
    if len(chosen)!=k: raise RuntimeError("wrong selected port count")
    return chosen,{"candidates":len(candidates),"vars":pool.top,"clauses":len(cnf.clauses)}


def build10(chosen,candidates,r,x,digits):
    centers={candidates[ci][0] for ci,s in chosen}
    if len(centers)!=len(chosen): raise RuntimeError("duplicate centers")
    b=[rv for i,rv in enumerate(r) if i not in centers]
    selected=[]
    for ci,s in chosen:
        ri,q=candidates[ci]
        selected.append((r[ri],q,s))

    ph=[(a,q)[s] for a,q,s in selected]
    pv=[(a,q)[1-s] for a,q,s in selected]
    A={xi for xi,z in enumerate(x) if any(conf(z,p,digits) for p in pv)}
    Dset={xi for xi,z in enumerate(x) if any(conf(z,p,digits) for p in ph)}
    if A & Dset: raise RuntimeError("SAT result violates footprint separation")

    out=set(a*U+c for a in b for c in b)
    for xi,z in enumerate(x):
        for a,q,s in selected:
            ep=(a,q)
            # Literal generalization of construct_cc_10_7_134753.py:
            # side s=0 corresponds to J0, side s=1 to J1.
            hidx = int((s==0 and xi in A) or (s==1 and xi in Dset))
            vidx = int((s==0 and xi in Dset) or (s==1 and xi in A))
            out.add(z*U + ep[hidx])
            out.add(ep[vidx]*U + z)
    expected=(N-len(chosen))**2+2*len(chosen)*N
    if len(out)!=expected: raise RuntimeError(f"candidate duplicates: {len(out)} != {expected}")
    return out,A,Dset,selected


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("r367",type=Path)
    ap.add_argument("baseline",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("status",type=Path)
    args=ap.parse_args()

    digits=tuple(dec(i) for i in range(U))
    r=read_r(args.r367)
    x=make_x(r,digits)
    audit=audit_known(r,x,digits)
    print("known8",json.dumps(audit,sort_keys=True),flush=True)

    candidates,hist=build_private_candidates(r,digits)
    centers=len({ri for ri,q in candidates})
    print("private",json.dumps({"pairs":len(candidates),"centers":centers,"support_hist":hist},sort_keys=True),flush=True)

    chosen,stats=solve_ports(candidates,r,x,digits,9)
    if chosen is None:
        status={"candidate":False,"score":BASELINE_SCORE,"method":"nine-private-ports-sat","audit8":audit,"private_pairs":len(candidates),"private_centers":centers,"support_histogram":hist,**stats}
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
        print("NONE",json.dumps(status,sort_keys=True),flush=True)
        return

    candidate,A,Dset,selected=build10(chosen,candidates,r,x,digits)
    if len(candidate)!=TARGET: raise RuntimeError("9-port construction score mismatch")
    base_ids={int(p,7) for p in json.loads(args.baseline.read_text())["points"]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"points":[dec10(v) for v in sorted(candidate)]},separators=(",",":"))+"\n")
    status={
        "candidate":True,"score":len(candidate),"method":"nine-private-ports-sat",
        "audit8":audit,"private_pairs":len(candidates),"private_centers":centers,
        "support_histogram":hist,"footprint_A":len(A),"footprint_D":len(Dset),
        "ports":[{"center":"".join(map(str,digits[a])),"alternative":"".join(map(str,digits[q])),"side":s} for a,q,s in selected],
        "removed_vs_baseline":len(base_ids-candidate),"added_vs_baseline":len(candidate-base_ids),**stats,
    }
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print("FOUND",json.dumps(status,sort_keys=True),flush=True)


if __name__=="__main__": main()
