#!/usr/bin/env python3
import argparse, json, pathlib, time

TARGET_NAMES=['w45','w59','w52','w57','w53','w49','w58','w55','w56']


def var(i):
    return sum((((x>>i)&1)<<x) for x in range(16))


def source_targets():
    a,b,c,d=[var(i) for i in range(4)]
    w42=a&b; w43=w42^c; w44=w43&d; w45=b^w44; w46=w42&c; w47=d^w46
    w48=a&w47; w49=w43^w48; w50=w48^b; w51=w49&w50; w52=w51^a; w53=w52^w49
    w54=w45&w53; w55=w54^w47; w56=w55^w49; w57=w53^w45; w58=w56^w57; w59=w55^w45
    return [a,b,c,d],[w45,w59,w52,w57,w53,w49,w58,w55,w56]


def rank_masks(ms):
    piv=[]
    for x in ms:
        y=x
        for p in piv:y=min(y,y^p)
        if y:piv.append(y);piv.sort(reverse=True)
    return len(piv)


def zsel(z3,idx,vals):
    e=vals[0]
    for k in range(1,len(vals)):
        e=z3.If(idx==k,vals[k],e)
    return e


def main():
    import z3
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis',default='1,2,4,8')
    ap.add_argument('--gates',type=int,default=17)
    ap.add_argument('--ands',type=int,default=5)
    ap.add_argument('--pattern',choices=['free','jain5'],default='jain5')
    ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    bm=[int(x,0) for x in args.basis.split(',')]
    assert len(bm)==4 and rank_masks(bm)==4
    prim,targets=source_targets(); BV=lambda x:z3.BitVecVal(x,16)
    ins=[]
    for m in bm:
        v=0
        for i,t in enumerate(prim):
            if (m>>i)&1:v^=t
        ins.append(BV(v))

    s=z3.Solver(); s.set(timeout=args.timeout*1000,random_seed=args.seed)
    vals=list(ins); A=[];B=[];O=[]; AND=[]
    # Jain five-AND schedule, 1-based AND gate positions 2,4,8,11,13.
    jpat=[0,2,0,2,0,0,0,2,0,0,2,0,2,0,0,0,0]
    for i in range(args.gates):
        n=len(vals); a=z3.Int(f'a{i}'); b=z3.Int(f'b{i}'); o=z3.Int(f'o{i}')
        s.add(a>=0,a<n,b>=0,b<n,a<b)
        if args.pattern=='jain5':
            if jpat[i]==2:s.add(o==2)
            else:s.add(o==0)  # all known target/core functions are zero-preserving; no XNOR needed here
        else:
            s.add(o>=0,o<=2)
        av=zsel(z3,a,vals); bv=zsel(z3,b,vals)
        v=z3.If(o==0,av^bv,z3.If(o==1,~(av^bv),av&bv))
        vals.append(v); A.append(a);B.append(b);O.append(o);AND.append(z3.If(o==2,1,0))

    if args.pattern=='free':
        s.add(z3.Sum(AND)==args.ands)
    # No duplicate functions, including duplicates of inputs.
    s.add(z3.Distinct(*vals))
    gatevals=vals[4:]

    # The goal is a SET: every one of the nine target functions must occur as a gate wire.
    target_hit=[]
    for t in targets:
        target_hit.append(z3.Or(*[v==BV(t) for v in gatevals]))
    s.add(*target_hit)

    # Gate-level target flags. Since all vals are distinct, each target occurs at most once.
    is_target=[]
    for v in gatevals:
        is_target.append(z3.Or(*[v==BV(t) for t in targets]))
    s.add(z3.Sum([z3.If(x,1,0) for x in is_target])==len(targets))

    # Prefix feasibility: only G-k gates remain after the first k gates, so by then at least
    # 9-(G-k) targets must already have appeared. These constraints are logically implied by
    # the full goal but make the finite horizon explicit to the solver.
    for k in range(1,args.gates+1):
        need=max(0,len(targets)-(args.gates-k))
        if need:
            s.add(z3.Sum([z3.If(is_target[i],1,0) for i in range(k)])>=need)

    # No dead helpers: every non-target gate must feed a later gate.
    for i in range(args.gates):
        idx=4+i
        later=[]
        for j in range(i+1,args.gates):
            later += [A[j]==idx,B[j]==idx]
        if later:
            s.add(z3.Or(is_target[i], *later))
        else:
            s.add(is_target[i])

    t0=time.time(); r=s.check(); dt=time.time()-t0
    summary={'basis_masks':bm,'gates':args.gates,'ands':args.ands,'pattern':args.pattern,'seed':args.seed,
             'solver':str(r),'seconds':round(dt,3),'reason':s.reason_unknown() if r==z3.unknown else None}
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)

    if r==z3.sat:
        m=s.model(); names=[f'b{i}' for i in range(4)]; gs=[]; ops=['XOR','XNOR','AND']; truth=[]
        for i in range(args.gates):
            ai=m.eval(A[i]).as_long();bi=m.eval(B[i]).as_long();oi=m.eval(O[i]).as_long();name=f'c{i}'
            gs.append({'op':ops[oi],'a':names[ai],'b':names[bi],'out':name});names.append(name)
        # Independent 16-state evaluation and target-wire identification.
        wire_tts={f'b{i}':ins[i].as_long() for i in range(4)}
        for g in gs:
            p,q=wire_tts[g['a']],wire_tts[g['b']]
            wire_tts[g['out']]=(p&q) if g['op']=='AND' else ((p^q) if g['op']=='XOR' else ((~(p^q))&0xffff))
        target_outputs={}
        for nm,t in zip(TARGET_NAMES,targets):
            hits=[n for n,v in wire_tts.items() if v==t and n.startswith('c')]
            assert len(hits)==1,(nm,hits)
            target_outputs[nm]=hits[0]
        model={'basis_masks':bm,'gates':gs,'target_outputs':target_outputs}
        json.dump(model,open(outdir/'core17.json','w'),indent=2)
        summary['target_outputs']=target_outputs
        summary['and_count']=sum(g['op']=='AND' for g in gs)

    json.dump(summary,open(outdir/'summary.json','w'),indent=2)
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__':main()
