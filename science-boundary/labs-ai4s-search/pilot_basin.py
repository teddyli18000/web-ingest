"""Small exact-cost basin-lookahead diagnostic. Python 3 standard library only."""
import argparse,json,random,time

def energy(s):
    n=len(s)
    return sum(sum(s[i]*s[i+k] for i in range(n-k))**2 for k in range(1,n))

def flip(s,positions):
    t=s.copy()
    for j in positions:t[j]=-t[j]
    return t

def relax(s):
    e=energy(s);calls=1
    while True:
        best=e;pos=-1
        for i in range(len(s)):
            z=energy(flip(s,[i]));calls+=1
            if z<best:best=z;pos=i
        if pos<0:return s,e,calls
        s=flip(s,[pos]);e=best

def run(n,seed,method,rounds,probes):
    r=random.Random(seed)
    s=[r.choice([-1,1]) for _ in range(n)]
    s,e,calls=relax(s);best=e
    for _ in range(rounds):
        pairs=set()
        while len(pairs)<probes:
            a,b=r.sample(range(n),2)
            pairs.add(tuple(sorted((a,b))))
        options=[]
        for pair in sorted(pairs):
            perturbed=flip(s,pair)
            immediate=energy(perturbed);calls+=1
            t,et,c=relax(perturbed);calls+=c
            options.append((et,t,immediate))
        if method=="post-relax":
            e,s,_=min(options,key=lambda x:x[0])
        elif method=="immediate":
            e,s,_=min(options,key=lambda x:x[2])
        else:
            e,s,_=options[r.randrange(len(options))]
        best=min(best,e)
    return dict(n=n,seed=seed,method=method,best=best,calls=calls)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=12)
    p.add_argument("--rounds",type=int,default=3)
    p.add_argument("--probes",type=int,default=8)
    p.add_argument("--lengths",type=int,nargs="+",default=[24,32])
    a=p.parse_args()
    t=time.monotonic();rows=[]
    for n in a.lengths:
        for seed in range(a.seeds):
            for method in ("random","immediate","post-relax"):
                rows.append(run(n,seed,method,a.rounds,a.probes))
    print(json.dumps(dict(config=vars(a),elapsed_seconds=round(time.monotonic()-t,3),rows=rows),indent=2))
if __name__=="__main__":main()
