#!/usr/bin/env python3
"""No hidden solution data: inspect selected/USED edges of the 5-case blind run.

This exposes ranking redundancy and separates candidate retrieval from any
incremental improvement over the parent-only exact tour merge.
"""
import argparse,json
from collections import defaultdict
from pathlib import Path
def E(a,b):return (min(a,b),max(a,b))
def edges(t):return {E(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--artifacts',required=True);p.add_argument('--output',required=True)
 args=p.parse_args()
 groups=defaultdict(dict)
 for file in Path(args.artifacts).rglob('result.json'):
    d=json.loads(file.read_text())
    groups[d['instance']][d['strategy']]=d
 report={}
 for instance,records in groups.items():
    assert set(records)=={'control','uncertainty','conflict','repair'},(instance,list(records))
    A=records['uncertainty'];B=records['conflict'];C=records['repair'];base=records['control']
    Sa={tuple(e) for e in A['selected_chords']}
    Sb={tuple(e) for e in B['selected_chords']}
    Sc={tuple(e) for e in C['selected_chords']}
    def summary(d):
      s=set(map(tuple,d['selected_chords']))
      t=set(edges(d['tour'])) if 'tour' in d else set()
      return {'score':d.get('score'),'status':d['status'],
        'new_chords':len(s),'selected_chords_used_in_solution':len(s&t),
        'seconds':d['seconds'],'gain_vs_reference':d.get('gain')}
    report[instance]={
      'scores':{name:summary(d) for name,d in records.items()},
      'uncertainty_vs_conflict_candidate_edge_overlap':len(Sa&Sb),
      'uncertainty_vs_conflict_identical_chord_sets':Sa==Sb,
      'uncertainty_vs_repair_edge_overlap':len(Sa&Sc),
      'conflict_vs_repair_edge_overlap':len(Sb&Sc),
      'incremental_gain_vs_parent_only':{name:base['score']-d.get('score',base['score'])
               for name,d in records.items() if name!='control'},
      'matched_pair_budget':len(Sa)}
 out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
