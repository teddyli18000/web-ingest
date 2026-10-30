#!/usr/bin/env python3
"""Exact structural census for the 429-factor support-3 product family.

The factor universe is the 425 support<=2 outside factors from the certified
owner-clique map plus the four support-3 exceptions from the first minimal
injection obstruction.  The ten-dimensional candidate universe is the ordered
square F x F (184041 vertices).

Two distinct product candidates (u,v),(x,y) conflict iff x is in the closed
C7^5 confusion neighbourhood of u and y is in the closed confusion
neighbourhood of v.  Hence if M is the number of ordered closed-conflict pairs
on F, the product graph has exactly (M^2-|F|^2)/2 undirected conflict edges.
This script computes that quantity and factor-level structure without
materializing the product graph.
"""
from __future__ import annotations
import argparse, json
from collections import Counter, deque
from pathlib import Path

import bpz_joint_row_defects_maxsat as J
from bpz_support3_first_mus_residual_prize import EXCEPTIONS, build_support2_assignment


def components(adj):
    seen=set(); sizes=[]
    for s in range(len(adj)):
        if s in seen: continue
        q=[s]; seen.add(s); n=0
        while q:
            u=q.pop(); n+=1
            for v in adj[u]:
                if v not in seen:
                    seen.add(v); q.append(v)
        sizes.append(n)
    return sorted(sizes, reverse=True)


def gf2_rank(rows, n):
    basis={}
    for x in rows:
        while x:
            p=x.bit_length()-1
            if p in basis: x ^= basis[p]
            else:
                basis[p]=x; break
    return len(basis)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args()
    _base, ring, B0, _fam = J.load_geometry(a.tan_root.resolve()); B=set(B0)
    regular, support, fmap = build_support2_assignment(ring,B)
    for z in EXCEPTIONS:
        support[z]=tuple(sorted(ring.NB[z]&B))
        if len(support[z])!=3: raise RuntimeError(('exception-support',z,support[z]))
    F=sorted(regular+list(EXCEPTIONS)); n=len(F)
    if n!=429 or len(set(F))!=n: raise RuntimeError(('factor-universe',n))
    pos={z:i for i,z in enumerate(F)}

    open_adj=[set() for _ in F]
    closed_adj=[set() for _ in F]
    for i,u in enumerate(F):
        for v in ring.NB[u]:
            j=pos.get(v)
            if j is None: continue
            closed_adj[i].add(j)
            if j!=i: open_adj[i].add(j)
        if i not in closed_adj[i]: raise RuntimeError(('missing-self',u))
    for i in range(n):
        for j in open_adj[i]:
            if i not in open_adj[j]: raise RuntimeError(('asymmetry',i,j))

    open_deg=[len(x) for x in open_adj]; closed_deg=[len(x) for x in closed_adj]
    m_open=sum(open_deg)//2; M=sum(closed_deg)
    prod_vertices=n*n
    prod_edges=(M*M-prod_vertices)//2
    if (M*M-prod_vertices)%2: raise RuntimeError('parity')

    # Exact closed-neighbourhood twins are an immediately safe quotient signal.
    twin=Counter(tuple(sorted(x)) for x in closed_adj)
    twin_sizes=sorted(twin.values(),reverse=True)

    # Support-signature multiplicities and owner-map multiplicities.
    sig=Counter(tuple(support[z]) for z in F)
    owner_counts=Counter(fmap[z] for z in regular)

    # GF(2) rank of the closed relation; low rank would suggest algebraic compression.
    bitrows=[]
    for nbr in closed_adj:
        x=0
        for j in nbr: x |= 1<<j
        bitrows.append(x)
    rank2=gf2_rank(bitrows,n)

    # Complement components: if disconnected, conflict graph is a join and MWIS decomposes.
    comp_adj=[]
    allv=set(range(n))
    for i in range(n): comp_adj.append(allv-{i}-open_adj[i])

    out={
      'method':'support3-factor-product-graph-stats',
      'factor_count':n,
      'regular_factors':len(regular),
      'exceptions':list(EXCEPTIONS),
      'support_size_histogram':dict(sorted(Counter(len(support[z]) for z in F).items())),
      'support_signature_count':len(sig),
      'max_support_signature_multiplicity':max(sig.values()),
      'owner_map_distinct':len(owner_counts),
      'owner_map_max_multiplicity':max(owner_counts.values()),
      'factor_open_edges':m_open,
      'factor_open_degree_min':min(open_deg),
      'factor_open_degree_max':max(open_deg),
      'factor_open_degree_mean':sum(open_deg)/n,
      'factor_closed_ordered_pairs':M,
      'factor_closed_degree_min':min(closed_deg),
      'factor_closed_degree_max':max(closed_deg),
      'factor_closed_degree_mean':sum(closed_deg)/n,
      'factor_conflict_components':components(open_adj),
      'factor_compatibility_components':components(comp_adj),
      'closed_neighborhood_twin_classes':len(twin),
      'closed_neighborhood_twin_max_class':max(twin_sizes),
      'closed_neighborhood_twin_nontrivial_classes':sum(1 for x in twin_sizes if x>1),
      'closed_relation_gf2_rank':rank2,
      'product_vertices':prod_vertices,
      'product_conflict_edges_exact':prod_edges,
      'product_conflict_average_degree':2*prod_edges/prod_vertices,
      'product_conflict_clause_memory_16bytes_gib':prod_edges*16/(1024**3),
    }
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__': main()
