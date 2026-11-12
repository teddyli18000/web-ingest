#!/usr/bin/env python3
"""Extract one small LJCR covering from Zenodo's 4.2 GB JSON using HTTP ranges.

No bulk archive download. Keys are ordered by (t,k,v), as in coverdata.json.
"""
import argparse
import json
import re
import urllib.request
from pathlib import Path

URL = "https://zenodo.org/api/records/19735294/files/covers.json/content"
TOTAL = 4191522340
HEADER = re.compile(rb'\n"(C\((\d+),(\d+),(\d+)\))":\s*\[')

def key(v, k, t):
    return int(t), int(k), int(v)

def get(start, count):
    stop = min(TOTAL - 1, start + count - 1)
    req = urllib.request.Request(
        URL, headers={"Range": f"bytes={start}-{stop}", "User-Agent": "p015-cover-research"})
    with urllib.request.urlopen(req, timeout=120) as response:
        assert response.status == 206, response.status
        return response.read()

def extract(target=(15,10,8)):
    v, k, t = target
    needle = f'"C({v},{k},{t})":'.encode()
    lo, hi = 0, TOTAL
    for i in range(32):
        mid = (lo + hi) // 2
        chunk = get(mid, 2_097_152)
        if (n := chunk.find(needle)) != -1:
            print("FOUND", target, "at", mid+n, "step", i, flush=True)
            start = n + len(needle)
            # Target small (<100 kB). Full content may cross chunk boundary.
            remainder = chunk[start:]
            if len(remainder) < 65_536:
                remainder += get(mid+len(chunk), 131_072)
            return json.JSONDecoder().raw_decode(remainder.decode("utf-8").lstrip())[0]
        match = HEADER.search(chunk)
        if match is None:
            # Can be inside very large neighboring covering; use larger range.
            chunk = get(mid, 8_388_608)
            match = HEADER.search(chunk)
        assert match, f"no key anchor near {mid}"
        current = key(match.group(2), match.group(3), match.group(4))
        desired = key(v,k,t)
        print("probe",i,"range",lo,hi,"anchor",match.group(1).decode(), "offset",mid+match.start(),flush=True)
        if current < desired:
            lo = mid + match.start()
        else:
            hi = mid
        if hi-lo < 131_072:
            chunk = get(max(0,lo-1_048_576), min(TOTAL-max(0,lo-1_048_576),4_194_304))
            pos = chunk.find(needle)
            assert pos >= 0, f"target not in final range {lo}..{hi}"
            return json.JSONDecoder().raw_decode(chunk[pos+len(needle):].decode("utf-8").lstrip())[0]
    raise RuntimeError("binary search did not converge")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--v",type=int,default=15)
    ap.add_argument("--k",type=int,default=10)
    ap.add_argument("--t",type=int,default=8)
    args=ap.parse_args()
    blocks=extract((args.v,args.k,args.t))
    print("retrieved",len(blocks),"blocks",flush=True)
    assert all(len(b)==args.k and len(set(b))==args.k and min(b)>=1 and max(b)<=args.v for b in blocks)
    covered=set()
    import itertools
    for b in blocks:
        covered.update(itertools.combinations(sorted(b),args.t))
    assert len(covered)==__import__("math").comb(args.v,args.t), len(covered)
    Path(args.out).write_text(json.dumps({"params":[args.v,args.k,args.t],"blocks":[[x-1 for x in b] for b in blocks]}, separators=(",",":")))
    print("verified",len(covered),"targets",flush=True)
