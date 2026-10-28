#!/usr/bin/env python3
import argparse, json, pathlib, time, urllib.request
SRC='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json'
MASK=(1<<16)-1
TARGET_NAMES=['w45','w59','w52','w57','w53','w49','w58','w55','w56']

def source_targets():
    # Independent 16-state evaluation of the live 103 core on a,b,c,d.
    def var(i):
        v=0
        for x in range(16):
            if (x>>i)&1:v|=1<<x
        return v
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
    for k in range(1,len(vals)):e=z3.If(idx==k,vals[k],e)
    return e

def main():
    import z3
    ap=argparse.ArgumentParser(); ap.add_argument('--basis',required=True); ap.add_argument('--gates',type=int,default=17); ap.add_argument('--ands',type=int,default=5); ap.add_argument('--pattern',choices=['free','jain5'],default='free'); ap.add_argument('--timeout',type=int,default=600); ap.add_argument('--seed',type=int,default=1); ap.add_argument('--out',required=True); args=ap.parse_args()
    bm=[int(x,0) for x in args.basis.split(',')]; assert len(bm)==4 and rank_masks(bm)==4
    prim,targets=source_targets(); BV=lambda x:z3.BitVecVal(x,16)
    ins=[]
    for m in bm:
        v=0
        for i,t in enumerate(prim):
            if (m>>i)&1:v^=t
        ins.append(BV(v))
    s=z3.Solver(); s.set(timeout=args.timeout*1000,random_seed=args.seed)
    vals=list(ins); A=[];B=[];O=[]; AND=[]
    jpat=[0,2,0,2,0,0,0,2,0,0,2,0,2,0,0,0,0]
    for i in range(args.gates):
        n=len(vals); a=z3.Int(f'a{i}'); b=z3.Int(f'b{i}'); o=z3.Int(f'o{i}')
        s.add(a>=0,a<n,b>=0,b<n,a<b)
        if args.pattern=='jain5':
            if jpat[i]==2:s.add(o==2)
            else:s.add(o>=0,o<=1)
        else:s.add(o>=0,o<=2)
        av=zsel(z3,a,vals); bv=zsel(z3,b,vals)
        v=z3.If(o==0,av^bv,z3.If(o==1,~(av^bv),av&bv))
        vals.append(v); A.append(a);B.append(b);O.append(o);AND.append(z3.If(o==2,1,0))
    s.add(z3.Sum(AND)==args.ands)
    gatevals=vals[4:]
    # A minimal <=17 circuit can be chosen with no duplicate wires or gates duplicating inputs.
    s.add(z3.Distinct(*(vals)))
    outs=[]
    for j,t in enumerate(targets):
        q=z3.Int(f'out{j}'); s.add(q>=4,q<4+args.gates); s.add(zsel(z3,q,vals)==BV(t)); outs.append(q)
    s.add(z3.Distinct(*outs))
    # No dead gates: each gate must feed a later gate or be one of the nine requested factors.
    for i in range(args.gates):
        idx=4+i; uses=[q==idx for q in outs]
        for j in range(i+1,args.gates):uses += [A[j]==idx,B[j]==idx]
        s.add(z3.Or(*uses))
    t0=time.time(); r=s.check(); dt=time.time()-t0
    summary={'basis_masks':bm,'gates':args.gates,'ands':args.ands,'pattern':args.pattern,'seed':args.seed,'solver':str(r),'seconds':round(dt,3),'reason':s.reason_unknown() if r==z3.unknown else None}
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    if r==z3.sat:
        m=s.model(); names=[f'b{i}' for i in range(4)]; gs=[]; ops=['XOR','XNOR','AND']
        for i in range(args.gates):
            ai=m.eval(A[i]).as_long();bi=m.eval(B[i]).as_long();oi=m.eval(O[i]).as_long();name=f'c{i}'
            gs.append({'op':ops[oi],'a':names[ai],'b':names[bi],'out':name});names.append(name)
        os=[m.eval(q).as_long() for q in outs]; model={'basis_masks':bm,'gates':gs,'outputs':[names[q] for q in os]}
        # Re-evaluate all 16 states independently.
        for x in range(16):
            vv={f'b{i}':(bm[i]&x).bit_count()&1 for i in range(4)}
            for g in gs:
                p,q=vv[g['a']],vv[g['b']]
                vv[g['out']]=(p&q) if g['op']=='AND' else ((p^q) if g['op']=='XOR' else (1^p^q))
            for j,q in enumerate(os):assert vv[names[q]]==((targets[j]>>x)&1)
        json.dump(model,open(outdir/'core.json','w'),indent=2); summary['output_selectors']=os
    json.dump(summary,open(outdir/'summary.json','w'),indent=2); print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':main()
