#!/usr/bin/env python3
"""Exact cost/orbit analysis for every known public 32-AND AES core.

This is a corrected standalone v2. 256-point boundary signals are first collapsed
to functions of a chosen 4-wire core basis. Linear coordinates are then solved
against canonical 16-state variables, not against the original 256-state basis.
"""
import collections, itertools, json, urllib.request

ROOT='https://raw.githubusercontent.com/ahrazzle/gf2m-circuits/main/'
FILES=[
 'sbox/circuits/sbox106_d34.json','sbox/circuits/sbox110_d38.json',
 'sbox/circuits/invsbox109_d30.json','sbox/circuits/invsbox109_d31.json',
 'sbox/prior/aes-sbox-a32-ad5-g110-gd22-xx78-3.json',
 'sbox/prior/SLP_AES_113.json',
 'sbox/prior/aes-invsbox-a32-ad5-g112-gd26-xx80-9.json',
]
MASK256=(1<<256)-1

def fetch(path):
 with urllib.request.urlopen(ROOT+path,timeout=30) as r:return json.load(r)

def opv(op,a,b,mask):
 if op=='XOR':return a^b
 if op=='XNOR':return (~(a^b))&mask
 if op=='AND':return a&b
 raise ValueError(op)

def rank(xs):
 piv=[]
 for x in xs:
  y=x
  for p in piv:y=min(y,y^p)
  if y:piv.append(y);piv.sort(reverse=True)
 return len(piv)

def v16(i):
 t=0
 for x in range(16):
  if (x>>i)&1:t|=1<<x
 return t
CANON=[v16(i) for i in range(4)]

def coord16(tt):
 for m in range(16):
  z=0
  for i,b in enumerate(CANON):
   if (m>>i)&1:z^=b
  if z==tt:return m
 return None

def eval256(c):
 vals=[];supports=[]
 for i in range(8):
  t=0
  for x in range(256):
   if (x>>(7-i))&1:t|=1<<x
  vals.append(t);supports.append(frozenset())
 for gi,(op,a,b) in enumerate(c['gates']):
  vals.append(opv(op,vals[a],vals[b],MASK256))
  s=set(supports[a])|set(supports[b])
  if op=='AND':s.add(gi)
  supports.append(frozenset(s))
 return vals,supports

def classify(c,supports):
 first=[];core=[];final=[]
 for gi,(op,a,b) in enumerate(c['gates']):
  if op!='AND':continue
  sa,sb=supports[a],supports[b]
  if not sa and not sb:first.append(gi)
  elif sa and sb:core.append(gi)
  else:final.append(gi)
 return first,core,final

def factor_cone(c,supports,core,factors):
 core_set=set(core);gates=set();boundary=set()
 def visit(s):
  if not (set(supports[s])&core_set):boundary.add(s);return
  assert s>=8
  gi=s-8
  if gi in gates:return
  gates.add(gi);_,a,b=c['gates'][gi];visit(a);visit(b)
 for s in factors:visit(s)
 return sorted(gates),sorted(boundary)

def choose_basis(signals,vals):
 out=[]
 for s in signals:
  if rank([vals[x] for x in out+[s]])>len(out):out.append(s)
  if len(out)==4:return out
 return out

def collapse16(tt,basis_tts):
 seen={}
 for x in range(256):
  p=0
  for i,b in enumerate(basis_tts):p|=((b>>x)&1)<<i
  y=(tt>>x)&1
  if p in seen and seen[p]!=y:return None
  seen[p]=y
 if len(seen)!=16:return None
 out=0
 for p,y in seen.items():out|=y<<p
 return out

def min_xors(target_masks,start=(1,2,4,8)):
 goals=set(target_masks);st=sum(1<<m for m in start if m)
 gb=sum(1<<m for m in goals if m)
 if (st&gb)==gb:return 0
 q=collections.deque([(st,0)]);seen={st}
 while q:
  s,d=q.popleft();av=[m for m in range(1,16) if (s>>m)&1]
  for i,a in enumerate(av):
   for b in av[i+1:]:
    z=a^b
    if z==0 or (s>>z)&1:continue
    ns=s|(1<<z)
    if (ns&gb)==gb:return d+1
    if ns not in seen:seen.add(ns);q.append((ns,d+1))
 raise RuntimeError

def gl4():
 for rows in itertools.permutations(range(1,16),4):
  if rank(rows)==4:yield rows

def transform(tt,rows):
 out=0
 for x in range(16):
  y=0
  for i,r in enumerate(rows):y|=((r&x).bit_count()&1)<<i
  out|=((tt>>y)&1)<<x
 return out

def current_targets():
 a,b,c,d=CANON
 w42=a&b;w43=w42^c;w44=w43&d;w45=b^w44;w46=w42&c;w47=d^w46
 w48=a&w47;w49=w43^w48;w50=w48^b;w51=w49&w50;w52=w51^a;w53=w52^w49
 w54=w45&w53;w55=w54^w47;w56=w55^w49;w57=w53^w45;w58=w56^w57;w59=w55^w45
 return [w45,w59,w52,w57,w53,w49,w58,w55,w56]
CUR=set(current_targets())

def analyze(path):
 c=fetch(path);vals,supp=eval256(c);first,core,final=classify(c,supp)
 rec={'file':path,'gates':len(c['gates']),'ands':sum(g[0]=='AND' for g in c['gates']),
      'and_layers':[len(first),len(core),len(final)]}
 if (len(first),len(core),len(final))!=(9,5,18):rec['error']='not 9+5+18';return rec
 fs=[]
 for gi in final:
  _,a,b=c['gates'][gi];s=a if supp[a] else b
  if s not in fs:fs.append(s)
 if len(fs)!=9:rec['error']=f'{len(fs)} unique factors';return rec
 cone,boundary=factor_cone(c,supp,core,fs);basis=choose_basis(boundary,vals)
 if len(basis)!=4:rec['error']='boundary rank !=4';return rec
 btts=[vals[x] for x in basis]
 b16=[collapse16(vals[s],btts) for s in boundary];f16=[collapse16(vals[s],btts) for s in fs]
 if any(x is None for x in b16+f16):rec['error']='collapse failed';return rec
 bm=[coord16(x) for x in b16]
 if any(x is None for x in bm):rec['error']='nonlinear boundary';rec['boundary16']=[hex(x) for x in b16];return rec
 extra=min_xors(bm);ops=collections.Counter(c['gates'][gi][0] for gi in cone)
 exact=[];best=0;hist={}
 for rows in gl4():
  hit=len({transform(t,rows) for t in f16}&CUR);hist[hit]=hist.get(hit,0)+1;best=max(best,hit)
  if {transform(t,rows) for t in f16}==CUR:exact.append(rows)
 rec.update({'factor_signals':fs,'cone_gates':cone,'cone_gate_count':len(cone),'cone_ops':dict(ops),
             'boundary':boundary,'basis':basis,'boundary_masks':bm,'boundary_extra_xors':extra,
             'released_factor_cost':len(cone)+extra,'exact_gl_count':len(exact),'exact_gl_maps':exact,
             'max_overlap':best,'overlap_hist':hist})
 return rec

def main():
 print(json.dumps([analyze(p) for p in FILES],indent=2,sort_keys=True))
if __name__=='__main__':main()
