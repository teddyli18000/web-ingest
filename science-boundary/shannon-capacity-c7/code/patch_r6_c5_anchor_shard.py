#!/usr/bin/env python3
"""Asserted patch for exact sharding of search_net2_r6_c5_anchor.cpp.

The validated solver's expensive outer loop is indexed by independent coverage-5
support anchors.  This patch changes only command-line parsing and inserts a
modular filter on that loop.  For shard_count=S, shards 0..S-1 partition the
original anchors exactly once; search logic inside each anchor is unchanged.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_r6_c5_anchor_shard.py SRC DST")
src, dst = map(Path, sys.argv[1:])
s = src.read_text(encoding="utf-8")

old_main = '''int main(int argc,char**argv)try{\n if(argc!=2){std::cerr<<"usage: search_net2_r6_c5_anchor BASELINE_IDS\\n";return 2;}auto base=load(argv[1]);'''
new_main = '''int main(int argc,char**argv)try{\n if(argc!=4){std::cerr<<"usage: search_net2_r6_c5_anchor BASELINE_IDS SHARD_INDEX SHARD_COUNT\\n";return 2;}\n const std::uint64_t shard_index=std::stoull(argv[2]),shard_count=std::stoull(argv[3]);\n if(!shard_count||shard_index>=shard_count)throw std::runtime_error("bad shard");\n auto base=load(argv[1]);'''
old_loop = ''' for(std::int64_t ai=0;ai<(std::int64_t)g5.size();++ai){if(found.load(std::memory_order_relaxed))continue;auto A=g5[ai].k;'''
new_loop = ''' for(std::int64_t ai=0;ai<(std::int64_t)g5.size();++ai){if((std::uint64_t)ai%shard_count!=shard_index)continue;if(found.load(std::memory_order_relaxed))continue;auto A=g5[ai].k;'''

for old, new, label in [(old_main, new_main, "main"), (old_loop, new_loop, "outer-loop")]:
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"assertion failed for {label}: expected 1 exact match, got {n}")
    s = s.replace(old, new, 1)

# Guard against accidentally modifying the mathematical core beyond the two
# asserted replacements: both original markers must now be absent, and the
# shard filter must occur exactly once.
if old_main in s or old_loop in s or s.count("ai%shard_count!=shard_index") != 1:
    raise SystemExit("post-patch assertion failed")
dst.write_text(s, encoding="utf-8")
print(f"patched {src} -> {dst}")
