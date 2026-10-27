#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import generalized9 as g
import rank3_square_relax as rs


def bits(mask):
    out=[]
    while mask:
        b=mask & -mask
        out.append(b.bit_length()-1)
        mask ^= b
    return out


def port_conflict(a,b,xset,digits):
    oa,ia,ea=a; ob,ib,eb=b
    if oa=="H" and ob=="H":
        return g.conflict(ea,eb,digits) and g.conflict(xset[ia],xset[ib],digits)
    if oa=="V" and ob=="V":
        return g.conflict(xset[ia],xset[ib],digits) and g.conflict(ea,eb,digits)
    if oa=="H":
        return g.conflict(ea,xset[ib],digits) and g.conflict(xset[ia],eb,digits)
    return g.conflict(xset[ib],ea,digits) and g.conflict(eb,xset[ia],digits)


def alpha_small(v,xset,digits):
    for k in range(len(v),0,-1):
        for sub in combinations(v,k):
            if all(not port_conflict(a,b,xset,digits) for a,b in combinations(sub,2)):
                return k, sub
    return 0, ()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("r367",type=Path); ap.add_argument("output",type=Path); args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U))
    r0=g.load_r(args.r367); xset=g.make_x(r0,digits); r=rs.load_rank3_state(r0,digits)
    supports,_=g.support_masks(r,digits)
    kset=set(rs.RANK3_K9); bidx=[i for i in range(g.R_SIZE) if i not in kset]; bmask=sum(1<<i for i in bidx); bvals={r[i] for i in bidx}

    egrp=defaultdict(list)
    for e,sm in enumerate(supports):
        if e in bvals: continue
        o=tuple(bits(sm & bmask))
        if 1 <= len(o) <= 2: egrp[o].append(e)
    xgrp=defaultdict(list)
    for xi,x in enumerate(xset):
        o=tuple(bits(supports[x] & bmask))
        if 1 <= len(o) <= 2: xgrp[o].append(xi)

    unlocked=defaultdict(list)
    one=defaultdict(list)
    for eo,es in egrp.items():
        for xo,xis in xgrp.items():
            cost=len(eo)*len(xo)
            if cost not in (1,2): continue
            for e in es:
                for xi in xis:
                    hs=tuple(sorted((a,b) for a in eo for b in xo)); vs=tuple(sorted((b,a) for a in eo for b in xo))
                    hd=("H",xi,e); vd=("V",xi,e)
                    if cost==1:
                        one[hs[0]].append(hd); one[vs[0]].append(vd)
                    else:
                        unlocked[hs].append(hd); unlocked[vs].append(vd)

    pairs=set(unlocked)
    oks=sorted(one)
    # Pairs formed solely by cost-1 candidates matter too.
    for a,b in combinations(oks,2): pairs.add(tuple(sorted((a,b))))

    hist=defaultdict(int); best=0; best_records=[]; checked=0
    for pair in pairs:
        a,b=pair
        ports=list(unlocked.get(pair,()))+list(one.get(a,()))+list(one.get(b,()))
        # de-duplicate descriptors defensively
        ports=list(dict.fromkeys(ports))
        al, witness=alpha_small(ports,xset,digits)
        hist[al]+=1; checked+=1
        rec={"square_pair":[list(a),list(b)],"raw":len(ports),"alpha":al,"witness":[list(p) for p in witness]}
        if al>best:
            best=al; best_records=[rec]
        elif al==best and len(best_records)<100:
            best_records.append(rec)

    out={"state":rs.STATE_INDEX,"k9":list(rs.RANK3_K9),"pairs_checked":checked,"max_compatible_nonzero_ports_after_two_deletions":best,"alpha_histogram":dict(sorted(hist.items())),"radius2_nonzero_gain_at_most_2":best<=2,"best_pairs":best_records}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True),flush=True)

if __name__=="__main__": main()
