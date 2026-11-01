#!/usr/bin/env python3
"""Exact individual-cone compression for the five independent FS101 suffix outputs.

After g90 the merged 101-gate record has five output cones:
  y3: g91,g92      (2 gates)
  y4: g93,g94      (2)
  y5: g95          (1)
  y6: g96,g97,g98  (3)
  y7: g99,g100     (2)
No gate in one cone feeds another cone.  Therefore any cone that can realize its
same AES output with one fewer arbitrary legal {AND,XOR,XNOR} gate immediately
yields a complete 100-gate circuit while all other cones remain unchanged.

For 2->1 and 1->0 cones the decision is direct.  For y6 3->2, enumerate every
distinct first-gate truth function obtainable from the 99 g90-prefix wires, then
test whether the target is one legal second gate from prefix wires plus that new
wire.  One witness per first-gate truth is complete for a single-output two-gate
SLP.  Operands are always distinct, matching the Few Shots verifier.
"""
from __future__ import annotations

import json
import pathlib
import time

import released_and_skeleton as ras
import search_arch_seed as sas

MASK=(1<<256)-1
OPS=('AND','XOR','XNOR')
CONES={
    3:['g91','g92'],
    4:['g93','g94'],
    5:['g95'],
    6:['g96','g97','g98'],
    7:['g99','g100'],
}


def op_eval(op,a,b):
    if op=='AND': return a & b
    if op=='XOR': return a ^ b
    return (a ^ b) ^ MASK


def one_gate_map(names,vals):
    out={}
    for i,a in enumerate(names):
        va=vals[a]
        for b in names[i+1:]:
            vb=vals[b]
            for op in OPS:
                out.setdefault(op_eval(op,va,vb),(op,a,b))
    return out


def synth_le2(target,names,vals,base_map):
    # 0-gate alias.
    for n in names:
        if vals[n]==target:return [],n,{'kind':'alias'}
    # 1-gate realization.
    if target in base_map:
        op,a,b=base_map[target]
        return [{'op':op,'a':a,'b':b,'out':'__c0'}],'__c0',{'kind':'one_gate'}
    # 2-gate realization: first truth h, then target from base+h.
    tested=0
    for h,(op1,a1,b1) in base_map.items():
        tested+=1
        hn='__c0'
        # second gate using h + one prefix wire. Two-prefix case was already
        # covered by the one-gate map above.
        for b in names:
            vb=vals[b]
            for op2 in OPS:
                if op_eval(op2,h,vb)==target:
                    return [
                        {'op':op1,'a':a1,'b':b1,'out':hn},
                        {'op':op2,'a':hn,'b':b,'out':'__c1'},
                    ],'__c1',{'kind':'two_gate','tested_first_truths':tested}
    return None,None,{'kind':'miss','tested_first_truths':tested}


def splice(c,cone,seq,outname):
    remove=set(cone); gates=[]; inserted=False
    first=cone[0]
    old_output=cone[-1]
    for g in c['gates']:
        if g['out']==first and not inserted:
            for q in seq:gates.append(dict(q))
            inserted=True
        if g['out'] in remove:continue
        gates.append(dict(g))
    outs=[outname if w==old_output else w for w in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    ok=ras.independent_check(full)
    if not ok[0]:raise AssertionError(('cone replacement failed AES',cone,seq,ok))
    return full


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101');assert len(c['gates'])==101 and ras.independent_check(c)[0]
    vals,outs=sas.eval_circuit(c)
    cut=next(i for i,g in enumerate(c['gates']) if g['out']=='g90')+1
    names=[f'x{i}' for i in range(8)]+[g['out'] for g in c['gates'][:cut]]
    base_map=one_gate_map(names,vals);rows=[];t0=time.time();best=None
    for oi,cone in CONES.items():
        old=len(cone);target=outs[oi];allowed=old-1
        if allowed==0:
            hit=next((n for n in names if vals[n]==target),None)
            seq=[] if hit else None;outname=hit;meta={'kind':'alias' if hit else 'miss'}
        elif allowed==1:
            hit=next((n for n in names if vals[n]==target),None)
            if hit:seq=[];outname=hit;meta={'kind':'alias'}
            elif target in base_map:
                op,a,b=base_map[target];seq=[{'op':op,'a':a,'b':b,'out':'__c0'}];outname='__c0';meta={'kind':'one_gate'}
            else:seq=None;outname=None;meta={'kind':'miss'}
        else:
            seq,outname,meta=synth_le2(target,names,vals,base_map)
            if seq is not None and len(seq)>allowed:seq=None;outname=None
        row={'output_index':oi,'old_gates':old,'target_max_gates':allowed,'result':meta,'found':seq is not None}
        if seq is not None:
            full=splice(c,cone,seq,outname);row['candidate_gates']=len(full['gates']);row['sequence']=seq;row['verified_all_256']=True
            if best is None or len(full['gates'])<best[0]:best=(len(full['gates']),oi,full,row)
            if len(full['gates'])<=100:
                (outdir/f'candidate-y{oi}.json').write_text(json.dumps(full,indent=2)+'\n')
        rows.append(row);print(json.dumps(row,sort_keys=True),flush=True)
    summary={'status':'found' if best and best[0]<=100 else 'exhausted','prefix_gates':cut,'prefix_sources':len(names),
             'distinct_one_gate_truths':len(base_map),'rows':rows,'best':None if best is None else {'gates':best[0],'output_index':best[1]},
             'elapsed_s':round(time.time()-t0,3),'family_scope':'compress one independent FS101 g90-suffix output cone by one arbitrary legal gate while leaving other cones unchanged'}
    if best and best[0]<=100:(outdir/'candidate.json').write_text(json.dumps(best[2],indent=2)+'\n')
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__':main()
