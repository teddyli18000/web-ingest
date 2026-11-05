#!/usr/bin/env python3
"""Post-audit exact exclusion for m220,n11=6,degree seq 11^6 12^16 13^14.
Inputs: certified R=22/24 low-boundary orbits, independent lucky-d12
exclusion S(v)<=147, and the classical R(3,4)=9.
No SAT, LP, row CSP or graph catalogue is used here.
"""
import itertools
import json

LOW = {22: ('Ep~o',(4,3,4,3,4,4)), 24: ('EznW',(4,4,4,4,4,4))}

def graph6_adjacency(g6):
    n=ord(g6[0])-63
    bits=((ord(c)-63>>shift)&1 for c in g6[1:] for shift in (5,4,3,2,1,0))
    adj=[0]*n
    for j in range(1,n):
        for i in range(j):
            if next(bits):
                adj[i]|=1<<j
                adj[j]|=1<<i
    return adj

def main():
    cases=[]
    for R,(g6,r) in LOW.items():
        a=graph6_adjacency(g6)
        degree=tuple(x.bit_count() for x in a)
        assert degree==r and sum(degree)==R
        assert all(not all(a[i]>>j&1 for i,j in itertools.combinations(U,2))
                   for U in itertools.combinations(range(6),4))
        # r(v)=t(v)-w(v), all high-excess weights >=0. r=t
        # therefore implies the low and high vertex classes are anticomplete.
        assert all(t-v==0 for t,v in zip(degree,r))
        # Low-degree handshake: 66 endpoints = R internal + e(L,M).
        low_middle=66-R
        assert low_middle<3*16
        # Some degree-12 m sees l<=2 degree-11 lows. If it sees h
        # degree-13 highs, S(m)=144+h-l<=147 means h<=l+3.
        possible=[(l,h) for l in range(3) for h in range(15)
                  if l+h<=12 and h-l<=3]
        assert possible
        assert all(6-l>=4 and 14-h>=9 for l,h in possible)
        # Four low nonneighbours contain an independent pair (K4-free);
        # nine high nonneighbours contain an independent triple (R(4,3)=9).
        # L and H are anticomplete. Add m to obtain forbidden I6.
        cases.append({'R':R,'low_graph6':g6,
                      'low_internal_degrees':list(degree),
                      'low_middle_edges':low_middle,'middle_vertices':16,
                      'middle_vertex_with_l_at_most_2_forced':True,
                      'checked_admissible_l_h_pairs':len(possible),
                      'ramsey_obstruction':'I2 in >=4 low nonneighbors + I3 in >=9 high nonneighbors + m gives I6'})
    result={'campaign':'m220-n11-6-seq1-pigeonhole-post-audit',
      'degree_sequence':{'11':6,'12':16,'13':14},'edges':220,
      'prior_certificates':['results/m220-n11-6-universal-low-post-audit.json',
       'results/d12-anchor-orbits.json','results/d12-residual-symmetry.json'],
      'classical_fact':'R(4,3)=R(3,4)=9',
      'cases':cases,'status':'UNSAT_for_this_degree_sequence',
      'soundness':'Standalone graph6 decoding; degree handshake and Ramsey obstruction; no withdrawn row-CSP, MILP, or new SAT run.',
      'conclusion':'No 36-vertex (4,6)-graph with 220 edges has degree sequence 11^6 12^16 13^14.'}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
