#!/usr/bin/env python3
import argparse, json, random, time, urllib.request, pathlib, hashlib

MASK=(1<<256)-1
SRC='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json'

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def inputs_truth():
    vals={}
    for bit in range(8):
        v=0
        for x in range(256):
            if (x>>bit)&1: v |= 1<<x
        vals[f'x{bit}']=v
    return vals

INP=inputs_truth()

def op_eval(op,a,b):
    if op=='XOR': return a^b
    if op=='XNOR': return (~(a^b)) & MASK
    if op=='AND': return a&b
    raise ValueError(op)

def eval_circuit(c, override_idx=None, flip=False):
    vals=dict(INP)
    for i,g in enumerate(c['gates']):
        v=op_eval(g['op'], vals[g['a']], vals[g['b']])
        if i==override_idx and flip: v ^= MASK
        vals[g['out']]=v
    return vals, [vals[o] for o in c['outputs']]

def prune_and_renumber(c):
    gates=c['gates']
    byout={g['out']:g for g in gates}
    needed=set(c['outputs'])
    stack=list(c['outputs'])
    while stack:
        w=stack.pop()
        g=byout.get(w)
        if not g: continue
        for u in (g['a'],g['b']):
            if u not in needed:
                needed.add(u); stack.append(u)
    kept=[g for g in gates if g['out'] in needed]
    mp={f'x{i}':f'x{i}' for i in range(8)}
    out=[]
    for i,g in enumerate(kept):
        ng={'op':g['op'],'a':mp[g['a']],'b':mp[g['b']],'out':f'w{i}'}
        mp[g['out']]=ng['out']; out.append(ng)
    return {'gates':out,'outputs':[mp[o] for o in c['outputs']]}

def replace_gate(c, idx, op, a, b):
    nc={'gates':[dict(g) for g in c['gates']], 'outputs':list(c['outputs'])}
    g=nc['gates'][idx]
    g['op']=op; g['a']=a; g['b']=b
    return prune_and_renumber(nc)

def alias_gate(c, idx, alias):
    nc={'gates':[dict(g) for g in c['gates']], 'outputs':list(c['outputs'])}
    old=nc['gates'][idx]['out']
    for j in range(idx+1,len(nc['gates'])):
        for k in ('a','b'):
            if nc['gates'][j][k]==old: nc['gates'][j][k]=alias
    nc['outputs']=[alias if o==old else o for o in nc['outputs']]
    del nc['gates'][idx]
    return prune_and_renumber(nc)

def care_mask(c, idx, base_out):
    _, alt=eval_circuit(c, override_idx=idx, flip=True)
    care=0
    for a,b in zip(base_out,alt): care |= a^b
    return care

def sig(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def aes_sbox(x):
    def mul(a,b):
        r=0
        for _ in range(8):
            if b&1:r^=a
            hi=a&0x80
            a=(a<<1)&0xff
            if hi:a^=0x1b
            b>>=1
        return r
    if x==0: inv=0
    else:
        inv=1; base=x; e=254
        while e:
            if e&1: inv=mul(inv,base)
            base=mul(base,base); e>>=1
    y=0
    for i in range(8):
        bit=((inv>>i)&1)^((inv>>((i+4)&7))&1)^((inv>>((i+5)&7))&1)^((inv>>((i+6)&7))&1)^((inv>>((i+7)&7))&1)^((0x63>>i)&1)
        y |= bit<<i
    return y

def independent_check(c):
    _,outs=eval_circuit(c)
    for x in range(256):
        y=sum(((outs[i]>>x)&1)<<i for i in range(8))
        if y!=aes_sbox(x): return False,x,y,aes_sbox(x)
    return True,None,None,None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--seconds',type=int,default=1200)
    ap.add_argument('--trials',type=int,default=1200)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    rng=random.Random(args.seed)
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    base=prune_and_renumber(fetch_json(SRC))
    _, target=eval_circuit(base)
    assert len(base['gates'])==103
    ok=independent_check(base)
    assert ok[0],ok
    cur=base; best=base; seen={sig(cur)}
    t0=time.time(); it=0; accepts=0; aliases=0
    events=[]
    while time.time()-t0 < args.seconds:
        it+=1
        vals,outs=eval_circuit(cur)
        idx=rng.randrange(len(cur['gates']))
        care=care_mask(cur,idx,outs)
        root=cur['gates'][idx]['out']; rv=vals[root]
        avail=[f'x{i}' for i in range(8)]+[g['out'] for g in cur['gates'][:idx]]
        cand_aliases=[w for w in avail if ((vals[w]^rv)&care)==0]
        rng.shuffle(cand_aliases)
        accepted=False
        for a in cand_aliases[:16]:
            nc=alias_gate(cur,idx,a)
            _,no=eval_circuit(nc)
            if no==target and len(nc['gates'])<=len(cur['gates']):
                s=sig(nc)
                if s not in seen:
                    oldn=len(cur['gates']); cur=nc; seen.add(s); accepts+=1; aliases+=1; accepted=True
                    events.append({'iter':it,'kind':'alias','old':oldn,'new':len(cur['gates']),'root':idx,'care_bits':care.bit_count()})
                    break
        if accepted:
            if len(cur['gates'])<len(best['gates']):
                best=cur
                json.dump(best,open(outdir/'best.json','w'),indent=2)
                if len(best['gates'])<103: break
            continue
        oldg=cur['gates'][idx]
        for _ in range(args.trials):
            a,b=rng.sample(avail,2)
            op=rng.choice(('XOR','XNOR','AND'))
            if op==oldg['op'] and {a,b}=={oldg['a'],oldg['b']}: continue
            cv=op_eval(op,vals[a],vals[b])
            if ((cv^rv)&care)!=0: continue
            nc=replace_gate(cur,idx,op,a,b)
            if len(nc['gates'])>len(cur['gates']): continue
            _,no=eval_circuit(nc)
            if no!=target: continue
            s=sig(nc)
            if s in seen: continue
            oldn=len(cur['gates']); cur=nc; seen.add(s); accepts+=1; accepted=True
            events.append({'iter':it,'kind':'rewrite','old':oldn,'new':len(cur['gates']),'root':idx,'care_bits':care.bit_count(),'op':op})
            if len(cur['gates'])<len(best['gates']):
                best=cur; json.dump(best,open(outdir/'best.json','w'),indent=2)
            break
        if len(best['gates'])<103: break
        if it%5000==0 and rng.random()<0.35: cur=base
    verified=independent_check(best)
    summary={'seed':args.seed,'iterations':it,'accepted':accepts,'aliases':aliases,'seen':len(seen),'best_gates':len(best['gates']),'seconds':round(time.time()-t0,3),'independent_check':verified[0],'events_tail':events[-30:]}
    json.dump(summary,open(outdir/'summary.json','w'),indent=2)
    if not (outdir/'best.json').exists(): json.dump(best,open(outdir/'best.json','w'),indent=2)
    print(json.dumps(summary))

if __name__=='__main__': main()
