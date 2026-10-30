#!/usr/bin/env python3
"""Globally resynthesize the linear network around a fixed AES AND skeleton.

Unlike the earlier pre/middle/core/output searches, this program erases all
linear-layer boundaries.  It keeps only the ordered nonlinear AND functions of a
seed.  Every AND operand and final output is represented symbolically as an
affine form of the primary inputs and earlier AND outputs.  A randomized staged
linear synthesizer then rebuilds all required forms with shared XOR/XNOR helpers
across the *entire* circuit.

This is intentionally a family-local experiment, not a lower-bound method.  A
failure says only that this heuristic did not rematerialize the selected AND
skeleton cheaply enough.
"""
import argparse, collections, json, pathlib, random, sys, time

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import seed_family_census as census


def symbolic_skeleton(c):
    n_and=sum(g['op']=='AND' for g in c['gates'])
    const=1<<(8+n_and)
    forms={f'x{i}':1<<i for i in range(8)}
    operands=[]; and_i=0; linear_forms=[]
    for g in c['gates']:
        a,b=forms[g['a']],forms[g['b']]
        if g['op']=='XOR': v=a^b
        elif g['op']=='XNOR': v=a^b^const
        elif g['op']=='AND':
            operands.append((a,b))
            v=1<<(8+and_i); and_i+=1
        else: raise ValueError(g['op'])
        forms[g['out']]=v
        if g['op']!='AND': linear_forms.append(v)
    outs=[forms[o] for o in c['outputs']]
    # Sanity: no operand may depend on its own/future AND symbol.
    for j,(a,b) in enumerate(operands):
        future_mask=sum(1<<(8+k) for k in range(j,n_and))
        assert not ((a|b)&future_mask),(j,a,b)
    return n_and,const,operands,outs,linear_forms


def gate_eval_form(op,a,b,const):
    return a^b^(const if op=='XNOR' else 0)


def synthesize(seed, rng, max_three_scan=1400, top_choices=10):
    c=seed['circuit']
    n_and,const,operands,outputs,old_linear=symbolic_skeleton(c)
    demand=collections.Counter(old_linear)
    for a,b in operands:
        demand[a]+=5; demand[b]+=5
    for t in outputs:demand[t]+=8

    gates=[]
    available={1<<i:f'x{i}' for i in range(8)}
    source_units={1<<i:f'x{i}' for i in range(8)}

    def add(op,fa,fb):
        w=f'w{len(gates)}'
        gates.append({'op':op,'a':available[fa],'b':available[fb],'out':w})
        fv=gate_eval_form(op,fa,fb,const)
        # Keep first wire for a symbolic form; duplicate forms are never useful.
        available.setdefault(fv,w)
        return fv

    def pair_map():
        items=list(available.items())
        pm={}
        for i,(fa,wa) in enumerate(items):
            for fb,wb in items[i+1:]:
                x=fa^fb
                pm.setdefault(x,(fa,fb,'XOR'))
                pm.setdefault(x^const,(fa,fb,'XNOR'))
        return pm

    def choose(scored):
        scored.sort(key=lambda z:z[0],reverse=True)
        pool=scored[:min(top_choices,len(scored))]
        # Soft rank bias rather than always taking the same local optimum.
        weights=list(range(len(pool),0,-1))
        return rng.choices(pool,weights=weights,k=1)[0]

    def direct_support(target):
        bits=[i for i in range(8+n_and) if (target>>i)&1]
        want_const=bool(target&const)
        assert bits,('constant-only target not expected',target)
        forms=[1<<i for i in bits]
        for f in forms:
            assert f in available,(target,f)
        rng.shuffle(forms)
        if len(forms)==1:
            if not want_const:return forms[0]
            # XNOR(a,a)=1, then XOR with a.  This path is rarely needed.
            a=forms[0]; one=const
            if one not in available:
                add('XNOR',a,a)
            add('XOR',a,one)
            return target
        cur=forms.pop()
        first=True
        while forms:
            # Prefer a next source whose resulting helper is demanded elsewhere.
            cand=[]
            for f in forms:
                op='XNOR' if want_const and first else 'XOR'
                h=gate_eval_form(op,cur,f,const)
                cand.append((demand[h]+rng.random()*0.2,f,op,h))
            _,f,op,h=choose(cand)
            forms.remove(f); add(op,cur,f); cur=h; first=False
        assert cur==target,(cur,target)
        return cur

    def ensure(target):
        if target in available:return target
        pm=pair_map()
        # One gate.
        if target in pm:
            a,b,op=pm[target]; add(op,a,b); return target

        # Two gates: helper h from one gate, then h (+/~+) d = target.
        scored=[]
        av=list(available)
        for d in av:
            for op2 in ('XOR','XNOR'):
                h=target^d^(const if op2=='XNOR' else 0)
                if h in available or h not in pm:continue
                a,b,op1=pm[h]
                score=8*demand[h]+rng.random()
                scored.append((score,h,a,b,op1,d,op2))
        if scored:
            _,h,a,b,op1,d,op2=choose(scored)
            add(op1,a,b)
            assert h in available
            add(op2,h,d)
            assert target in available
            return target

        # Three gates: two one-gate helpers followed by XOR/XNOR.  Scan a
        # randomized subset of pair forms to keep each trial cheap.
        keys=list(pm)
        rng.shuffle(keys)
        scored=[]
        for p in keys[:max_three_scan]:
            for op3 in ('XOR','XNOR'):
                q=target^p^(const if op3=='XNOR' else 0)
                if q==p or q not in pm:continue
                a,b,op1=pm[p]; d,e,op2=pm[q]
                # Avoid the degenerate case where adding p changes the chosen q
                # expression only in naming; formal forms make the final check exact.
                score=5*(demand[p]+demand[q])+rng.random()
                scored.append((score,p,q,a,b,op1,d,e,op2,op3))
        if scored:
            _,p,q,a,b,op1,d,e,op2,op3=choose(scored)
            if p not in available:add(op1,a,b)
            if q not in available:
                # q's recorded decomposition used the pre-p available set.
                add(op2,d,e)
            add(op3,p,q)
            assert target in available
            return target
        return direct_support(target)

    for j,(ta,tb) in enumerate(operands):
        pair=[ta,tb]
        if rng.random()<0.5:pair.reverse()
        for t in pair:ensure(t)
        wa,wb=available[ta],available[tb]
        out=f'w{len(gates)}'
        gates.append({'op':'AND','a':wa,'b':wb,'out':out})
        sym=1<<(8+j)
        available[sym]=out; source_units[sym]=out

    out_forms=list(outputs)
    # Synthesize higher-demand output forms first to maximize sharing.
    order=list(range(len(out_forms)))
    rng.shuffle(order)
    order.sort(key=lambda i:demand[out_forms[i]],reverse=True)
    for i in order:ensure(out_forms[i])
    result={'gates':gates,'outputs':[available[t] for t in outputs]}
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--family',choices=sorted(census.DEFAULTS),required=True)
    ap.add_argument('--trials',type=int,default=1000)
    ap.add_argument('--seconds',type=int,default=1200)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--out',required=True)
    ap.add_argument('--max-three-scan',type=int,default=1400)
    args=ap.parse_args()
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    src=census.load(args.family,census.DEFAULTS[args.family])
    base=src['circuit']; assert src['summary']['verified_all_256']
    rng=random.Random(args.seed)
    t0=time.time(); best=base; rows=[]; trials=0
    while trials<args.trials and time.time()-t0<args.seconds:
        trials+=1
        cand=synthesize(src,rng,args.max_three_scan)
        ok=census.load if False else None
        # Independent truth-table check through the same arithmetic AES oracle,
        # but not through the symbolic construction path.
        vals,*_=census.eval_circuit(cand,False)
        good=True
        for x in range(256):
            y=sum(((vals[w]>>x)&1)<<i for i,w in enumerate(cand['outputs']))
            if y!=census.aes_sbox(x):good=False;break
        if not good:raise AssertionError(('bad synthesized candidate',trials,x,y,census.aes_sbox(x)))
        n=len(cand['gates']); rows.append(n)
        if n<len(best['gates']):
            best=cand
            (outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
            print(json.dumps({'event':'best','trial':trials,'gates':n,'linear':n-sum(g['op']=='AND' for g in cand['gates'])}),flush=True)
            if n<=100:break
    if not (outdir/'best.json').exists():(outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={
      'family':args.family,'source_gates':len(base['gates']),'source_ops':src['summary']['ops'],
      'trials':trials,'best_gates':len(best['gates']),
      'best_and':sum(g['op']=='AND' for g in best['gates']),
      'best_linear':sum(g['op']!='AND' for g in best['gates']),
      'min_trial_gate_count':min(rows) if rows else None,
      'median_trial_gate_count':sorted(rows)[len(rows)//2] if rows else None,
      'seconds':round(time.time()-t0,3),'verified_all_256':True}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
