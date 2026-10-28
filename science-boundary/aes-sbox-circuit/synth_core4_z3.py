#!/usr/bin/env python3
import argparse, json, pathlib, time, urllib.request

SRC='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json'
CORE_LO,CORE_HI=42,60
PRIMARY_INPUTS=['w35','w33','w38','w41']
PRIMARY_TARGETS=['w45','w59','w52','w57','w53','w49','w58','w55','w56']
MASK16=(1<<16)-1

def fetch():
    with urllib.request.urlopen(SRC,timeout=30) as r:return json.load(r)
def opv(op,a,b):
    if op=='XOR':return a^b
    if op=='XNOR':return (~(a^b))&MASK16
    if op=='AND':return a&b
    raise ValueError(op)
def primary_truths(c):
    # Evaluate the published 18-gate core on all 16 assignments of its four independent inputs.
    vals={}
    for i,w in enumerate(PRIMARY_INPUTS):
        t=0
        for x in range(16):
            if (x>>i)&1:t|=1<<x
        vals[w]=t
    for g in c['gates'][CORE_LO:CORE_HI]:
        vals[g['out']]=opv(g['op'],vals[g['a']],vals[g['b']])
    return [vals[w] for w in PRIMARY_INPUTS],[vals[w] for w in PRIMARY_TARGETS]
def rank_masks(ms):
    p=[]
    for x in ms:
        y=x
        for q in p:y=min(y,y^q)
        if y:p.append(y);p.sort(reverse=True)
    return len(p)
def zselect(z3,idx,vals):
    e=vals[0]
    for k in range(1,len(vals)):e=z3.If(idx==k,vals[k],e)
    return e

def synth(basis_masks,G,and_count,timeout_ms,seed,fixed_pattern):
    import z3
    c=fetch(); prim,targets=primary_truths(c)
    assert rank_masks(basis_masks)==4
    inp=[]
    for m in basis_masks:
        v=0
        for i,t in enumerate(prim):
            if (m>>i)&1:v^=t
        inp.append(z3.BitVecVal(v,16))
    s=z3.Solver(); s.set(timeout=timeout_ms,random_seed=seed)
    vals=list(inp); A=[];B=[];O=[];ands=[]
    pattern=[2,0,2,0,2,0,2,0,0,2,0,0,2,0,0,0,0,0]  # primary core: 2=AND,0=XOR
    for i in range(G):
        n=len(vals); a=z3.Int(f'a{i}');b=z3.Int(f'b{i}');o=z3.Int(f'o{i}')
        s.add(a>=0,b>=0,a<n,b<n,a<b)
        if fixed_pattern and i<len(pattern):
            if pattern[i]==2:s.add(o==2)
            else:s.add(o>=0,o<=1)  # permit XOR/XNOR orientation
        else:s.add(o>=0,o<=2)
        av=zselect(z3,a,vals);bv=zselect(z3,b,vals)
        v=z3.If(o==0,av^bv,z3.If(o==1,~(av^bv),av&bv))
        vals.append(v);A.append(a);B.append(b);O.append(o);ands.append(z3.If(o==2,1,0))
    if and_count>=0:s.add(z3.Sum(ands)==and_count)
    outs=[]
    for j,t in enumerate(targets):
        q=z3.Int(f'out{j}');s.add(q>=0,q<len(vals));s.add(zselect(z3,q,vals)==z3.BitVecVal(t,16));outs.append(q)
    t0=time.time();res=s.check();elapsed=time.time()-t0
    summary={'basis_masks':basis_masks,'gates':G,'and_count':and_count,'fixed_pattern':fixed_pattern,'seed':seed,'solver':str(res),'seconds':round(elapsed,3),'reason':s.reason_unknown() if res==z3.unknown else None}
    if res!=z3.sat:return summary,None
    m=s.model();names=[f'b{i}' for i in range(4)];gates=[];ops=['XOR','XNOR','AND']
    for i in range(G):
        ai=m.eval(A[i]).as_long();bi=m.eval(B[i]).as_long();oi=m.eval(O[i]).as_long();name=f'c{i}'
        gates.append({'op':ops[oi],'a':names[ai],'b':names[bi],'out':name});names.append(name)
    outsel=[m.eval(q).as_long() for q in outs]
    # Independent 16-state check of reconstructed model.
    rv=[]
    for x in range(16):
        vv={f'b{i}':sum((((sum(((x>>k)&1) for k in range(4) if (basis_masks[i]>>k)&1))&1))<<0) for _ in [0]) for i in range(4)}
        # simpler direct parity
        for i,bm in enumerate(basis_masks):vv[f'b{i}']=(bm & x).bit_count()&1
        for g in gates:
            a=vv[g['a']];b=vv[g['b']]
            vv[g['out']]= (a^b) if g['op']=='XOR' else ((1^a^b) if g['op']=='XNOR' else (a&b))
        rv.append([vv[names[q]] for q in outsel])
    for x in range(16):
        for j,t in enumerate(targets):
            assert rv[x][j]==((t>>x)&1),(x,j)
    summary.update({'output_selectors':outsel,'ops':[g['op'] for g in gates]})
    return summary,{'basis_masks':basis_masks,'gates':gates,'outputs':[names[q] for q in outsel]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--basis',required=True,help='comma-separated masks 1..15');ap.add_argument('--gates',type=int,required=True);ap.add_argument('--ands',type=int,default=6);ap.add_argument('--timeout',type=int,default=900);ap.add_argument('--seed',type=int,default=1);ap.add_argument('--fixed-pattern',action='store_true');ap.add_argument('--out',required=True);args=ap.parse_args()
    basis=[int(x,0) for x in args.basis.split(',')];assert len(basis)==4 and rank_masks(basis)==4
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    summary,model=synth(basis,args.gates,args.ands,args.timeout*1000,args.seed,args.fixed_pattern)
    json.dump(summary,open(out/'summary.json','w'),indent=2)
    if model:json.dump(model,open(out/'core.json','w'),indent=2)
    print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
