#!/usr/bin/env python3
"""Rebuild the verifier-valid 134753 neutral mother found by exact k6 plateau RC2.

The source state is the pinned BPZ/Tan terminal q=H,r=H,orientation=0 at
commit c753408492dde92a239708986d16c15dbf6c3235.  The exact lexicographic
plateau search (run 40993717057) found a largest 18-for-18 zero-gain exchange.
This script freezes that state without rerunning the 288-scenario MaxSAT sweep
and intentionally has no python-sat dependency.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

SELECTED = {
 (6110,6494),(6494,1553),(6494,3716),(6494,13158),(6494,13358),
 (6494,13600),(6494,14027),(6494,14329),(6494,14733),(6494,15996),
 (10708,6494),(10960,6494),(12277,6494),(13065,6494),(13677,6494),
 (15075,6494),(15910,6494),(16046,6494),
}
DELETED = {
 (1553,4092),(3716,4092),(4092,1553),(4092,3716),(4092,13158),
 (4092,13358),(4092,14027),(4092,14329),(4092,14733),(4092,15996),
 (8888,13600),(10960,8888),(13158,4092),(13358,4092),(14027,4092),
 (14329,4092),(14733,4092),(15996,4092),
}
EXPECTED_HASH = "636cbc9a3368fccd6bac3155aa0a73eaf9ddd5d9f053ba74ca00f748437b9d94"


def load_geometry(root: Path):
    sys.path.insert(0,str(root))
    from shannon.certificates import load_base  # type: ignore
    p=root/"data"/"base_c7.json"; raw=json.loads(p.read_text())
    base,_t,_e,ax=load_base(p)
    if not all(ax.values()): raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring; I=set(map(int,raw["I0"])); owners={int(p[0]) for p in raw["private_pairs"]}; B=I-owners
    PH=set(map(int,raw["PH"])); PV=set(map(int,raw["PV"]))
    fam={"B":B,"N":set(base.X0.elements),"A":set(base.XV.elements),"D":set(base.XH.elements),"O":set(base.R.elements),"H":PH,"V":PV}
    if len(B)!=359 or len(PH)!=8 or len(PV)!=8: raise RuntimeError((len(B),len(PH),len(PV)))
    return ring,B,fam


def terminal_hh0(fam):
    # terminal_periphery(fam,"H","H",0) copied explicitly so this frozen seed
    # does not import any MaxSAT module.
    words=(("N","H"),("A","H"),("D","V"),("H","N"),("H","D"),("V","A"))
    P=set()
    for u,v in words:P.update((a,b) for a in fam[u] for b in fam[v])
    if len(P)!=5872: raise RuntimeError(("periphery",len(P)))
    return P


def main():
    ap=argparse.ArgumentParser();ap.add_argument("tan_root",type=Path);ap.add_argument("certificate",type=Path);ap.add_argument("status",type=Path);a=ap.parse_args()
    ring,B,fam=load_geometry(a.tan_root.resolve()); B=set(B)
    core={(x,y) for x in B for y in B}; per=terminal_hh0(fam); base=core|per
    if len(base)!=134753 or len(SELECTED)!=18 or len(DELETED)!=18: raise RuntimeError((len(base),len(SELECTED),len(DELETED)))
    if not DELETED <= base: raise RuntimeError(("deleted-not-baseline",sorted(DELETED-base)))
    if SELECTED & (base-DELETED): raise RuntimeError(("selected-overlap",sorted(SELECTED&(base-DELETED))))
    cand=(base-DELETED)|SELECTED
    if len(cand)!=134753: raise RuntimeError(("score",len(cand)))
    kept=base-DELETED
    for p in SELECTED:
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in kept:
            if z[0] in nx and z[1] in ny: raise RuntimeError(("new-old conflict",p,z))
        for z in SELECTED:
            if z<=p: continue
            if z[0] in nx and z[1] in ny: raise RuntimeError(("new-new conflict",p,z))
    def enc(p): return "".join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc(p) for p in cand)
    a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({"points":pts},separators=(",",":"))+"\n")
    st={"method":"pinned-k6-neutral-best-seed","score":134753,"selected":18,"deleted":18,"q":"H","r":"H","terminal_orientation":0,"expected_canonical_hash":EXPECTED_HASH,"selected_points":[list(p) for p in sorted(SELECTED)],"deleted_points":[list(p) for p in sorted(DELETED)]}
    a.status.parent.mkdir(parents=True,exist_ok=True);a.status.write_text(json.dumps(st,indent=2,sort_keys=True)+"\n");print(json.dumps(st,sort_keys=True))
if __name__=="__main__":main()
