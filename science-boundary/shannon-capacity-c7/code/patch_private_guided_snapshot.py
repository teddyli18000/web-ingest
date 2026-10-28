#!/usr/bin/env python3
"""Patch c7_10d_private_guided_walk.cpp to persist its final 134753 tie state.

The scientific walk logic is unchanged.  This patch only adds an optional
seventh argument FINAL_IDS and, on a no-breakthrough exit, writes the current
selected 134753 IDs there.  Exact byte assertions make source drift fail loudly.
Existing six-argument workflows remain untouched because they compile the
unpatched source.
"""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_private_guided_snapshot.py SOURCE OUTPUT")
src = Path(sys.argv[1]).read_text()

old1 = 'if(argc!=6){std::cerr<<"usage: c7_10d_private_guided_walk BASELINE_IDS RESULT_IDS STEPS SEED DOWN_RATE\\n";return 2;}'
new1 = 'if(argc!=6&&argc!=7){std::cerr<<"usage: c7_10d_private_guided_walk BASELINE_IDS RESULT_IDS STEPS SEED DOWN_RATE [FINAL_IDS]\\n";return 2;}'
if src.count(old1) != 1:
    raise SystemExit(f"argc patch assertion failed: {src.count(old1)}")
src = src.replace(old1, new1)

needle = ' std::cout<<"{\\\"kind\\\":\\\"none\\\",\\\"method\\\":\\\"heuristic-private-pair-guided-neutral1\\\"'
if src.count(needle) != 1:
    raise SystemExit(f"final-output patch assertion failed: {src.count(needle)}")
insert = ''' if(argc==7){
  std::ofstream snap(argv[6]);if(!snap)throw std::runtime_error("write final snapshot");
  std::uint64_t nsel=0;for(std::uint32_t v=0;v<N;++v)if(bg(sel,v)){snap<<v<<'\\n';++nsel;}
  if(nsel!=134753)throw std::runtime_error("final snapshot size");
 }
'''
src = src.replace(needle, insert + needle)
Path(sys.argv[2]).write_text(src)
