#!/usr/bin/env python3
"""Beam search over history-dependent same-count Delaunay scar walks.

Each topology move is chosen *after* the preceding move has changed the
triangulation.  We retain an exact edge-membership signature rather than a list
of independent flips, because later moves may delete edges created by earlier
moves (as in the q1->q2->q3 R->A positive-control path).

The search is deliberately local and small: after every crossed boundary we
hold the accumulated active support fixed while the rest of the crystal adapts,
re-enumerate same-count legal flips, prefer moves newly legal relative to the
parent topology, exclude the immediate inverse, and periodically fully release
the state.  The objective is to discover qualitatively new free basins, not to
exhaust a static flip list.
"""
from __future__ import annotations
import argparse,json,pathlib,collections,math
from dataclasses import dataclass
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb
from search_e564_scaffolded_flip import fixed_relax


def parse_quad(s):
    q=tuple(int(z) for z in s.split(','))
    if len(q)!=4: raise ValueError('quad must be u,v,a,b')
    return q


def edge(a,b): return (min(int(a),int(b)),max(int(a),int(b)))

def counts(x):
    d,_=topology(x); c=collections.Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def legal_rows(x):
    deg,ef=topology(x); edges=set(ef); base=collections.Counter(deg.tolist()); rows=[]
    for (u,v),opp in ef.items():
        if len(opp)!=2: continue
        a,b=opp; add=edge(a,b); delete=edge(u,v)
        if add in edges: continue
        nd=deg.copy(); nd[u]-=1; nd[v]-=1; nd[a]+=1; nd[b]+=1
        if collections.Counter(nd.tolist())!=base: continue
        q=(int(u),int(v),int(a),int(b)); t=threshold(x,q,'balanced')
        if t is None or not math.isfinite(t): continue
        rows.append({'quad':q,'delete':delete,'add':add,'threshold':float(t)})
    rows.sort(key=lambda r:(r['threshold'],r['quad']))
    return ef,rows


def key(r): return (r['delete'],r['add'])

def edge_set(x):
    _,ef=topology(x); return set(ef)


def signature_ok(x,expected):
    es=edge_set(x)
    return all((e in es)==want for e,want in expected.items())


def graph_distances(ef,sources,n):
    adj=[set() for _ in range(n)]
    for u,v in ef: adj[u].add(v); adj[v].add(u)
    inf=10**9; d=[inf]*n; q=collections.deque()
    for s in sources: d[s]=0; q.append(s)
    while q:
        u=q.popleft()
        for v in adj[u]:
            if d[v]>d[u]+1: d[v]=d[u]+1; q.append(v)
    return d


def classify_energy(e,live):
    refs={'R':live,'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443,
          'e432':444368.4322496275}
    name,minerr=min(((n,abs(e-v)) for n,v in refs.items()),key=lambda z:z[1])
    return name if minerr<2e-6 else 'novel'


def free_release(x,maxiter,live):
    e,raw,y,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(x),maxiter=maxiter)
    return {'energy':float(e),'delta_live':float(e-live),'raw_energy':float(raw),
            'coord_counts':counts(y),'class':classify_energy(e,live),'nit':int(nit),
            'success':bool(ok),'message':str(msg),'points':y}


def compact_path(path):
    return [{'quad':list(m['quad']),'delete':list(m['delete']),'add':list(m['add']),
             'threshold':m['threshold'],'multiplier':m['multiplier'],'newly_legal':m.get('newly_legal',True)} for m in path]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--first-quad',required=True)
    ap.add_argument('--tag',default='seed'); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--depth',type=int,default=4); ap.add_argument('--beam',type=int,default=3)
    ap.add_argument('--branch',type=int,default=4); ap.add_argument('--max-graph-distance',type=int,default=1)
    ap.add_argument('--first-multiplier',type=float,default=1.003); ap.add_argument('--step-multiplier',type=float,default=1.01)
    ap.add_argument('--fixed-maxiter',type=int,default=1300); ap.add_argument('--release-maxiter',type=int,default=2600)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    _,xroot=load_seed(args.seed_json); root_cc=counts(xroot); _,root_legal=legal_rows(xroot); root_keys={key(r) for r in root_legal}
    first_q=parse_quad(args.first_quad); t1=threshold(xroot,first_q,'balanced')
    if t1 is None: raise RuntimeError('first flip unavailable')
    first={'quad':first_q,'delete':edge(first_q[0],first_q[1]),'add':edge(first_q[2],first_q[3]),
           'threshold':float(t1),'multiplier':args.first_multiplier,'newly_legal':False}
    x1=perturb(xroot,first_q,t1*args.first_multiplier,'balanced')
    expected={first['delete']:False,first['add']:True}; support=set(first_q)
    q1=sm.xyz_to_vars(x1); Efix,raw,qfix,xfix,nit,ok,msg=fixed_relax(q1,sorted(support),args.fixed_maxiter)
    if not signature_ok(xfix,expected): raise RuntimeError('first path signature healed during fixed adaptation')
    free1=free_release(xfix,args.release_maxiter,args.live_score)
    _,legal1=legal_rows(xfix); legal1keys={key(r) for r in legal1}
    node={'x':xfix,'fixed_energy':float(Efix),'support':support,'expected':expected,'path':[first],
          'parent_legal_keys':root_keys,'legal_keys':legal1keys,'free':free1}
    beam=[node]; all_nodes=[]; endpoints=[]
    print('ROOT',args.tag,'Efix',f'{Efix:.12f}','first_t',t1,'free',free1['class'],f"{free1['energy']:.12f}",flush=True)

    def record(n,depth):
        f=n['free']; rec={'depth':depth,'fixed_energy':n['fixed_energy'],'free_energy':f['energy'],
             'delta_live':f['delta_live'],'free_class':f['class'],'coord_counts':f['coord_counts'],
             'path':compact_path(n['path']),'support':sorted(n['support'])}
        all_nodes.append(rec)
        if f['class']=='novel' or f['energy']<args.live_score+0.02:
            endpoints.append((f['energy'],rec,f['points'].copy()))
        print('NODE','d',depth,'fix',f"{n['fixed_energy']:.12f}",'free',f['class'],f"{f['energy']:.12f}",
              'dlive',f"{f['delta_live']:+.9g}",'path',' -> '.join(f"{m['delete']}->{m['add']}" for m in n['path']),flush=True)

    record(node,1)
    for depth in range(2,args.depth+1):
        children=[]
        for parent in beam:
            ef,rows=legal_rows(parent['x']); dist=graph_distances(ef,parent['support'],len(parent['x']))
            last=parent['path'][-1]; inverse=(last['add'],last['delete'])
            cand=[]
            for r in rows:
                if key(r)==inverse: continue
                d=min(dist[v] for v in r['quad'])
                if d>args.max_graph_distance: continue
                isnew=key(r) not in parent['parent_legal_keys']
                # Dynamic events first. Existing local moves are fallback only.
                novelty_rank=0 if isnew else 1
                cand.append((novelty_rank,d,r['threshold'],r))
            cand.sort(key=lambda z:(z[0],z[1],z[2]))
            # If newly-created moves exist, devote most branches to them but keep at most one fallback.
            newc=[z for z in cand if z[0]==0][:args.branch]
            oldc=[z for z in cand if z[0]==1][:1]
            chosen=(newc+oldc)[:args.branch] if newc else oldc[:args.branch]
            for novelty_rank,d,t,r in chosen:
                mult=args.step_multiplier
                xs=perturb(parent['x'],r['quad'],t*mult,'balanced')
                exp=dict(parent['expected']); exp[r['delete']]=False; exp[r['add']]=True
                sup=set(parent['support'])|set(r['quad'])
                try:
                    Ef,raw,qf,xf,nit,ok,msg=fixed_relax(sm.xyz_to_vars(xs),sorted(sup),args.fixed_maxiter)
                except Exception as exc:
                    print('CHILD_FAIL',depth,r['quad'],repr(exc),flush=True); continue
                if counts(xf)!=root_cc or not signature_ok(xf,exp):
                    print('CHILD_HEAL',depth,r['quad'],'cc',counts(xf),'sigok',signature_ok(xf,exp),flush=True); continue
                fr=free_release(xf,args.release_maxiter,args.live_score)
                _,lrows=legal_rows(xf); lkeys={key(z) for z in lrows}
                move=dict(r); move['multiplier']=mult; move['newly_legal']=(novelty_rank==0); move['graph_distance']=int(d)
                child={'x':xf,'fixed_energy':float(Ef),'support':sup,'expected':exp,
                       'path':parent['path']+[move], 'parent_legal_keys':parent['legal_keys'],
                       'legal_keys':lkeys,'free':fr}
                # Primary: low fixed elastic cost; favor newly-created events and local support.
                score=float(Ef)+0.25*t+0.002*d+(0.0 if novelty_rank==0 else 0.004)
                # Strongly prioritize any genuinely new low free basin.
                if fr['class']=='novel' and fr['energy']<args.live_score+0.05: score-=0.02
                if fr['energy']<args.live_score-2e-7: score-=1.0
                child['score']=score; children.append(child); record(child,depth)
        if not children: break
        # Dedup by expected edge signature plus rounded fixed energy; symmetry copies within a shard are rare.
        uniq={}
        for c in sorted(children,key=lambda z:z['score']):
            sk=tuple(sorted((e,w) for e,w in c['expected'].items()))
            if sk not in uniq: uniq[sk]=c
        beam=list(uniq.values())[:args.beam]
        print('BEAM',depth,[(round(c['fixed_energy'],9),c['free']['class'],round(c['free']['energy'],9),len(c['path'])) for c in beam],flush=True)

    # Keep coordinates only for distinct best endpoints to make the artifact useful but bounded.
    endpoints.sort(key=lambda z:z[0]); saved=[]; seen=[]
    for e,rec,pts in endpoints:
        if any(abs(e-ee)<2e-7 and rec['coord_counts']==cc for ee,cc in seen): continue
        seen.append((e,rec['coord_counts']))
        rr=dict(rec); rr['points']=pts.tolist(); saved.append(rr)
        if len(saved)>=12: break
    best=min((r['free_energy'] for r in all_nodes),default=float('inf'))
    out={'tag':args.tag,'live_score':args.live_score,'root_coord':root_cc,'first_quad':list(first_q),
         'depth':args.depth,'beam_width':args.beam,'branch':args.branch,'nodes':all_nodes,
         'saved_endpoints':saved,'best_free_energy':best,'best_delta_live':best-args.live_score}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('candidate below live; inspect saved_endpoints\n')

if __name__=='__main__': main()
