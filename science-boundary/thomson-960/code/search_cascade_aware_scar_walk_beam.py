#!/usr/bin/env python3
"""Cascade-aware beam over history-dependent same-count Delaunay scar walks.

Extends search_dynamic_scar_walk_beam.py with a physically motivated second
objective.  After each fixed-adapted topology path we partially release the
active support under a modest harmonic restraint and measure whether *remote*
root glides have either fired or softened relative to their root thresholds.
The R->A positive control shows this signal before orbit2/orbit3 fire.

Beam retention is Pareto-like: keep representatives with low fixed elastic
cost, high remote-cascade signal, and low next-event threshold rather than
collapsing everything into one fixed-energy score.
"""
from __future__ import annotations
import argparse,json,pathlib,math
import numpy as np

import diagnose_soft_modes as sm
import search_dynamic_scar_walk_beam as base
from search_from_seed_modes import load_seed
from search_e564_defect_flip_parallel import topology,threshold,perturb
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax


def root_follower_metrics(x,support,root_rows,remote_distance=2,topk=4):
    """Measure remote root-glide activation/softening around state x."""
    _,ef=topology(x); edges=set(ef)
    dist=base.graph_distances(ef,support,len(x))
    triggered=[]; softened=[]; available=0
    for r in root_rows:
        if min(dist[v] for v in r['quad']) < remote_distance:
            continue
        olde,newe=r['delete'],r['add']; t0=float(r['threshold'])
        if newe in edges and olde not in edges:
            triggered.append({'delete':list(olde),'add':list(newe),'root_threshold':t0})
            continue
        if olde not in edges or newe in edges:
            continue
        t=threshold(x,tuple(r['quad']),'balanced')
        if t is None or not math.isfinite(t):
            continue
        available+=1; t=float(t)
        if t < t0:
            frac=max(0.0,1.0-t/max(t0,1e-15))
            softened.append({'delete':list(olde),'add':list(newe),'root_threshold':t0,
                             'threshold':t,'fractional_drop':frac})
    softened.sort(key=lambda z:(-z['fractional_drop'],z['threshold']))
    top=softened[:topk]
    signal=float(len(triggered))+sum(z['fractional_drop'] for z in top)
    return {'signal':signal,'triggered_count':len(triggered),'triggered':triggered,
            'softened_count':len(softened),'top_softened':top,'available_remote':available}


def compact_path(path):
    return [{'quad':list(m['quad']),'delete':list(m['delete']),'add':list(m['add']),
             'threshold':m['threshold'],'multiplier':m['multiplier'],
             'newly_legal':m.get('newly_legal',True),'graph_distance':m.get('graph_distance')} for m in path]


def select_beam(children,width):
    # Deduplicate by complete expected edge signature first.
    uniq={}
    for c in children:
        sk=tuple(sorted((e,w) for e,w in c['expected'].items()))
        old=uniq.get(sk)
        if old is None or (c['fixed_energy'], -c['cascade_effective']) < (old['fixed_energy'],-old['cascade_effective']):
            uniq[sk]=c
    vals=list(uniq.values())
    by_cascade=sorted(vals,key=lambda z:(-z['cascade_effective'],-z['cascade']['triggered_count'],z['fixed_energy']))
    by_cost=sorted(vals,key=lambda z:(z['fixed_energy'],-z['cascade_effective']))
    by_thresh=sorted(vals,key=lambda z:(z['path'][-1]['threshold'],z['fixed_energy']))
    by_free=sorted(vals,key=lambda z:(z['free']['energy'],z['fixed_energy']))
    out=[]; seen=set()
    # Reserve two slots for cascade potential and one for elastic cost before filling.
    streams=[by_cascade[:2],by_cost[:2],by_thresh[:1],by_free[:1],by_cascade,by_cost]
    for stream in streams:
        for c in stream:
            sk=tuple(sorted((e,w) for e,w in c['expected'].items()))
            if sk in seen: continue
            seen.add(sk); out.append(c)
            if len(out)>=width: return out
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--first-quad',required=True)
    ap.add_argument('--tag',default='seed'); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--depth',type=int,default=5); ap.add_argument('--beam',type=int,default=4)
    ap.add_argument('--branch',type=int,default=5); ap.add_argument('--max-graph-distance',type=int,default=2)
    ap.add_argument('--remote-distance',type=int,default=2); ap.add_argument('--probe-kappa',type=float,default=100.0)
    ap.add_argument('--first-multiplier',type=float,default=1.003); ap.add_argument('--step-multiplier',type=float,default=1.01)
    ap.add_argument('--fixed-maxiter',type=int,default=1300); ap.add_argument('--probe-maxiter',type=int,default=900)
    ap.add_argument('--release-maxiter',type=int,default=2600); ap.add_argument('--out',required=True); args=ap.parse_args()

    _,xroot=load_seed(args.seed_json); root_cc=base.counts(xroot); _,root_rows=base.legal_rows(xroot)
    root_keys={base.key(r) for r in root_rows}
    first_q=base.parse_quad(args.first_quad); t1=threshold(xroot,first_q,'balanced')
    if t1 is None: raise RuntimeError('first flip unavailable')
    first={'quad':first_q,'delete':base.edge(first_q[0],first_q[1]),'add':base.edge(first_q[2],first_q[3]),
           'threshold':float(t1),'multiplier':args.first_multiplier,'newly_legal':False,'graph_distance':0}
    x1=perturb(xroot,first_q,t1*args.first_multiplier,'balanced')
    expected={first['delete']:False,first['add']:True}; support=set(first_q)
    Efix,raw,qfix,xfix,nit,ok,msg=fixed_relax(sm.xyz_to_vars(x1),sorted(support),args.fixed_maxiter)
    if not base.signature_ok(xfix,expected): raise RuntimeError('first signature healed during fixed adaptation')
    free1=base.free_release(xfix,args.release_maxiter,args.live_score)
    _,legal1=base.legal_rows(xfix); legal1keys={base.key(r) for r in legal1}
    Ep,rawp,qp,xp,np,okp,msgp,arms,pen=restraint_relax(qfix.copy(),xfix.copy(),sorted(support),args.probe_kappa,args.probe_maxiter)
    cascade=root_follower_metrics(xp,support,root_rows,args.remote_distance)
    pgood=base.signature_ok(xp,expected); ceff=cascade['signal']*(1.0 if pgood else 0.25)
    node={'x':xfix,'q':qfix,'fixed_energy':float(Efix),'support':support,'expected':expected,'path':[first],
          'parent_legal_keys':root_keys,'legal_keys':legal1keys,'free':free1,'cascade':cascade,
          'cascade_effective':ceff,'probe_chain_ok':pgood,'probe_energy':float(Ep)}
    beam=[node]; all_nodes=[]; endpoints=[]

    def record(n,depth):
        f=n['free']; rec={'depth':depth,'fixed_energy':n['fixed_energy'],'free_energy':f['energy'],
          'delta_live':f['delta_live'],'free_class':f['class'],'coord_counts':f['coord_counts'],
          'cascade':n['cascade'],'cascade_effective':n['cascade_effective'],'probe_chain_ok':n['probe_chain_ok'],
          'probe_energy':n['probe_energy'],'path':compact_path(n['path']),'support':sorted(n['support'])}
        all_nodes.append(rec)
        if f['class']=='novel' or f['energy']<args.live_score+0.02:
            endpoints.append((f['energy'],rec,f['points'].copy()))
        print('NODE','d',depth,'fix',f"{n['fixed_energy']:.12f}",'probe',f"{n['probe_energy']:.12f}",
              'cascade',f"{n['cascade_effective']:.6f}",'trig',n['cascade']['triggered_count'],
              'chain',n['probe_chain_ok'],'free',f['class'],f"{f['energy']:.12f}",'dlive',f"{f['delta_live']:+.9g}",
              'path',' -> '.join(f"{m['delete']}->{m['add']}" for m in n['path']),flush=True)
        if n['cascade']['top_softened']:
            print('SOFT',[(z['delete'],z['add'],round(z['root_threshold'],8),round(z['threshold'],8),round(z['fractional_drop'],4)) for z in n['cascade']['top_softened']],flush=True)

    record(node,1)
    for depth in range(2,args.depth+1):
        children=[]
        for parent in beam:
            ef,rows=base.legal_rows(parent['x']); dist=base.graph_distances(ef,parent['support'],len(parent['x']))
            last=parent['path'][-1]; inverse=(last['add'],last['delete']); cand=[]
            for r in rows:
                if base.key(r)==inverse: continue
                d=min(dist[v] for v in r['quad'])
                if d>args.max_graph_distance: continue
                isnew=base.key(r) not in parent['parent_legal_keys']; novelty_rank=0 if isnew else 1
                cand.append((novelty_rank,d,r['threshold'],r))
            cand.sort(key=lambda z:(z[0],z[1],z[2]))
            newc=[z for z in cand if z[0]==0][:args.branch]
            oldc=[z for z in cand if z[0]==1][:2]
            chosen=(newc+oldc)[:args.branch] if newc else oldc[:args.branch]
            for novelty_rank,d,t,r in chosen:
                xs=perturb(parent['x'],r['quad'],t*args.step_multiplier,'balanced')
                exp=dict(parent['expected']); exp[r['delete']]=False; exp[r['add']]=True
                sup=set(parent['support'])|set(r['quad'])
                try:
                    Ef,raw,qf,xf,nit,ok,msg=fixed_relax(sm.xyz_to_vars(xs),sorted(sup),args.fixed_maxiter)
                except Exception as exc:
                    print('CHILD_FAIL',depth,r['quad'],repr(exc),flush=True); continue
                if base.counts(xf)!=root_cc or not base.signature_ok(xf,exp):
                    print('CHILD_HEAL',depth,r['quad'],'cc',base.counts(xf),'sigok',base.signature_ok(xf,exp),flush=True); continue
                fr=base.free_release(xf,args.release_maxiter,args.live_score)
                _,lrows=base.legal_rows(xf); lkeys={base.key(z) for z in lrows}
                try:
                    Ep,rawp,qp,xp,np,okp,msgp,arms,pen=restraint_relax(qf.copy(),xf.copy(),sorted(sup),args.probe_kappa,args.probe_maxiter)
                    pgood=base.signature_ok(xp,exp)
                    cas=root_follower_metrics(xp,sup,root_rows,args.remote_distance)
                    ceff=cas['signal']*(1.0 if pgood else 0.25)
                except Exception as exc:
                    print('PROBE_FAIL',depth,r['quad'],repr(exc),flush=True)
                    Ep=float(Ef); pgood=False; cas={'signal':0.0,'triggered_count':0,'triggered':[],
                         'softened_count':0,'top_softened':[],'available_remote':0}; ceff=0.0
                move=dict(r); move['multiplier']=args.step_multiplier; move['newly_legal']=(novelty_rank==0); move['graph_distance']=int(d)
                child={'x':xf,'q':qf,'fixed_energy':float(Ef),'support':sup,'expected':exp,
                       'path':parent['path']+[move],'parent_legal_keys':parent['legal_keys'],'legal_keys':lkeys,
                       'free':fr,'cascade':cas,'cascade_effective':float(ceff),'probe_chain_ok':bool(pgood),'probe_energy':float(Ep)}
                children.append(child); record(child,depth)
        if not children: break
        beam=select_beam(children,args.beam)
        print('BEAM',depth,[(round(c['fixed_energy'],6),round(c['cascade_effective'],4),c['cascade']['triggered_count'],c['free']['class'],round(c['free']['energy'],9)) for c in beam],flush=True)

    endpoints.sort(key=lambda z:z[0]); saved=[]; seen=[]
    for e,rec,pts in endpoints:
        if any(abs(e-ee)<2e-7 and rec['coord_counts']==cc for ee,cc in seen): continue
        seen.append((e,rec['coord_counts'])); rr=dict(rec); rr['points']=pts.tolist(); saved.append(rr)
        if len(saved)>=12: break
    best=min((r['free_energy'] for r in all_nodes),default=float('inf'))
    best_cascade=max((r['cascade_effective'] for r in all_nodes),default=0.0)
    out={'tag':args.tag,'live_score':args.live_score,'root_coord':root_cc,'first_quad':list(first_q),
         'depth':args.depth,'beam_width':args.beam,'branch':args.branch,'probe_kappa':args.probe_kappa,
         'nodes':all_nodes,'saved_endpoints':saved,'best_free_energy':best,'best_delta_live':best-args.live_score,
         'best_cascade_effective':best_cascade}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('candidate below live; inspect saved_endpoints\n')

if __name__=='__main__': main()
