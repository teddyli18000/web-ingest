#!/usr/bin/env python3
"""Retarget the exact connected max-support-3 radius-6 engine to net+1.

Prerequisite: complete unrestricted net+1 negativity through radius 5 on the
same 134753 baseline.  The source enumerates all connected six-owner unions
anchored by a real selected support-3 hyperedge via the complete extension
patterns 1+1+1, 1+2, and 2+1, then reconstructs the full P_{<=3}(U).  It uses
no net+2-only Hall incidence pruning, so only baseline size, target 8->7, a
known mixed-auto compile typo, and labels are changed.
"""
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_r6_c3_extensions_net2_to_net1.py SRC DST")
s=Path(sys.argv[1]).read_text()

def rep(old,new,want=1):
    global s
    n=s.count(old)
    if n!=want: raise SystemExit(f"expected {want} occurrences of {old!r}, found {n}")
    s=s.replace(old,new)

rep("a.size()!=134752", "a.size()!=134753")
rep("auto k=lo[i].k,n=ksize(k);", "auto k=lo[i].k;auto n=ksize(k);")
rep("bool find8(", "bool find7(")
rep("if(n<8)return false", "if(n<7)return false")
rep("std::array<unsigned,8>ch{}", "std::array<unsigned,7>ch{}")
rep("if(d==8)", "if(d==7)")
rep("for(unsigned t=0;t<8;++t)", "for(unsigned t=0;t<7;++t)")
rep("if(std::popcount(m)<8-d)return false;", "if(std::popcount(m)<7-d)return false;")
rep("if(std::popcount(m)<7-d)break;", "if(std::popcount(m)<6-d)break;")
rep("ch.size()==8", "ch.size()==7")
rep("ch.size()+p.size()-s<8", "ch.size()+p.size()-s<7")
rep("if(pool.size()<8)return false", "if(pool.size()<7)return false")
rep("if(!find8(pool,ch))", "if(!find7(pool,ch))")
rep('replace6add8', 'replace6add7')
rep('exact-r6-c3-support-extensions', 'exact-net1-r6-c3-support-extensions', 2)
Path(sys.argv[2]).write_text(s)
