#!/usr/bin/env python3
"""Cheap census for terminal-aware outside-outside factor filtering."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from bpz_joint_row_defects_maxsat import load_geometry


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B)
    qs=('O','H','V'); caps=(0,1,2,3,4)
    counts={q:{c:0 for c in caps} for q in qs}; dh={q:{} for q in qs}; sh={}
    exact_supports=set(); rows=[]
    for z in range(ring.n):
        if z in B:continue
        S=frozenset(ring.NB[z]&B); exact_supports.add(S); sk=len(S);sh[sk]=sh.get(sk,0)+1
        rec={'z':z,'support':sk}
        for q in qs:
            h=len(ring.NB[z]&fam[q]);d=sk+h-1;rec[q]=d;dh[q][d]=dh[q].get(d,0)+1
            for c in caps:
                if d<=c:counts[q][c]+=1
        if min(rec[q] for q in qs)<=2:rows.append(rec)
    pair_counts={str(c):{f'{q}{r}':counts[q][c]*counts[r][c] for q in qs for r in qs} for c in caps}
    out={'method':'outside-factor-deficit-census','outsiders':ring.n-len(B),'unique_exact_supports':len(exact_supports),'support_size_histogram':{str(k):v for k,v in sorted(sh.items())},'deficit_histograms':{q:{str(k):v for k,v in sorted(h.items())} for q,h in dh.items()},'counts_le_cap':{q:{str(c):counts[q][c] for c in caps} for q in qs},'pair_counts':pair_counts,'near_neutral_factors':sorted(rows,key=lambda x:(min(x[q] for q in qs),x['support'],x['z']))}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('near_neutral_factors','deficit_histograms','support_size_histogram')},sort_keys=True))
    print(json.dumps({'near_neutral_count':len(rows),'best20':out['near_neutral_factors'][:20]},sort_keys=True))
if __name__=='__main__':main()
