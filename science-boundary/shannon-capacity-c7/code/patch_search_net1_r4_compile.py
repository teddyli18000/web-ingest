#!/usr/bin/env python3
"""Assertively fix the single mixed-auto declaration in search_net1_r4_complete.cpp.

The original declaration
    auto k=lo[i].k,n=ks(k);
is ill-formed because k is Key while n is unsigned.  This patch is deliberately
byte-exact: it refuses to touch a source that has drifted.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_search_net1_r4_compile.py SRC DST")
src = Path(sys.argv[1]).read_text()
old = "auto k=lo[i].k,n=ks(k);"
new = "Key k=lo[i].k;unsigned n=ks(k);"
if src.count(old) != 1:
    raise SystemExit(f"expected exactly one target occurrence, got {src.count(old)}")
Path(sys.argv[2]).write_text(src.replace(old, new))
