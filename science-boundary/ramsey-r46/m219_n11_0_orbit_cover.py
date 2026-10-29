#!/usr/bin/env python3
"""Generate exact symmetry-reduced label covers for the two m=219,n11=0 cases.

Prior exact work proves a Ramsey(4,6,36) graph has no lucky degree-12 vertex.
At m=219 this means every degree-12 vertex sees high-degree excess weight <=2.
For either surviving n11=0 degree sequence, a degree-12 vertex of weight exactly
2 must exist.  For such an anchor v, S(v)=146 and

    e(B)-e(A) = m-S(v) = 73.

The complete endpoint catalogues and extremal edge bounds then leave only
(A28,B101) or (A29,B102).  This script quotients all high-degree label
placements by Aut(A) x Aut(B), producing the finite-domain CSP branch files.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import networkx as nx

EXPECTED_COUNTS = {'A28':8,'A29':1,'B101':1,'B102':76}

def decode_g6(s:str)->nx.Graph:
    s=s.strip(); n=ord(s[0])-63; bits=[]
    for ch in s[1:]:
        z=ord(ch)-63; bits.extend((z>>k)&1 for k in range(5,-1,-1))
    g=nx.Graph(); g.add_nodes_from(range(n)); p=0
    for j in range(1,n):
        for i in range(j):
            if bits[p]: g.add_edge(i,j)
            p+=1
    return g

def autos(g:nx.Graph):
    gm=nx.algorithms.isomorphism.GraphMatcher(g,g)
    return [tuple(m[i] for i in range(len(g))) for m in gm.isomorphisms_iter()]

def set_orbit_reps(items, group):
    unseen=set(tuple(x) for x in items); reps=[]
    while unseen:
        p=min(unseen); full={tuple(sorted(a[x] for x in p)) for a in group}
        unseen-=full; reps.append(p)
    return reps

def colored_orbit_reps(items, group):
    unseen=set(items); reps=[]
    while unseen:
        p=min(unseen)
        full={(a[p[0]],tuple(sorted(a[x] for x in p[1]))) for a in group}
        unseen-=full; reps.append(p)
    return reps

def valid_low_weight(g:nx.Graph,b13,b14):
    s13=set(b13); s14=set(b14); high=s13|s14
    for v in g:
        if v in high: continue
        w=sum(g.has_edge(v,x) for x in s13)+2*sum(g.has_edge(v,x) for x in s14)
        if w>2: return False
    return True

def mask(xs): return sum(1<<x for x in xs)
def sha(path:Path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read_catalog(path:Path): return [x.strip() for x in path.read_text(encoding='ascii').splitlines() if x.strip()]
def write_reps(path:Path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='ascii') as f:
        for r in rows: f.write(' '.join(map(str,r))+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalog-dir',type=Path,required=True);ap.add_argument('--outdir',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);a=ap.parse_args()
    cats={k:read_catalog(a.catalog_dir/f'{k}.g6') for k in EXPECTED_COUNTS}
    assert {k:len(v) for k,v in cats.items()}==EXPECTED_COUNTS
    gs={k:[decode_g6(s) for s in rows] for k,rows in cats.items()}
    groups={k:[autos(g) for g in gg] for k,gg in gs.items()}
    result={'campaign':'m219-n11-0-label-orbit-cover-v1','catalogs':{},'s0':{'a28_b101':[],'a29_b102':[]},'s1':{'a28_b101':[],'a29_b102':[]}}
    for k in cats: result['catalogs'][k]={'count':len(cats[k]),'sha256':sha(a.catalog_dir/f'{k}.g6')}

    # S0 = 12^30 13^6. Anchor has two degree-13 neighbours.
    B=gs['B101'][0]; bg=groups['B101'][0]
    b4=[S for S in itertools.combinations(range(23),4) if valid_low_weight(B,S,())]
    b4r=set_orbit_reps(b4,bg)
    for ai,A in enumerate(gs['A28']):
        ar=set_orbit_reps(list(itertools.combinations(range(12),2)),groups['A28'][ai])
        rows=[(mask(x),0,mask(y),0) for x in ar for y in b4r]
        path=a.outdir/f's0-A28-{ai}-B101.reps';write_reps(path,rows)
        result['s0']['a28_b101'].append({'a':ai,'autA':len(groups['A28'][ai]),'a_label_orbits':len(ar),'autB':len(bg),'b_label_orbits':len(b4r),'placements':len(rows),'file':path.name})
    A=gs['A29'][0]; ag=groups['A29'][0]; ar=set_orbit_reps(list(itertools.combinations(range(12),2)),ag)
    for bi,B in enumerate(gs['B102']):
        bg=groups['B102'][bi]; b4=[S for S in itertools.combinations(range(23),4) if valid_low_weight(B,S,())]; b4r=set_orbit_reps(b4,bg)
        rows=[(mask(x),0,mask(y),0) for x in ar for y in b4r]
        path=a.outdir/f's0-A29-B102-{bi}.reps';write_reps(path,rows)
        result['s0']['a29_b102'].append({'b':bi,'autB':len(bg),'b_valid_labels':len(b4),'b_label_orbits':len(b4r),'a_label_orbits':len(ar),'placements':len(rows),'file':path.name})

    # S1 = 12^31 13^4 14. Weight-2 anchor has one of two typed patterns:
    # P: two degree-13 neighbours in A, degree-14 lies in B;
    # Q: degree-14 neighbour in A, all four degree-13 vertices lie in B.
    B=gs['B101'][0]; bg=groups['B101'][0]
    cfg=[]
    for q in range(23):
        for pair in itertools.combinations([x for x in range(23) if x!=q],2):
            if valid_low_weight(B,pair,(q,)): cfg.append((q,tuple(pair)))
    pbr=colored_orbit_reps(cfg,bg)
    qlabels=[S for S in itertools.combinations(range(23),4) if valid_low_weight(B,S,())]; qbr=set_orbit_reps(qlabels,bg)
    for ai,A in enumerate(gs['A28']):
        ag=groups['A28'][ai]
        par=set_orbit_reps(list(itertools.combinations(range(12),2)),ag)
        qar=set_orbit_reps([(x,) for x in range(12)],ag)
        prows=[(mask(x),0,mask(pair),1<<q) for x in par for q,pair in pbr]
        qrows=[(0,1<<x[0],mask(y),0) for x in qar for y in qbr]
        pp=a.outdir/f's1P-A28-{ai}-B101.reps';qp=a.outdir/f's1Q-A28-{ai}-B101.reps';write_reps(pp,prows);write_reps(qp,qrows)
        result['s1']['a28_b101'].append({'a':ai,'autA':len(ag),'P':{'a_orbits':len(par),'b_valid':len(cfg),'b_orbits':len(pbr),'placements':len(prows),'file':pp.name},'Q':{'a_orbits':len(qar),'b_valid':len(qlabels),'b_orbits':len(qbr),'placements':len(qrows),'file':qp.name}})
    A=gs['A29'][0];ag=groups['A29'][0];par=set_orbit_reps(list(itertools.combinations(range(12),2)),ag);qar=set_orbit_reps([(x,) for x in range(12)],ag)
    for bi,B in enumerate(gs['B102']):
        bg=groups['B102'][bi]
        cfg=[]
        for q in range(23):
            for pair in itertools.combinations([x for x in range(23) if x!=q],2):
                if valid_low_weight(B,pair,(q,)): cfg.append((q,tuple(pair)))
        pbr=colored_orbit_reps(cfg,bg)
        qlabels=[S for S in itertools.combinations(range(23),4) if valid_low_weight(B,S,())];qbr=set_orbit_reps(qlabels,bg)
        prows=[(mask(x),0,mask(pair),1<<q) for x in par for q,pair in pbr]
        qrows=[(0,1<<x[0],mask(y),0) for x in qar for y in qbr]
        pp=a.outdir/f's1P-A29-B102-{bi}.reps';qp=a.outdir/f's1Q-A29-B102-{bi}.reps';write_reps(pp,prows);write_reps(qp,qrows)
        result['s1']['a29_b102'].append({'b':bi,'autB':len(bg),'P':{'b_valid':len(cfg),'b_orbits':len(pbr),'placements':len(prows),'file':pp.name},'Q':{'b_valid':len(qlabels),'b_orbits':len(qbr),'placements':len(qrows),'file':qp.name}})

    result['counts']={
      's0_a28_b101':sum(x['placements'] for x in result['s0']['a28_b101']),
      's0_a29_b102':sum(x['placements'] for x in result['s0']['a29_b102']),
      's1_a28_b101_P':sum(x['P']['placements'] for x in result['s1']['a28_b101']),
      's1_a28_b101_Q':sum(x['Q']['placements'] for x in result['s1']['a28_b101']),
      's1_a29_b102_P':sum(x['P']['placements'] for x in result['s1']['a29_b102']),
      's1_a29_b102_Q':sum(x['Q']['placements'] for x in result['s1']['a29_b102']),
    }
    assert result['counts']=={'s0_a28_b101':7296,'s0_a29_b102':56358,'s1_a28_b101_P':0,'s1_a28_b101_Q':1920,'s1_a29_b102_P':9,'s1_a29_b102_Q':18786},result['counts']
    result['proof_scope']={
      's0':'degree sequence 12^30 13^6; a weight-2 degree-12 anchor exists because every low vertex has weight<=2 and the six degree-13 vertices send at least 54 edges to the 30 low vertices',
      's1':'degree sequence 12^31 13^4 14; a weight-2 degree-12 anchor exists because total high-to-low excess weight is at least 56>31 while every low vertex has weight<=2',
      'local_pair':'for either anchor S(v)=146, so e(B)-e(A)=73; e(B)>=101 and e(A)<=29 force (28,101) or (29,102)'
    }
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(result['counts'],sort_keys=True))
if __name__=='__main__':main()
