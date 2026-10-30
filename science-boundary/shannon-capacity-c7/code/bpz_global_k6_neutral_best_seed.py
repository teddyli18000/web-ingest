#!/usr/bin/env python3
"""Rebuild the verifier-valid 134753 all-k6 neutral mother (47-for-47).

Found by the exact lexicographic global k6-gap union plateau search in Actions
run 40994306953.  The pinned terminal is q=H,r=H,orientation=0.  This script
avoids rerunning the 8.5-minute 18-scenario MaxSAT and has no python-sat
dependency.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

SELECTED={
(951,6494),(6110,6494),(6494,1048),(6494,1553),(6494,1644),(6494,3648),(6494,3716),(6494,3940),(6494,6790),(6494,9177),(6494,9631),(6494,11145),(6494,11237),(6494,11388),(6494,13158),(6494,13358),(6494,13381),(6494,13600),(6494,14027),(6494,14085),(6494,14238),(6494,14329),(6494,14368),(6494,14733),(6494,15996),(6494,16064),(6494,16239),(6494,16324),(6494,16423),(6790,6494),(9177,6494),(9631,6494),(10695,6494),(10708,6494),(10960,6494),(11213,6494),(11237,6494),(11388,6494),(12277,6494),(13065,6494),(13381,6494),(13677,6494),(15075,6494),(15910,6494),(16046,6494),(16239,6494),(16324,6494)
}
DELETED={
(951,8888),(1553,4092),(3716,4092),(4092,1553),(4092,3716),(4092,13158),(4092,13358),(4092,14027),(4092,14329),(4092,14733),(4092,15996),(6790,8888),(8888,1048),(8888,1644),(8888,3648),(8888,3940),(8888,6790),(8888,9177),(8888,9631),(8888,11145),(8888,11237),(8888,11388),(8888,13381),(8888,13600),(8888,14085),(8888,14238),(8888,14368),(8888,16064),(8888,16239),(8888,16324),(8888,16423),(9177,8888),(9631,8888),(10695,8888),(10960,8888),(11213,8888),(11237,8888),(11388,8888),(13158,4092),(13358,4092),(13381,8888),(14027,4092),(14329,4092),(14733,4092),(15996,4092),(16239,8888),(16324,8888)
}
EXPECTED_HASH="58e42b76eb31b1d0b719d5152b2a91d04c830fc275f540b4228062c10cb56b16"

def load_geometry(root:Path):
    sys.path.insert(0,str(root));from shannon.certificates import load_base
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring;I=set(map(int,raw['I0']));owners={int(x) for x,_ in raw['private_pairs']};B=I-owners
    PH=set(map(int,raw['PH']));PV=set(map(int,raw['PV']));fam={'B':B,'N':set(base.X0.elements),'A':set(base.XV.elements),'D':set(base.XH.elements),'O':set(base.R.elements),'H':PH,'V':PV}
    return ring,B,fam

def terminal_hh0(fam):
    words=(('N','H'),('A','H'),('D','V'),('H','N'),('H','D'),('V','A'));P=set()
    for u,v in words:P.update((a,b) for a in fam[u] for b in fam[v])
    if len(P)!=5872:raise RuntimeError(('periphery',len(P)))
    return P

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('status',type=Path);a=ap.parse_args()
    ring,B,fam=load_geometry(a.tan_root.resolve());core={(x,y) for x in B for y in B};base=core|terminal_hh0(fam)
    if len(base)!=134753 or len(SELECTED)!=47 or len(DELETED)!=47:raise RuntimeError((len(base),len(SELECTED),len(DELETED)))
    if not DELETED<=base:raise RuntimeError(('deleted-not-baseline',sorted(DELETED-base)))
    if SELECTED&(base-DELETED):raise RuntimeError(('selected-overlap',sorted(SELECTED&(base-DELETED))))
    cand=(base-DELETED)|SELECTED
    if len(cand)!=134753:raise RuntimeError(('score',len(cand)))
    kept=base-DELETED
    for p in SELECTED:
        nx,ny=ring.NB[p[0]],ring.NB[p[1]]
        for z in kept:
            if z[0] in nx and z[1] in ny:raise RuntimeError(('new-old',p,z))
        for z in SELECTED:
            if z<=p:continue
            if z[0] in nx and z[1] in ny:raise RuntimeError(('new-new',p,z))
    def enc(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    st={'method':'pinned-global-k6-neutral-best-seed','score':134753,'selected':47,'deleted':47,'q':'H','r':'H','terminal_orientation':0,'expected_canonical_hash':EXPECTED_HASH,'source_run':40994306953}
    a.status.parent.mkdir(parents=True,exist_ok=True);a.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(json.dumps(st,sort_keys=True))
if __name__=='__main__':main()
