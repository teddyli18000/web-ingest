#!/usr/bin/env python3
"""Convert a floating Thomson N=960 candidate to the exact p007 certificate form.

Uses the same denominator scale documented for the Few Shots baseline: choose the
largest-magnitude coordinate as the local stereographic axis, orient it toward
the south pole, round the two stereographic coordinates on q=2^29, map back to
an exact rational point on S^2, and reduce by gcd.

Input may be a JSON object containing `best_points` or `points`, or a raw list of
960 xyz triples.  If --few-shots is provided, the official p007 verifier is run
on the emitted directory.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess
import sys

Q=1<<29


def load_points(path: pathlib.Path):
    data=json.loads(path.read_text())
    if isinstance(data,dict):
        pts=data.get("best_points")
        if pts is None:
            pts=data.get("points")
    else:
        pts=data
    if pts is None:
        raise ValueError("input has no non-null best_points/points")
    if len(pts)!=960:
        raise ValueError(f"expected 960 points, got {len(pts)}")
    return pts


def rationalize_one(v):
    x=[float(z) for z in v]
    n=math.sqrt(sum(z*z for z in x))
    if not math.isfinite(n) or n==0:
        raise ValueError("bad floating point")
    x=[z/n for z in x]
    j=max(range(3),key=lambda k:abs(x[k]))
    s=1 if x[j]>=0 else -1
    other=[k for k in range(3) if k!=j]
    # Oriented local coordinates: c=-s*x_j, so c is near -1 and u,v are small.
    c=-s*x[j]
    den=1.0-c
    u=x[other[0]]/den
    w=x[other[1]]/den
    p=int(round(u*Q)); r=int(round(w*Q)); q=Q
    A=2*p*q; B=2*r*q; C=p*p+r*r-q*q; D=p*p+r*r+q*q
    out=[0,0,0]
    out[other[0]]=A
    out[other[1]]=B
    out[j]=-s*C
    g=math.gcd(math.gcd(abs(out[0]),abs(out[1])),math.gcd(abs(out[2]),D))
    out=[z//g for z in out]; D//=g
    if D<=0 or D>10**18:
        raise ValueError(f"denominator out of range: {D}")
    if out[0]*out[0]+out[1]*out[1]+out[2]*out[2] != D*D:
        raise AssertionError("Pythagorean identity failed")
    approx=[z/D for z in out]
    err=math.sqrt(sum((approx[k]-x[k])**2 for k in range(3)))
    return [out[0],out[1],out[2],D],err


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--few-shots")
    args=ap.parse_args()
    pts=load_points(pathlib.Path(args.input))
    cert=[]; errs=[]
    for v in pts:
        z,e=rationalize_one(v); cert.append(z); errs.append(e)
    if len({tuple(z) for z in cert})!=960:
        raise ValueError("rationalization created duplicate points")
    out=pathlib.Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"certificate.json").write_text(json.dumps({"points":cert},separators=(",",":"))+"\n")
    print(f"rationalized n=960 max_chord_error={max(errs):.3e} rms_chord_error={(sum(e*e for e in errs)/960)**0.5:.3e}")
    print(f"max_denominator={max(z[3] for z in cert)} bytes={(out/'certificate.json').stat().st_size}")
    if args.few_shots:
        root=pathlib.Path(args.few_shots)
        verifier=root/"problems/p007-thomson-problem/verify/verify.py"
        cp=subprocess.run([sys.executable,str(verifier),str(out)],cwd=root,text=True,capture_output=True)
        sys.stdout.write(cp.stdout); sys.stderr.write(cp.stderr)
        if cp.returncode:
            raise SystemExit(cp.returncode)

if __name__=="__main__":
    main()
