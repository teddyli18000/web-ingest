#!/usr/bin/env python3
"""Patch c7_10d_private_guided12_walk.cpp to trace all accepted additions.

The walk/acceptance logic is unchanged.  The patched binary accepts optional
argument TRACE.  For every accepted 1-for-1 or 2-for-2 move, each added point y
is written as

    y b1 b2 ...

where b_i are all confusable vertices of the ORIGINAL verified 134753 baseline.
Thus a downstream exact optimizer may arbitrarily recombine every point ever
visited by the mixed walk, including points introduced by genuine neutral2
moves.  All edits are byte-asserted against the durable source.
"""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_private_guided12_trace.py SOURCE OUTPUT")
s = Path(sys.argv[1]).read_text()

old = 'if(argc!=7){std::cerr<<"usage: guided12 BASELINE_IDS RESULT_IDS STEPS SEED TWO_RATE DOWN_RATE\\n";return 2;}'
new = 'if(argc!=7&&argc!=8){std::cerr<<"usage: guided12 BASELINE_IDS RESULT_IDS STEPS SEED TWO_RATE DOWN_RATE [TRACE]\\n";return 2;}'
if s.count(old) != 1: raise SystemExit(f"argc drift: {s.count(old)}")
s = s.replace(old, new)

old = 'for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}trans<std::uint16_t,Op::Sum>(cnt,tmp16);'
new = 'for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}auto baseline_sel=sel;trans<std::uint16_t,Op::Sum>(cnt,tmp16);'
if s.count(old) != 1: raise SystemExit(f"baseline copy drift: {s.count(old)}")
s = s.replace(old, new)

old = 'std::mt19937_64 rng(seed);std::uint64_t acc1=0,acc2=0,rej1=0,rej2=0,down=0,fail2=0;'
new = 'std::mt19937_64 rng(seed);std::ofstream trace;if(argc==8){trace.open(argv[7]);if(!trace)throw std::runtime_error("trace open");}std::uint64_t acc1=0,acc2=0,rej1=0,rej2=0,down=0,fail2=0;'
if s.count(old) != 1: raise SystemExit(f"trace stream drift: {s.count(old)}")
s = s.replace(old, new)

old = 'if(accept){cur=nxt;if(is2)++acc2;else ++acc1;if(better(cur,best))best=cur;}else{'
new = '''if(accept){cur=nxt;if(trace){for(auto yy:add){trace<<yy;nb(yy,z);for(auto v:z)if(bg(baseline_sel,v))trace<<' '<<v;trace<<'\\n';}}if(is2)++acc2;else ++acc1;if(better(cur,best))best=cur;}else{'''
if s.count(old) != 1: raise SystemExit(f"accept patch drift: {s.count(old)}")
s = s.replace(old, new)

Path(sys.argv[2]).write_text(s)
