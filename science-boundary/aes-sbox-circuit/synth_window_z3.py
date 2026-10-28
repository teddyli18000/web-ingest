#!/usr/bin/env python3
import argparse, json, pathlib, urllib.request, time

MASK=(1<<256)-1
SRC='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json'
LO,HI=26,60


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def inputs_truth():
    d={}
    for b in range(8):
        v=0
        for x in range(256):
            if (x>>b)&1: v|=1<<x
        d[f'x{b}']=v
    return d

def op_eval(op,a,b):
    if op=='XOR': return a^b
    if op=='XNOR': return (~(a^b))&MASK
    if op=='AND': return a&b
    raise ValueError(op)

def evaluate(c):
    vals=inputs_truth()
    for g in c['gates']:
        vals[g['out']]=op_eval(g['op'],vals[g['a']],vals[g['b']])
    return vals,[vals[o] for o in c['outputs']]

def external_inputs(c,lo,hi):
    made={g['out'] for g in c['gates'][lo:hi]}
    out=[]; seen=set()
    for g in c['gates'][lo:hi]:
        for w in (g['a'],g['b']):
            if w not in made and w not in seen:
                seen.add(w); out.append(w)
    return out

def used_after(c,lo,hi):
    made={g['out'] for g in c['gates'][lo:hi]}
    out=[]; seen=set()
    for g in c['gates'][hi:]:
        for w in (g['a'],g['b']):
            if w in made and w not in seen:
                seen.add(w); out.append(w)
    for w in c['outputs']:
        if w in made and w not in seen:
            seen.add(w); out.append(w)
    return out

def aes_sbox(x):
    def mul(a,b):
        r=0
        for _ in range(8):
            if b&1:r^=a
            hi=a&0x80; a=(a<<1)&0xff
            if hi:a^=0x1b
            b>>=1
        return r
    if x==0: inv=0
    else:
        inv=1; b=x; e=254
        while e:
            if e&1: inv=mul(inv,b)
            b=mul(b,b); e>>=1
    y=0
    for i in range(8):
        bit=((inv>>i)&1)^((inv>>((i+4)&7))&1)^((inv>>((i+5)&7))&1)^((inv>>((i+6)&7))&1)^((inv>>((i+7)&7))&1)^((0x63>>i)&1)
        y|=bit<<i
    return y

def independent_check(c):
    _,outs=evaluate(c)
    for x in range(256):
        y=sum(((outs[i]>>x)&1)<<i for i in range(8))
        if y!=aes_sbox(x): return False,x,y,aes_sbox(x)
    return True,None,None,None

def zselect(z3,idx,vals):
    e=vals[0]
    for k in range(1,len(vals)):
        e=z3.If(idx==k,vals[k],e)
    return e

def synth(c,L,G,and_count,timeout_ms,seed,outdir):
    import z3
    vals,_=evaluate(c)
    ext=external_inputs(c,LO,HI)
    targets=used_after(c,LO,HI)
    # The whole window really has a 15-wire external cut and nine nonlinear outputs.
    assert len(ext)==15,(len(ext),ext)
    assert len(targets)==9,(len(targets),targets)
    tail_removed_refs=[]
    removed={g['out'] for g in c['gates'][LO:HI]}
    for g in c['gates'][HI:]:
        for w in (g['a'],g['b']):
            if w in removed and w not in targets: tail_removed_refs.append(w)
    assert not tail_removed_refs,tail_removed_refs

    s=z3.Solver()
    s.set(timeout=timeout_ms, random_seed=seed)
    BV=lambda v:z3.BitVecVal(v,256)
    lin_vals=[BV(vals[w]) for w in ext]
    la=[]; lb=[]; lx=[]
    for i in range(L):
        n=len(lin_vals)
        a=z3.Int(f'la{i}'); b=z3.Int(f'lb{i}'); xn=z3.Bool(f'lx{i}')
        s.add(a>=0,b>=0,a<n,b<n,a<b)
        av=zselect(z3,a,lin_vals); bv=zselect(z3,b,lin_vals)
        v=z3.If(xn,~(av^bv),av^bv)
        la.append(a); lb.append(b); lx.append(xn); lin_vals.append(v)

    # Four movable interface wires selected from the external cut plus the L linear helpers.
    iface_idx=[z3.Int(f'if{i}') for i in range(4)]
    for q in iface_idx: s.add(q>=0,q<len(lin_vals))
    for i in range(3): s.add(iface_idx[i] < iface_idx[i+1])
    iface=[zselect(z3,q,lin_vals) for q in iface_idx]
    # Require a genuine four-dimensional linear interface.
    for m in range(1,16):
        e=None
        for i in range(4):
            if (m>>i)&1: e=iface[i] if e is None else e^iface[i]
        s.add(e != BV(0))

    core_vals=list(iface)
    ca=[]; cb=[]; cop=[]
    and_flags=[]
    for i in range(G):
        n=len(core_vals)
        a=z3.Int(f'ca{i}'); b=z3.Int(f'cb{i}'); o=z3.Int(f'co{i}')
        s.add(a>=0,b>=0,a<n,b<n,a<b,o>=0,o<=2)
        av=zselect(z3,a,core_vals); bv=zselect(z3,b,core_vals)
        v=z3.If(o==0,av^bv,z3.If(o==1,~(av^bv),av&bv))
        ca.append(a); cb.append(b); cop.append(o); and_flags.append(z3.If(o==2,1,0)); core_vals.append(v)
    if and_count>=0: s.add(z3.Sum(and_flags)==and_count)

    out_idx=[]
    for j,w in enumerate(targets):
        q=z3.Int(f'out{j}'); s.add(q>=0,q<len(core_vals))
        s.add(zselect(z3,q,core_vals)==BV(vals[w])); out_idx.append(q)

    t0=time.time(); res=s.check(); elapsed=time.time()-t0
    summary={'linear_gates':L,'core_gates':G,'and_count':and_count,'seed':seed,'solver':str(res),'seconds':round(elapsed,3),'reason':s.reason_unknown() if res==z3.unknown else None,'external':ext,'targets':targets}
    if res!=z3.sat:
        return summary,None
    m=s.model()
    lin_names=list(ext); newg=[]
    for i in range(L):
        ai=m.eval(la[i]).as_long(); bi=m.eval(lb[i]).as_long(); xn=z3.is_true(m.eval(lx[i],model_completion=True))
        name=f'sL{i}'
        newg.append({'op':'XNOR' if xn else 'XOR','a':lin_names[ai],'b':lin_names[bi],'out':name})
        lin_names.append(name)
    iface_sel=[m.eval(q).as_long() for q in iface_idx]
    iface_names=[lin_names[k] for k in iface_sel]
    core_names=list(iface_names)
    ops=['XOR','XNOR','AND']
    core_defs=[]
    for i in range(G):
        ai=m.eval(ca[i]).as_long(); bi=m.eval(cb[i]).as_long(); oi=m.eval(cop[i]).as_long()
        name=f'sC{i}'
        g={'op':ops[oi],'a':core_names[ai],'b':core_names[bi],'out':name}
        newg.append(g); core_defs.append(g); core_names.append(name)
    target_sel=[m.eval(q).as_long() for q in out_idx]
    replacement={targets[j]:core_names[target_sel[j]] for j in range(len(targets))}

    tail=[]
    for g in c['gates'][HI:]:
        ng=dict(g)
        ng['a']=replacement.get(ng['a'],ng['a']); ng['b']=replacement.get(ng['b'],ng['b'])
        tail.append(ng)
    candidate={'gates':[dict(g) for g in c['gates'][:LO]]+newg+tail,'outputs':list(c['outputs'])}
    ok=independent_check(candidate)
    summary.update({'iface_selectors':iface_sel,'iface_names':iface_names,'target_selectors':target_sel,'replacement':replacement,'candidate_gates':len(candidate['gates']),'independent_check':ok[0]})
    assert ok[0],ok
    return summary,candidate

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--linear',type=int,required=True)
    ap.add_argument('--core',type=int,required=True)
    ap.add_argument('--ands',type=int,default=6)
    ap.add_argument('--timeout',type=int,default=1200,help='solver timeout seconds')
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    c=fetch(SRC)
    assert len(c['gates'])==103
    assert independent_check(c)[0]
    summary,cand=synth(c,args.linear,args.core,args.ands,args.timeout*1000,args.seed,outdir)
    if cand is not None:
        json.dump(cand,open(outdir/'certificate.json','w'),indent=2)
    json.dump(summary,open(outdir/'summary.json','w'),indent=2)
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
