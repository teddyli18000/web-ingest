#!/usr/bin/env python3
import argparse, json, pathlib, time, urllib.request

SRC='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json'
MASK=(1<<256)-1
LO,HI=26,42
PRIMARY=['w35','w33','w38','w41']

def fetch():
    with urllib.request.urlopen(SRC,timeout=30) as r:return json.load(r)
def inputs_truth():
    d={}
    for b in range(8):
        v=0
        for x in range(256):
            if (x>>b)&1:v|=1<<x
        d[f'x{b}']=v
    return d
def opv(op,a,b):
    if op=='XOR':return a^b
    if op=='XNOR':return (~(a^b))&MASK
    if op=='AND':return a&b
    raise ValueError(op)
def evaluate(c):
    v=inputs_truth()
    for g in c['gates']:v[g['out']]=opv(g['op'],v[g['a']],v[g['b']])
    return v
def external(c,lo,hi):
    made={g['out'] for g in c['gates'][lo:hi]};out=[];seen=set()
    for g in c['gates'][lo:hi]:
        for w in (g['a'],g['b']):
            if w not in made and w not in seen:seen.add(w);out.append(w)
    return out
def rank_masks(ms):
    p=[]
    for x in ms:
        y=x
        for q in p:y=min(y,y^q)
        if y:p.append(y);p.sort(reverse=True)
    return len(p)

def independent_basis(vecs):
    piv=[]; idx=[]
    for i,x in enumerate(vecs):
        y=x
        for pv in piv:y=min(y,y^pv)
        if y:
            piv.append(y);piv.sort(reverse=True);idx.append(i)
    return idx

def coordinate_system(generators):
    # Return exact coordinates in an independently chosen basis spanning generators.
    inds=independent_basis(generators)
    basis=[generators[i] for i in inds]
    piv={}  # pivot bit -> (vector, coordinate mask)
    for j,x in enumerate(basis):
        y=x;co=1<<j
        for p in sorted(piv,reverse=True):
            if (y>>p)&1:
                pv,pc=piv[p];y^=pv;co^=pc
        assert y
        p=y.bit_length()-1;piv[p]=(y,co)
    def coord(x):
        y=x;co=0
        for p in sorted(piv,reverse=True):
            if (y>>p)&1:
                pv,pc=piv[p];y^=pv;co^=pc
        if y:return None
        return co
    return len(basis),coord,inds

def zselect(z3,idx,vals):
    e=vals[0]
    for k in range(1,len(vals)):e=z3.If(idx==k,vals[k],e)
    return e

def main():
    import z3
    ap=argparse.ArgumentParser();ap.add_argument('--basis',required=True);ap.add_argument('--gates',type=int,required=True);ap.add_argument('--timeout',type=int,default=900);ap.add_argument('--seed',type=int,default=1);ap.add_argument('--out',required=True);args=ap.parse_args()
    masks=[int(x,0) for x in args.basis.split(',')];assert len(masks)==4 and rank_masks(masks)==4
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=fetch();vals=evaluate(c);ext=external(c,LO,HI);assert len(ext)==15
    target_truth=[]
    for m in masks:
        t=0
        for i,w in enumerate(PRIMARY):
            if (m>>i)&1:t^=vals[w]
        target_truth.append(t)
    gens=[vals[w] for w in ext]+[MASK]
    width,coord,_=coordinate_system(gens)
    extc=[coord(vals[w]) for w in ext];cc=coord(MASK);tc=[coord(t) for t in target_truth]
    assert all(x is not None for x in extc+tc) and cc is not None
    BV=lambda x:z3.BitVecVal(x,width)
    s=z3.Solver();s.set(timeout=args.timeout*1000,random_seed=args.seed)
    sigs=[BV(x) for x in extc];A=[];B=[];XN=[]
    for i in range(args.gates):
        n=len(sigs);a=z3.Int(f'a{i}');b=z3.Int(f'b{i}');xn=z3.Bool(f'xn{i}')
        s.add(a>=0,b>=0,a<n,b<n,a<b)
        av=zselect(z3,a,sigs);bv=zselect(z3,b,sigs)
        sigs.append(z3.If(xn,av^bv^BV(cc),av^bv));A.append(a);B.append(b);XN.append(xn)
    outs=[]
    for j,t in enumerate(tc):
        q=z3.Int(f'out{j}');s.add(q>=0,q<len(sigs));s.add(zselect(z3,q,sigs)==BV(t));outs.append(q)
    t0=time.time();res=s.check();elapsed=time.time()-t0
    summary={'basis_masks':masks,'gates':args.gates,'seed':args.seed,'solver':str(res),'seconds':round(elapsed,3),'reason':s.reason_unknown() if res==z3.unknown else None,'coordinate_width':width,'external':ext}
    if res==z3.sat:
        m=s.model();names=list(ext);gates=[]
        for i in range(args.gates):
            ai=m.eval(A[i]).as_long();bi=m.eval(B[i]).as_long();xn=z3.is_true(m.eval(XN[i],model_completion=True));name=f'L{i}'
            gates.append({'op':'XNOR' if xn else 'XOR','a':names[ai],'b':names[bi],'out':name});names.append(name)
        os=[m.eval(q).as_long() for q in outs]
        # Verify reconstructed truth tables directly against the requested basis functions.
        tv={w:vals[w] for w in ext}
        for g in gates:tv[g['out']]=opv(g['op'],tv[g['a']],tv[g['b']])
        for j,q in enumerate(os):assert tv[names[q]]==target_truth[j]
        model={'basis_masks':masks,'gates':gates,'outputs':[names[q] for q in os]}
        summary['output_selectors']=os
        json.dump(model,open(out/'linear.json','w'),indent=2)
    json.dump(summary,open(out/'summary.json','w'),indent=2);print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
