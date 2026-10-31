#!/usr/bin/env python3
"""Exact SAT shaving of non-contiguous output cones in the G103 22-gate suffix.

Contiguous windows can miss rewrites that cross interleaved output cones.  This
superoptimizer instead chooses a subset of final AES outputs, takes the complete
transitive fan-in cone of those outputs *within the pure-linear suffix*, and asks
whether all externally visible values produced by that cone can be computed with
one fewer XOR gate from the 17 last-AND boundary signals.

Because the cone is ancestor-closed, all of its live-ins are suffix-boundary
signals.  Its live-outs are selected/final outputs plus any cone value consumed
by a suffix gate outside the cone.  A replacement can therefore be synthesized
as one block immediately after the nonlinear prefix, then the untouched
non-cone suffix is replayed with live-out rewiring.

The local linear map is solved with the pinned 2026 `refutation-gap` CaDiCaL
shortest-SLP encoder.  SAT is replayed and the full AES circuit is independently
checked on all 256 inputs.  Timeout is inconclusive; UNSAT is exact only for the
chosen cone/interface and is not promoted to a global lower bound here.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys
import time

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf


def suffix_affine(suffix,boundary):
    m=len(boundary); C=1<<m
    vals={w:1<<i for i,w in enumerate(boundary)}
    const={w:0 for w in boundary}
    for g in suffix:
        vals[g['out']]=vals[g['a']]^vals[g['b']]
        const[g['out']]=const[g['a']]^const[g['b']]^(1 if g['op']=='XNOR' else 0)
    return m,C,vals,const


def cone_problem(suffix,boundary,final_outputs,selected,vals,const):
    by={g['out']:i for i,g in enumerate(suffix)}
    need=set(selected); stack=list(selected); cone_idx=set()
    while stack:
        w=stack.pop(); gi=by.get(w)
        if gi is None or gi in cone_idx: continue
        cone_idx.add(gi); g=suffix[gi]
        stack.extend([g['a'],g['b']])
    if not cone_idx: return None
    cone=[suffix[i] for i in sorted(cone_idx)]
    produced={g['out'] for g in cone}
    liveins=[]; seen=set()
    for g in cone:
        for w in (g['a'],g['b']):
            if w not in produced and w not in seen:
                seen.add(w); liveins.append(w)
    # Ancestor-closed final-output cone should enter only through the suffix cut.
    if any(w not in boundary for w in liveins):
        raise AssertionError(('non-boundary cone live-in',selected,liveins))
    outside=[g for i,g in enumerate(suffix) if i not in cone_idx]
    outside_uses={w for g in outside for w in (g['a'],g['b'])}
    liveouts=[]
    for g in cone:
        w=g['out']
        if (w in outside_uses or w in final_outputs) and w not in liveouts:
            liveouts.append(w)
    if not liveouts: return None

    # Express cone live-outs relative to just the boundary values it actually uses.
    lm=len(liveins); loc={w:1<<i for i,w in enumerate(liveins)}; lc={w:const[w] for w in liveins}
    for g in cone:
        loc[g['out']]=loc[g['a']]^loc[g['b']]
        lc[g['out']]=lc[g['a']]^lc[g['b']]^(1 if g['op']=='XNOR' else 0)
    targets=[loc[w] for w in liveouts]; tconst=[lc[w] for w in liveouts]
    if len(set(targets))!=len(targets): return None
    # Avoid complemented-free-input false positives in the linear-only solver.
    for q,cbit in zip(targets,tconst):
        if q and q&(q-1)==0:
            k=q.bit_length()-1
            if cbit!=lc[liveins[k]]: return None
    return {'selected':list(selected),'cone_idx':sorted(cone_idx),'old_gates':len(cone),
            'liveins':liveins,'liveouts':liveouts,'n_inputs':lm,'targets':targets,
            'target_consts':tconst,'input_consts':[lc[w] for w in liveins]}


def splice(c,prefix,suffix,wp,program):
    sig=[1<<i for i in range(wp['n_inputs'])]; names=list(wp['liveins']); const=list(wp['input_consts'])
    want={q:c for q,c in zip(wp['targets'],wp['target_consts'])}; repl=[]
    for gi,(a,b) in enumerate(program):
        v=sig[a]^sig[b]; desired=want.get(v,0); neg=desired^const[a]^const[b]
        out=f'__cref_{gi}'
        repl.append({'op':'XNOR' if neg else 'XOR','a':names[a],'b':names[b],'out':out})
        sig.append(v); names.append(out); const.append(desired)
    by={}
    for si,v in enumerate(sig): by.setdefault((v,const[si]),names[si])
    mp={}
    for w,q,cbit in zip(wp['liveouts'],wp['targets'],wp['target_consts']):
        n=by.get((q,cbit))
        if n is None: return None
        mp[w]=n
    cone=set(wp['cone_idx']); gates=[dict(g) for g in prefix]+repl
    for i,g in enumerate(suffix):
        if i in cone: continue
        ng=dict(g); ng['a']=mp.get(ng['a'],ng['a']); ng['b']=mp.get(ng['b'],ng['b'])
        gates.append(ng)
    outs=[mp.get(o,o) for o in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    return full if ras.independent_check(full)[0] else None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--refgap',required=True)
    ap.add_argument('--min-outputs',type=int,default=2)
    ap.add_argument('--max-outputs',type=int,default=5)
    ap.add_argument('--max-cone',type=int,default=18)
    ap.add_argument('--shard',type=int,default=0); ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--conf-budget',type=int,default=500000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    root=str(pathlib.Path(args.refgap).resolve()); sys.path.insert(0,root)
    from slp.instance import SLPInstance,verify
    from slp.optimal import exists_program

    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    _last,prefix,suffix,boundary=suf.split(c); m,C,vals,const=suffix_affine(suffix,boundary)
    final=list(c['outputs']); probs=[]; serial=0; seen_shapes=set()
    for r in range(args.min_outputs,args.max_outputs+1):
        for selected in itertools.combinations(final,r):
            wp=cone_problem(suffix,boundary,set(final),selected,vals,const)
            if wp is None or wp['old_gates']<3 or wp['old_gates']>args.max_cone: continue
            shape=(tuple(wp['cone_idx']),tuple(wp['liveouts']))
            if shape in seen_shapes: continue
            seen_shapes.add(shape)
            if serial%args.shards==args.shard: probs.append(wp)
            serial+=1

    rows=[]; best=None; t0=time.time()
    for wp in probs:
        k=wp['old_gates']-1
        inst=SLPInstance(name='g103-cone-'+'-'.join(wp['selected']),n_inputs=wp['n_inputs'],targets=tuple(wp['targets']))
        r=exists_program(inst,k,conf_budget=args.conf_budget)
        rec={'selected':wp['selected'],'old':wp['old_gates'],'target_k':k,
             'liveins':wp['n_inputs'],'liveouts':len(wp['liveouts']),
             'sat':r.sat,'timed_out':r.timed_out,'seconds':round(r.seconds,3),
             'vars':r.n_vars,'clauses':r.n_clauses}
        if r.sat:
            verify(inst,r.program); full=splice(c,prefix,suffix,wp,r.program); rec['splice_ok']=full is not None
            if full is not None:
                rec['full_gates']=len(full['gates']); p=out/('candidate-'+str(len(rows))+'.json'); p.write_text(json.dumps(full,indent=2)+'\n')
                if best is None or len(full['gates'])<best[0]: best=(len(full['gates']),p.name,rec)
        rows.append(rec); print(json.dumps(rec,sort_keys=True),flush=True)
        if best is not None and best[0]<=102: break
    summary={'shard':args.shard,'shards':args.shards,'problems':len(probs),'best':best,'rows':rows,
             'elapsed_s':round(time.time()-t0,3),'interpretation':'non-contiguous ancestor-closed output cones; SAT replayed and all-256 checked'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__': main()
