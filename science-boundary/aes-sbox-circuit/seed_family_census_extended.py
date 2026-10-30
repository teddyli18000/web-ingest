#!/usr/bin/env python3
"""Extended near-best AES seed census; intentionally separate from search trigger."""
import json, pathlib
import seed_family_census as c

URLS={
 "nist-a32-g103":c.DEFAULTS["nist-g103"],
 "nist-a32-g104":c.DEFAULTS["nist-g104"],
 "nist-a32-g105":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt",
 "nist-a32-g109":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt",
 "nist-a33-g105":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt",
 "nist-a33-g108":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt",
 "nist-a34-g110":"https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a34-ad4-g110-gd22-xx76-3.circ.txt",
 "fs-101":c.DEFAULTS["fs-101"],
 "fs-102":c.DEFAULTS["fs-102"],
 "fs-103":c.DEFAULTS["fs-103"],
}

def main():
    seeds=[c.load(n,u) for n,u in URLS.items()]
    out={"seeds":{s["name"]:s["summary"] for s in seeds},"pairs":{}}
    for i,a in enumerate(seeds):
        for b in seeds[i+1:]:
            aa,ab=a["and_functions"],b["and_functions"]
            wa,wb=a["wire_functions"],b["wire_functions"]
            k=f"{a['name']}__{b['name']}"
            out["pairs"][k]={"shared_and":len(aa&ab),"and_union":len(aa|ab),
              "and_jaccard":round(len(aa&ab)/len(aa|ab),6),"shared_wire":len(wa&wb),
              "same_and_shape_hash":a["summary"]["and_shape_hash"]==b["summary"]["and_shape_hash"]}
    # Greedy exact-function-overlap clustering only as a descriptive aid, not an equivalence proof.
    names=list(URLS); clusters=[]; left=set(names)
    while left:
        root=sorted(left)[0]; cluster={root}; changed=True
        while changed:
            changed=False
            for x in list(left-cluster):
                for y in cluster:
                    if x==y:continue
                    key=f"{x}__{y}" if f"{x}__{y}" in out["pairs"] else f"{y}__{x}"
                    if out["pairs"][key]["and_jaccard"]>=0.70:
                        cluster.add(x);changed=True;break
        clusters.append(sorted(cluster));left-=cluster
    out["descriptive_clusters_jaccard_ge_0_70"]=clusters
    pathlib.Path("seed-family-census-extended.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__":main()
