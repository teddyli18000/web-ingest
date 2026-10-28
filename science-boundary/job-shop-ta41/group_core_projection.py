#!/usr/bin/env python3
"""Exact finite projection of 1,433 adjacency UNSAT cores to machine groups.

This is a controlled weakness test of a tempting abstraction:
if an adjacency core touches machines G, then any <=2005 schedule must
change at least one machine in G. The projection is logically valid but
throws away *which* adjacent relation on that machine must change.
Enumerate every one of the 2^20 machine-change masks to find the exact
distance bound preserved by the projected hypergraph.
"""
import argparse
import json
from pathlib import Path

def main(inp,out):
    src=json.loads(inp.read_text())
    assert src['target']==2005 and src['baseline']==2006
    raw=src['core_sets']
    groups={sum(1 << m for m in set(i//29 for i in core)) for core in raw}
    ordered=sorted(groups,key=lambda x:(x.bit_count(),x))
    reduced=[]
    for mask in ordered:
        if not any(mask & prior == prior for prior in reduced):
            reduced.append(mask)
    assert all(any(c&d==d for d in reduced) for c in groups)
    counts=[0]*21
    witness=[None]*21
    for released in range(1<<20):
        if all(released&group for group in reduced):
            k=released.bit_count()
            counts[k]+=1
            if witness[k] is None:witness[k]=released
    first=next((i for i,n in enumerate(counts) if n),None)
    assert first is not None
    report={
      'original_adjacency_unsat_core_count':len(raw),
      'unique_group_core_count':len(groups),
      'nondominated_group_core_count':len(reduced),
      'all_group_change_masks_exhaustively_enumerated':1<<20,
      'exact_lower_bound_from_group_projected_cores':first,
      'minimal_mask_witness':witness[first],
      'minimal_mask_machine_ids':[m for m in range(20) if witness[first] & (1<<m)],
      'accepted_mask_counts_by_changed_machine_cardinality':counts,
      'reduced_group_cores_machine_masks':reduced,
      'interpretation':'This weak lower bound is a LOGICAL projection consequence of the sampled UNSAT cores. It is not an upper or lower bound on makespan; the exact NoOverlap constraints may imply much stronger restrictions.'
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='reduced_group_cores_machine_masks'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path(__file__).parent/'results'/'core-seed4107'/'core-analysis.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'group-core-projection.json')
    a=p.parse_args();main(a.input,a.out)
