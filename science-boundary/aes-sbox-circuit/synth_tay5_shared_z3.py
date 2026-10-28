#!/usr/bin/env python3
"""Exact linear resynthesis around Tay et al.'s 5-product GF(16) inverter.

Keep the published five AND functions, but discard its published XOR network.
For each of the 60 GL(4,2) input maps whose four inverter outputs span the live
102 core-output space, synthesize a 17-gate network with exactly those five AND
products and 12 arbitrary XOR/XNOR gates.  The unknown linear network is encoded
only as 10-bit affine masks over four inputs, five product generators and the
constant bit, rather than 16-state Boolean truth tables.

A SAT model therefore proves that this fixed multiplicative decomposition can
be linearly resynthesized to expose all nine live-102 tail factors in 17 gates.
"""
import argparse, json, pathlib, time
from itertools import permutations

TARGET_NAMES=['q45','q59','q52','q57','q53','q49','q58','q55','q56']
WIDTH=10
CONST=1<<9


def var(i):
    v=0
    for x in range(16):
        if (x>>i)&1:v|=1<<x
    return v
A,B,C,D=[var(i) for i in range(4)]; VARS=[A,B,C,D]


def lf(m):
    v=0
    for i,t in enumerate(VARS):
        if (m>>i)&1:v^=t
    return v


def rank(ms):
    piv=[]
    for x in ms:
        y=x
        for p in piv:y=min(y,y^p)
        if y:piv.append(y);piv.sort(reverse=True)
    return len(piv)


def span(bs):
    out=set()
    for m in range(1<<len(bs)):
        v=0
        for i,b in enumerate(bs):
            if (m>>i)&1:v^=b
        out.add(v)
    return out


def live_targets():
    a,b,c,d=A,B,C,D
    q42=a&b;q43=q42^c;q44=q43&d;q45=b^q44;q46=q42&c;q47=d^q46
    q48=a&q47;q49=q43^q48;q50=q48^b;q51=q49&q50;q52=q51^a;q53=q52^q49
    q54=q45&q53;q55=q54^q47;q56=q55^q49;q57=q53^q45;q58=q56^q57;q59=q55^q45
    return [q45,q59,q52,q57,q53,q49,q58,q55,q56]
TARGET_TT=live_targets(); TARGET_SPACE=span(TARGET_TT[:4])


def tay_truth(inp):
    m19,m20,m21,m22=inp
    m23=m20&m22;m24=m19^m20;m25=m23^m24;m26=m21&m25
    m27=m21^m22;m28=m26^m27;m29=m26^m23;m30=m29&m27
    m31=m22^m30;m32=m27^m23;m33=m19&m32;m34=m24^m33
    m35=m23^m34;m36=m35&m24;m37=m19^m36
    return [m28,m31,m34,m37]


def compatible_bases():
    out=[]
    for b in permutations(range(1,16),4):
        if rank(b)!=4:continue
        if span(tay_truth([lf(m) for m in b]))==TARGET_SPACE:out.append(b)
    assert len(out)==60
    return out


def skeleton(basis):
    # Symbolic linear masks over x0..x3, p0..p4. Constant bit stays zero here.
    m19,m20,m21,m22=basis
    p0=1<<4;m24=m19^m20;m25=p0^m24
    p1=1<<5;m27=m21^m22;m28=p1^m27;m29=p1^p0
    p2=1<<6;m31=m22^p2;m32=m27^p0
    p3=1<<7;m34=m24^p3;m35=p0^m34
    p4=1<<8;m37=m19^p4
    operands=[(m20,m22),(m21,m25),(m29,m27),(m19,m32),(m35,m24)]
    outs=[m28,m31,m34,m37]
    ott=tay_truth([lf(m) for m in basis])
    targets=[]
    for t in TARGET_TT:
        coeff=None
        for cm in range(16):
            z=0
            for i,o in enumerate(ott):
                if (cm>>i)&1:z^=o
            if z==t:coeff=cm;break
        assert coeff is not None
        sm=0
        for i,o in enumerate(outs):
            if (coeff>>i)&1:sm^=o
        targets.append(sm)
    return operands,targets


def zselect(z3,idx,vals):
    e=vals[0]
    for k in range(1,len(vals)):e=z3.If(idx==k,vals[k],e)
    return e


def unit_for_stage(z3,s):
    e=z3.BitVecVal(1<<8,WIDTH)
    for k in range(3,-1,-1):e=z3.If(s==k,z3.BitVecVal(1<<(4+k),WIDTH),e)
    return e


def solve_one(basis,allow_xnor,timeout_s,seed):
    import z3
    operands,targets=skeleton(basis)
    G=17
    s=z3.Solver();s.set(timeout=int(timeout_s*1000),random_seed=seed)
    init=[z3.BitVecVal(1<<i,WIDTH) for i in range(4)]
    vals=[]; Aidx=[];Bidx=[];IsAnd=[];IsXnor=[]
    stage=[z3.Int(f'st{i}') for i in range(G+1)]
    s.add(stage[0]==0)
    for i in range(G):
        prev=init+vals;n=len(prev)
        ia=z3.Int(f'a{i}');ib=z3.Int(f'b{i}');aa=z3.Bool(f'and{i}');xx=z3.Bool(f'xn{i}')
        s.add(ia>=0,ia<n,ib>=0,ib<n,ia<ib)
        s.add(stage[i]>=0,stage[i]<=5)
        s.add(stage[i+1]==stage[i]+z3.If(aa,1,0),stage[i+1]<=5)
        if not allow_xnor:s.add(xx==False)
        s.add(z3.Implies(aa,xx==False),z3.Implies(aa,stage[i]<5))
        av=zselect(z3,ia,prev);bv=zselect(z3,ib,prev)
        lin=av^bv^z3.If(xx,z3.BitVecVal(CONST,WIDTH),z3.BitVecVal(0,WIDTH))
        out=z3.If(aa,unit_for_stage(z3,stage[i]),lin)
        vals.append(out);Aidx.append(ia);Bidx.append(ib);IsAnd.append(aa);IsXnor.append(xx)
        # If this slot is product p_k, both exact Tay operands must already exist.
        for k,(u,v) in enumerate(operands):
            have_u=z3.Or(*[q==z3.BitVecVal(u,WIDTH) for q in prev])
            have_v=z3.Or(*[q==z3.BitVecVal(v,WIDTH) for q in prev])
            s.add(z3.Implies(z3.And(aa,stage[i]==k),z3.And(have_u,have_v)))
        s.add(out!=z3.BitVecVal(0,WIDTH))
    s.add(stage[G]==5)
    # Exactly five ANDs follows from final stage, hence 12 linear gates.
    s.add(z3.Distinct(*(init+vals)))
    for t in targets:s.add(z3.Or(*[v==z3.BitVecVal(t,WIDTH) for v in vals]))

    t0=time.time();r=s.check();dt=time.time()-t0
    summary={'basis':basis,'allow_xnor':allow_xnor,'solver':str(r),'seconds':round(dt,3),
             'reason':s.reason_unknown() if r==z3.unknown else None,'seed':seed}
    if r!=z3.sat:return summary,None

    m=s.model();names=['q34','q36','q39','q41'];maskvals=[1,2,4,8];gates=[];prod=0
    for i in range(G):
        isand=z3.is_true(m.eval(IsAnd[i]));ai=m.eval(Aidx[i]).as_long();bi=m.eval(Bidx[i]).as_long()
        out=f'ts{i}'
        if isand:
            u,v=operands[prod]
            # Use actual wires carrying the exact required operand masks; the selector vars are irrelevant on AND slots.
            cand_u=[j for j,x in enumerate(maskvals) if x==u];cand_v=[j for j,x in enumerate(maskvals) if x==v]
            assert cand_u and cand_v,(i,prod,u,v,maskvals)
            gates.append({'op':'AND','a':names[cand_u[0]],'b':names[cand_v[0]],'out':out})
            mask=1<<(4+prod);prod+=1
        else:
            xnor=z3.is_true(m.eval(IsXnor[i]));op='XNOR' if xnor else 'XOR'
            gates.append({'op':op,'a':names[ai],'b':names[bi],'out':out})
            mask=maskvals[ai]^maskvals[bi]^(CONST if xnor else 0)
        names.append(out);maskvals.append(mask)
    assert prod==5 and sum(g['op']=='AND' for g in gates)==5
    target_wire={}
    for name,t in zip(TARGET_NAMES,targets):
        hits=[names[4+i] for i,x in enumerate(maskvals[4:]) if x==t]
        assert len(hits)==1,(name,t,hits)
        target_wire[name]=hits[0]

    # Independent 16-state Boolean check of the reconstructed gates.
    got=[0]*9
    for x in range(16):
        vv={'q34':(x>>0)&1,'q36':(x>>1)&1,'q39':(x>>2)&1,'q41':(x>>3)&1}
        for g in gates:
            a,b=vv[g['a']],vv[g['b']]
            vv[g['out']]=(a&b) if g['op']=='AND' else ((a^b) if g['op']=='XOR' else (1^a^b))
        for j,n in enumerate(TARGET_NAMES):got[j]|=vv[target_wire[n]]<<x
    assert got==TARGET_TT,(got,TARGET_TT)
    summary['target_wire']=target_wire
    return summary,{'gates':gates,'target_wire':target_wire}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,default=0);ap.add_argument('--count',type=int,default=10)
    ap.add_argument('--allow-xnor',action='store_true');ap.add_argument('--timeout-per-map',type=float,default=20)
    ap.add_argument('--seed',type=int,default=1);ap.add_argument('--out',required=True);args=ap.parse_args()
    bases=compatible_bases();end=min(len(bases),args.start+args.count)
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True);results=[]
    for idx in range(args.start,end):
        sm,model=solve_one(bases[idx],args.allow_xnor,args.timeout_per_map,args.seed+idx);sm['index']=idx;results.append(sm)
        print(json.dumps(sm,sort_keys=True),flush=True)
        if model:
            json.dump(model,open(out/'core.json','w'),indent=2);json.dump(results,open(out/'results.json','w'),indent=2)
            print('SAT_INDEX',idx,flush=True);return
    json.dump(results,open(out/'results.json','w'),indent=2)

if __name__=='__main__':main()
