#!/usr/bin/env python3
"""Sound m220,n11=6,seq4 high-anchor reduction after the row-CSP audit.

Degree sequence 11^6 12^18 13^11 15. The certified universal low-graph
orbits force zero edges between degree 11 and degree 13/15. Exact class
handshakes give 32 patterns; the local lemmas below exclude 28.

This script does NOT claim the other four patterns are impossible.
"""
import itertools
import json
import networkx as nx

A32 = 'Ls`rbPgB_[ANC]'
LOW = {22: ('Ep~o', [4, 3, 4, 3, 4, 4]),
       24: ('EznW', [4, 4, 4, 4, 4, 4])}

def profile():
    A = nx.from_graph6_bytes(A32.encode())
    assert len(A) == 13 and A.number_of_edges() == 32
    assert sorted(d for _, d in A.degree()) == [4] + [5] * 12
    selected = []
    for U in itertools.combinations(A, 8):
        H = A.subgraph(U)
        if any(H.subgraph(S).number_of_edges() == 0
               for S in itertools.combinations(U, 4)):
            continue
        selected.append((H.number_of_edges(), tuple(sorted(d for _, d in H.degree()))))
    assert len(selected) == 32 and set(selected) == {(12, (3,) * 8)}
    return dict(subsets=1287, alpha_le3=32, edges=12, degrees=[3] * 8)

def matrices():
    out = []
    for R, (g6, r) in LOW.items():
        L = nx.from_graph6_bytes(g6.encode())
        assert [L.degree(i) for i in L] == r and sum(r) == R
        c = 66 - 2 * L.number_of_edges()  # e11_12
        for x in range(56):  # e13_13
            for y in range(12):  # e13_15
                b = 15 - y                  # e12_15
                a = 143 - 2 * x - y          # e12_13
                q = 216 - c - a - b
                if a < 0 or q < 0 or q % 2:
                    continue
                p = q // 2                   # e12_12
                S12 = 11*c + 24*p + 13*a + 15*b
                S13 = 12*a + 26*x + 15*y
                S15 = 12*b + 13*y
                if 132*18 <= S12 <= 147*18 and 143*11 <= S13 <= 164*11 and 165 <= S15 <= 189:
                    out.append(dict(R=R, e11_12=c, e12_12=p, e12_13=a, e12_15=b,
                                    e13_13=x, e13_15=y, S12=S12, S13=S13,
                                    S15=S15, D13=164*11-S13))
    assert len(out) == 32
    return out

def classify(row):
    x,y,D = row['e13_13'],row['e13_15'],row['D13']
    # No K4 and the low independent pair imply that the high graph H
    # has alpha(H)<=3. N_H(z) is triangle-free, so R(3,4)=9 implies y<=8.
    if y >= 9:
        return 'EXCLUDED_R34'
    # At most D of the eleven degree-13 vertices fail S(v)=164.
    # If 11-y>D, an extreme v is nonadjacent to the unique degree-15 z.
    if 11-y > D:
        # Its eight degree-13 neighbours W induce the unique alpha<=3
        # 8-subgraph of A32: 3-regular, 12 edges. Let p,q be the two
        # remaining degree-13 vertices, s=e(z,W), h=e(z,{p,q}),
        # t=e(W,{p,q}), b=e(p,q). For each w in W,
        # 4 + deg_{p,q}(w) + 3*1_{wz} <= 8, hence t<=16-s.
        # e(H)=20+t+b+s+h <=36+b+h <=39.
        # Equality requires b=1,h=2,t=16-s. S(z)<=189 implies
        # y=s+2<=9, so s<=7 and t>=9. But for p and q,
        # deg_W(p)+b+3<=8 and similarly q, hence t<=8.
        # Contradiction: e(H)<=38.
        assert x+y >= 39
        return 'EXCLUDED_EXTREME_ANCHOR'
    return 'UNRESOLVED'

def main():
    p = profile()
    patterns = matrices()
    rows = [{**r,'high_edges':r['e13_13']+r['e13_15'],
             'status':classify(r)} for r in patterns]
    unresolved = [r for r in rows if r['status']=='UNRESOLVED']
    assert len(unresolved) == 4
    assert sorted((r['R'],r['e13_13'],r['e13_15'],r['D13']) for r in unresolved) == [
        (22,29,8,6),(22,30,8,4),(22,31,7,5),(24,30,8,4)]
    out = dict(campaign='m220-n11-6-seq4-high-anchor-post-audit',
               degree_sequence={'11':6,'12':18,'13':11,'15':1}, edges=220,
               A32_profile=p, class_patterns=len(rows),
               excluded_R34=sum(r['status']=='EXCLUDED_R34' for r in rows),
               excluded_anchor=sum(r['status']=='EXCLUDED_EXTREME_ANCHOR' for r in rows),
               unresolved=unresolved,
               high_anchor_edge_bound=38,
               soundness='Exact class handshake, certified low-orbits and unique A32, finite induced-subset census, R(3,4)=9, degree caps. No withdrawn row-domain predicate.',
               conclusion='28 of 32 class patterns excluded; four remain unresolved.')
    assert out['excluded_R34']==7 and out['excluded_anchor']==21
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':
    main()
