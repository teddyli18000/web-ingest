#!/usr/bin/env python3
import argparse
import gzip
import json
from pathlib import Path

import family_ports as fp


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("bundle",type=Path)
    ap.add_argument("r367",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("status",type=Path)
    args=ap.parse_args()
    digits=tuple(fp.dec5(v) for v in range(fp.U))
    xset=fp.make_x(fp.load_r(args.r367),digits)
    with gzip.open(args.bundle,"rt") as f:bundle=json.load(f)
    raw=[*bundle["parents"],bundle["witness"]]
    states=[];seen=set()
    for s in raw:
        key=tuple(sorted(s))
        if key not in seen:seen.add(key);states.append(list(key))
    summary=[]
    for si,state in enumerate(states):
        pairs=fp.private_pairs(state,digits);centers=len({c for c,a in pairs})
        summary.append({"state":si,"private_pairs":len(pairs),"private_centers":centers})
        print("parent",si,"private",len(pairs),"centers",centers,flush=True)
        ports=fp.find_ports(pairs,xset,digits,9)
        if ports is None:continue
        cand,A,Dset=fp.build_candidate(state,ports,xset,digits)
        if len(cand)!=fp.TARGET:
            print("parent",si,"ports-found-but-score",len(cand),flush=True);continue
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({"points":[fp.dec10(v) for v in sorted(cand)]},separators=(",",":"))+"\n")
        status={"candidate":True,"score":len(cand),"method":"archived-parent-nine-ports","state":si,"private_pairs":len(pairs),"private_centers":centers,"footprint_A":len(A),"footprint_D":len(Dset),"ports":[{"center":c,"alt":a,"side":s} for c,a,s in ports],"states_summary":summary}
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n");print("FOUND",json.dumps(status,sort_keys=True));return
    status={"candidate":False,"score":134753,"method":"archived-parent-nine-ports","states":len(states),"max_private_pairs":max(s["private_pairs"] for s in summary),"max_private_centers":max(s["private_centers"] for s in summary),"states_summary":summary}
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+"\n");print("NONE",json.dumps(status,sort_keys=True))

if __name__=="__main__":main()
