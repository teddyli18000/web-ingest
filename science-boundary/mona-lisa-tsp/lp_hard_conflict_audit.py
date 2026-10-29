#!/usr/bin/env python3
"""LP–tour hard conflicts: alternative edges with x≈1 vs incumbent x≈0.

Primal LP x=1 is not an optimal-tour edge certificate; it may be useful as a
distinct signal from fractional LP support. This computes incident spatial/
historical variable-component distributions and checks cross-snapshot status.
"""
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
import numpy as np
import historical_lp_disagreement as h
N=100000
def main():
 p=argparse.ArgumentParser()
 for k in ('baseline','tours','lps','components','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args()
 baseline=np.asarray(json.loads(Path(a.baseline).read_text())['tour'],dtype=np.int32)-1
 base=set(map(int,h.tour_edges(baseline)))
 comps=json.loads(Path(a.components).read_text())['components']
 owner=np.full(N,-1,dtype=np.int32)
 for c in comps:owner[c['members_0based']]=int(c['id'])
 hist=set()
 for path in json.loads(Path(a.tours).read_text()).values():
    t=h.parse_tour(path);hist.update(map(int,h.tour_edges(t)))
    assert len(t)==N
 snapshots={name:h.lp_read(p) for name,p in json.loads(Path(a.lps).read_text()).items()}
 out={}
 for name,lp in snapshots.items():
    x1={int(e) for e,x in zip(lp['edge_ids'],lp['x']) if x>=1-1e-5}
    frac={int(e) for e,x in zip(lp['edge_ids'],lp['x']) if 1e-5<x<1-1e-5}
    hard=x1-base
    missing=base-x1-frac
    source_hit=hard&hist
    per=Counter();link_to_stable=0;cross=0
    for e in hard:
        u,w=divmod(e,N)
        o1,o2=int(owner[u]),int(owner[w])
        if o1>=0:per[o1]+=1
        if o2>=0 and o2!=o1:per[o2]+=1
        if o1!=o2:cross+=1
        if o1==-1 or o2==-1:link_to_stable+=1
    out[name]={'lp_x1_edges':len(x1),'lp_fractional_edges':len(frac),
      'lp_x1_not_Nagata':len(hard),
      'hard_lp_conflicts_already_in_historical_tours':len(source_hit),
      'hard_lp_conflicts_new_to_all_historical_tours':len(hard-hist),
      'Nagata_x0_or_absent_edges':len(missing),
      'hard_lp_conflicts_cross_component':cross,
      'hard_lp_conflicts_touching_historically_undisputed_city':link_to_stable,
      'hard_lp_conflicts_by_component':dict(per.most_common(15))}
 x1s=[{int(e) for e,x in zip(lp['edge_ids'],lp['x']) if x>=1-1e-5} for lp in snapshots.values()]
 persistent=set.intersection(*x1s)-base
 out['persistent_x1_not_Nagata_in_three_snapshots']={
     'count':len(persistent),'unseen_in_all_historical_tours':len(persistent-hist)}
 target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(out),flush=True)
if __name__=='__main__':main()
