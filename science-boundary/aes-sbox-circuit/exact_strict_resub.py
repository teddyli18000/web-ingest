#!/usr/bin/env python3
"""Exact strict-resubstitution search from a complete AES circuit.

For every reachable gate root, compute its exact full-circuit observability mask.
Then exhaust:
  * aliasing the root to any earlier wire; and
  * replacing the root by every two-input XOR/XNOR/AND over earlier wires.
Only strict gate-count reductions after reachability pruning are retained.
Every retained circuit is independently checked on all 256 AES inputs.

With --depth 2 this is a deterministic test of the mechanism
    architecture mutation -> strict shave -> strict shave,
which is deliberately different from a neutral random ODC walk.
With --archive-improvements every distinct reduced circuit is persisted, which
is useful for building a semantic census of the 101-gate frontier.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib
import seed_family_census as census
import released_and_skeleton as ras

MASK=(1<<256)-1
OPS=('XOR','XNOR','AND')


def sig(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def eval_all(c,flip_idx=None):
    vals=census.input_tables(False)
    for i,g in enumerate(c['gates']):
        v=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
        if i==flip_idx:v^=MASK
        vals[g['out']]=v
    return vals,[vals[o] for o in c['outputs']]


def care_mask(c,idx,base_out):
    _,alt=eval_all(c,idx)
    care=0
    for x,y in zip(base_out,alt):care|=x^y
    return care


def alias_gate(c,idx,wire):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    old=nc['gates'][idx]['out']
    for j in range(idx+1,len(nc['gates'])):
        for k in ('a','b'):
            if nc['gates'][j][k]==old:nc['gates'][j][k]=wire
    nc['outputs']=[wire if o==old else o for o in nc['outputs']]
    del nc['gates'][idx]
    return ras.prune(nc)


def replace_gate(c,idx,op,a,b):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    nc['gates'][idx]['op']=op;nc['gates'][idx]['a']=a;nc['gates'][idx]['b']=b
    return ras.prune(nc)


def strict_children(c,max_children=100000):
    vals,outs=eval_all(c);n=len(c['gates'])
    seen=set();children=[]
    stats=collections.Counter()
    for idx,g in enumerate(c['gates']):
        care=care_mask(c,idx,outs);rv=vals[g['out']]&care
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in c['gates'][:idx]]
        for w in earlier:
            stats['alias_tests']+=1
            if (vals[w]&care)!=rv:continue
            nc=alias_gate(c,idx,w)
            if len(nc['gates'])>=n:continue
            h=sig(nc)
            if h in seen:continue
            assert ras.independent_check(nc)[0],('bad alias',idx,w)
            seen.add(h);children.append((nc,{'kind':'alias','root_index':idx,'care_bits':care.bit_count(),'wire':w}))
            stats['strict_aliases']+=1
            if len(children)>=max_children:return children,stats
        for ia,a in enumerate(earlier):
            va=vals[a]
            for b in earlier[ia:]:
                vb=vals[b]
                for op in OPS:
                    stats['gate_tests']+=1
                    if op==g['op'] and {a,b}=={g['a'],g['b']}:continue
                    if (census.op_eval(op,va,vb)&care)!=rv:continue
                    nc=replace_gate(c,idx,op,a,b)
                    if len(nc['gates'])>=n:continue
                    h=sig(nc)
                    if h in seen:continue
                    assert ras.independent_check(nc)[0],('bad replacement',idx,op,a,b)
                    seen.add(h);children.append((nc,{'kind':'gate','root_index':idx,'care_bits':care.bit_count(),'op':op,'a':a,'b':b}))
                    stats['strict_gate_replacements']+=1
                    if len(children)>=max_children:return children,stats
    return children,stats


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--depth',type=int,default=2)
    ap.add_argument('--target',type=int,default=100)
    ap.add_argument('--max-children',type=int,default=100000)
    ap.add_argument('--archive-improvements',action='store_true')
    args=ap.parse_args()
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    archive_dir=outdir/'improvements'
    if args.archive_improvements:archive_dir.mkdir(exist_ok=True)
    start=ras.prune(json.load(open(args.input)))
    assert ras.independent_check(start)[0]
    queue=[(start,0,[])];seen={sig(start)};best=start;improvements=[]
    aggregate=collections.Counter();states_by_depth=collections.Counter({0:1})
    while queue:
        cur,d,path=queue.pop(0)
        if d>=args.depth or len(cur['gates'])<=args.target:continue
        kids,stats=strict_children(cur,args.max_children)
        aggregate.update(stats)
        for nc,move in kids:
            h=sig(nc)
            if h in seen:continue
            seen.add(h);np=path+[move]
            rec={'depth':d+1,'gates':len(nc['gates']),'hash':h,'path':np}
            improvements.append(rec);states_by_depth[d+1]+=1
            if args.archive_improvements:
                fn=f'd{d+1}-g{len(nc["gates"])}-{h[:16]}.json'
                (archive_dir/fn).write_text(json.dumps(nc,indent=2)+'\n')
                rec['file']=str(pathlib.Path('improvements')/fn)
            if len(nc['gates'])<len(best['gates']):
                best=nc
                (outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
                (outdir/'best-path.json').write_text(json.dumps(rec,indent=2)+'\n')
                print(json.dumps({'event':'best',**rec}),flush=True)
            if len(nc['gates'])>args.target and d+1<args.depth:queue.append((nc,d+1,np))
    if not (outdir/'best.json').exists():(outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={'input':args.input,'start_gates':len(start['gates']),'best_gates':len(best['gates']),
             'depth':args.depth,'target':args.target,'states_seen':len(seen),
             'states_by_depth':dict(sorted(states_by_depth.items())),
             'improvements_by_size':dict(sorted(collections.Counter(x['gates'] for x in improvements).items())),
             'improvements':improvements if args.archive_improvements else [],
             'tests':dict(aggregate),'verified_best':ras.independent_check(best)[0],
             'best_hash':sig(best),'best_path':next((x['path'] for x in improvements if x['hash']==sig(best)),[])}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
