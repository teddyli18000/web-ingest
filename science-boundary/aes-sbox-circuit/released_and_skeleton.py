#!/usr/bin/env python3
"""Whole-circuit released-AND affine representation and heuristic synthesis.

An XAG/XNAG circuit can be viewed as an ordered sequence of AND atoms.  Every
AND operand and every final output is affine in the eight primary inputs and
previously released AND atoms.  This representation deliberately removes named
linear boundaries (pre/middle/core/final/output): a linear helper may be kept
alive across any number of AND releases.

The synthesizer here is a calibration/search heuristic, not an exact solver.
Failure to beat or reproduce a circuit is evidence only about this heuristic.
"""
from __future__ import annotations
import argparse, collections, json, pathlib, random, urllib.request
import seed_family_census as census

SOURCES={
 "fs-101":census.DEFAULTS["fs-101"],
 "nist-g103":census.DEFAULTS["nist-g103"],
 "nist-g104":census.DEFAULTS["nist-g104"],
 "nist-a34-g110":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a34-ad4-g110-gd22-xx76-3.circ.txt",
}

def load_circuit(name):
    text=census.get(SOURCES[name])
    if text.lstrip().startswith('{'):
        c=json.loads(text)
    else:
        c,_=census.normalize_nist(census.parse_nist(text))
    return prune(c)

def prune(c):
    by={g['out']:g for g in c['gates']}; need=set(c['outputs']); stack=list(need)
    while stack:
        w=stack.pop(); g=by.get(w)
        if not g: continue
        for u in (g['a'],g['b']):
            if u not in need: need.add(u); stack.append(u)
    kept=[g for g in c['gates'] if g['out'] in need]
    mp={f'x{i}':f'x{i}' for i in range(8)}; out=[]
    for i,g in enumerate(kept):
        ng={'op':g['op'],'a':mp[g['a']],'b':mp[g['b']],'out':f'g{i}'}
        mp[g['out']]=ng['out']; out.append(ng)
    return {'gates':out,'outputs':[mp[o] for o in c['outputs']]}

def independent_check(c):
    vals={f'x{i}':census.input_tables(False)[f'x{i}'] for i in range(8)}
    for g in c['gates']:
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
    for x in range(256):
        y=sum(((vals[o]>>x)&1)<<i for i,o in enumerate(c['outputs']))
        if y!=census.aes_sbox(x): return False,x,y,census.aes_sbox(x)
    return True,None,None,None

def extract_skeleton(c):
    nands=sum(g['op']=='AND' for g in c['gates'])
    const_bit=8+nands; C=1<<const_bit
    vals={f'x{i}':1<<i for i in range(8)}
    ands=[]; ai=0
    for g in c['gates']:
        a,b=vals[g['a']],vals[g['b']]
        if g['op']=='XOR': v=a^b
        elif g['op']=='XNOR': v=a^b^C
        elif g['op']=='AND':
            ands.append({'a':a,'b':b})
            v=1<<(8+ai); ai+=1
        else: raise ValueError(g['op'])
        vals[g['out']]=v
    sk={'n_and':nands,'const_bit':const_bit,'ands':ands,'outputs':[vals[o] for o in c['outputs']]}
    assert verify_skeleton(sk)[0]
    return sk

def affine_value(v,bits,const_bit):
    z=(v>>const_bit)&1
    m=v & ((1<<const_bit)-1)
    while m:
        l=m & -m; i=l.bit_length()-1; z^=bits[i]; m^=l
    return z

def eval_skeleton(sk,x):
    bits=[(x>>i)&1 for i in range(8)]
    for ab in sk['ands']:
        a=affine_value(ab['a'],bits,sk['const_bit'])
        b=affine_value(ab['b'],bits,sk['const_bit'])
        bits.append(a&b)
    y=0
    for i,v in enumerate(sk['outputs']): y|=affine_value(v,bits,sk['const_bit'])<<i
    return y

def verify_skeleton(sk):
    for x in range(256):
        y=eval_skeleton(sk,x); z=census.aes_sbox(x)
        if y!=z:return False,x,y,z
    return True,None,None,None

def gf_mul(a,b):
    r=0
    for _ in range(8):
        if b&1:r^=a
        hi=a&0x80; a=(a<<1)&255
        if hi:a^=0x1b
        b>>=1
    return r

def frob(x,k):
    for _ in range(k%8):x=gf_mul(x,x)
    return x

def semilinear(c,k,x):return gf_mul(c,frob(x,k))

def transport_skeleton(sk,c,k):
    """Transport inputs by P(x)=c*x^(2^k), then affine-compensate outputs."""
    n=sk['n_and']; cb=sk['const_bit']; C=1<<cb
    # old input bit i as a linear form in new input bits
    inp=[]
    cols=[semilinear(c,k,1<<j) for j in range(8)]
    for i in range(8):
        v=0
        for j,z in enumerate(cols):
            if (z>>i)&1:v^=1<<j
        inp.append(v)
    def sub(v):
        r=C if ((v>>cb)&1) else 0
        for i in range(8):
            if (v>>i)&1:r^=inp[i]
        for a in range(n):
            if (v>>(8+a))&1:r^=1<<(8+a)
        return r
    ands=[{'a':sub(ab['a']),'b':sub(ab['b'])} for ab in sk['ands']]
    outs=[sub(v) for v in sk['outputs']]
    # derive Q from Q(S(P(x)))=S(x), then prove it is affine on all 256 values
    qmap={}
    for x in range(256):
        y=census.aes_sbox(semilinear(c,k,x)); qmap[y]=census.aes_sbox(x)
    assert len(qmap)==256
    q0=qmap[0]; qcols=[qmap[1<<i]^q0 for i in range(8)]
    for y,z in qmap.items():
        q=q0
        for i,col in enumerate(qcols):
            if (y>>i)&1:q^=col
        assert q==z,(c,k,y,q,z)
    newouts=[]
    for j in range(8):
        v=C if ((q0>>j)&1) else 0
        for i,col in enumerate(qcols):
            if (col>>j)&1:v^=outs[i]
        newouts.append(v)
    res={'n_and':n,'const_bit':cb,'ands':ands,'outputs':newouts,'transport':{'c':c,'k':k}}
    assert verify_skeleton(res)[0]
    return res

def max_atom_dep(v,sk):
    mask=(v>>8)&((1<<sk['n_and'])-1)
    return mask.bit_length()-1

def affine_support(v,sk):
    return [i for i in range(8+sk['n_and']) if (v>>i)&1], (v>>sk['const_bit'])&1

class Builder:
    def __init__(self,sk,rng,future_weight=8.0,topk=8):
        self.sk=sk; self.rng=rng; self.future_weight=future_weight; self.topk=topk
        self.gates=[]; self.wires=[]; self.byvec={}
        for i in range(8):self._register(1<<i,f'x{i}',kind='input')
    def _register(self,v,name,kind):
        wid=len(self.wires); self.wires.append({'vec':v,'name':name,'kind':kind}); self.byvec.setdefault(v,wid); return wid
    def add_linear(self,ia,ib,op):
        a,b=self.wires[ia],self.wires[ib]; C=1<<self.sk['const_bit']
        v=a['vec']^b['vec']^(C if op=='XNOR' else 0)
        if v in self.byvec:return self.byvec[v]
        name=f'g{len(self.gates)}'; self.gates.append({'op':op,'a':a['name'],'b':b['name'],'out':name})
        return self._register(v,name,'linear')
    def add_and(self,ia,ib,idx):
        a,b=self.wires[ia],self.wires[ib]; name=f'g{len(self.gates)}'
        self.gates.append({'op':'AND','a':a['name'],'b':b['name'],'out':name})
        v=1<<(8+idx); assert v not in self.byvec
        return self._register(v,name,'and')
    def available_ids(self):return list(range(len(self.wires)))
    def fallback(self,t):
        if t in self.byvec:return self.byvec[t]
        supp,const=affine_support(t,self.sk)
        ids=[self.byvec[1<<i] for i in supp]
        if len(ids)>=2:
            cur=ids[0]
            for j,nxt in enumerate(ids[1:]):
                op='XNOR' if const and j==0 else 'XOR'
                cur=self.add_linear(cur,nxt,op)
            assert self.wires[cur]['vec']==t
            return cur
        if len(ids)==1 and not const:return ids[0]
        if len(ids)==1 and const:
            # Complement a single source using h=s XOR q; XNOR(h,q)=~s.
            s=ids[0]; q=next(i for i,w in enumerate(self.wires) if i!=s and w['kind']!='and' or i!=s)
            h=self.add_linear(s,q,'XOR'); z=self.add_linear(h,q,'XNOR')
            assert self.wires[z]['vec']==t; return z
        if not ids and const:
            # XNOR(s,s) is a legal two-input gate and materializes one if ever needed.
            z=self.add_linear(0,0,'XNOR'); assert self.wires[z]['vec']==t; return z
        raise AssertionError(('zero affine target',t))
    def choose_helper(self,due,active,stage):
        C=1<<self.sk['const_bit']; avail=self.available_ids(); vecs=[self.wires[i]['vec'] for i in avail]
        # Scores for a candidate that makes a target one gate away from an existing wire.
        oneaway=collections.defaultdict(float); direct=collections.defaultdict(float)
        targets=[]
        for t,deadline in active:
            if t in self.byvec:continue
            wt=1000.0 if t in due else self.future_weight/(1+max(0,deadline-stage))
            targets.append((t,wt))
            direct[t]+=100.0*wt
            for v in vecs:
                oneaway[t^v]+=10.0*wt; oneaway[t^v^C]+=10.0*wt
        if not targets:return None
        cand={}
        # Candidate set is every XOR/XNOR of two currently available signals.
        for p in range(len(avail)):
            vp=vecs[p]
            for q in range(p+1,len(avail)):
                v=vp^vecs[q]
                for op,cv in (('XOR',v),('XNOR',v^C)):
                    if cv in self.byvec:continue
                    score=direct.get(cv,0.0)+oneaway.get(cv,0.0)
                    # Small canonical-support preference for due targets, useful when farther than one gate.
                    for t in due:
                        before=(t & ((1<<self.sk['const_bit'])-1)).bit_count()
                        after=((t^cv) & ((1<<self.sk['const_bit'])-1)).bit_count()
                        if after<before:score+=(before-after)*2.0
                    old=cand.get(cv)
                    if old is None or score>old[0]:cand[cv]=(score,avail[p],avail[q],op)
        if not cand:return None
        best=sorted(cand.values(),key=lambda x:x[0],reverse=True)[:self.topk]
        # Randomized top-k exploration; strongly favor higher-scored candidates.
        if best[0][0]<=0:return None
        weights=[max(0.001,b[0]-best[-1][0]+0.25) for b in best]
        return self.rng.choices(best,weights=weights,k=1)[0]
    def ensure_due(self,due,active,stage,max_helpers=10):
        due=set(due); helpers=0
        while any(t not in self.byvec for t in due) and helpers<max_helpers:
            ch=self.choose_helper(due,active,stage)
            if ch is None:break
            _,a,b,op=ch; self.add_linear(a,b,op); helpers+=1
        for t in due:
            if t not in self.byvec:self.fallback(t)
        return [self.byvec[t] for t in due]

def synthesize(sk,seed=1,future_weight=8.0,topk=8,max_helpers=10):
    rng=random.Random(seed); B=Builder(sk,rng,future_weight,topk)
    # Targets carry their hard deadline (before AND i; outputs at n).
    targets=[]
    for i,ab in enumerate(sk['ands']):
        targets.append((ab['a'],i)); targets.append((ab['b'],i))
    for v in sk['outputs']:targets.append((v,sk['n_and']))
    for i,ab in enumerate(sk['ands']):
        due=[ab['a'],ab['b']]
        active=[]
        for t,d in targets:
            if d<i:continue
            if max_atom_dep(t,sk)<i:active.append((t,d))
        B.ensure_due(due,active,i,max_helpers)
        ia=B.byvec[ab['a']]; ib=B.byvec[ab['b']]; B.add_and(ia,ib,i)
    active=[(v,sk['n_and']) for v in sk['outputs']]
    B.ensure_due(sk['outputs'],active,sk['n_and'],max_helpers*2)
    c={'gates':B.gates,'outputs':[B.wires[B.byvec[v]]['name'] for v in sk['outputs']]}
    c=prune(c); ok=independent_check(c); assert ok[0],ok
    return c

def gate_stats(c):return dict(collections.Counter(g['op'] for g in c['gates']))|{'total':len(c['gates'])}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed-family',choices=sorted(SOURCES),required=True)
    ap.add_argument('--rng-seed',type=int,default=1)
    ap.add_argument('--future-weight',type=float,default=8.0)
    ap.add_argument('--topk',type=int,default=8)
    ap.add_argument('--max-helpers',type=int,default=10)
    ap.add_argument('--transport-c',type=lambda s:int(s,0),default=1)
    ap.add_argument('--transport-k',type=int,default=0)
    ap.add_argument('--out')
    args=ap.parse_args()
    base=load_circuit(args.seed_family); assert independent_check(base)[0]
    sk=extract_skeleton(base)
    if (args.transport_c,args.transport_k)!=(1,0):sk=transport_skeleton(sk,args.transport_c,args.transport_k)
    c=synthesize(sk,args.rng_seed,args.future_weight,args.topk,args.max_helpers)
    res={'seed_family':args.seed_family,'base':gate_stats(base),'result':gate_stats(c),'transport':{'c':args.transport_c,'k':args.transport_k},'rng_seed':args.rng_seed,'verified_all_256':True}
    print(json.dumps(res,sort_keys=True))
    if args.out:pathlib.Path(args.out).write_text(json.dumps(c,indent=2)+'\n')

if __name__=='__main__':main()
