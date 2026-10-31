#!/usr/bin/env python3
"""Exact structured RR-strip recoloring for the first support-3 product family.

The 100-round greedy recoloring trace released 199 RR product points, but their
second coordinate belonged to only four regular factors:
    1299, 3421, 3723, 13359.
This script replaces pointwise greedy unfreezing by a structural search.  For
every nonempty subset of these four factors it tests:
  * column mode: all regular x selected-strip RR points are movable;
  * biaxial mode: all RR points with either coordinate in the selected strip are movable.
All 3416 exception-containing product points remain movable as before.  Each
case is an exact clique-fiber SAT under that release family, followed by a full
429^2 replay if SAT.

A SAT case proves raw core gain <= 0 for the entire 429x429 family.  UNSAT cases
are only exclusions of the tested structured recoloring families.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

from bpz_product_level_injection_sat import build_instance
from bpz_product_level_recolor import solve_round, replay_full

STRIP = (1299, 3421, 3723, 13359)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args(); t0=time.time()
    ring,B,regular,exceptions,support,fmap,groups,exception_points,_allowed,_no=build_instance(a.tan_root.resolve())
    R=set(regular)
    missing=[z for z in STRIP if z not in R]
    if missing: raise RuntimeError(('strip factor not regular',missing))
    rows=[]; best=None
    # Smaller structured releases first; first SAT is minimal by subset size then mode.
    for k in range(1,len(STRIP)+1):
        for sub in itertools.combinations(STRIP,k):
            S=set(sub)
            for mode in ('columns','biaxial'):
                if mode=='columns': release={(u,v) for u in regular for v in S}
                else: release={(u,v) for u in regular for v in regular if u in S or v in S}
                ts=time.time()
                rr,movable,_fixed=solve_round(ring,regular,exceptions,support,fmap,groups,exception_points,release)
                rec={k0:v for k0,v in rr.items() if k0 not in ('assignment','blocked')}
                rec.update(strip=list(sub),mode=mode,release_size=len(release),wall_seconds=time.time()-ts)
                if rr['status']=='sat':
                    replay=replay_full(ring,regular,exception_points,support,fmap,release,rr['assignment'])
                    rec['replay']=replay; rec['replay_ok']=True
                    if best is None: best={'strip':list(sub),'mode':mode,'release_size':len(release),'replay':replay}
                rows.append(rec); print(json.dumps(rec,sort_keys=True),flush=True)
            if best is not None:
                # Both modes for this subset were tested; no need to scan larger subsets.
                break
        if best is not None: break
    out={'method':'exact-structured-product-strip-recolor','source_recolor_run':41233309138,'strip_factors':list(STRIP),'cases_tested':len(rows),'sat_cases':sum(r['status']=='sat' for r in rows),'best':best,'rows':rows,'wall_seconds':time.time()-t0}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},sort_keys=True))

if __name__=='__main__': main()
