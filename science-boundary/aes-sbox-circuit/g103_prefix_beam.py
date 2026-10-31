#!/usr/bin/env python3
"""Diverse beam search for a 48-linear G103 nonlinear prefix.

The one-track released-AND RNBP search gets very close at the 48-linear frontier:
for cut basis [1,3,4] one observed state released 30/32 ANDs with all nonlinear
atoms covered and only three units of positive support distance remaining.  A
single greedy trajectory is therefore too brittle to decide this frontier.

This search keeps several semantically distinct prefix states.  Each state is
represented by the set of available affine functions, exact support caches,
released AND atoms, distances to all 64 ordered AND operands plus the three cut
basis values, and a reconstructible gate list.  Expansion includes the strongest
one-step reducers *and* a small number of non-reducing guide values from the
original G103 linear network; the latter deliberately changes the old search
space instead of merely adding more random tie breaks.

Beam selection is completion-first but diversity preserving: one representative
per (released-AND count, ready-basis count, INF-target count) bucket is retained
before globally filling the beam.  States with the same semantic signal set are
future-equivalent and are deduplicated exactly.

This is a constructive heuristic, not a lower bound.  A successful prefix is
written with its transformed 17-wire cut interface for downstream exact suffix
synthesis.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import time
from dataclasses import dataclass

import released_and_skeleton as ras
import released_rnbp_support_synth as rr
import released_rnbp_support_fast as rf
import g103_boundary_prefix_rnbp as bp
import g103_cut_basis_census as cb
import g103_joint_cut_basis_search as joint

INF=rr.INF


@dataclass
class State:
    S:set
    sx:list
    names:dict
    gates:list
    released:set
    dist:list
    linear:int
    parent_kind:str='root'


def clone_state(s:State)->State:
    # sx[0..4] is the expensive object; copy only the sets that are mutated.
    return State(set(s.S),[set(x) for x in s.sx],dict(s.names),
                 [dict(g) for g in s.gates],set(s.released),list(s.dist),
                 s.linear,s.parent_kind)


def normalize(s,sk,targets,C,max_support):
    added=rr.release_ready(sk,s.S,s.sx,s.names,s.gates,s.released)
    if added:
        rr.initialize_covered_inf(s.dist,targets,s.S,s.sx,C,max_support)
    return added


def metrics(s,bvecs):
    basis_ready=sum(v in s.S for v in bvecs)
    inf=sum(d==INF for d in s.dist)
    positive=sum(d for d in s.dist if 0<d<INF)
    finite=sum(0<d<INF for d in s.dist)
    return {
        'released_ands':len(s.released),'basis_ready':basis_ready,
        'basis_missing':len(bvecs)-basis_ready,'inf_remaining':inf,
        'positive_sum':positive,'finite_remaining':finite,'linear':s.linear,
    }


def score(s,bvecs):
    m=metrics(s,bvecs)
    # Completion dominates, but support geometry decides among states at the same
    # nonlinear frontier.  Basis readiness is counted separately because the cut
    # cannot be exported without all three values.
    return (-(m['released_ands']+m['basis_ready']),
            -m['released_ands'],m['basis_missing'],m['inf_remaining'],
            m['positive_sum'],m['finite_remaining'])


def semantic_key(s):
    return frozenset(s.S)


def candidate_moves(s,targets,labels,bvecs,guide_values,C,
                    reducer_branch,guide_branch):
    WD=rr.pair_candidates(s.S,C)
    reducers,fallback=rf.reducer_map(s.dist,targets,WD,s.S,s.sx,C)
    moves=[];seen=set()

    ones=[i for i,d in enumerate(s.dist) if d==1]
    # Unlike the old greedy search, branch over distinct distance-1 targets.
    for i in ones:
        w=targets[i]
        if w not in WD or w in seen:continue
        inds=set(reducers.get(w,set()));inds.add(i)
        moves.append((w,sorted(inds),'distance1'));seen.add(w)

    ranked=[]
    for w,inds0 in reducers.items():
        if w in seen:continue
        inds=sorted(inds0);count=len(inds)
        penalty=sum(2*s.dist[i]-1 for i in inds)
        bcount=sum(labels[i].startswith('basis') for i in inds)
        guide=1 if w in guide_values else 0
        direct_basis=1 if w in bvecs else 0
        ranked.append((-count,penalty,-bcount,-direct_basis,-guide,w,inds))
    ranked.sort(key=lambda z:z[:-1])
    for row in ranked[:max(0,reducer_branch)]:
        w=row[-2]
        if w in seen:continue
        moves.append((w,row[-1],'reducer'));seen.add(w)

    # Deliberately admit some non-reducing original-network/basis moves.  This is
    # the escape hatch from strict monotone RNBP; beam selection decides whether
    # their delayed benefit is worth retaining.
    guides=[]
    for w in WD:
        if w in seen or w in reducers:continue
        if w not in guide_values and w not in bvecs:continue
        kind='basis_bridge' if w in bvecs else 'guide_bridge'
        # Prefer basis outputs, then values that share many atoms with currently
        # finite residual targets (a cheap deterministic second-order proxy).
        overlap=max((w & targets[i]).bit_count() for i,d in enumerate(s.dist)
                    if 0<d<INF) if any(0<d<INF for d in s.dist) else 0
        guides.append((0 if kind=='basis_bridge' else 1,-overlap,w,kind))
    guides.sort()
    for _,_,w,kind in guides[:max(0,guide_branch)]:
        moves.append((w,[],kind));seen.add(w)

    return WD,moves,len(reducers),len(fallback)


def apply_move(s,w,reductions,kind,WD,sk,targets,C,max_support):
    c=clone_state(s);op,a,b=WD[w]
    out=f'__beam_{c.linear}_{len(c.gates)}'
    c.gates.append({'op':op,'a':c.names[a],'b':c.names[b],'out':out})
    for i in reductions:
        if 0<c.dist[i]<INF:c.dist[i]-=1
    c.S.add(w);c.names[w]=out;rr.add_sx(c.sx,w);c.linear+=1
    rr.initialize_covered_inf(c.dist,targets,c.S,c.sx,C,max_support)
    normalize(c,sk,targets,C,max_support)
    c.parent_kind=kind
    return c


def choose_beam(children,bvecs,width,bridge_reserve):
    # Exact semantic deduplication.
    best_by_sem={}
    for c in children:
        k=semantic_key(c)
        old=best_by_sem.get(k)
        if old is None or score(c,bvecs)<score(old,bvecs):best_by_sem[k]=c
    pool=sorted(best_by_sem.values(),key=lambda c:score(c,bvecs))
    if len(pool)<=width:return pool

    chosen=[];used=set();bucket_seen=set()
    # First preserve feature-frontier diversity.
    for c in pool:
        m=metrics(c,bvecs);bucket=(m['released_ands'],m['basis_ready'],m['inf_remaining'])
        if bucket in bucket_seen:continue
        chosen.append(c);used.add(id(c));bucket_seen.add(bucket)
        if len(chosen)>=max(1,width//2):break

    # Reserve a few slots for non-monotone bridge children if they survived at a
    # scientifically competitive frontier.
    bridges=[c for c in pool if 'bridge' in c.parent_kind and id(c) not in used]
    for c in bridges[:max(0,bridge_reserve)]:
        if len(chosen)>=width:break
        chosen.append(c);used.add(id(c))

    for c in pool:
        if len(chosen)>=width:break
        if id(c) in used:continue
        chosen.append(c);used.add(id(c))
    chosen.sort(key=lambda c:score(c,bvecs))
    return chosen


def build_prefix_result(c,rows,s,bvecs,extras,boundary,vals):
    extra_pos={w:j for j,w in enumerate(extras)}
    input_names=[]
    for w in boundary:
        if w in extra_pos:
            v=bvecs[extra_pos[w]]
        else:v=vals[w]
        if v not in s.names:raise AssertionError(('missing boundary semantic',w,v))
        input_names.append(s.names[v])
    prefix={'gates':s.gates,'input_names':input_names,'basis_vectors':bvecs,
            'basis_rows':list(rows),'extras':extras,'boundary':boundary}
    return prefix


def search(c,rows,budget,max_support,beam_width,reducer_branch,guide_branch,bridge_reserve):
    sk,C,vals,linear_vecs=bp.wire_vectors(c)
    _last,_orig_prefix,_suffix,boundary=bp.split(c)
    extras,_=cb.semantic_cut_extras(c,boundary)
    bvecs=joint.basis_vectors(vals,extras,rows)
    targets=[];labels=[]
    for i,ab in enumerate(sk['ands']):
        targets += [ab['a'],ab['b']];labels += [f'a{i}',f'b{i}']
    for j,v in enumerate(bvecs):targets.append(v);labels.append(f'basis{j}')

    S={1<<i for i in range(8)};sx=rr.init_sx(S);names={1<<i:f'x{i}' for i in range(8)}
    root=State(S,sx,names,[],set(),[],0)
    normalize(root,sk,targets,C,max_support)
    root.dist=[rr.min_distance(root.S,root.sx,t,C,max_support) for t in targets]
    normalize(root,sk,targets,C,max_support)
    beam=[root];history=[];best=root

    for depth in range(budget):
        children=[];move_count=0;reducer_counts=[]
        for s in beam:
            WD,moves,nred,nfallback=candidate_moves(
                s,targets,labels,bvecs,linear_vecs,C,reducer_branch,guide_branch)
            reducer_counts.append(nred)
            for w,reds,kind in moves:
                child=apply_move(s,w,reds,kind,WD,sk,targets,C,max_support)
                children.append(child);move_count+=1
                if score(child,bvecs)<score(best,bvecs):best=child
                if len(child.released)==sk['n_and'] and all(v in child.S for v in bvecs):
                    meta={'status':'found','depth':child.linear,'metrics':metrics(child,bvecs),
                          'beam_width':beam_width,'reducer_branch':reducer_branch,
                          'guide_branch':guide_branch,'history':history}
                    return child,bvecs,extras,boundary,vals,meta
        if not children:
            break
        beam=choose_beam(children,bvecs,beam_width,bridge_reserve)
        front=metrics(beam[0],bvecs)
        rec={'depth':depth+1,'parents':len(beam) if depth==0 else None,
             'children':len(children),'moves':move_count,'best':front,
             'best_score':list(score(beam[0],bvecs)),
             'bridge_states':sum('bridge' in s.parent_kind for s in beam),
             'max_reducers':max(reducer_counts) if reducer_counts else 0}
        history.append(rec)
        print(json.dumps({'beam':rec},sort_keys=True),flush=True)

    meta={'status':'miss','budget':budget,'best_metrics':metrics(best,bvecs),
          'beam_width':beam_width,'reducer_branch':reducer_branch,
          'guide_branch':guide_branch,'history':history,
          'best_score':list(score(best,bvecs))}
    return best,bvecs,extras,boundary,vals,meta


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=joint.parse_rows,default=(1,3,4))
    ap.add_argument('--budget',type=int,default=48)
    ap.add_argument('--max-support',type=int,default=8)
    ap.add_argument('--beam-width',type=int,default=8)
    ap.add_argument('--reducer-branch',type=int,default=6)
    ap.add_argument('--guide-branch',type=int,default=2)
    ap.add_argument('--bridge-reserve',type=int,default=2)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    t0=time.time()
    state,bvecs,extras,boundary,vals,meta=search(
        c,args.basis_rows,args.budget,args.max_support,args.beam_width,
        args.reducer_branch,args.guide_branch,args.bridge_reserve)
    meta['basis_rows']=list(args.basis_rows);meta['elapsed_s']=round(time.time()-t0,3)
    prefix=build_prefix_result(c,args.basis_rows,state,bvecs,extras,boundary,vals) \
        if meta['status']=='found' else None
    if prefix is not None:(out/'prefix.json').write_text(json.dumps(prefix,indent=2)+'\n')
    # Preserve the best miss as a reproducible frontier state too.
    best={'gates':state.gates,'released_ands':sorted(state.released),
          'available_semantics':sorted(state.S),'dist':state.dist,
          'metrics':metrics(state,bvecs),'basis_vectors':bvecs,
          'basis_rows':list(args.basis_rows)}
    (out/'best-frontier.json').write_text(json.dumps(best,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in meta.items() if k!='history'},sort_keys=True),flush=True)

if __name__=='__main__':main()
