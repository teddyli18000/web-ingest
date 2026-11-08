#!/usr/bin/env python3
"""Generate verified full AES circuits with TWO coordinated AND-basis shears.

For earlier P=a&b and later Q=a&c, replace Q by:
  h = b XOR c,  Q'=a&h,  Q=P XOR Q'.
The old Q is reconstructed only if its other users need it. Pruning, exact
function CSE and complement absorption through XOR/XNOR can share/delete wires.
Apply the move twice, not fixing the original AND truth-function set.

Constructive outputs are checked on all 256 AES bytes and stored as usable
parents for future global multi-parent + helper co-synthesis.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,pathlib
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1
def trace(c):
    vals=census.input_tables(False)
    for g in c['gates']:
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
    return vals

def exact_alias(c):
    vals=census.input_tables(False); rep={v:w for w,v in vals.items()}
    wire={w:w for w in vals}; gates=[]
    for g in c['gates']:
        a,b=wire[g['a']],wire[g['b']]
        v=census.op_eval(g['op'],vals[a],vals[b])
        if v in rep:wire[g['out']]=rep[v]
        else:
            out=g['out'];gates.append({'op':g['op'],'a':a,'b':b,'out':out})
            vals[out]=v;wire[out]=out;rep[v]=out
    return ras.prune({'gates':gates,'outputs':[wire[w] for w in c['outputs']]})

def phase_alias(c):
    c=exact_alias(c)
    while True:
        vals=trace(c);seen={v:w for w,v in census.input_tables(False).items()}
        uses=collections.defaultdict(list)
        for g in c['gates']:
            uses[g['a']].append(g);uses[g['b']].append(g)
        for w in c['outputs']:uses[w].append(None)
        change=None
        for g in c['gates']:
            w=g['out'];v=vals[w];p=seen.get(v^MASK)
            if p is not None and all(u is not None and u['op'] in ('XOR','XNOR') for u in uses[w]):
                change=(w,p);break
            seen[v]=w
        if change is None:return c
        w,p=change;new=[]
        for g in c['gates']:
            if g['out']==w:continue
            h=dict(g)
            if h['a']==w:
                h['a']=p;h['op']='XNOR' if h['op']=='XOR' else 'XOR'
            if h['b']==w:
                h['b']=p;h['op']='XNOR' if h['op']=='XOR' else 'XOR'
            new.append(h)
        c=exact_alias({'gates':new,'outputs':c['outputs']})

def shears(c):
    gs=c['gates'];ands=[(i,g) for i,g in enumerate(gs) if g['op']=='AND']
    for ai,(i,p) in enumerate(ands):
        for j,q in ands[ai+1:]:
            for shared in sorted({p['a'],p['b']} & {q['a'],q['b']}):
                b=p['b'] if p['a']==shared else p['a']
                d=q['b'] if q['a']==shared else q['a']
                name='__shear_'+str(len(gs))+'_'+str(i)+'_'+str(j)
                helper=name+'_h';atom=name+'_and'
                old=gs[:j];tail=gs[j+1:]
                # New atom and reconstruction share P; old Q remains a wire
                # name so every downstream reference stays causally legal.
                mutated={'gates':[dict(x) for x in old]+[
                    {'op':'XOR','a':b,'b':d,'out':helper},
                    {'op':'AND','a':shared,'b':helper,'out':atom},
                    {'op':'XOR','a':p['out'],'b':atom,'out':q['out']},
                ]+[dict(x) for x in tail], 'outputs':list(c['outputs'])}
                transformed=phase_alias(mutated)
                if not ras.independent_check(transformed)[0]:
                    raise AssertionError(('invalid nonlinear basis mutation',i,j,shared))
                yield (i,j,shared),transformed

def andset(c):
    v=trace(c)
    return frozenset(v[g['out']] for g in c['gates'] if g['op']=='AND')
def sig(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',required=True)
    ap.add_argument('--keep',type=int,default=120)
    ap.add_argument('--max-gates',type=int,default=104)
    args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    root=ras.load_circuit('fs-101');assert len(root['gates'])==101
    assert ras.independent_check(root)[0]
    old=andset(root)
    stats=collections.Counter();seen=set();kept=[];first=list(shears(root))
    for desc,c in first:
        stats['first_level']+=1
        for desc2,d in shears(c):
            stats['double_generated']+=1
            diff=len(andset(d)^old)
            stats['raw_gate_'+str(len(d['gates']))+'_ANDdiff_'+str(diff)]+=1
            if not diff:continue
            hash_=sig(d)
            if hash_ in seen:continue
            seen.add(hash_)
            stats['novel_distinct']+=1
            if len(d['gates'])<=args.max_gates:
                kept.append((len(d['gates']),-diff,hash_,desc,desc2,d))
    kept.sort(key=lambda z:(z[0],z[1],z[2]))
    archived=[]
    for index,(n,negative_diff,h,p,q,c) in enumerate(kept[:args.keep]):
        name=f'candidate-{index:03d}-g{n}-{h[:12]}.json'
        (out/name).write_text(json.dumps(c,indent=2)+'\n')
        archived.append({'file':name,'gates':n,'AND_truth_set_symmetric_difference':-negative_diff,
                         'first_shear':p,'second_shear':q})
    summary={'source_gates':101,'first_shears':len(first),'statistics':dict(stats),
             'best_novel_gates':kept[0][0] if kept else None,
             'archives':archived,'archive_count':len(archived),
             'all_candidates_checked_256':True,
             'scope':'two distinct or interacting bilinear AND-basis changes followed by exact polarity-aware CSE'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='archives'},sort_keys=True),flush=True)
if __name__=='__main__':main()
