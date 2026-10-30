#!/usr/bin/env python3
"""Post-audit coverage checker for the complete 219-edge exclusion.

Verifies that all 23 structural degree-sequence candidates are covered by durable
certificates.  The two formerly row-CSP-dependent sequences are required to use
the sound post-audit replacement certificate.
"""
from pathlib import Path
import argparse,json
HERE=Path(__file__).resolve().parent; R=HERE/'results'
def load(name): return json.loads((R/name).read_text())
def C(d): return tuple(sorted((int(k),int(v)) for k,v in d.items() if v))
def imp(d): return 'impossible' in d.get('conclusion','').lower() or d.get('all_unsat') is True

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path); a=ap.parse_args()
 audit=load('row-csp-tf-audit-2026-10-30.json')
 assert audit['status'].startswith('affected UNSAT conclusions withdrawn')
 st=load('m219-structure.json'); universe={C(x) for x in st['after_degree11_local']}; assert len(universe)==23
 evidence={}
 def add(seq,path,kind):
  q=C(seq); assert q in universe and q not in evidence,(seq,path)
  evidence[q]={'degree_sequence':{str(k):v for k,v in seq.items()},'evidence':path,'kind':kind}

 z0=[C(x) for x in st['n11_zero_survivors']]; assert z0==[C({12:30,13:6}),C({12:31,13:4,14:1})]
 for q in sorted(x for x in universe if dict(x).get(11,0)==0):
  if q not in z0: add(dict(q),'results/m219-structure.json','weighted high-set capacity')
 typed=load('m219-n11-0-typed-column-csp.json'); assert typed['all_unsat'] is True
 add({12:30,13:6},'results/m219-n11-0-typed-column-csp.json','typed column CSP')
 add({12:31,13:4,14:1},'results/m219-n11-0-typed-column-csp.json','typed column CSP')

 f5=load('m219-n11-5-fixedA.json'); assert f5['complete'] and f5['all_unsat']
 for s in ({11:5,12:20,13:11},{11:5,12:21,13:9,14:1},{11:5,12:22,13:7,14:2}):
  add(s,'results/m219-n11-5-fixedA.json','fixed-A exact cover')
 f6=load('m219-n11-6-fixedlow-csp.json'); assert f6['complete'] and f6['unsat']==f6['branches'] and f6['timeout']==0
 for s in ({11:6,12:18,13:12},{11:6,12:19,13:10,14:1}):
  add(s,'results/m219-n11-6-fixedlow-csp.json','fixed-low column CSP')
 f62=load('m219-n11-6-seq2-fixedlow-csp.json'); assert f62['complete'] and f62['unsat']==f62['fixed_low_branches'] and f62['timeout']==0
 add({11:6,12:20,13:8,14:2},'results/m219-n11-6-seq2-fixedlow-csp.json','fixed-low column CSP')

 # Post-audit replacement for the two sequences previously dependent on the unsound row-CSP.
 fin=load('m219-final-two-sound-post-audit.json')
 assert fin['campaign']=='m219-final-two-sound-post-audit' and fin['all_unsat']
 assert fin['seq0']['status']=='UNSAT' and fin['seq1']['status']=='UNSAT'
 add({11:7,12:16,13:13},'results/m219-final-two-sound-post-audit.json','post-audit structural/column closure')
 add({11:8,12:14,13:14},'results/m219-final-two-sound-post-audit.json','post-audit structural/column closure')

 q=load('m219-n11-7-seq1-common-neighbor.json'); assert q['survivors_after_exact_low_incidence_DP_and_common_neighbor_capacity']==0
 add({11:7,12:17,13:11,14:1},'results/m219-n11-7-seq1-common-neighbor.json','low-graph exhaustive obstruction')
 q=load('m219-n11-7-lowgraph-obstruction.json'); assert imp(q)
 add({11:7,12:18,13:9,14:2},'results/m219-n11-7-lowgraph-obstruction.json','low-graph obstruction')
 q=load('m219-n11-8-r3-lowgraph-obstruction.json'); assert imp(q) and q['low_complement_survivors']==0
 add({11:8,12:15,13:12,14:1},'results/m219-n11-8-r3-lowgraph-obstruction.json','low-complement exhaustive obstruction')
 q=load('m219-n11-9-r3-lowgraph-obstruction.json'); assert imp(q)
 add({11:9,12:12,13:15},'results/m219-n11-9-r3-lowgraph-obstruction.json','r3 low-graph obstruction')
 q=load('m219-seq6-lowgraph-obstruction.json'); assert imp(q)
 add({11:9,12:13,13:13,14:1},'results/m219-seq6-lowgraph-obstruction.json','r3 low-graph obstruction')
 for s,p in [({11:10,12:10,13:16},'m219-n11-10-r3-lowgraph-obstruction.json'),
             ({11:11,12:8,13:17},'m219-n11-11-r3-obstruction.json'),
             ({11:12,12:6,13:18},'m219-n11-12-r3-obstruction.json')]:
  q=load(p); assert imp(q); add(s,'results/'+p,'r3 obstruction')

 assert set(evidence)==universe,(len(evidence),len(universe),sorted(universe-set(evidence)),sorted(set(evidence)-universe))
 assert all('m219-final-two-sequences.json' not in x['evidence'] for x in evidence.values())
 out={'campaign':'m219-complete-exclusion-post-audit','edges':219,
      'structural_candidate_count':len(universe),'covered_candidate_count':len(evidence),
      'complete':True,'all_unsat':True,'minimum_edges_for_any_R46_36_witness':220,
      'audit':'row-csp-tf-audit-2026-10-30.json',
      'coverage':[evidence[q] for q in sorted(evidence)]}
 text=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(text,end='')
 if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text)
if __name__=='__main__': main()
