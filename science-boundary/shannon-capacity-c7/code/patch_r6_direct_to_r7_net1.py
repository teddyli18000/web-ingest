#!/usr/bin/env python3
"""Retarget the proven direct-support r6 engine to net+1 radius 7.

For a 134753 baseline a remove-7/add-8 witness has net gain +1.  This stage is
complete for witnesses containing an outside vertex whose exact blocker support
has size 7.  It changes only the support cap / owner-set size and emitted labels;
the independent-set target remains 8.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_r6_direct_to_r7_net1.py SRC DST")
s = Path(sys.argv[1]).read_text()

def rep(old, new, want=1):
    global s
    n=s.count(old)
    if n != want:
        raise SystemExit(f"expected {want} occurrences of {old!r}, found {n}")
    s=s.replace(old,new)

rep("constexpr unsigned K=6;", "constexpr unsigned K=7;")
rep("std::array<std::uint32_t,6>wrem{}", "std::array<std::uint32_t,7>wrem{}")
rep("for(unsigned mask=1;mask<63;++mask)", "for(unsigned mask=1;mask<127;++mask)")
rep('replace6add8', 'replace7add8')
rep('exact-unrestricted-r6-direct-support', 'exact-unrestricted-net1-r7-direct-support', 2)
rep("for(unsigned i=0;i<6;++i)std::cout", "for(unsigned i=0;i<7;++i)std::cout")
Path(sys.argv[2]).write_text(s)
