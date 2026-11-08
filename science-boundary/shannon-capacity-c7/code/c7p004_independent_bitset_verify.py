#!/usr/bin/env python3
"""Independent 10D C7 strong-product certificate check by 5D prefix bitsets."""
import itertools,json,sys
from functools import lru_cache
from pathlib import Path

P=(2401,343,49,7,1)
def digits(v):
    return tuple((v//p)%7 for p in P)

@lru_cache(maxsize=None)
def neighbors(v):
    d=digits(v)
    return tuple(sum((d[i]+z[i])%7*P[i] for i in range(5))
                 for z in itertools.product((-1,0,1),repeat=5))

@lru_cache(maxsize=None)
def mask(v):
    return sum(1<<x for x in neighbors(v))

def verify(path):
    words=json.loads(Path(path).read_text())["points"]
    assert len(words)==len(set(words))
    assert all(isinstance(w,str) and len(w)==10 and set(w)<=set("0123456")
               for w in words)
    groups={}
    for word in words:
        a=int(word[:5],7);b=int(word[5:],7)
        groups.setdefault(a,[]).append(b)
    covers={};members={}
    for a,Z in groups.items():
        cover=0;member=0
        for z in Z:
            bit=1<<z
            assert not cover&bit,("same-prefix conflict",a,z)
            member|=bit
            cover|=mask(z)
        covers[a]=cover;members[a]=member
    for a,cover in covers.items():
        for b in neighbors(a):
            if b>a and b in members:
                assert not cover&members[b],("different-prefix conflict",a,b)
    return {"valid":True,"score":len(words),"prefix_groups":len(groups)}

if __name__=="__main__":
    print(json.dumps(verify(sys.argv[1]),sort_keys=True))
