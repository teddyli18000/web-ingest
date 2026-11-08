#!/usr/bin/env python3
"""Screen a newly synthesized valid (4,6,35) parent for direct extension.

Both independent exact extension solvers from extension_check.py must agree.
Distinct triangle/I5 fingerprints certify non-isomorphism to all 37 supplied
Exoo graph types when the pair is absent from their known fingerprint list.
"""
import argparse
import json
from pathlib import Path
from extension_check import build_constraints, solve_hitting, solve_dpll
from extension_check import complement, has_clique, verify_extension

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--outdir",type=Path,required=True)
    p.add_argument("--reference",type=Path,required=True)
    args=p.parse_args()
    args.outdir.mkdir(parents=True,exist_ok=True)
    rows=json.loads(args.parent.read_text())["adjacency"]
    assert len(rows)==35 and all(len(r)==35 for r in rows)
    assert all(rows[i][i]=="0" and rows[i][j]==rows[j][i]
               for i in range(35) for j in range(35))
    graph=[sum(1<<j for j,c in enumerate(r) if c=="1") for r in rows]
    assert not has_clique(graph,4) and not has_clique(complement(graph),6)
    constr=build_constraints(graph)
    signature=(len(constr.tris),len(constr.ind5))
    published=json.loads(args.reference.read_text())["results"]
    matches=[x["name"] for x in published
             if (x["triangles"],x["independent5"])==signature]
    x=solve_dpll(constr)
    y=solve_hitting(graph,constr)
    assert (x is None)==(y is None)
    result={"parent_edges":sum(g.bit_count() for g in graph)//2,
            "triangles":signature[0],
            "independent5":signature[1],
            "matches_published_fingerprint":matches,
            "fingerprint_not_in_published_set":not matches,
            "extendable":x is not None}
    if x is not None:
        assert verify_extension(graph,x) and verify_extension(graph,y)
        n=len(graph)
        h=graph[:]+[0]
        for i in range(n):
            if x>>i&1:
                h[i]|=1<<n
                h[n]|=1<<i
        assert not has_clique(h,4) and not has_clique(complement(h),6)
        rows36=["".join("1" if h[i]>>j&1 else "0" for j in range(36))
                for i in range(36)]
        file=args.outdir/"certificate36.json"
        file.write_text(json.dumps({"adjacency":rows36})+"\n")
        result["certificate"]=str(file)
    (args.outdir/"screen-summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
