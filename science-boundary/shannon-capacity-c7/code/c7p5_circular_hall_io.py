#!/usr/bin/env python3
"""Independent 367-seed input validation and Few Shots 10D square materializer."""
import argparse
import base64
import hashlib
import json
import struct
from pathlib import Path

POWERS=(1,7,49,343,2401)

def confusable(a,b):
    return all(((a//p)-(b//p))%7 in (0,1,6) for p in POWERS)

def independent(words):
    return len(words)==len(set(words)) and all(
        not confusable(a,b) for i,a in enumerate(words) for b in words[i+1:])

def read_circular(path):
    d=json.loads(path.read_text())
    raw=base64.b64decode(d["data"])
    assert len(raw)==2*d["n"] and hashlib.sha256(raw).hexdigest()==d["sha256_decoded_bytes"]
    words=list(struct.unpack("<"+str(d["n"])+"H",raw))
    assert all(0<=v<7**5 for v in words) and words==sorted(words)
    return words

def profile(words):
    out=[]
    for p in POWERS:
        hist=[0]*7
        for v in words:hist[(v//p)%7]+=1
        out.append(tuple(sorted(hist)))
    return tuple(sorted(out))

def dump(words,path):
    assert len(words)==367 and independent(words)
    path.write_text("".join(f"{v}\n" for v in words))

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="mode",required=True)
    a=sub.add_parser("prepare")
    a.add_argument("circular",type=Path)
    a.add_argument("bpz",type=Path)
    a.add_argument("family",type=Path)
    a.add_argument("output",type=Path)
    b=sub.add_parser("verify")
    b.add_argument("candidate",type=Path)
    b.add_argument("shot",type=Path)
    args=ap.parse_args()
    if args.mode=="prepare":
        args.output.mkdir(parents=True,exist_ok=True)
        C=read_circular(args.circular)
        bpz=json.loads(args.bpz.read_text())
        family=json.loads(args.family.read_text())
        rows=[("circle",C),("I0",list(map(int,bpz["I0"]))),("X",list(map(int,bpz["X"])))]
        rows.extend((f"F{i}",list(map(int,L))) for i,L in enumerate(family["states"]))
        assert len(rows)==39
        for name,W in rows:dump(W,args.output/(name+".ids"))
        assert all(profile(W)!=profile(C) for name,W in rows if name!="circle")
        print(json.dumps({"status":"verified","seeds":len(rows),"circular_n":len(C),
             "distinct_from_other_seed_automorphism_orbits_by_marginals":True},sort_keys=True))
    else:
        S=sorted({int(x) for x in args.candidate.read_text().splitlines()})
        assert len(S)>=368 and all(0<=v<7**5 for v in S) and independent(S)
        S=S[:368]
        ds=["".join(str((v//p)%7) for p in POWERS) for v in S]
        pts=sorted(a+b for a in ds for b in ds)
        assert len(pts)==135424 and len(set(pts))==135424
        args.shot.mkdir(parents=True,exist_ok=True)
        (args.shot/"certificate.json").write_text(json.dumps({"points":pts},separators=(",",":"))+"\n")
        print(json.dumps({"verified_five_dimensional_size":len(S),"square_score":len(pts)},sort_keys=True))

if __name__=="__main__":
    main()
