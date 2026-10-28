#!/usr/bin/env python3
import argparse, json, pathlib, time

MASK16=(1<<16)-1
TARGET_NAMES=['w45','w59','w52','w57','w53','w49','w58','w55','w56']


def var(i):
    v=0
    for x in range(16):
        if (x>>i)&1:
            v |= 1<<x
    return v


def source_targets():
    a,b,c,d=[var(i) for i in range(4)]
    w42=a&b; w43=w42^c; w44=w43&d; w45=b^w44; w46=w42&c; w47=d^w46
    w48=a&w47; w49=w43^w48; w50=w48^b; w51=w49&w50; w52=w51^a; w53=w52^w49
    w54=w45&w53; w55=w54^w47; w56=w55^w49; w57=w53^w45; w58=w56^w57; w59=w55^w45
    return [a,b,c,d],[w45,w59,w52,w57,w53,w49,w58,w55,w56]


def rank_truths(vals):
    piv=[]
    for x in vals:
        y=x
        for p in piv:
            y=min(y,y^p)
        if y:
            piv.append(y); piv.sort(reverse=True)
    return len(piv)


def zsel(z3,idx,vals):
    e=vals[0]
    for k in range(1,len(vals)):
        e=z3.If(idx==k,vals[k],e)
    return e


def coordinates(target, basis):
    for m in range(16):
        v=0
        for i,b in enumerate(basis):
            if (m>>i)&1:
                v ^= b
        if v==target:
            return m
    raise ValueError('target not in basis span')


def completion_plan(selected, targets):
    basis_truth=[targets[i] for i in selected]
    coords=[coordinates(t,basis_truth) for t in targets]
    available={1:(selected[0],None),2:(selected[1],None),4:(selected[2],None),8:(selected[3],None)}
    remaining=[i for i in range(len(targets)) if i not in selected]

    def rec(av, rem, seq):
        if not rem:
            return seq
        keys=list(av)
        for ti in rem:
            tm=coords[ti]
            for ii,a in enumerate(keys):
                for b in keys[ii+1:]:
                    if a^b != tm:
                        continue
                    nxt=dict(av); nxt[tm]=(ti,(a,b))
                    nr=[x for x in rem if x!=ti]
                    ans=rec(nxt,nr,seq+[(ti,tm,a,b)])
                    if ans is not None:
                        return ans
        return None

    plan=rec(dict(available),remaining,[])
    if plan is None or len(plan)!=5:
        raise RuntimeError('selected basis does not admit five-target XOR closure')
    return coords,plan


def main():
    import z3
    ap=argparse.ArgumentParser()
    ap.add_argument('--targets',required=True,help='comma-separated four target names')
    ap.add_argument('--basis',default='1,2,4,8',help='four input masks in canonical a,b,c,d basis')
    ap.add_argument('--gates',type=int,default=12)
    ap.add_argument('--max-ands',type=int,default=5)
    ap.add_argument('--timeout',type=int,default=600)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    selected_names=args.targets.split(',')
    assert len(selected_names)==4 and len(set(selected_names))==4
    selected=[TARGET_NAMES.index(x) for x in selected_names]
    basis_masks=[int(x,0) for x in args.basis.split(',')]
    assert len(basis_masks)==4

    prim,targets=source_targets()
    assert rank_truths([targets[i] for i in selected])==4
    assert rank_truths([sum([],[])]) if False else True
    coords,plan=completion_plan(selected,targets)

    in_truth=[]
    for m in basis_masks:
        v=0
        for i,t in enumerate(prim):
            if (m>>i)&1:
                v ^= t
        in_truth.append(v)
    assert rank_truths(in_truth)==4

    BV=lambda x:z3.BitVecVal(x,16)
    s=z3.Solver(); s.set(timeout=args.timeout*1000,random_seed=args.seed)
    vals=[BV(v) for v in in_truth]
    A=[]; B=[]; O=[]; AND=[]
    for i in range(args.gates):
        n=len(vals)
        a=z3.Int(f'a{i}'); b=z3.Int(f'b{i}'); o=z3.Int(f'o{i}')
        s.add(a>=0,a<n,b>=0,b<n,a<b,o>=0,o<=2)
        av=zsel(z3,a,vals); bv=zsel(z3,b,vals)
        v=z3.If(o==0,av^bv,z3.If(o==1,~(av^bv),av&bv))
        vals.append(v); A.append(a); B.append(b); O.append(o); AND.append(z3.If(o==2,1,0))
    s.add(z3.Sum(AND)<=args.max_ands)
    s.add(z3.Distinct(*vals))

    outs=[]
    for j,ti in enumerate(selected):
        q=z3.Int(f'out{j}')
        s.add(q>=4,q<4+args.gates)
        s.add(zsel(z3,q,vals)==BV(targets[ti]))
        outs.append(q)
    s.add(z3.Distinct(*outs))

    t0=time.time(); r=s.check(); elapsed=time.time()-t0
    summary={
        'input_basis_masks':basis_masks,
        'selected_targets':selected_names,
        'selected_indices':selected,
        'gates':args.gates,
        'max_ands':args.max_ands,
        'seed':args.seed,
        'solver':str(r),
        'seconds':round(elapsed,3),
        'reason':s.reason_unknown() if r==z3.unknown else None,
        'completion_plan':[(TARGET_NAMES[ti],tm,a,b) for ti,tm,a,b in plan],
    }
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)

    if r==z3.sat:
        m=s.model(); names=[f'b{i}' for i in range(4)]; gates=[]; ops=['XOR','XNOR','AND']
        for i in range(args.gates):
            ai=m.eval(A[i]).as_long(); bi=m.eval(B[i]).as_long(); oi=m.eval(O[i]).as_long(); name=f'c{i}'
            gates.append({'op':ops[oi],'a':names[ai],'b':names[bi],'out':name})
            names.append(name)
        selected_wires=[names[m.eval(q).as_long()] for q in outs]
        coord_wire={1:selected_wires[0],2:selected_wires[1],4:selected_wires[2],8:selected_wires[3]}
        target_wire={selected[i]:selected_wires[i] for i in range(4)}
        for k,(ti,tm,ca,cb) in enumerate(plan):
            name=f'p{k}'
            gates.append({'op':'XOR','a':coord_wire[ca],'b':coord_wire[cb],'out':name})
            coord_wire[tm]=name; target_wire[ti]=name
        assert len(gates)==args.gates+5

        # Independent 16-state reconstruction against all nine abstract tail factors.
        for x in range(16):
            vv={f'b{i}':(basis_masks[i]&x).bit_count()&1 for i in range(4)}
            for g in gates:
                u,v=vv[g['a']],vv[g['b']]
                vv[g['out']]=(u&v) if g['op']=='AND' else ((u^v) if g['op']=='XOR' else (1^u^v))
            for ti,t in enumerate(targets):
                assert vv[target_wire[ti]]==((t>>x)&1),(x,TARGET_NAMES[ti])

        model={
            'input_basis_masks':basis_masks,
            'selected_targets':selected_names,
            'gates':gates,
            'target_outputs':{TARGET_NAMES[i]:target_wire[i] for i in range(9)},
        }
        json.dump(model,open(outdir/'core17.json','w'),indent=2)
        summary['and_count']=sum(g['op']=='AND' for g in gates)
        summary['linear_count']=sum(g['op']!='AND' for g in gates)
        summary['selected_output_wires']=selected_wires

    json.dump(summary,open(outdir/'summary.json','w'),indent=2)
    print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':
    main()
