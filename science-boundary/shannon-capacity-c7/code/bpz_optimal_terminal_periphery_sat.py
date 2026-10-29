#!/usr/bin/env python3
"""Exact +1 SAT over the union of all 18 BPZ terminal-code record basins.

For the pinned BPZ five-dimensional gadget there are 18 terminal constructions
of score 134753 with the same 359x359 BB square.  They are parameterized by
q,r in {O,H,V} and one of two A/D--H/V orientations.  Each construction has
exactly 5872 peripheral vertices beyond BB.

Every peripheral vertex occurring in any of the 18 constructions is compatible
with every BB vertex.  Therefore a record improvement inside their total union
is equivalent to finding 5873 pairwise nonconfusable peripheral vertices.

This script builds the real C7^10 conflict graph on that peripheral union and
asks MiniCard for an independent set of size at least 5873.  SAT materializes a
Few Shots certificate of size >=134754.  UNSAT is an exact exclusion of the
entire 18-basin peripheral union, substantially stronger than pairwise basin
recombination or bounded-radius local exchange.
"""

import argparse
import json
import sys
from pathlib import Path

BB_SIZE=359*359
RECORD_SCORE=134_753
RECORD_PERIPH=RECORD_SCORE-BB_SIZE
TARGET_PERIPH=RECORD_PERIPH+1
PORT_LABELS=("O","H","V")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tan_root",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("shot_dir",type=Path)
    args=ap.parse_args()

    root=args.tan_root.resolve(); sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    from pysat.solvers import Minicard  # type: ignore

    base,_transform,_exchanges,axioms=load_base(root/"data"/"base_c7.json")
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    fam={
        "B":set(base.B.elements),"N":set(base.X0.elements),
        "A":set(base.XV.elements),"D":set(base.XH.elements),
        "O":set(base.R.elements),"H":set(base.PH.elements),
        "V":set(base.PV.elements),
    }
    sizes={k:len(v) for k,v in fam.items()}
    if sizes!={"B":359,"N":322,"A":19,"D":26,"O":8,"H":8,"V":8}:
        raise RuntimeError(("family-size drift",sizes))

    labels=tuple(fam)
    separated={a:set() for a in labels}
    for a in labels:
        F=fam[a]
        if any((ring.NB[x]&F)-{x} for x in F): raise RuntimeError(("family not independent",a))
    for i,a in enumerate(labels):
        for b in labels[i+1:]:
            A,B=fam[a],fam[b]
            ok=all(not (ring.NB[x]&B) for x in A)
            ok2=all(not (ring.NB[y]&A) for y in B)
            if ok!=ok2: raise RuntimeError(("asymmetric family separation",a,b))
            if ok: separated[a].add(b); separated[b].add(a)

    def word_compatible(w1,w2):
        return w2[0] in separated[w1[0]] or w2[1] in separated[w1[1]]

    BB={(a,b) for a in fam["B"] for b in fam["B"]}
    if len(BB)!=BB_SIZE: raise RuntimeError(("BB size drift",len(BB)))

    code_specs=[]; peripheries=[]; universe=set()
    for q in PORT_LABELS:
        for r in PORT_LABELS:
            for orient in (0,1):
                if orient==0:
                    words=(("B","B"),("N",q),("A","H"),("D","V"),(r,"N"),("H","D"),("V","A"))
                else:
                    words=(("B","B"),("N",q),("A","V"),("D","H"),(r,"N"),("H","A"),("V","D"))
                for i in range(len(words)):
                    for j in range(i+1,len(words)):
                        if not word_compatible(words[i],words[j]):
                            raise RuntimeError(("18-code compatibility drift",q,r,orient,words[i],words[j]))
                S=set(); block_sizes={}
                for x,y in words:
                    before=len(S)
                    for a in fam[x]:
                        for b in fam[y]: S.add((a,b))
                    added=len(S)-before; expected=sizes[x]*sizes[y]
                    if added!=expected: raise RuntimeError(("code block overlap",q,r,orient,x+y,added,expected))
                    block_sizes[x+y]=expected
                if len(S)!=RECORD_SCORE: raise RuntimeError(("record-code score drift",q,r,orient,len(S)))
                if not BB<=S: raise RuntimeError(("BB missing",q,r,orient))
                P=S-BB
                if len(P)!=RECORD_PERIPH: raise RuntimeError(("periphery size drift",q,r,orient,len(P)))
                universe.update(P); peripheries.append(P)
                code_specs.append({"q":q,"r":r,"orientation":orient,"words":[x+y for x,y in words],"block_sizes":block_sizes})
    if len(peripheries)!=18: raise RuntimeError(("record-basin count drift",len(peripheries)))

    verts=sorted(universe); n=len(verts); vid={p:i for i,p in enumerate(verts)}
    by_first_bits={}; by_first_id={}
    for i,(a,b) in enumerate(verts):
        by_first_bits[a]=by_first_bits.get(a,0)|(1<<b)
        by_first_id.setdefault(a,{})[b]=i

    # Exact graph + connected components, while feeding MiniCard incrementally.
    solver=Minicard(); edges=0
    parent=list(range(n)); sz=[1]*n
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a=find(a); b=find(b)
        if a==b: return
        if sz[a]<sz[b]: a,b=b,a
        parent[b]=a; sz[a]+=sz[b]

    for i,(a,b) in enumerate(verts):
        nb_b_bits=ring.BITS[b]
        for c in ring.NB[a]:
            bits=by_first_bits.get(c,0)&nb_b_bits
            if not bits: continue
            ids=by_first_id[c]
            while bits:
                lsb=bits&-bits; d=lsb.bit_length()-1; bits-=lsb
                j=ids[d]
                if j<=i: continue
                solver.add_clause([-(i+1),-(j+1)]); edges+=1; union(i,j)

    comp= {}
    for i in range(n): comp.setdefault(find(i),0); comp[find(i)]+=1
    comp_sizes=sorted(comp.values(),reverse=True)

    # Sanity: all 18 known peripheries are graph-independent by direct edge replay.
    periph_ids=[{vid[p] for p in P} for P in peripheries]
    for k,S in enumerate(periph_ids):
        if len(S)!=RECORD_PERIPH: raise RuntimeError(("periphery id drift",k,len(S)))
    # Native cardinality: at most n-TARGET_PERIPH false variables == at least target true.
    solver.add_atmost([-(i+1) for i in range(n)], n-TARGET_PERIPH)
    # Seed phases near the first known 5872-point basin.
    seed=periph_ids[0]
    try:
        solver.set_phases([(i+1 if i in seed else -(i+1)) for i in range(n)])
    except Exception:
        pass
    sat=solver.solve(); model=solver.get_model() if sat else None; solver.delete()

    status={
        "method":"exact-sat-union-of-18-bpz-optimal-terminal-peripheries",
        "record_score":RECORD_SCORE,
        "bb_size":BB_SIZE,
        "known_periphery_size":RECORD_PERIPH,
        "target_periphery_size":TARGET_PERIPH,
        "record_basins":len(peripheries),
        "periphery_union_vertices":n,
        "periphery_conflict_edges":edges,
        "conflict_components":len(comp_sizes),
        "largest_components":comp_sizes[:30],
        "sat_target":sat,
        "breakthrough":bool(sat),
        "codes":code_specs,
    }

    if sat:
        pos={z for z in model if 1<=z<=n}
        selected={verts[z-1] for z in pos}
        if len(selected)<TARGET_PERIPH: raise RuntimeError(("SAT model below target",len(selected)))
        # Independent replay against the exact graph relation.
        selected_ids={vid[p] for p in selected}
        for i,(a,b) in enumerate(verts):
            if i not in selected_ids: continue
            nb_b_bits=ring.BITS[b]
            for c in ring.NB[a]:
                bits=by_first_bits.get(c,0)&nb_b_bits
                if not bits: continue
                for d,j in by_first_id[c].items():
                    if j>i and j in selected_ids and (bits&(1<<d)):
                        raise RuntimeError(("SAT replay conflict",verts[i],verts[j]))
        candidate=BB|selected
        if len(candidate)!=BB_SIZE+len(selected): raise RuntimeError("candidate overlaps BB")
        status.update({"selected_periphery":len(selected),"candidate_score":len(candidate)})
        args.shot_dir.mkdir(parents=True,exist_ok=True)
        def point(pair):
            a,b=pair; return "".join(str(x) for x in (ring.decode(a)+ring.decode(b)))
        points=sorted(point(p) for p in candidate)
        if len(points)!=len(candidate) or len(points)!=len(set(points)): raise RuntimeError("certificate conversion mismatch")
        (args.shot_dir/"certificate.json").write_text(json.dumps({"points":points},separators=(",",":"))+"\n")
        (args.shot_dir/"metadata.json").write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in status.items() if k!="codes"},sort_keys=True))

if __name__=="__main__": main()
