#!/usr/bin/env python3
"""Retarget exact r6 c5-anchor search from 134752 net+2 to 134753 net+1.

Completeness for target seven additions uses the already completed unrestricted
net+1 radius-5 negative result: if the sixth owner x occurred in only one of the
seven additions, the other six additions would form a remove5/add6 witness.  If
x occurred twice only as singleton support {x}, exact one-owner alpha<=1 would
be violated.  Hence x co-occurs with an anchor owner and is enumerated by the
same support-adjacency construction.

Only baseline size, independent-set target, pool threshold, and output labels
are changed. Support recovery and owner-set generation are unchanged.
"""
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_r6_c5_anchor_net2_to_net1.py SRC DST")
s=Path(sys.argv[1]).read_text()

def rep(old,new,want=1):
    global s
    n=s.count(old)
    if n!=want: raise SystemExit(f"expected {want} occurrences of {old!r}, found {n}")
    s=s.replace(old,new)

rep("a.size()!=134752", "a.size()!=134753")
rep("bool rec8(", "bool rec7(")
rep("if(ch.size()==8)", "if(ch.size()==7)")
rep("ch.size()+p.size()-s<8", "ch.size()+p.size()-s<7")
rep("if(rec8(p,i+1,ch))", "if(rec7(p,i+1,ch))")
rep("bool find8(", "bool find7(")
rep("p.size()>=8&&rec8(p,0,ch)", "p.size()>=7&&rec7(p,0,ch)")
rep("if(ps<8)continue", "if(ps<7)continue")
rep("if(find8(pool,ch))", "if(find7(pool,ch))")
rep('replace6add8', 'replace6add7')
rep('exact-r6-c5-anchor', 'exact-net1-r6-c5-anchor', 2)
Path(sys.argv[2]).write_text(s)
