#!/usr/bin/env python3
"""Patch the private-guided plateau walker to trace every accepted addition.

The walk logic and acceptance rule are unchanged.  The patched binary accepts an
optional seventh argument TRACE.  On every accepted neutral swap x->y it writes
one line

    y b1 b2 ...

where b_i are **all** vertices of the original 134753-point baseline that are
confusable with y.  The original baseline selection bitset is copied before the
walk, so this trace is independent of the changing plateau state.  A downstream
exact optimizer can therefore recombine every point ever visited by the walk,
not merely its final endpoint.

All source edits are byte-asserted and fail loudly on drift.
"""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_private_guided_trace.py SOURCE OUTPUT")
s = Path(sys.argv[1]).read_text()

old = 'if(argc!=6){std::cerr<<"usage: c7_10d_private_guided_walk BASELINE_IDS RESULT_IDS STEPS SEED DOWN_RATE\\n";return 2;}'
new = 'if(argc!=6&&argc!=7){std::cerr<<"usage: c7_10d_private_guided_walk BASELINE_IDS RESULT_IDS STEPS SEED DOWN_RATE [TRACE]\\n";return 2;}'
if s.count(old) != 1:
    raise SystemExit(f"argc assertion failed: {s.count(old)}")
s = s.replace(old, new)

old = 'for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}trans<std::uint16_t,Op::Sum>(cnt,tmp16);'
new = 'for(auto v:base){cnt[v]=1;xo[v]=v+1;bs(sel,v,true);}auto baseline_sel=sel;trans<std::uint16_t,Op::Sum>(cnt,tmp16);'
if s.count(old) != 1:
    raise SystemExit(f"baseline bitset assertion failed: {s.count(old)}")
s = s.replace(old, new)

old = 'std::mt19937_64 rng(seed);std::uint64_t accepted=0,uphill=0,downhill=0,rejected=0;Pot best=cur;'
new = 'std::mt19937_64 rng(seed);std::ofstream trace;if(argc==7){trace.open(argv[6]);if(!trace)throw std::runtime_error("trace open");}std::uint64_t accepted=0,uphill=0,downhill=0,rejected=0;Pot best=cur;'
if s.count(old) != 1:
    raise SystemExit(f"trace stream assertion failed: {s.count(old)}")
s = s.replace(old, new)

old = 'if(acc){cur=nxt;++accepted;if(better(cur,best))best=cur;}else{apply(y,x);++rejected;'
new = '''if(acc){cur=nxt;++accepted;if(trace){trace<<y;nb(y,z);for(auto v:z)if(bg(baseline_sel,v))trace<<' '<<v;trace<<'\\n';}if(better(cur,best))best=cur;}else{apply(y,x);++rejected;'''
if s.count(old) != 1:
    raise SystemExit(f"accepted trace assertion failed: {s.count(old)}")
s = s.replace(old, new)

Path(sys.argv[2]).write_text(s)
