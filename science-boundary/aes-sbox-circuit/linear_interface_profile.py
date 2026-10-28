#!/usr/bin/env python3
import itertools, json, urllib.request

MASK=(1<<256)-1
SRC='https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/fancify/aes103-joint-plane-orientations/certificate.json'

def fetch():
    with urllib.request.urlopen(SRC,timeout=30) as r:return json.load(r)
def inp():
    d={}
    for b in range(8):
        v=0
        for x in range(256):
            if (x>>b)&1:v|=1<<x
        d[f'x{b}']=v
    return d
def ev(op,a,b):
    if op=='XOR':return a^b
    if op=='XNOR':return (~(a^b))&MASK
    return a&b
def evaluate(c):
    v=inp()
    for g in c['gates']:v[g['out']]=ev(g['op'],v[g['a']],v[g['b']])
    return v
def external(c,lo,hi):
    made={g['out'] for g in c['gates'][lo:hi]}; out=[]; seen=set()
    for g in c['gates'][lo:hi]:
        for w in (g['a'],g['b']):
            if w not in made and w not in seen:seen.add(w);out.append(w)
    return out
def rank(xs):
    p=[]
    for x in xs:
        y=x
        for q in p:y=min(y,y^q)
        if y:p.append(y);p.sort(reverse=True)
    return len(p)

def main():
    c=fetch(); vals=evaluate(c)
    ext=external(c,26,42)
    core=['w35','w33','w38','w41']
    assert len(ext)==15 and rank([vals[w] for w in core])==4
    # Enumerate every XOR of the 15 external cut wires and retain minimum Hamming-weight representation.
    best={0:(0,0)}
    cur=0; prev_gray=0
    for n in range(1,1<<len(ext)):
        gray=n^(n>>1); diff=gray^prev_gray; i=(diff & -diff).bit_length()-1
        cur ^= vals[ext[i]]; prev_gray=gray
        wt=gray.bit_count()
        old=best.get(cur)
        if old is None or wt<old[0]:best[cur]=(wt,gray)
    # Enumerate the 4D target subspace and label each function by a 4-bit coefficient mask.
    U={}
    for m in range(16):
        t=0
        for i,w in enumerate(core):
            if (m>>i)&1:t^=vals[w]
        U[m]=t
    rows=[]
    for m in range(1,16):
        t=U[m]; wt,em=best.get(t,(999,None))
        rep=[] if em is None else [ext[i] for i in range(15) if (em>>i)&1]
        rows.append((m,wt,rep))
        print(f'U[{m:04b}] min_external_weight={wt} rep={rep}')
    # Find independent bases with lowest no-sharing XOR-tree upper bound sum(w-1).
    cand=[]
    for ms in itertools.combinations(range(1,16),4):
        if rank(ms)!=4:continue  # coefficient masks are 4-bit vectors
        ws=[best[U[m]][0] for m in ms]
        cost=sum(max(0,w-1) for w in ws)
        cand.append((cost,sum(ws),ms,ws))
    cand.sort()
    print('\nTop independent bases by separate-tree bound:')
    for row in cand[:25]:print(row)
    # Identify current and supplementary interface masks in the primary basis.
    current=(1,2,4,8)
    mixed=(1^2,2,1^4^8,8)  # g34,g39,g37,g41
    def desc(name,ms):
        ws=[best[U[m]][0] for m in ms]
        print(name,'masks=',[f'{m:04b}' for m in ms],'weights=',ws,'separate_cost=',sum(w-1 for w in ws))
    print();desc('current',current);desc('mixed',mixed)
    # Rank reached by cheap U elements.
    for k in range(1,9):
        cheap=[m for m in range(1,16) if best[U[m]][0]<=k]
        print('weight<=',k,'count=',len(cheap),'coefficient_rank=',rank(cheap),'masks=',[f'{m:04b}' for m in cheap])

if __name__=='__main__':main()
