#!/usr/bin/env python3
"""Apply exact early canonical-anchor pruning to search_net2_r6_c3_anchor.cpp.

The base solver assigns each final six-owner set U to its lexicographically
smallest observed exact c3 support A contained in U, but checks this only after
three owner expansions.  If a partial 4- or 5-owner set already contains an
observed c3 support B<A, every later superset also contains B, so the current A
can never be canonical.  Pruning such a branch is therefore exact and changes
only work, not the searched owner-six family.

All edits are byte-asserted against the durable source and fail loudly on drift.
"""
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_r6_c3_early_anchor.py SOURCE OUTPUT")
s = Path(sys.argv[1]).read_text()

needle = ''' auto canonical_order=[&](const Key&A,const Key&U,std::array<std::uint32_t,3>&ord){'''
if s.count(needle) != 1:
    raise SystemExit(f"canonical anchor insertion point drift: {s.count(needle)}")
insert = ''' auto has_smaller_anchor=[&](const std::vector<std::uint32_t>&owners,const Key&A){
  const unsigned n=owners.size();
  for(unsigned i=0;i<n;++i)for(unsigned j=i+1;j<n;++j)for(unsigned k=j+1;k<n;++k){
   Key B{};B.a[0]=owners[i];B.a[1]=owners[j];B.a[2]=owners[k];
   if(B<A&&idx.find(B)!=idx.end())return true;
  }
  return false;
 };
'''
s = s.replace(needle, insert + needle)

old4 = '''for(auto x:xs){if(found.load(std::memory_order_relaxed))break;++level1;auto c4=ao;c4.push_back(x);std::sort(c4.begin(),c4.end());auto ys=neigh(c4);'''
new4 = '''for(auto x:xs){if(found.load(std::memory_order_relaxed))break;++level1;auto c4=ao;c4.push_back(x);std::sort(c4.begin(),c4.end());if(has_smaller_anchor(c4,A))continue;auto ys=neigh(c4);'''
if s.count(old4) != 1:
    raise SystemExit(f"c4 prune point drift: {s.count(old4)}")
s = s.replace(old4, new4)

old5 = '''auto c5=c4;c5.push_back(y);std::sort(c5.begin(),c5.end());if(std::adjacent_find(c5.begin(),c5.end())!=c5.end())continue;auto zs=neigh(c5);'''
new5 = '''auto c5=c4;c5.push_back(y);std::sort(c5.begin(),c5.end());if(std::adjacent_find(c5.begin(),c5.end())!=c5.end())continue;if(has_smaller_anchor(c5,A))continue;auto zs=neigh(c5);'''
if s.count(old5) != 1:
    raise SystemExit(f"c5 prune point drift: {s.count(old5)}")
s = s.replace(old5, new5)

Path(sys.argv[2]).write_text(s)
