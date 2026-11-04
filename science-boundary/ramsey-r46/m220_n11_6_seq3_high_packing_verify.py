#!/usr/bin/env python3
"""Independent exact exclusion: m=220, n11=6, 11^6 12^18 13^10 14^2.

Inputs already separately certified: n11=6 low-orbits R in {22,24} with
no low/high edges; S12<=147; S13<=164; complete B88 extreme-edge stratum.
No withdrawn row-domain predicate, SAT, or heuristic result is used.
"""
import collections
import hashlib
import itertools
import json

B88 = (
    'U?`@?bGKdWSWRELSWk?fGtHUMVEuH@VP`}HA[Ui?',
    'U?`D@`gFCkIWwcbK\\CPVOdQWu[Cqsadm@ddCRPM?',
    'U?`@?bGpDcCY[PCyTahjgxobZG@tbAxIaMYGRY`?',
)
B88_SHA256 = 'cdb6bbe20c73cd578590d57d896a343fceed76f5216d2a8524ccd1afd9559fb8'
LOW_PROFILES = {22: (3, 3, 4, 4, 4, 4), 24: (4, 4, 4, 4, 4, 4)}

def decode_graph6(code):
    """Standard graph6 COLUMN-major upper triangle ordering."""
    n = ord(code[0]) - 63
    stream = ((ord(ch) - 63) >> shift & 1
              for ch in code[1:] for shift in (5, 4, 3, 2, 1, 0))
    adj = [0] * n
    for j in range(1, n):
        for i in range(j):
            if next(stream):
                adj[i] |= 1 << j
                adj[j] |= 1 << i
    return adj

def scan_b88():
    raw = ('\n'.join(B88) + '\n').encode('ascii')
    assert hashlib.sha256(raw).hexdigest() == B88_SHA256
    records = {}
    for bi, code in enumerate(B88):
        adj = decode_graph6(code)
        assert len(adj) == 22 and sum(x.bit_count() for x in adj) == 176
        per_low = {}
        for R, profile in LOW_PROFILES.items():
            counts = collections.Counter()
            three_cliques = 0
            for S in itertools.combinations(range(22), 6):
                mask = sum(1 << v for v in S)
                degrees = tuple(sorted((adj[v] & mask).bit_count() for v in S))
                if degrees != profile:
                    continue
                anti = [w for w in range(22) if not (mask >> w & 1)
                        and not (adj[w] & mask)]
                counts[len(anti)] += 1
                if len(anti) == 3:
                    assert all((adj[u] >> v) & 1
                               for u, v in itertools.combinations(anti, 2))
                    three_cliques += 1
            per_low[str(R)] = {
                'anticomplete_histogram': dict(sorted(counts.items())),
                'maximum_anticomplete': max(counts, default=-1),
                'three_vertex_clique_count': three_cliques,
            }
        records[str(bi)] = per_low
    assert [records[str(i)]['22']['maximum_anticomplete']
            for i in range(3)] == [3, 2, 2]
    assert all(records[str(i)]['24']['anticomplete_histogram'] == {}
               for i in range(3))
    assert [records[str(i)]['22']['three_vertex_clique_count']
            for i in range(3)] == [12, 0, 0]
    return records

def enumerate_class_matrices():
    """Superset of every possible degree-class edge matrix, not a SAT model."""
    rows = []
    for R in (22, 24):
        c = 66 - R  # e(11,12)
        for x in range(46):  # e(13,13)
            for y in range(21):  # e(13,14)
                for z in range(2):  # e(14,14)
                    a, b = 130 - 2*x - y, 28 - y - 2*z
                    twice_p = 216 - c - a - b
                    if min(a, b, twice_p) < 0 or twice_p % 2:
                        continue
                    p = twice_p // 2
                    s12 = 11*c + 24*p + 13*a + 14*b
                    s13 = 12*a + 26*x + 14*y
                    s14 = 12*b + 13*y + 28*z
                    if not (132*18 <= s12 <= 147*18
                            and 143*10 <= s13 <= 164*10
                            and 154*2 <= s14 <= 178*2):
                        continue
                    D = 1640 - s13
                    assert D == 80 - 2*(x+y)
                    assert 2632 + R + D - y - 4*z == s12
                    assert y + 4*z >= R + D - 14
                    rows.append({'R': R, 'x': x, 'y': y, 'z': z, 'D': D})
    assert len(rows) == 170
    return rows

def main():
    catalogue = scan_b88()
    matrices = enumerate_class_matrices()
    # Rigorous structural lemma:
    # An extreme degree-13 v with S(v)=164 forces (eA,eB)=(32,88).
    # Let k be its number of degree-14 neighbours. Since all low vertices
    # have no high neighbours, deg_13(v)=8-2k, and its high nonneighbours
    # number 3+k. The complete B88 profile scan forces R=22, k=0.
    # Its unique nonadjacent degree-13 vertex and both degree-14 vertices
    # are the B88 3-anticomplete vertices, and form a triangle.
    # Thus two extreme d13 vertices cannot be nonadjacent. If adjacent,
    # they have >=6 common degree-13 neighbours; these are independent
    # by K4-freeness, contradicting alpha(G)<=5.
    # Therefore at most one of ten d13 vertices is extreme. The integer
    # deficit D=1640-S13 is even and >=9, hence D>=10.
    compatible = []
    after_deficit = 0
    for row in matrices:
        if row['D'] < 10:
            continue
        after_deficit += 1
        # The high graph has alpha<=3: its 6 low anticomplete vertices
        # contain an independent pair. If z=0, both degree-14 vertices
        # have <=8 high neighbours by R(3,4)=9, giving y<=16.
        # If z=1, the pair's common degree-13 neighbours are independent;
        # there are at least y-10 of them, giving y<=13.
        y_limit = 16 if row['z'] == 0 else 13
        if row['y'] <= y_limit:
            compatible.append(row)
    assert after_deficit == 10 and not compatible
    result = {
        'campaign': 'm220-n11-6-seq3-high-packing-post-audit',
        'degree_sequence': {'11': 6, '12': 18, '13': 10, '14': 2},
        'edges': 220, 'complete_B88_member_sha256': B88_SHA256,
        'B88_profile_scan': catalogue,
        'class_matrices_before_new_constraints': len(matrices),
        'matrices_after_extreme_deficit': after_deficit,
        'matrices_after_high_graph_degree_constraints': len(compatible),
        'D_lower_bound': 10, 'D_even': True,
        'inequality_lower': 'y+4z >= R+D-14 >= 18',
        'inequality_upper': 'y+4z <= 17 (z=0: y<=16; z=1: y<=13)',
        'soundness': 'Published complete B88 stratum, independent graph6 decoder; '
                     'post-audit exact low-graph boundary, degree handshakes, '
                     'edge-extreme bounds, K4/I6 and R(3,4)=9. No withdrawn row CSP.',
        'all_unsat': True,
        'conclusion': 'No 220-edge (4,6)-graph on 36 vertices has this degree sequence.'
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result

if __name__ == '__main__':
    main()
