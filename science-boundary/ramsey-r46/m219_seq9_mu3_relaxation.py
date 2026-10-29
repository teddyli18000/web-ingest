#!/usr/bin/env python3
"""Exact 0-1 relaxation excluding mu=3 low-low nonedges for h=1,2,3.

Scope: m=219 degree sequence 11^12 12^6 13^18.  The exact degree-class
relaxation proves every degree-11 vertex has r(v)=132-S(v)=3, hence each such
vertex has local (A,B) edge strata A26/B116.  Among B116 types, ordinal 1 is
the only type other than the already-excluded ordinal 4 that can realize a
mu=3 low-low nonedge; its unique internal-degree-8 B vertex is forced to be
low here.

This model intentionally omits *all* K4/independent-6 constraints.  It keeps
only necessary degree labels, cross-edge degree equations, and r=3 equations
for every low vertex.  Infeasibility is therefore a sound exclusion for the
full Ramsey problem.
"""
from __future__ import annotations
import argparse, json, platform, time
import networkx as nx
import numpy as np
import scipy
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix

A26 = ("JiQC@{}N`{?", "JqPA@{}N`{?")
B116_ORDINAL1 = "WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?"
NA, NB = 11, 24
DEGS = (11,12,13)
SEQ = {11:12,12:6,13:18}

def solve(a_type:int, h:int, time_limit:float=30.0):
    assert a_type in (0,1) and h in (1,2,3)
    A=nx.from_graph6_bytes(A26[a_type].encode()); B=nx.from_graph6_bytes(B116_ORDINAL1.encode())
    assert A.number_of_nodes()==11 and A.number_of_edges()==26
    assert B.number_of_nodes()==24 and B.number_of_edges()==116
    db=[B.degree(b) for b in range(NB)]; assert db.count(8)==1 and db[0]==8
    da=[A.degree(a) for a in range(NA)]
    nxv=NA*NB; qa0=nxv; qb0=qa0+NA*3
    zB110=qb0+NB*3; zB130=zB110+nxv; zA110=zB130+nxv; zA130=zA110+nxv; nvar=zA130+nxv
    def X(a,b): return a*NB+b
    def QA(a,j): return qa0+a*3+j
    def QB(b,j): return qb0+b*3+j
    def Z(base,a,b): return base+a*NB+b
    rows=[]; lo=[]; hi=[]
    def add(co,l,h): rows.append(co);lo.append(l);hi.append(h)
    # one-hot labels
    for a in range(NA): add([(QA(a,j),1) for j in range(3)],1,1)
    for b in range(NB): add([(QB(b,j),1) for j in range(3)],1,1)
    for j,d in enumerate(DEGS):
        add([(QA(a,j),1) for a in range(NA)]+[(QB(b,j),1) for b in range(NB)], SEQ[d]-(d==11), SEQ[d]-(d==11))
    # anchor v has h high neighbours; r(v)=t-h=3 fixes A class counts.
    ac={11:h+3,12:8-2*h,13:h}
    for j,d in enumerate(DEGS): add([(QA(a,j),1) for a in range(NA)],ac[d],ac[d])
    # Unique degree-8 vertex of B1 is the other low endpoint, so mu(v,u)=11-8=3.
    add([(QB(0,0),1)],1,1)
    # Cross degrees determined by final degree labels.
    for a in range(NA):
        add([(X(a,b),1) for b in range(NB)]+[(QA(a,j),-(d-1-da[a])) for j,d in enumerate(DEGS)],0,0)
    for b in range(NB):
        add([(X(a,b),1) for a in range(NA)]+[(QB(b,j),-(d-db[b])) for j,d in enumerate(DEGS)],0,0)
    add([(i,1) for i in range(nxv)],66,66)
    # Product variables x_ab AND endpoint-label(low/high).
    for a in range(NA):
        for b in range(NB):
            x=X(a,b)
            for z,q in ((Z(zB110,a,b),QB(b,0)),(Z(zB130,a,b),QB(b,2)),
                        (Z(zA110,a,b),QA(a,0)),(Z(zA130,a,b),QA(a,2))):
                add([(z,1),(x,-1)],-np.inf,0); add([(z,1),(q,-1)],-np.inf,0)
                add([(z,1),(x,-1),(q,-1)],-1,np.inf)
    # Conditional r=3 for every low vertex.  Weight is +1 for low, 0 for 12, -1 for high.
    M=20
    for a in range(NA):
        co=[]
        for aa in A.neighbors(a): co += [(QA(aa,0),1),(QA(aa,2),-1)]
        for b in range(NB): co += [(Z(zB110,a,b),1),(Z(zB130,a,b),-1)]
        q=QA(a,0) # anchor contributes +1, so the displayed expression must equal 2
        add(co+[(q,M)],-np.inf,2+M); add(co+[(q,-M)],2-M,np.inf)
    for b in range(NB):
        co=[]
        for bb in B.neighbors(b): co += [(QB(bb,0),1),(QB(bb,2),-1)]
        for a in range(NA): co += [(Z(zA110,a,b),1),(Z(zA130,a,b),-1)]
        q=QB(b,0)
        add(co+[(q,M)],-np.inf,3+M); add(co+[(q,-M)],3-M,np.inf)
    mat=lil_matrix((len(rows),nvar),dtype=float)
    for r,co in enumerate(rows):
        for c,v in co: mat[r,c]+=v
    t=time.time(); res=milp(np.zeros(nvar),integrality=np.ones(nvar),
        bounds=Bounds(np.zeros(nvar),np.ones(nvar)),
        constraints=LinearConstraint(mat.tocsr(),np.asarray(lo),np.asarray(hi)),
        options={'time_limit':time_limit,'presolve':True,'disp':False})
    return {'a_type':a_type,'h':h,'status_code':int(res.status),
        'status':'INFEASIBLE' if res.status==2 else ('FEASIBLE' if res.x is not None else 'UNKNOWN'),
        'message':res.message,'seconds':time.time()-t,'variables':nvar,'constraints':len(rows),
        'scipy':scipy.__version__,'python':platform.python_version()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--a-type',type=int);p.add_argument('--h',type=int);p.add_argument('--all',action='store_true');p.add_argument('--time-limit',type=float,default=30);p.add_argument('--output')
    a=p.parse_args(); rows=[]
    cases=[(i,h) for h in (1,2,3) for i in (0,1)] if a.all else [(a.a_type,a.h)]
    for i,h in cases: rows.append(solve(i,h,a.time_limit))
    out={'campaign':'m219-seq9-mu3-degree-relaxation','degree_sequence':{'11':12,'12':6,'13':18},
         'ramsey_constraints_included':False,'cases':rows,'all_infeasible':len(rows)==6 and all(r['status']=='INFEASIBLE' for r in rows)}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(text,end='')
    if a.output: open(a.output,'w').write(text)
if __name__=='__main__': main()
