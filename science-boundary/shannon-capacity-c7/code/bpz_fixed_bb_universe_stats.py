#!/usr/bin/env python3
"""Exact structural audit of the complete 10D universe compatible with BPZ BB.

Let I0 be the pinned 367-point five-dimensional parent, R the eight owners from
its private pairs, and B=I0\R (|B|=359).  Define

    Z = {z in C7^5 : N[z] intersect B = empty}.

A 10D vertex (u,v) is compatible with every point of BB=B x B iff u in Z or
v in Z.  Hence the *complete* fixed-core candidate universe is

    U = (Z x V5) union (V5 x Z).

This script computes Z exhaustively from the pinned Tandon/BPZ data, compares it
with the 16 private-pair endpoints Q=PH union PV, audits the graph on Q, and
checks that the union of all 18 score-134753 terminal peripheries is exactly
X x Q union Q x X.
"""

import argparse
import json
from pathlib import Path
import sys


def alpha_bruteforce(vertices, edges):
    n=len(vertices)
    adj=[0]*n
    for i,j in edges:
        adj[i]|=1<<j; adj[j]|=1<<i
    best=0; best_mask=0
    # n is expected to be 16. Branch-and-bound maximum independent set.
    def dfs(cand, chosen):
        nonlocal best,best_mask
        if chosen.bit_count()+cand.bit_count()<=best: return
        if not cand:
            k=chosen.bit_count()
            if k>best: best=k; best_mask=chosen
            return
        # branch on a high-degree remaining vertex
        vs=[i for i in range(n) if (cand>>i)&1]
        v=max(vs,key=lambda x:(adj[x]&cand).bit_count())
        dfs(cand & ~(1<<v) & ~adj[v], chosen | (1<<v))
        dfs(cand & ~(1<<v), chosen)
    dfs((1<<n)-1,0)
    return best,[vertices[i] for i in range(n) if (best_mask>>i)&1]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tan_root",type=Path)
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore

    base,_transform,_exchanges,axioms=load_base(root/"data"/"base_c7.json")
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    I=set(base.I0.elements); X=set(base.X.elements)
    PH=set(base.PH.elements); PV=set(base.PV.elements); Q=PH|PV
    pairs=[tuple(map(int,p)) for p in base.private_pairs]
    owners={p[0] for p in pairs}
    alts={p[1] for p in pairs}
    B=I-owners
    if (len(I),len(X),len(B),len(PH),len(PV),len(Q),len(pairs))!=(367,367,359,8,8,16,8):
        raise RuntimeError(("base size drift",len(I),len(X),len(B),len(PH),len(PV),len(Q),len(pairs)))
    if owners|alts!=Q or owners&alts:
        raise RuntimeError(("private endpoint partition drift",owners,alts,Q))

    Z={z for z in range(ring.n) if not (ring.NB[z]&B)}
    q_edges=[]; qv=sorted(Q); qi={z:i for i,z in enumerate(qv)}
    for i,a in enumerate(qv):
        for j in range(i+1,len(qv)):
            b=qv[j]
            if b in ring.NB[a]: q_edges.append((i,j))
    pair_conflicts=[b in ring.NB[a] for a,b in pairs]
    if not all(pair_conflicts):
        raise RuntimeError(("private pair lost conflict",pair_conflicts))
    ph_ind=all(not ((ring.NB[x]&PH)-{x}) for x in PH)
    pv_ind=all(not ((ring.NB[x]&PV)-{x}) for x in PV)
    alpha_q,alpha_q_witness=alpha_bruteforce(qv,q_edges)

    # 18 terminal optima, directly from the two orientations and q,r choices.
    fam={"B":B,"N":set(base.X0.elements),"A":set(base.XV.elements),
         "D":set(base.XH.elements),"O":set(base.R.elements),"H":PH,"V":PV}
    code_periphery_union=set(); code_sizes=[]
    for q in ("O","H","V"):
        for r in ("O","H","V"):
            for orient in (0,1):
                if orient==0:
                    words=(("N",q),("A","H"),("D","V"),(r,"N"),("H","D"),("V","A"))
                else:
                    words=(("N",q),("A","V"),("D","H"),(r,"N"),("H","A"),("V","D"))
                P=set()
                for a,b in words:
                    P.update((x,y) for x in fam[a] for y in fam[b])
                code_sizes.append(len(P)); code_periphery_union|=P
    expected_xq={(x,q) for x in X for q in Q}|{(q,x) for q in Q for x in X}

    status={
        "method":"exact-pinned-bpz-fixed-BB-universe-audit",
        "I0_size":len(I),"B_size":len(B),"X_size":len(X),
        "private_pairs":[list(p) for p in pairs],
        "PH":sorted(PH),"PV":sorted(PV),"Q":qv,
        "Z_size":len(Z),"Z":sorted(Z),"Z_equals_Q":Z==Q,
        "Q_conflict_edges":len(q_edges),
        "Q_edge_pairs":[[qv[i],qv[j]] for i,j in q_edges],
        "private_pairs_all_conflict":all(pair_conflicts),
        "PH_independent":ph_ind,"PV_independent":pv_ind,
        "alpha_Q":alpha_q,"alpha_Q_witness":alpha_q_witness,
        "fixed_BB_universe_size":2*ring.n*len(Z)-len(Z)*len(Z),
        "terminal_optimum_periphery_sizes":sorted(set(code_sizes)),
        "terminal_periphery_union_size":len(code_periphery_union),
        "XQ_union_size":len(expected_xq),
        "terminal_periphery_union_equals_XQ_union":code_periphery_union==expected_xq,
        "terminal_periphery_alpha_upper_from_split":2*len(X)*alpha_q,
        "terminal_periphery_known_record_size":5872,
        "fixed_BB_breakthrough_implies_alpha_C7_5_at_least":368 if len(Z)==16 and all(pair_conflicts) else None,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps(status,sort_keys=True))

if __name__=="__main__": main()
