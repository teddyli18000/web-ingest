#!/usr/bin/env python3
"""Materialize the 18 BPZ terminal-optimal 134753 basins as numeric C7^10 ids."""
import argparse,json,sys
from pathlib import Path

HALF=7**5


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("tan_root",type=Path); ap.add_argument("out_dir",type=Path)
    args=ap.parse_args(); root=args.tan_root.resolve();sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    base,_T,_ex,axioms=load_base(root/"data"/"base_c7.json")
    if not all(axioms.values()): raise RuntimeError({k:v for k,v in axioms.items() if not v})
    ring=base.ring
    fam={"B":set(base.B.elements),"N":set(base.X0.elements),"A":set(base.XV.elements),"D":set(base.XH.elements),"O":set(base.R.elements),"H":set(base.PH.elements),"V":set(base.PV.elements)}
    sizes={k:len(v) for k,v in fam.items()}
    separated={a:set() for a in fam}
    for a,F in fam.items():
        if any((ring.NB[x]&F)-{x} for x in F): raise RuntimeError(("family not independent",a))
    labels=tuple(fam)
    for i,a in enumerate(labels):
        for b in labels[i+1:]:
            ok=all(not (ring.NB[x]&fam[b]) for x in fam[a])
            ok2=all(not (ring.NB[y]&fam[a]) for y in fam[b])
            if ok!=ok2: raise RuntimeError(("asymmetric separation",a,b))
            if ok: separated[a].add(b); separated[b].add(a)
    def compatible(w,z): return z[0] in separated[w[0]] or z[1] in separated[w[1]]

    args.out_dir.mkdir(parents=True,exist_ok=True); manifest=[]; sets=[]
    idx=0
    for q in ("O","H","V"):
        for r in ("O","H","V"):
            for orient in (0,1):
                words=(
                    (("B","B"),("N",q),("A","H"),("D","V"),(r,"N"),("H","D"),("V","A"))
                    if orient==0 else
                    (("B","B"),("N",q),("A","V"),("D","H"),(r,"N"),("H","A"),("V","D"))
                )
                for i in range(len(words)):
                    for j in range(i+1,len(words)):
                        if not compatible(words[i],words[j]): raise RuntimeError(("code incompatibility",q,r,orient,words[i],words[j]))
                S=set()
                for a,b in words:
                    block={(x+HALF*y) for x in fam[a] for y in fam[b]}
                    before=len(S);S|=block
                    if len(S)-before!=len(block): raise RuntimeError(("block overlap",q,r,orient,a+b))
                if len(S)!=134753: raise RuntimeError(("score drift",q,r,orient,len(S)))
                path=args.out_dir/f"basin-{idx:02d}.ids";path.write_text("\n".join(map(str,sorted(S)))+"\n")
                manifest.append({"index":idx,"q":q,"r":r,"orientation":orient,"words":[a+b for a,b in words],"size":len(S),"file":path.name})
                sets.append(frozenset(S));idx+=1
    if idx!=18: raise RuntimeError(("basin count drift",idx))
    unique=len(set(sets))
    if unique<2: raise RuntimeError(("materialized optima collapsed",unique))
    (args.out_dir/"manifest.json").write_text(json.dumps({"family_sizes":sizes,"basins":manifest,"unique_sets":unique},indent=2,sort_keys=True)+"\n")
    print(json.dumps({"basins":idx,"unique_sets":unique,"family_sizes":sizes},sort_keys=True))

if __name__=="__main__":main()
