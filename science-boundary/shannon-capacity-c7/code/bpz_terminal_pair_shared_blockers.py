#!/usr/bin/env python3
"""Audit the shared baseline-blocker interface of every omitted terminal-block pair."""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
LABELS=("B","N","A","D","O","H","V")
RECORD_CODE=(("B","B"),("N","O"),("A","H"),("D","V"),("O","N"),("H","D"),("V","A"))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
 base,_t,_e,ax=load_base(root/'data'/'base_c7.json');
 if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
 ring=base.ring;fam={'B':set(base.B.elements),'N':set(base.X0.elements),'A':set(base.XV.elements),'D':set(base.XH.elements),'O':set(base.R.elements),'H':set(base.PH.elements),'V':set(base.PV.elements)}
 owner={};owner_word=[]
 for w,(x,y) in enumerate(RECORD_CODE):
  for u in sorted(fam[x]):
   for v in sorted(fam[y]):owner[(u,v)]=len(owner_word);owner_word.append(x+y)
 if len(owner)!=134753:raise RuntimeError(('record',len(owner)))
 baseline=set(owner);nbm={lab:[None]*ring.n for lab in LABELS}
 for lab in LABELS:
  F=fam[lab]
  for z in range(ring.n):nbm[lab][z]=tuple(q for q in ring.NB[z] if q in F)
 blocks=[]
 for x in LABELS:
  for y in LABELS:
   if (x,y) in RECORD_CODE:continue
   S=[(u,v) for u in fam[x] for v in fam[y] if (u,v) not in baseline];bs=set()
   for u,v in S:
    for a0,b0 in RECORD_CODE:
     for q in nbm[a0][u]:
      for r in nbm[b0][v]:bs.add(owner[(q,r)])
   hist=Counter(owner_word[i] for i in bs);blocks.append({'word':x+y,'candidates':len(S),'blockers':bs,'blocker_count':len(bs),'blocker_words':dict(sorted(hist.items()))})
 pairs=[]
 for i in range(len(blocks)):
  for j in range(i+1,len(blocks)):
   L,R=blocks[i],blocks[j];sh=L['blockers']&R['blockers'];h=Counter(owner_word[k] for k in sh)
   pairs.append({'word1':L['word'],'word2':R['word'],'candidates1':L['candidates'],'candidates2':R['candidates'],'blockers1':L['blocker_count'],'blockers2':R['blocker_count'],'shared_blockers':len(sh),'shared_words':dict(sorted(h.items()))})
 pairs.sort(key=lambda r:(r['shared_blockers'],r['candidates1']+r['candidates2'],r['word1'],r['word2']))
 huge={'BN','NB','NN'};hp=[r for r in pairs if r['word1'] in huge or r['word2'] in huge]
 out={'method':'exact-terminal-pair-shared-blocker-interface','blocks':[dict((k,v) for k,v in b.items() if k!='blockers') for b in blocks],'pair_count':len(pairs),'zero_shared':sum(r['shared_blockers']==0 for r in pairs),'min_shared':pairs[0]['shared_blockers'],'max_shared':max(r['shared_blockers'] for r in pairs),'huge_pairs':hp,'smallest_pairs':pairs[:50]}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('blocks','huge_pairs','smallest_pairs')},sort_keys=True));print('huge_min',min((r['shared_blockers'] for r in hp),default=None),'huge_max',max((r['shared_blockers'] for r in hp),default=None))
if __name__=='__main__':main()
