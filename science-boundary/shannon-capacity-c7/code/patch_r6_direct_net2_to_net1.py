#!/usr/bin/env python3
"""Retarget the exact direct-support r6 solver from net+2 to net+1.

Only the independent-set target changes from 8 additions to 7 and the emitted
result/method labels are renamed. Support recovery and owner-set enumeration are
unchanged. This direct support-size-6 stratum does not depend on lower-radius
negative results.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_r6_direct_net2_to_net1.py SRC DST")
s = Path(sys.argv[1]).read_text()

def rep(old, new, want):
    global s
    n=s.count(old)
    if n!=want:
        raise SystemExit(f"expected {want} occurrences of {old!r}, found {n}")
    s=s.replace(old,new)

rep("p.size()<8", "p.size()<7", 1)
rep("find_rec(p,0,8,out)", "find_rec(p,0,7,out)", 1)
rep('replace6add8', 'replace6add7', 1)
rep('exact-unrestricted-r6-direct-support', 'exact-unrestricted-net1-r6-direct-support', 2)
Path(sys.argv[2]).write_text(s)
