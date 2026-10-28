#!/usr/bin/env python3
import argparse, json, random, time, pathlib, hashlib
import search_odc as s

OPS=('XOR','XNOR','AND')

def two_gate_replace(c, idx, op1, a, b, op2, d):
    nc={'gates':[dict(g) for g in c['gates']], 'outputs':list(c['outputs'])}
    root=nc['gates'][idx]
    helper='odc_helper_tmp'
    assert helper not in {g['out'] for g in nc['gates']}
    hg={'op':op1,'a':a,'b':b,'out':helper}
    rg=dict(root); rg['op']=op2; rg['a']=helper; rg['b']=d
    nc['gates'][idx:idx+1]=[hg,rg]
    return s.prune_and_renumber(nc)

def sig(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--seconds',type=int,default=900)
    ap.add_argument('--trials',type=int,default=2200)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    rng=random.Random(args.seed)
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    base=s.prune_and_renumber(s.fetch_json(s.SRC))
    _,target=s.eval_circuit(base)
    assert len(base['gates'])==103 and s.independent_check(base)[0]
    cur=base; best=base; seen={sig(base)}
    t0=time.time(); it=0; accepts=0; reductions=[]
    while time.time()-t0 < args.seconds:
        it+=1
        vals,outs=s.eval_circuit(cur)
        idx=rng.randrange(len(cur['gates']))
        care=s.care_mask(cur,idx,outs)
        root=cur['gates'][idx]['out']; rv=vals[root]
        avail=[f'x{i}' for i in range(8)]+[g['out'] for g in cur['gates'][:idx]]
        # First take any immediate alias, as in the one-gate walk.
        aliases=[w for w in avail if ((vals[w]^rv)&care)==0]
        rng.shuffle(aliases)
        moved=False
        for a in aliases[:8]:
            nc=s.alias_gate(cur,idx,a)
            _,no=s.eval_circuit(nc)
            if no==target and len(nc['gates'])<=len(cur['gates']) and sig(nc) not in seen:
                old=len(cur['gates']); cur=nc; seen.add(sig(nc)); accepts+=1; moved=True
                if len(cur['gates'])<old: reductions.append({'iter':it,'kind':'alias','old':old,'new':len(cur['gates'])})
                break
        if moved:
            if len(cur['gates'])<len(best['gates']):
                best=cur; json.dump(best,open(outdir/'best.json','w'),indent=2)
                if len(best['gates'])<103: break
            continue
        # Search h=op1(a,b), root'=op2(h,d). One extra gate is allowed only if pruning offsets it.
        for _ in range(args.trials):
            a,b=rng.sample(avail,2); op1=rng.choice(OPS)
            hv=s.op_eval(op1,vals[a],vals[b])
            d=rng.choice(avail); op2=rng.choice(OPS)
            if d in (a,b) and rng.random()<0.15: continue
            cv=s.op_eval(op2,hv,vals[d])
            if ((cv^rv)&care)!=0: continue
            nc=two_gate_replace(cur,idx,op1,a,b,op2,d)
            if len(nc['gates'])>len(cur['gates']): continue
            _,no=s.eval_circuit(nc)
            if no!=target: continue
            h=sig(nc)
            if h in seen: continue
            old=len(cur['gates']); cur=nc; seen.add(h); accepts+=1; moved=True
            if len(cur['gates'])<old: reductions.append({'iter':it,'kind':'two-gate','old':old,'new':len(cur['gates']),'care_bits':care.bit_count()})
            if len(cur['gates'])<len(best['gates']):
                best=cur; json.dump(best,open(outdir/'best.json','w'),indent=2)
            break
        if len(best['gates'])<103: break
        if it%2500==0 and rng.random()<0.4: cur=base
    ok=s.independent_check(best)[0]
    summary={'seed':args.seed,'iterations':it,'accepted':accepts,'seen':len(seen),'best_gates':len(best['gates']),'seconds':round(time.time()-t0,3),'independent_check':ok,'reductions':reductions[-20:]}
    json.dump(summary,open(outdir/'summary.json','w'),indent=2)
    if not (outdir/'best.json').exists(): json.dump(best,open(outdir/'best.json','w'),indent=2)
    print(json.dumps(summary))

if __name__=='__main__': main()
