"""Audit LABS corpus and generate explicitly parent-derived near-skew diagnostics."""
from pathlib import Path
import itertools,csv,json
ROOT=Path(__file__).resolve().parent
def energy(bits):
 s=[1 if q=='1' else -1 for q in bits];n=len(s)
 return sum(sum(s[i]*s[i+k] for i in range(n-k))**2 for k in range(1,n))
def skew(a):
 m=len(a)//2
 return len(a)%2==1 and all(a[m+j] == (a[m-j] if j%2==0 else ('0' if a[m-j]=='1' else '1')) for j in range(1,m+1))
def nearskew(x):
 return skew(x) if len(x)%2 else skew(x[:-1]) or skew(x[1:])
def sym(x):
 def neg(t):return ''.join('0' if q=='1' else '1' for q in t)
 def alt(t):return ''.join(q if i%2==0 else ('0' if q=='1' else '1') for i,q in enumerate(t))
 return {q for base in (x,x[::-1]) for q in (base,neg(base),alt(base),neg(alt(base)))}
def canon(x):return min(sym(x))
rows=list(csv.DictReader((ROOT/'corpus.tsv').open(),delimiter='\t'))
refs=list(csv.DictReader((ROOT/'anchors_corpus.tsv').open(),delimiter='\t'))
for r in rows:
 assert energy(r['bits'])==int(r['energy'])
 assert (nearskew(r['bits']) == (r['near_skew']=='1'))
 assert canon(r['bits'])==r['canonical']
print('validated',len(rows),'rows')
for r in refs:
 x=r['bits'];n=len(x)
 if not nearskew(x):continue
 begin=0 if skew(x[:-1]) else (1 if n%2==0 else 0)
 m=(n-1)//2
 pairs=[(begin+m-j,begin+m+j) for j in range(1,m+1)]
 scored=[]
 for size in (1,2):
  for q in itertools.combinations(range(len(pairs)),size):
   y=list(x)
   for j in q:
    for i in pairs[j]: y[i]='0' if y[i]=='1' else '1'
   z=''.join(y)
   assert nearskew(z)
   scored.append((energy(z),z,tuple(q)))
 scored.sort()
 selected=[];seen={r['canonical']}
 for e,x,q in scored:
  can=canon(x)
  if can not in seen:
   selected.append(dict(n=str(n),energy=str(e),bits=x,provenance='near_skew_manifold',parent=r['parent'],seed='-1',near_skew='1',canonical=can))
   seen.add(can)
  if len(selected)>=8:break
 rows.extend(selected)
 print('n',n,'min one/two skew-group edit E',scored[0][0])
rows.sort(key=lambda x:(int(x['n']),int(x['energy']),x['provenance'],x['canonical']))
with (ROOT/'curated.tsv').open('w',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=['n','energy','bits','provenance','parent','seed','near_skew','canonical'],delimiter='\t')
 wr.writeheader();wr.writerows(rows)
summary={}
for n in sorted(set(int(r['n']) for r in rows)):
 sub=[r for r in rows if int(r['n'])==n]
 summary[str(n)]={'total':len(sub),'best':min(int(z['energy']) for z in sub),
 'min_generated':min([int(z['energy']) for z in sub if z['provenance']!='public_anchor'],default=None),
 'near_skew':sum(z['near_skew']=='1' for z in sub),
 'provenance':{p:sum(z['provenance']==p for z in sub)for p in set(z['provenance']for z in sub)}}
(ROOT/'curated_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
