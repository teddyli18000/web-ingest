#!/usr/bin/env python3
"""Patch the exact unrestricted r2 net+2 solver into a net+1 solver.

The resulting C++ program searches, in order, for:
  * add 1 coverage-zero vertex;
  * remove 1 / add 2 compatible coverage-one vertices with the same owner;
  * remove 2 / add 3 independent vertices from the complete two-owner pool.

The owner/support recovery and complete owner-pair enumeration are inherited
unchanged from search_net2_r2.cpp.  This is useful for moving a 134752 seed to
a different 134753 plateau point before asking for a second +1 improvement.
"""
import sys
from pathlib import Path

if len(sys.argv)!=3:
    raise SystemExit('usage: patch_search_net2_r2_net1.py INPUT OUTPUT')
s=Path(sys.argv[1]).read_text()

# Replace the local exact independent-4 helper by independent-3.
a=s.index('bool find4(')
b=s.index('\n}\n\nint main',a)
helper=r'''bool find3(const std::vector<std::uint32_t>&supp,std::array<std::uint32_t,3>&out){
 for(std::size_t i=0;i<supp.size();++i)for(std::size_t j=i+1;j<supp.size();++j){if(conflict(supp[i],supp[j]))continue;
  for(std::size_t k=j+1;k<supp.size();++k)if(!conflict(supp[i],supp[k])&&!conflict(supp[j],supp[k])){out={supp[i],supp[j],supp[k]};return true;}
 }
 return false;
}'''
s=s[:a]+helper+s[b:]

anchor=' // Direct +2 settles support-union size zero.\n'
if s.count(anchor)!=1: raise SystemExit('direct anchor drift')
s=s.replace(anchor,''' // Direct +1 settles support-union size zero.\n if(!freev.empty()){std::cout<<"{\\"kind\\":\\"add1\\",\\"method\\":\\"exact-unrestricted-r2-net1\\",\\"baseline_size\\":"<<base.size()<<",\\"coverage0\\":"<<freev.size()<<",\\"add\\":["<<freev[0]<<"]}\\n";return 0;}\n // The old direct +2 check is now unreachable but retained as an independent replay.\n''',1)

# Replace the radius-one net+2 check with the exact net+1 condition.
ra=s.index(' // Before radius two, settle support-union size one exactly.')
rb=s.index('\n\n std::unordered_set<std::uint64_t>done;',ra)
r1=r''' // Before radius two, settle support-union size one exactly: two
 // compatible coverage-one vertices with the same owner give remove1/add2.
 for(std::uint32_t a=0;a<g1.size();++a){auto &g=g1[a];if(g.size()<2)continue;for(std::size_t i=0;i<g.size();++i)for(std::size_t j=i+1;j<g.size();++j)if(!conflict(g[i],g[j])){std::cout<<"{\"kind\":\"replace1add2\",\"method\":\"exact-unrestricted-r2-net1\",\"baseline_size\":"<<base.size()<<",\"coverage0\":"<<freev.size()<<",\"coverage1\":"<<c1ids.size()<<",\"remove\":["<<base[a]<<"],\"add\":["<<g[i]<<','<<g[j]<<"]}\n";return 0;}}'''
s=s[:ra]+r1+s[rb:]

s=s.replace('std::array<std::uint32_t,4>add{};','std::array<std::uint32_t,3>add{};',1)
old='if(find4(supp,freev,add)){std::cout<<"{\\"kind\\":\\"replace2add4\\",\\"method\\":\\"exact-unrestricted-r2-net2\\",\\"baseline_size\\":"<<base.size()<<",\\"coverage0\\":"<<freev.size()<<",\\"coverage1\\":"<<c1ids.size()<<",\\"coverage2\\":"<<c2ids.size()<<",\\"remove\\":["<<base[x]<<\',\'<<base[y]<<"],\\"add\\":["<<add[0]<<\',\'<<add[1]<<\',\'<<add[2]<<\',\'<<add[3]<<"]}\\n";return true;}'
new='if(find3(supp,add)){std::cout<<"{\\"kind\\":\\"replace2add3\\",\\"method\\":\\"exact-unrestricted-r2-net1\\",\\"baseline_size\\":"<<base.size()<<",\\"coverage0\\":"<<freev.size()<<",\\"coverage1\\":"<<c1ids.size()<<",\\"coverage2\\":"<<c2ids.size()<<",\\"remove\\":["<<base[x]<<\',\'<<base[y]<<"],\\"add\\":["<<add[0]<<\',\'<<add[1]<<\',\'<<add[2]<<"]}\\n";return true;}'
if old not in s: raise SystemExit('check_pair witness anchor drift')
s=s.replace(old,new,1)
s=s.replace('"exact-unrestricted-r2-net2"','"exact-unrestricted-r2-net1"')
Path(sys.argv[2]).write_text(s)
print('patched exact net+1 through radius2')
