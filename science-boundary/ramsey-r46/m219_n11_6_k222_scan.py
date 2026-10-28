#!/usr/bin/env python3
"""Catalogue test for the special m=219,n11=6 branch L=K_{2,2,2}.

Choose any degree-11 anchor v in one 2-vertex part of L.  Its four L-neighbours
are the two other parts and lie in A=N(v); the mate u in v's own part lies in
B.  Since u is adjacent to all four L-vertices in A, u needs at least four
A--B cross edges.  As deg_G(u)=11, necessarily deg_B(u)<=7.

For v, S(v)=128+w where w is the high-degree excess among its seven non-L
neighbours; S(v)<=129 gives w=0 or 1.  Therefore the exact local pair is one of
(A25,B116), (A26,B117), or (A26,B116).  Consequently, if every complete B116
and B117 catalogue graph has minimum degree at least 8, the entire K222 branch
is impossible.
"""
from __future__ import annotations

import argparse,json
from collections import Counter
from pathlib import Path
import d12_fixed_ab_sat as base


def scan(path:Path, wanted:set[int]):
    out={e:[] for e in wanted};hist={e:Counter() for e in wanted};total=0
    for _,s,adj,e in base.iter_g6(path):
        if len(adj)!=24:continue
        total+=1
        if e not in wanted:continue
        ds=base.degrees(adj);m=min(ds);hist[e][m]+=1
        out[e].append({'graph6':s,'degree_sequence':sorted(ds),'min_degree':m})
    assert total==352366,total
    return {str(e):{'count':len(out[e]),'min_degree_histogram':{str(k):v for k,v in sorted(hist[e].items())},
                    'minimum_over_stratum':min(x['min_degree'] for x in out[e]),'graphs':out[e]} for e in sorted(wanted)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--r45-24',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    d=scan(a.r45_24,{116,117})
    assert d['116']['count']==9 and d['117']['count']==90,(d['116']['count'],d['117']['count'])
    killed=d['116']['minimum_over_stratum']>=8 and d['117']['minimum_over_stratum']>=8
    result={'campaign':'m219-n11-6-K222-antineighborhood-scan','B_strata':d,
            'mate_cross_edges_required':4,'mate_global_degree':11,'required_B_degree_max':7,
            'K222_impossible':killed}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'B116_min':d['116']['minimum_over_stratum'],'B117_min':d['117']['minimum_over_stratum'],
                      'B116_hist':d['116']['min_degree_histogram'],'B117_hist':d['117']['min_degree_histogram'],'K222_impossible':killed},sort_keys=True))
if __name__=='__main__':main()
