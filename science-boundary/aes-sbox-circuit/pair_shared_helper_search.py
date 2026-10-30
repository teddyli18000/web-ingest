#!/usr/bin/env python3
"""Search coupled two-root AND operand rewrites using one shared linear helper.

Motivation: every earlier p008 care search mutates one nonlinear root at a time.
A new XOR/XNOR helper can be locally neutral or even +1 around either root, yet
become globally useful when the same helper replaces operands at two different
AND roots and lets old linear support disappear after pruning.

For each AND operand site, enumerate every one-gate affine helper h = a XOR/XNOR b
from wires available before that root. Keep helpers satisfying exact full-circuit
observability care at the root. Then pair distinct roots that admit the same
syntactic helper, materialize the helper once before the earlier root, rewrite
both operands, prune dead logic, and independently verify all 256 AES inputs.

This is an exact enumeration for this represented move family. It does not imply
a lower bound outside two-root/shared-one-helper rewrites.
"""
from __future__ import annotations
import argparse, collections, hashlib, itertools, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1
OPS=('XOR','XNOR')


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
    for a,b in zip(base_out,alt):care|=a^b
    return care


def load_seed(args):
    if args.seed_file:
        c=ras.prune(json.load(open(args.seed_file)))
        label=args.seed_label or pathlib.Path(args.seed_file).stem
    else:
        c=ras.load_circuit(args.seed_family);label=args.seed_family
    assert ras.independent_check(c)[0]
    return c,label


def enumerate_matches(c):
    vals,base_out=eval_all(c)
    matches=collections.defaultdict(list)
    site_counts=collections.Counter()
    for idx,g in enumerate(c['gates']):
        if g['op']!='AND':continue
        care=care_mask(c,idx,base_out)
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in c['gates'][:idx]]
        for side in ('a','b'):
            old=g[side];other=g['b' if side=='a' else 'a']
            target=(vals[old]&vals[other])&care
            for ia,a in enumerate(earlier):
                va=vals[a]
                for b in earlier[ia:]:
                    vb=vals[b]
                    for op in OPS:
                        tv=census.op_eval(op,va,vb)
                        if (tv&vals[other]&care)!=target:continue
                        # Do not collapse locally equivalent helpers: two helpers
                        # can agree on this site's care set but differ on another
                        # root's care set, which is exactly the coupled effect we
                        # are trying to enumerate completely.
                        ek=(op,a,b)
                        matches[ek].append({'idx':idx,'out':g['out'],'side':side,
                                            'old':old,'other':other,
                                            'care_bits':care.bit_count()})
                        site_counts[(idx,side)]+=1
    return matches,site_counts


def materialize(base,expr,s1,s2):
    op,a,b=expr
    nc={'gates':[dict(g) for g in base['gates']],'outputs':list(base['outputs'])}
    roots={g['out']:g for g in nc['gates']}
    early=min(s1['idx'],s2['idx'])
    name='__pair_shared_helper__'
    nc['gates'].insert(early,{'op':op,'a':a,'b':b,'out':name})
    roots[s1['out']][s1['side']]=name
    roots[s2['out']][s2['side']]=name
    return ras.prune(nc)


def main():
    ap=argparse.ArgumentParser()
    src=ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--seed-family',choices=sorted(ras.SOURCES))
    src.add_argument('--seed-file')
    ap.add_argument('--seed-label')
    ap.add_argument('--out',required=True)
    ap.add_argument('--max-kept',type=int,default=300)
    args=ap.parse_args()
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    base,label=load_seed(args);base_n=len(base['gates'])
    matches,site_counts=enumerate_matches(base)
    kept=[];seen={sig(base)};pairs_tested=0;verified=0
    for expr,sites in matches.items():
        if len(sites)<2:continue
        for s1,s2 in itertools.combinations(sites,2):
            if s1['out']==s2['out']:continue
            pairs_tested+=1
            nc=materialize(base,expr,s1,s2)
            h=sig(nc)
            if h in seen:continue
            seen.add(h)
            ok=ras.independent_check(nc)
            if not ok[0]:
                raise AssertionError(('invalid coupled rewrite',expr,s1,s2,ok))
            verified+=1
            if len(nc['gates'])>base_n:continue
            rec={'gates':len(nc['gates']),'hash':h,'expr':{'op':expr[0],'a':expr[1],'b':expr[2]},
                 'site1':s1,'site2':s2}
            kept.append((len(nc['gates']),h,rec,nc))
    kept.sort(key=lambda z:(z[0],z[1]))
    archive=[]
    for rank,(n,h,rec,nc) in enumerate(kept[:args.max_kept]):
        fn=f'candidate-{rank:03d}-g{n}-{h[:12]}.json'
        (outdir/fn).write_text(json.dumps(nc,indent=2)+'\n')
        archive.append({**rec,'file':fn})
    best=kept[0][3] if kept else base
    (outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={'seed_label':label,'base_gates':base_n,'best_gates':len(best['gates']),
             'helper_expressions_with_matches':len(matches),
             'operand_sites_with_matches':len(site_counts),
             'pair_candidates_tested':pairs_tested,'verified_distinct':verified,
             'kept_nonworsening':len(kept),
             'kept_by_size':dict(sorted(collections.Counter(n for n,_,_,_ in kept).items())),
             'archive':archive,'verified_best':ras.independent_check(best)[0]}
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='archive'}),flush=True)

if __name__=='__main__':main()
