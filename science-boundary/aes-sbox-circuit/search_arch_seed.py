#!/usr/bin/env python3
"""Full-circuit observability resubstitution from an arbitrary verified seed family.

Unlike the older p008 scripts this does not assume a GF(16) core boundary.  It is
intended for structurally distinct complete circuits (currently NIST A32/G103
and the merged Few Shots 101).  It permits neutral moves and bounded temporary
increases, keeps searching after intermediate improvements, and stops only at a
user target (100 by default).
"""
import argparse, hashlib, json, pathlib, random, time, urllib.request
import seed_family_census as census

MASK=(1<<256)-1
OPS=("XOR","XNOR","AND")
SEEDS={
 "nist-g103":census.DEFAULTS["nist-g103"],
 "fs-101":census.DEFAULTS["fs-101"],
}

def fetch_seed(name):
    url=SEEDS[name]
    text=census.get(url)
    if text.lstrip().startswith("{"):
        c=json.loads(text)
    else:
        c,_=census.normalize_nist(census.parse_nist(text))
    c=prune(c)
    assert independent_check(c)[0]
    return c,url

def inputs_truth():
    return census.input_tables(False)

def op_eval(op,a,b):return census.op_eval(op,a,b)

def eval_circuit(c,flip_idx=None):
    vals=inputs_truth()
    for i,g in enumerate(c["gates"]):
        v=op_eval(g["op"],vals[g["a"]],vals[g["b"]])
        if i==flip_idx:v^=MASK
        vals[g["out"]]=v
    return vals,[vals[o] for o in c["outputs"]]

def independent_check(c):
    vals,outs=eval_circuit(c)
    for x in range(256):
        y=sum(((outs[i]>>x)&1)<<i for i in range(8))
        if y!=census.aes_sbox(x):return False,x,y,census.aes_sbox(x)
    return True,None,None,None

def prune(c):
    byout={g["out"]:g for g in c["gates"]}; need=set(c["outputs"]); stack=list(need)
    while stack:
        w=stack.pop(); g=byout.get(w)
        if not g:continue
        for u in (g["a"],g["b"]):
            if u not in need:need.add(u);stack.append(u)
    kept=[g for g in c["gates"] if g["out"] in need]
    mp={f"x{i}":f"x{i}" for i in range(8)}; out=[]
    for i,g in enumerate(kept):
        ng={"op":g["op"],"a":mp[g["a"]],"b":mp[g["b"]],"out":f"w{i}"}
        mp[g["out"]]=ng["out"];out.append(ng)
    return {"gates":out,"outputs":[mp[o] for o in c["outputs"]]}

def sig(c):return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def care_mask(c,idx,base_out):
    _,alt=eval_circuit(c,idx); care=0
    for a,b in zip(base_out,alt):care|=a^b
    return care

def alias_gate(c,idx,alias):
    nc={"gates":[dict(g) for g in c["gates"]],"outputs":list(c["outputs"])}
    old=nc["gates"][idx]["out"]
    for j in range(idx+1,len(nc["gates"])):
        for k in ("a","b"):
            if nc["gates"][j][k]==old:nc["gates"][j][k]=alias
    nc["outputs"]=[alias if o==old else o for o in nc["outputs"]]
    del nc["gates"][idx]
    return prune(nc)

def replace_one(c,idx,op,a,b):
    nc={"gates":[dict(g) for g in c["gates"]],"outputs":list(c["outputs"])}
    nc["gates"][idx].update(op=op,a=a,b=b)
    return prune(nc)

def replace_two(c,idx,op1,a,b,op2,d):
    nc={"gates":[dict(g) for g in c["gates"]],"outputs":list(c["outputs"])}
    root=dict(nc["gates"][idx]); helper="__helper__"
    assert helper not in {g["out"] for g in nc["gates"]}
    hg={"op":op1,"a":a,"b":b,"out":helper}
    root.update(op=op2,a=helper,b=d)
    nc["gates"][idx:idx+1]=[hg,root]
    return prune(nc)

def accept_candidate(nc,target,seen,max_gates):
    if len(nc["gates"])>max_gates:return None
    _,outs=eval_circuit(nc)
    if outs!=target:return None
    h=sig(nc)
    if h in seen:return None
    return h

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed-family",choices=sorted(SEEDS),required=True)
    ap.add_argument("--rng-seed",type=int,required=True)
    ap.add_argument("--seconds",type=int,default=1200)
    ap.add_argument("--trials1",type=int,default=900)
    ap.add_argument("--trials2",type=int,default=1600)
    ap.add_argument("--max-extra",type=int,default=1)
    ap.add_argument("--target",type=int,default=100)
    ap.add_argument("--out",required=True)
    args=ap.parse_args(); rng=random.Random(args.rng_seed)
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    base,url=fetch_seed(args.seed_family); base_n=len(base["gates"])
    _,target=eval_circuit(base)
    max_gates=base_n+args.max_extra
    cur=base;best=base;seen={sig(base)};events=[];accepts=0
    json.dump(base,open(outdir/"normalized-seed.json","w"),indent=2)
    t0=time.time();it=0
    while time.time()-t0<args.seconds and len(best["gates"])>args.target:
        it+=1;vals,outs=eval_circuit(cur);idx=rng.randrange(len(cur["gates"]));rv=vals[cur["gates"][idx]["out"]]
        care=care_mask(cur,idx,outs);avail=[f"x{i}" for i in range(8)]+[g["out"] for g in cur["gates"][:idx]]
        moved=False
        aliases=[w for w in avail if ((vals[w]^rv)&care)==0];rng.shuffle(aliases)
        for a in aliases[:12]:
            nc=alias_gate(cur,idx,a);h=accept_candidate(nc,target,seen,max_gates)
            if h:
                old=len(cur["gates"]);cur=nc;seen.add(h);accepts+=1;moved=True
                events.append({"iter":it,"kind":"alias","old":old,"new":len(cur["gates"]),"care":care.bit_count()});break
        if not moved:
            oldg=cur["gates"][idx]
            for _ in range(args.trials1):
                a,b=rng.sample(avail,2);op=rng.choice(OPS)
                if op==oldg["op"] and {a,b}=={oldg["a"],oldg["b"]}:continue
                if ((op_eval(op,vals[a],vals[b])^rv)&care):continue
                nc=replace_one(cur,idx,op,a,b);h=accept_candidate(nc,target,seen,max_gates)
                if h:
                    old=len(cur["gates"]);cur=nc;seen.add(h);accepts+=1;moved=True
                    events.append({"iter":it,"kind":"one","old":old,"new":len(cur["gates"]),"care":care.bit_count()});break
        if not moved:
            for _ in range(args.trials2):
                a,b=rng.sample(avail,2);op1=rng.choice(OPS);hv=op_eval(op1,vals[a],vals[b])
                d=rng.choice(avail);op2=rng.choice(OPS);cv=op_eval(op2,hv,vals[d])
                if ((cv^rv)&care):continue
                nc=replace_two(cur,idx,op1,a,b,op2,d);h=accept_candidate(nc,target,seen,max_gates)
                if not h:continue
                # Temporary +1 is useful but should be rare; neutral/reducing moves always accepted.
                if len(nc["gates"])>len(cur["gates"]) and rng.random()>0.08:continue
                old=len(cur["gates"]);cur=nc;seen.add(h);accepts+=1;moved=True
                events.append({"iter":it,"kind":"two","old":old,"new":len(cur["gates"]),"care":care.bit_count()});break
        if len(cur["gates"])<len(best["gates"]):
            best=cur;json.dump(best,open(outdir/"best.json","w"),indent=2)
            print(json.dumps({"event":"new_best","seed_family":args.seed_family,"iter":it,"gates":len(best["gates"])}),flush=True)
        # Diversify around both the original architecture and the best basin.
        if it%3000==0:
            r=rng.random()
            if r<0.25:cur=base
            elif r<0.55:cur=best
        # Avoid a long excursion at max size if it is not opening anything.
        if len(cur["gates"])==max_gates and it%700==0 and rng.random()<0.3:cur=best
    ok=independent_check(best)[0]
    if not (outdir/"best.json").exists():json.dump(best,open(outdir/"best.json","w"),indent=2)
    summary={"seed_family":args.seed_family,"source":url,"rng_seed":args.rng_seed,"base_gates":base_n,
             "target":args.target,"iterations":it,"accepted":accepts,"seen":len(seen),"best_gates":len(best["gates"]),
             "seconds":round(time.time()-t0,3),"independent_check":ok,"events_tail":events[-50:]}
    json.dump(summary,open(outdir/"summary.json","w"),indent=2);print(json.dumps(summary),flush=True)
    assert ok

if __name__=="__main__":main()
