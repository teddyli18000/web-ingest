#!/usr/bin/env python3
"""Remove probabilistic partial-set hash dedup from the r6 c3 prototype.

The prototype used 64-bit FNV values only to suppress duplicate 4/5-owner DFS
states.  A hash collision could in principle suppress a branch, so no exact
result may use that source unpatched.  This script performs byte-for-byte
asserted replacements on a temporary copy.  Final six-owner dedup remains an
unordered_set<U6,...> whose hash is only a bucket selector: C++ equality is
checked, so collisions there do not affect completeness.
"""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_search_net2_r6_c3_exact.py IN OUT")
p = Path(sys.argv[1])
s = p.read_text()
old1 = '''  std::unordered_set<std::uint64_t>seen4,seen5;seen4.reserve(256);seen5.reserve(4096);\n  auto smallkey=[](const std::vector<std::uint32_t>&v){std::vector<std::uint32_t>x=v;std::sort(x.begin(),x.end());std::uint64_t h=1469598103934665603ULL;for(auto z:x){h^=z;h*=1099511628211ULL;}return h;};\n'''
old2 = '''for(auto x:front){++expansions;curv.push_back(x);auto hk=smallkey(curv);bool fresh=curv.size()==4?seen4.insert(hk).second:seen5.insert(hk).second;if(fresh)self(self,curv);curv.pop_back();if(found)return;}'''
new2 = '''for(auto x:front){++expansions;curv.push_back(x);self(self,curv);curv.pop_back();if(found)return;}'''
if s.count(old1) != 1 or s.count(old2) != 1:
    raise SystemExit(f"prototype drift: block={s.count(old1)} loop={s.count(old2)}")
s = s.replace(old1, "").replace(old2, new2)
Path(sys.argv[2]).write_text(s)
print("patched c3 prototype: removed collision-prone partial hash dedup")
