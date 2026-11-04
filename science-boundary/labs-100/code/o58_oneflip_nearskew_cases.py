#!/usr/bin/env python3
"""Exact parity-DSU enumeration of O58 reachable from a near-skew N100 by one B flip."""
from collections import Counter

class DSU:
    def __init__(self,n):
        self.p=list(range(n));self.rank=[0]*n;self.parity=[0]*n
    def find(self,i):
        if self.p[i] == i:return i,0
        root,b=self.find(self.p[i]);self.parity[i]^=b;self.p[i]=root
        return root,self.parity[i]
    def unite(self,a,b,z):
        x,bx=self.find(a);y,by=self.find(b)
        if x==y:return (bx^by)==z
        if self.rank[x]<self.rank[y]:x,y=y,x;bx,by=by,bx
        self.p[y]=x;self.parity[y]=bx^by^z
        if self.rank[x]==self.rank[y]:self.rank[x]+=1
        return True

def generate():
    for j in range(50):
        buckets=[[] for _ in range(25)]
        for i in range(50):
            lag=(j-i) if i<=j else (i-j-1)
            buckets[min(lag,49-lag)].append(i)
        assert all(len(b)==2 for b in buckets)
        for h in range(25):
            d=DSU(51)
            for i in range(1,25):assert d.unite(i,50-i,0)
            valid=True
            for k,(a,b) in enumerate(buckets):
                if k==h:
                    valid=d.unite(50,a,0) and d.unite(50,b,0)
                else:valid=d.unite(a,b,1)
                if not valid:break
            if not valid:continue
            root,rb=d.find(50)
            components=sorted({d.find(i)[0] for i in range(51)})
            free=[v for v in components if v!=root]
            for mask in range(1<<len(free)):
                values={root:rb}
                values.update((v,(mask>>idx)&1) for idx,v in enumerate(free))
                A=[1 if not (values[d.find(i)[0]] ^ d.find(i)[1]) else -1 for i in range(50)]
                assert sum(A)==2
                yield j,h,A

if __name__=='__main__':
    count=0
    hist=Counter()
    for j,h,A in generate():
        print(j,h,''.join('+' if v==1 else '-' for v in A))
        count+=1
        hist[j]+=1
    import sys
    print('CASES',count,'per-j',dict(hist),file=sys.stderr)
    assert count==9352
