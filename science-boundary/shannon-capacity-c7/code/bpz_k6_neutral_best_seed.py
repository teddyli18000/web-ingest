#!/usr/bin/env python3
"""Rebuild the verifier-valid 134753 neutral mother found by exact k6 plateau RC2.

The source state is the pinned BPZ/Tan terminal q=H,r=H,orientation=0 at
commit c753408492dde92a239708986d16c15dbf6c3235.  The exact lexicographic
plateau search (run 40993717057) found a largest 18-for-18 zero-gain exchange.
This script freezes that state without rerunning the 288-scenario MaxSAT sweep.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery

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


def main():
    ap=argparse.ArgumentParser();ap.add_argument("tan_root",type=Path);ap.add_argument("certificate",type=Path);ap.add_argument("status",type=Path);a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve()); B=set(B)
    core={(x,y) for x in B for y in B}; per=terminal_periphery(fam,"H","H",0); base=core|per
    if len(base)!=134753 or len(SELECTED)!=18 or len(DELETED)!=18: raise RuntimeError((len(base),len(SELECTED),len(DELETED)))
    if not DELETED <= base: raise RuntimeError(("deleted-not-baseline",sorted(DELETED-base)))
    if SELECTED & (base-DELETED): raise RuntimeError(("selected-overlap",sorted(SELECTED&(base-DELETED))))
    cand=(base-DELETED)|SELECTED
    if len(cand)!=134753: raise RuntimeError(("score",len(cand)))
    # Independent structural replay, with neighborhoods supplied by the pinned source.
    cv=list(cand)
    # Checking all ~9e9 pairs is unnecessary: only selected points are new, and
    # the original base is already certified.  Check every selected-new against
    # retained old and against every other selected-new.
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
