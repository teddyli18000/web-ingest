#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import IDPool, WCNF

import generalized9 as g
import neutral2_maxsat as nm
import rank3_xzero_local_maxsat as loc

BASELINE=134753


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("r367",type=Path); ap.add_argument("baseline",type=Path); ap.add_argument("output",type=Path); ap.add_argument("model_output",type=Path); ap.add_argument("status",type=Path)
    args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U)); r0=g.load_r(args.r367); xset=g.make_x(r0,digits); r=loc.load_state(r0,digits)
    supports,_=g.support_masks(r,digits)
    base_model,base_stats=nm.solve_maxsat(loc.K9,r,xset,digits,supports)
    if base_model is None or base_stats["score"]!=BASELINE: raise RuntimeError(f"rank3 base drift: {base_stats}")
    _,hs,vs=base_model
    kset=set(loc.K9); bidx=[i for i in range(g.R_SIZE) if i not in kset]; bvals=sorted(r[i] for i in bidx); x0=xset[loc.XZERO]
    if any(g.conflict(x0,b,digits) for b in bvals): raise RuntimeError("x294 not square-zero")

    selected=[]; selected_set=set(); h_old=[[] for _ in range(g.R_SIZE)]; v_old=[[] for _ in range(g.R_SIZE)]
    for i,arr in enumerate(hs):
        for e in arr:
            idx=len(selected); p=("H",i,e); selected.append(p); selected_set.add(p); h_old[i].append((e,idx))
    for i,arr in enumerate(vs):
        for e in arr:
            idx=len(selected); p=("V",i,e); selected.append(p); selected_set.add(p); v_old[i].append((e,idx))

    x_hits=[[] for _ in range(g.U)]
    for j,xv in enumerate(xset):
        for e in loc.neighborhood(xv,digits): x_hits[e].append(j)
    vbad=[[] for _ in range(g.R_SIZE)]; hbad=[[] for _ in range(g.R_SIZE)]
    for j in range(g.R_SIZE):
        vbad[j]=[idx for e,idx in v_old[j] if g.conflict(x0,e,digits)]
        hbad[j]=[idx for e,idx in h_old[j] if g.conflict(e,x0,digits)]

    raw=[]; csets=[]; hist={}
    for ori in ("H","V"):
        same=h_old[loc.XZERO] if ori=="H" else v_old[loc.XZERO]
        bad=vbad if ori=="H" else hbad
        for e in bvals:
            p=(ori,loc.XZERO,e)
            if p in selected_set: continue
            cs={idx for f,idx in same if g.conflict(e,f,digits)}
            for j in x_hits[e]: cs.update(bad[j])
            hist[len(cs)]=hist.get(len(cs),0)+1; raw.append(p); csets.append(tuple(sorted(cs)))

    pool=IDPool(); w=WCNF()
    def vp(i): return pool.id(("new",i))
    def vd(i): return pool.id(("drop",i))
    touched=set()
    for i,cs in enumerate(csets):
        w.append([vp(i)],weight=1)
        for old in cs: touched.add(old); w.append([-vp(i),vd(old)])
    for old in sorted(touched): w.append([-vd(old)],weight=1)

    key={(p[0],p[2]):i for i,p in enumerate(raw)}; pair_clauses=0
    for i,(ori,_,e) in enumerate(raw):
        for f in loc.neighborhood(e,digits):
            j=key.get((ori,f))
            if j is not None and i<j: w.append([-vp(i),-vp(j)]); pair_clauses+=1
    hnear=[i for i,p in enumerate(raw) if p[0]=="H" and g.conflict(p[2],x0,digits)]
    vnear=[i for i,p in enumerate(raw) if p[0]=="V" and g.conflict(x0,p[2],digits)]
    for i in hnear:
        for j in vnear: w.append([-vp(i),-vp(j)]); pair_clauses+=1

    setup={"base_selected":len(selected),"new_b_endpoint_ports":len(raw),"old_conflict_histogram":hist,"touched_old_ports":len(touched),"new_pair_clauses":pair_clauses,"variables":pool.top,"hard":len(w.hard),"soft":len(w.soft)}
    print("SETUP",json.dumps(setup,sort_keys=True),flush=True)
    with RC2(w,solver="g3",adapt=True,exhaust=True,verbose=1) as rc2: model=rc2.compute(); cost=rc2.cost
    if model is None: raise RuntimeError("no local model")
    pos={v for v in model if v>0}; addi=[i for i in range(len(raw)) if vp(i) in pos]; dropi=[i for i in sorted(touched) if vd(i) in pos]
    gain=len(addi)-len(dropi); score=BASELINE+gain; adds=[raw[i] for i in addi]
    stats=dict(setup); stats.update({"selected_new":len(addi),"dropped_old":len(dropi),"net_gain":gain,"score":score,"rc2_cost":cost})
    args.model_output.parent.mkdir(parents=True,exist_ok=True); args.model_output.write_text(json.dumps({"stats":stats,"added_ports":adds,"dropped_old_indices":dropi},separators=(",",":"))+"\n")
    status={"candidate":score>BASELINE,"score":score,"method":"rank3-x294-b-endpoint-local-maxsat","stats":stats}
    if score>BASELINE:
        drop=set(dropi); keep=[p for i,p in enumerate(selected) if i not in drop]
        for p in adds:
            if any(loc.port_conflict(p,q,xset,digits) for q in keep): raise RuntimeError("new-old replay conflict")
        for i in range(len(adds)):
            for j in range(i+1,len(adds)):
                if loc.port_conflict(adds[i],adds[j],xset,digits): raise RuntimeError("new-new replay conflict")
        ports=keep+adds; cand={r[a]*g.U+r[b] for a in bidx for b in bidx}
        for ori,i,e in ports:
            xv=xset[i]; cand.add(e*g.U+xv if ori=="H" else xv*g.U+e)
        if len(cand)!=score: raise RuntimeError(f"candidate size {len(cand)} != {score}")
        baseline={int(p,7) for p in json.loads(args.baseline.read_text())["points"]}; status.update({"removed_vs_baseline":len(baseline-cand),"added_vs_baseline":len(cand-baseline)})
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({"points":[g.dec10(v) for v in sorted(cand)]},separators=(",",":"))+"\n")
        print("FOUND",json.dumps(status,sort_keys=True),flush=True)
    else: print("NONE",json.dumps(status,sort_keys=True),flush=True)
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
