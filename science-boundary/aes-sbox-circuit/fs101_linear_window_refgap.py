#!/usr/bin/env python3
"""Exact one-gate shaving of linear-only windows in the 101-gate Few Shots AES circuit.

The current record has 33 AND + 68 XOR/XNOR gates.  Any verified one-gate shave
inside a linear-only window therefore gives a 100-gate circuit immediately.

For every contiguous window lying entirely inside one maximal linear run between
AND gates, preserve the exact live-in/live-out Boolean interface and ask the
pinned 2026 refutation-gap shortest-SLP CaDiCaL encoding whether the same local
linear map is realizable with one fewer gate.  Replacement helpers are completely
new.  SAT witnesses are spliced back into the full circuit, pruned, and checked on
all 256 AES inputs.  UNSAT is only a lower bound for that fixed local interface;
timeouts are inconclusive.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import released_and_skeleton as ras


def linear_runs(c):
    runs=[]
    i=0
    gs=c['gates']
    while i < len(gs):
        while i < len(gs) and gs[i]['op']=='AND':
            i+=1
        if i>=len(gs): break
        j=i
        while j < len(gs) and gs[j]['op']!='AND':
            j+=1
        runs.append((i,j))
        i=j
    return runs


def window_problem(c,i,j):
    gs=c['gates']; win=gs[i:j]
    assert win and all(g['op']!='AND' for g in win)
    produced={g['out'] for g in win}
    liveins=[]; seen=set()
    for g in win:
        for w in (g['a'],g['b']):
            if w not in produced and w not in seen:
                seen.add(w); liveins.append(w)

    used_after={w for g in gs[j:] for w in (g['a'],g['b'])}
    out_set=set(c['outputs'])
    liveouts=[]
    for g in win:
        w=g['out']
        if (w in used_after or w in out_set) and w not in liveouts:
            liveouts.append(w)
    if not liveouts:
        return None

    # Exact local affine forms over opaque live-in signals.
    lm=len(liveins)
    loc={w:1<<k for k,w in enumerate(liveins)}
    const={w:0 for w in liveins}
    for g in win:
        loc[g['out']]=loc[g['a']] ^ loc[g['b']]
        const[g['out']]=const[g['a']] ^ const[g['b']] ^ (1 if g['op']=='XNOR' else 0)
    targets=[loc[w] for w in liveouts]
    target_consts=[const[w] for w in liveouts]
    if len(set(targets)) != len(targets):
        return None
    # refutation-gap treats an input basis vector target as free.  Its complement
    # is not free in our two-input XOR/XNOR model, so skip such windows.
    for q,cbit in zip(targets,target_consts):
        if q and q&(q-1)==0 and cbit:
            return None
    return {'i':i,'j':j,'old_gates':j-i,'liveins':liveins,'liveouts':liveouts,
            'n_inputs':lm,'targets':targets,'target_consts':target_consts}


def splice(c,wp,program):
    i,j=wp['i'],wp['j']; liveins=wp['liveins']; liveouts=wp['liveouts']
    sig=[1<<k for k in range(len(liveins))]
    names=list(liveins); const=[0]*len(liveins)
    wanted={q:c for q,c in zip(wp['targets'],wp['target_consts'])}
    repl=[]
    for gi,(a,b) in enumerate(program):
        v=sig[a]^sig[b]
        desired=wanted.get(v,0)
        neg=desired ^ const[a] ^ const[b]
        out=f'__fsw_{i}_{j}_{gi}'
        repl.append({'op':'XNOR' if neg else 'XOR','a':names[a],'b':names[b],'out':out})
        sig.append(v); names.append(out); const.append(desired)
    by={}
    for k,v in enumerate(sig):
        by.setdefault((v,const[k]),names[k])
    mp={}
    for w,q,cbit in zip(liveouts,wp['targets'],wp['target_consts']):
        n=by.get((q,cbit))
        if n is None: return None
        mp[w]=n

    gates=[dict(g) for g in c['gates'][:i]] + repl
    for g in c['gates'][j:]:
        ng=dict(g)
        ng['a']=mp.get(ng['a'],ng['a']); ng['b']=mp.get(ng['b'],ng['b'])
        mp[ng['out']]=ng['out']
        gates.append(ng)
    outs=[mp.get(w,w) for w in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    if not ras.independent_check(full)[0]: return None
    return full


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--refgap',required=True)
    ap.add_argument('--min-len',type=int,default=3)
    ap.add_argument('--max-len',type=int,default=12)
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--conf-budget',type=int,default=300000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(pathlib.Path(args.refgap).resolve()))
    from slp.instance import SLPInstance,verify
    from slp.optimal import exists_program

    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    assert sum(g['op']=='AND' for g in c['gates'])==33
    runs=linear_runs(c)
    windows=[]; serial=0
    for lo,hi in runs:
        for L in range(args.min_len,min(args.max_len,hi-lo)+1):
            for i in range(lo,hi-L+1):
                wp=window_problem(c,i,i+L)
                if wp is None: continue
                if serial % args.shards == args.shard: windows.append(wp)
                serial+=1

    rows=[]; best=None; t0=time.time()
    for wp in windows:
        k=wp['old_gates']-1
        inst=SLPInstance(name=f'fs101-window-{wp["i"]}-{wp["j"]}',n_inputs=wp['n_inputs'],targets=tuple(wp['targets']))
        r=exists_program(inst,k,conf_budget=args.conf_budget)
        rec={'i':wp['i'],'j':wp['j'],'old':wp['old_gates'],'target_k':k,'liveins':wp['n_inputs'],
             'liveouts':len(wp['liveouts']),'sat':r.sat,'timed_out':r.timed_out,'seconds':round(r.seconds,3),
             'vars':r.n_vars,'clauses':r.n_clauses}
        if r.sat:
            verify(inst,r.program)
            full=splice(c,wp,r.program)
            rec['splice_ok']=full is not None
            if full is not None:
                rec['full_gates']=len(full['gates'])
                p=out/f'candidate-{wp["i"]}-{wp["j"]}.json'; p.write_text(json.dumps(full,indent=2)+'\n')
                if best is None or len(full['gates'])<best[0]: best=(len(full['gates']),p.name,rec)
                if len(full['gates'])<=100:
                    rows.append(rec); print(json.dumps(rec,sort_keys=True),flush=True); break
        rows.append(rec); print(json.dumps(rec,sort_keys=True),flush=True)
    summary={'shard':args.shard,'shards':args.shards,'runs':runs,'windows_considered':len(windows),'rows':rows,
             'best':best,'elapsed_s':round(time.time()-t0,3),
             'interpretation':'SAT witnesses replayed/all-256 checked; UNSAT only fixed-window/interface; timeout inconclusive'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__': main()
