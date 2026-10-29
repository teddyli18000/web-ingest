#!/usr/bin/env python3
"""Exact unconstrained cross-edge gluing for the extreme d=11 local pair.

Fix v of degree 11, A=N(v) with A one of the two e(A)=26 R(3,6,11)
graphs, and B the 24 non-neighbours with B one of the nine e(B)=116
R(4,5,24) graphs.  The only variables are the 11*24 cross edges.

Unlike the m=219 campaigns, this encoding imposes NO total-edge count and NO
chosen global degree sequence.  It contains every mixed K4 and independent-6
clause.  Therefore any SAT model is immediately a full 36-vertex (4,6) graph,
regardless of its edge count.  Conversely UNSAT closes exactly that fixed A/B
pair for every possible edge count.
"""
from __future__ import annotations
import argparse,gzip,itertools,json
from pathlib import Path

NA,NB=11,24

def decode_g6(s:str):
    s=s.strip(); n=ord(s[0])-63; bits=[]
    for ch in s[1:]:
        z=ord(ch)-63; bits.extend((z>>k)&1 for k in range(5,-1,-1))
    need=n*(n-1)//2
    if len(bits)<need: raise ValueError('truncated graph6')
    a=[0]*n;p=0;e=0
    for j in range(1,n):
        for i in range(j):
            if bits[p]: a[i]|=1<<j;a[j]|=1<<i;e+=1
            p+=1
    return a,e

def iter_g6(path:Path):
    op=gzip.open if path.suffix=='.gz' else open
    with op(path,'rt',encoding='ascii') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith('>>'): continue
            yield s,*decode_g6(s)

def extract(inp:Path,n:int,e:int,out:Path):
    rows=[s for s,a,ee in iter_g6(inp) if len(a)==n and ee==e]
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text('\n'.join(rows)+'\n',encoding='ascii')
    print(json.dumps({'n':n,'edges':e,'count':len(rows),'out':str(out)},sort_keys=True));return len(rows)

def select(path:Path,ordinal:int,n:int):
    rows=list(iter_g6(path))
    if not 0<=ordinal<len(rows): raise IndexError((ordinal,len(rows)))
    s,a,e=rows[ordinal]
    if len(a)!=n: raise ValueError((len(a),n))
    return s,a,e

def clique(a,C): return all((a[u]>>v)&1 for u,v in itertools.combinations(C,2))
def indep(a,C): return all(not((a[u]>>v)&1) for u,v in itertools.combinations(C,2))
def subs(a,k,edge):
    p=clique if edge else indep
    return [C for C in itertools.combinations(range(len(a)),k) if p(a,C)]
def validate(A,B):
    if len(A)!=NA or subs(A,3,True) or subs(A,6,False): raise ValueError('bad A')
    if len(B)!=NB or subs(B,4,True) or subs(B,5,False): raise ValueError('bad B')

def vm(a,b): return a*NB+b+1

def generate(acat,bcat,ao,bo,cnf,meta):
    ag6,A,ae=select(acat,ao,NA);bg6,B,be=select(bcat,bo,NB);validate(A,B)
    if ae!=26 or be!=116: raise ValueError((ae,be))
    clauses=[];counts={k:0 for k in ('k4_1a3b','k4_2a2b','i6_5a1b','i6_4a2b','i6_3a3b','i6_2a4b')}
    btri=subs(B,3,True); aedge=subs(A,2,True); bedge=subs(B,2,True)
    ai5=subs(A,5,False); ai4=subs(A,4,False); bnon=subs(B,2,False)
    ai3=subs(A,3,False); bi3=subs(B,3,False); anon=subs(A,2,False); bi4=subs(B,4,False)
    for a in range(NA):
        for bs in btri: clauses.append([-vm(a,b) for b in bs]);counts['k4_1a3b']+=1
    for aa in aedge:
        for bb in bedge: clauses.append([-vm(a,b) for a in aa for b in bb]);counts['k4_2a2b']+=1
    for aa in ai5:
        for b in range(NB): clauses.append([vm(a,b) for a in aa]);counts['i6_5a1b']+=1
    for aa in ai4:
        for bb in bnon: clauses.append([vm(a,b) for a in aa for b in bb]);counts['i6_4a2b']+=1
    for aa in ai3:
        for bb in bi3: clauses.append([vm(a,b) for a in aa for b in bb]);counts['i6_3a3b']+=1
    for aa in anon:
        for bb in bi4: clauses.append([vm(a,b) for a in aa for b in bb]);counts['i6_2a4b']+=1
    with cnf.open('w',encoding='ascii') as f:
        f.write(f'p cnf {NA*NB} {len(clauses)}\n')
        for cl in clauses:f.write(' '.join(map(str,cl))+' 0\n')
    d={'campaign':'d11-extreme-unconstrained-glue','a_ordinal':ao,'b_ordinal':bo,'a_graph6':ag6,'b_graph6':bg6,'a_edges':ae,'b_edges':be,'variables':NA*NB,'clauses':len(clauses),'clauses_by_kind':counts}
    meta.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(d,sort_keys=True))

def model_true(path:Path):
    sat=False;vals=set()
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('s ') and 'SATISFIABLE' in line and 'UNSATISFIABLE' not in line:sat=True
        if line.startswith('v '):
            for z in line.split()[1:]:
                try:q=int(z)
                except:continue
                if q>0:vals.add(q)
    if not sat:raise ValueError('model is not SAT')
    return vals

def decode(acat,bcat,ao,bo,model,out):
    _,A,_=select(acat,ao,NA);_,B,_=select(bcat,bo,NB);T=model_true(model)
    R=[['0']*36 for _ in range(36)]
    for a in range(NA):R[0][1+a]=R[1+a][0]='1'
    for i in range(NA):
        for j in range(i+1,NA):
            if (A[i]>>j)&1:R[1+i][1+j]=R[1+j][1+i]='1'
    for i in range(NB):
        for j in range(i+1,NB):
            if (B[i]>>j)&1:R[12+i][12+j]=R[12+j][12+i]='1'
    for a in range(NA):
        for b in range(NB):
            if vm(a,b) in T:R[1+a][12+b]=R[12+b][1+a]='1'
    rr=[''.join(r) for r in R]
    for C in itertools.combinations(range(36),4):
        if all(rr[u][v]=='1' for u,v in itertools.combinations(C,2)):raise AssertionError(('K4',C))
    for C in itertools.combinations(range(36),6):
        if all(rr[u][v]=='0' for u,v in itertools.combinations(C,2)):raise AssertionError(('I6',C))
    deg=[r.count('1') for r in rr];edges=sum(deg)//2
    d={'adjacency':rr}
    out.write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'valid':True,'edges':edges,'degree_sequence':sorted(deg),'cross_edges':sum(1 for a in range(NA) for b in range(NB) if vm(a,b) in T)},sort_keys=True))

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    ex=sp.add_parser('extract');ex.add_argument('input',type=Path);ex.add_argument('n',type=int);ex.add_argument('edges',type=int);ex.add_argument('output',type=Path)
    ge=sp.add_parser('generate');ge.add_argument('a_catalog',type=Path);ge.add_argument('b_catalog',type=Path);ge.add_argument('a_ordinal',type=int);ge.add_argument('b_ordinal',type=int);ge.add_argument('cnf',type=Path);ge.add_argument('meta',type=Path)
    de=sp.add_parser('decode');de.add_argument('a_catalog',type=Path);de.add_argument('b_catalog',type=Path);de.add_argument('a_ordinal',type=int);de.add_argument('b_ordinal',type=int);de.add_argument('model',type=Path);de.add_argument('output',type=Path)
    a=ap.parse_args()
    if a.cmd=='extract': return 0 if extract(a.input,a.n,a.edges,a.output)>=0 else 1
    if a.cmd=='generate':generate(a.a_catalog,a.b_catalog,a.a_ordinal,a.b_ordinal,a.cnf,a.meta);return 0
    decode(a.a_catalog,a.b_catalog,a.a_ordinal,a.b_ordinal,a.model,a.output);return 0
if __name__=='__main__':raise SystemExit(main())
