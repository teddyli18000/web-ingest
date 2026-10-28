#!/usr/bin/env python3
"""Retarget the exact connected max-support-2 radius-6 engine to net+1.

Prerequisite: complete unrestricted net+1 negativity through radius 5 on the
same 134753 baseline. Then any seven-addition/six-owner witness has connected
selected-support hypergraph. With maximum selected support 2, the selected pair
supports form a connected graph on all six owners; the source enumerates every
such owner set from real exact c2 edges and reconstructs the complete P_{<=2}.
Only baseline size, exact independent-set target 8->7, and labels change.
"""
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_r6_c2_graph_net2_to_net1.py SRC DST")
s=Path(sys.argv[1]).read_text()

def rep(old,new,want=1):
    global s
    n=s.count(old)
    if n!=want:
        raise SystemExit(f"expected {want} occurrences of {old!r}, found {n}")
    s=s.replace(old,new)

rep("a.size()!=134752", "a.size()!=134753")
rep("bool rec8(", "bool rec7(")
rep("ch.size()==8", "ch.size()==7")
rep("ch.size()+p.size()-s<8", "ch.size()+p.size()-s<7")
rep("if(rec8(p,i+1,ch))", "if(rec7(p,i+1,ch))")
rep("bool find8(", "bool find7(")
rep("p.size()>=8&&rec8(p,0,out)", "p.size()>=7&&rec7(p,0,out)")
rep("if(ps<8)continue", "if(ps<7)continue")
rep("if(find8(pool,ch))", "if(find7(pool,ch))")
rep('replace6add8', 'replace6add7')
rep('exact-r6-c2-graph', 'exact-net1-r6-c2-graph', 2)
Path(sys.argv[2]).write_text(s)
