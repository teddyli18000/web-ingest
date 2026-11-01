#!/usr/bin/env python3
"""Shard h18 affine-witness inputs by QHIT support orbit.

The qgroup output uses affine-canonical `(supp(alpha),supp(gamma))` masks.
Instead of making the final witness verifier rescan every compressed HIT for
every QHIT, expand only the support orbits that actually have QHITs (500
AGL(1,Z25) images each), hash raw compressed support pairs into those orbits,
and emit one tiny hits/qgroup pair per canonical support group.

This is an exact join/reindexing only: it does not reject candidates.
"""
from __future__ import annotations
import argparse, math, re
from pathlib import Path

N=25
UNITS=[a for a in range(N) if math.gcd(a,N)==1]
QRE=re.compile(r'^QHIT as=(\d+) gs=(\d+) ')

def aff(mask:int,a:int,b:int)->int:
    y=0
    for i in range(N):
        if (mask>>i)&1:
            y |= 1 << ((a*i+b)%N)
    return y

def support_pair(line:str)->tuple[int,int]:
    if not line.startswith('HIT '):
        raise ValueError('not HIT')
    ps=line.split('p=',1)[1].split('|c=',1)[0].replace(',',' ').split()
    cs=line.split('|c=',1)[1].replace(',',' ').split()
    p=list(map(int,ps)); c=list(map(int,cs))
    if len(p)!=N or len(c)!=N:
        raise ValueError('bad HIT vector length')
    am=sum(1<<i for i,v in enumerate(p) if v==0)
    gm=sum(1<<i for i,v in enumerate(c) if v==0)
    return am,gm

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument('hits'); ap.add_argument('qgroup'); ap.add_argument('outdir')
    args=ap.parse_args()
    qlines=[x for x in Path(args.qgroup).read_text().splitlines() if x.startswith('QHIT ')]
    bykey:dict[tuple[int,int],list[str]]={}
    for line in qlines:
        m=QRE.match(line)
        if not m: raise SystemExit(f'bad QHIT: {line}')
        k=(int(m.group(1)),int(m.group(2)))
        bykey.setdefault(k,[]).append(line)
    if not bykey: raise SystemExit('no QHITs')

    # The selected canonical support orbits are disjoint.  Build a reverse
    # lookup from every affine image to its canonical QHIT key.
    image_to_key:dict[tuple[int,int],tuple[int,int]]={}
    for k in bykey:
        a0,g0=k
        for a in UNITS:
            for b in range(N):
                z=(aff(a0,a,b),aff(g0,a,b))
                old=image_to_key.setdefault(z,k)
                if old!=k:
                    raise SystemExit(f'orbit collision {old} {k}')

    matched:dict[tuple[int,int],list[str]]={k:[] for k in bykey}
    total_hits=0; selected_hits=0
    for line in Path(args.hits).read_text().splitlines():
        if not line.startswith('HIT '): continue
        total_hits+=1
        k=image_to_key.get(support_pair(line))
        if k is not None:
            matched[k].append(line); selected_hits+=1

    out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for idx,k in enumerate(sorted(bykey)):
        hs=matched[k]
        if not hs:
            raise SystemExit(f'QHIT support orbit has no compressed HIT: {k}')
        d=out/f'{idx:05d}'; d.mkdir()
        (d/'hits.txt').write_text('\n'.join(hs)+'\n')
        (d/'qgroup.txt').write_text('\n'.join(bykey[k])+'\n')
        manifest.append(f'{idx:05d} as={k[0]} gs={k[1]} qhits={len(bykey[k])} raw_hits={len(hs)}')
    (out/'manifest.txt').write_text('\n'.join(manifest)+'\n')
    print(f'WITNESS_SHARD_SUMMARY qhits={len(qlines)} support_groups={len(bykey)} total_raw_hits={total_hits} selected_raw_hits={selected_hits} orbit_images={len(image_to_key)}')

if __name__=='__main__': main()
