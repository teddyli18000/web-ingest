#!/usr/bin/env python3
"""Exact prize optimization over small pairs of omitted BPZ product blocks.

Unlike the earlier Hall sweep, this allows genuine cross-conflicts between the
two candidate blocks.  For candidate union C and record I it solves exactly

    max |S| - |N_I(S)|

subject to S being independent in C7^10.  Candidate selection variables carry
+1 reward; a baseline blocker variable carries -1 cost and every selected
candidate implies deletion of each of its blockers.  Candidate conflict edges
are hard clauses.  RC2 therefore gives the exact best arbitrary-radius exchange
inside that two-block universe.

We pack many small block pairs into one Action and use process-level parallelism.
"""
from __future__ import annotations
import argparse, json, multiprocessing as mp, os, sys
from pathlib import Path

LABELS=("B","N","A","D","O","H","V")
RECORD_CODE=(("B","B"),("N","O"),("A","H"),("D","V"),("O","N"),("H","D"),("V","A"))
EXPECTED=134753
G={}
def init_worker(g):
    global G; G=g

def solve_pair(spec):
    i,j=spec; P,Q=G['blocks'][i],G['blocks'][j]
    union=sorted(P['set']|Q['set']); n=len(union); uid={p:k for k,p in enumerate(union)}
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    w=WCNF(); delvar={}
    def dv(b):
        v=delvar.get(b)
        if v is None: v=n+len(delvar)+1;delvar[b]=v
        return v
    # Each selected candidate forces every baseline blocker to be deleted.
    blocker_edges=0
    for k,p in enumerate(union):
        for b in G['blockers'][p]: w.append([-(k+1),dv(b)]);blocker_edges+=1
    # Exact candidate conflict graph.  Each source block is independent, so
    # all distinct conflicts are cross-block; enumerate via Q membership bits.
    qm=Q['members']; qidx={p:uid[p] for p in Q['set']}
    edges=set()
    for p in P['set']:
        a,b=p; u=uid[p]
        for c in G['NB'][a]:
            bits=qm.get(c,0)&G['BITS'][b]
            while bits:
                bb=bits&-bits; d=bb.bit_length()-1;bits-=bb
                q=(c,d)
                if q==p:continue
                v=qidx.get(q)
                if v is None:continue
                if u>v:u0,v0=v,u
                else:u0,v0=u,v
                edges.add((u0,v0))
    for u,v in edges:w.append([-(u+1),-(v+1)])
    for k in range(n):w.append([k+1],weight=1)
    for b,v in delvar.items():w.append([-v],weight=1)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=False) as rc2:
        model=rc2.compute();cost=rc2.cost
    pos={z for z in model if z>0}; selected=[union[k] for k in range(n) if k+1 in pos]; deleted=[b for b,v in delvar.items() if v in pos]
    gain=n-cost
    rec={'word1':P['word'],'word2':Q['word'],'candidates':n,'candidate_overlap':len(P['set']&Q['set']),
         'cross_conflicts':len(edges),'blocker_edges':blocker_edges,'touched_blockers':len(delvar),
         'gain':gain,'selected':len(selected),'deleted':len(deleted)}
    if gain>0:rec['selected_vertices']=[list(p) for p in selected];rec['deleted_ids']=deleted
    return rec

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('shot_dir',type=Path);ap.add_argument('--cap',type=int,default=6000);ap.add_argument('--workers',type=int,default=max(1,min(4,os.cpu_count() or 1)));a=ap.parse_args()
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    base,_t,_e,ax=load_base(root/'data'/'base_c7.json');
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;fam={'B':set(base.B.elements),'N':set(base.X0.elements),'A':set(base.XV.elements),'D':set(base.XH.elements),'O':set(base.R.elements),'H':set(base.PH.elements),'V':set(base.PV.elements)}
    sizes={k:len(v) for k,v in fam.items()};expect={'B':359,'N':322,'A':19,'D':26,'O':8,'H':8,'V':8}
    if sizes!=expect:raise RuntimeError(('size drift',sizes))
    owner_pair=[];owner={}
    for x,y in RECORD_CODE:
        for u in sorted(fam[x]):
            for v in sorted(fam[y]):
                p=(u,v)
                if p in owner:raise RuntimeError(('overlap',p))
                owner[p]=len(owner_pair);owner_pair.append(p)
    if len(owner_pair)!=EXPECTED:raise RuntimeError(('score drift',len(owner_pair)))
    baseline=set(owner)
    nbm={lab:[None]*ring.n for lab in LABELS}
    for lab in LABELS:
        F=fam[lab]
        for z in range(ring.n):nbm[lab][z]=tuple(q for q in ring.NB[z] if q in F)
    blockers={}
    def getb(p):
        got=blockers.get(p)
        if got is not None:return got
        u,v=p;out=[]
        for x,y in RECORD_CODE:
            for q in nbm[x][u]:
                for r in nbm[y][v]:out.append(owner[(q,r)])
        if len(out)!=len(set(out)):raise RuntimeError(('dup blocker',p))
        blockers[p]=tuple(out);return blockers[p]
    blocks=[]
    for x in LABELS:
        for y in LABELS:
            if (x,y) in RECORD_CODE:continue
            S={(u,v) for u in fam[x] for v in fam[y] if (u,v) not in baseline}
            members={}
            for u,v in S:members[u]=members.get(u,0)|(1<<v)
            blocks.append({'word':x+y,'set':S,'members':members})
    # First identify genuinely cross-incompatible small pairs.  Compatible pairs
    # were already exactly solved by Hall and are skipped.
    def cross_bad(P,Q):
        qm=Q['members']
        for u,v in P['set']:
            for x in ring.NB[u]:
                bits=qm.get(x,0)&ring.BITS[v]
                if x==u and (u,v) in Q['set']:bits&=~(1<<v)
                if bits:return True
        return False
    specs=[];meta=[]
    for i in range(len(blocks)):
        for j in range(i+1,len(blocks)):
            U=len(blocks[i]['set']|blocks[j]['set'])
            if U>a.cap:continue
            if not cross_bad(blocks[i],blocks[j]):continue
            specs.append((i,j));meta.append((U,blocks[i]['word'],blocks[j]['word']))
    allcand=set()
    for i,j in specs:allcand|=blocks[i]['set'];allcand|=blocks[j]['set']
    for p in allcand:getb(p)
    state={'blocks':blocks,'blockers':blockers,'NB':ring.NB,'BITS':ring.BITS}
    ctx=mp.get_context('fork')
    with ctx.Pool(a.workers,initializer=init_worker,initargs=(state,)) as P:results=list(P.imap_unordered(solve_pair,specs,chunksize=1))
    results.sort(key=lambda r:(-r['gain'],r['candidates'],r['word1'],r['word2']))
    best=results[0] if results else None
    status={'method':'exact-bpz-two-incompatible-block-prize-maxsat','cap':a.cap,'block_pairs_tested':len(results),'max_gain':None if best is None else best['gain'],'best':best,'results':results}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    if best and best['gain']>0:
        sel={tuple(p) for p in best['selected_vertices']};deleted={owner_pair[b] for b in best['deleted_ids']};cand=(baseline-deleted)|sel
        if len(cand)!=EXPECTED+best['gain']:raise RuntimeError(('materialize size',len(cand),best['gain']))
        a.shot_dir.mkdir(parents=True,exist_ok=True)
        def point(p):u,v=p;return ''.join(str(d) for d in (ring.decode(u)+ring.decode(v)))
        pts=sorted(point(p) for p in cand)
        if len(pts)!=len(set(pts)):raise RuntimeError('duplicate points')
        (a.shot_dir/'certificate.json').write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
        (a.shot_dir/'metadata.json').write_text(json.dumps(best,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in status.items() if k!='results'},sort_keys=True))
if __name__=='__main__':main()
