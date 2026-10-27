#!/usr/bin/env python3
"""Scan all zero-translation signed coordinate permutations of BPZ 367-sets.

For every one of 5! * 2^5 = 3840 monomial automorphisms of C7^5, apply it to
both published BPZ independent sets X and I0 as candidate auxiliary sets.  Test
against all 160 distinct t=9 obstruction masks arising from the complete
243-state private-swap component of the main I.  Any zero hit gives a valid
Definition-2 t=9 gadget and a 134770-point C7^10 construction.
"""
import argparse,json,sys
from itertools import combinations,permutations,product
from pathlib import Path
Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T;POW=(1,7,49,343,2401)

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def values(bits):
    while bits:z=bits&-bits;yield z.bit_length()-1;bits^=z

def priv(bits,nb):
    out=[]
    for q in range(U):
        if (bits>>q)&1:continue
        h=nb[q]&bits
        if h.bit_count()==1:out.append((h.bit_length()-1,q))
    return sorted(out)
def icomp(start,nb):
    seen={start};front=[start];pm={}
    while front:
        nxt=[]
        for b in front:
            pp=priv(b,nb);pm[b]=pp
            for a,q in pp:
                c=b^(1<<a)^(1<<q)
                if c not in seen:seen.add(c);nxt.append(c)
        front=nxt
    return seen,pm
def obs_witnesses(start,nb,ring,d):
    comp,pm=icomp(start,nb)
    if len(comp)!=243:raise RuntimeError(f'I component drift {len(comp)}')
    obs={};ss=0
    for ib in comp:
        pp=pm[ib]
        if len({a for a,q in pp})<T:continue
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T:continue
            for o in product((0,1),repeat=T):
                PH=[q if s else a for (a,q),s in zip(pairs,o)];PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,d) or not independent(PV,d):continue
                ss+=1;mask=sum(1<<z for z in (ring.nbhd(set(PH))&ring.nbhd(set(PV))));obs.setdefault(mask,(ib,pairs,o,PH,PV))
    if ss!=640 or len(obs)!=160:raise RuntimeError(f'obstruction drift ss={ss} unique={len(obs)}')
    return obs

def transform(v,p,s,d):
    w=d[v];return sum(((w[p[j]] if s[j]==1 else -w[p[j]])%Q)*POW[j] for j in range(D))
def build(Ibits,Xbits,pairs,PH,PV,ring):
    I=set(values(Ibits));X=set(values(Xbits));R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('winner still double-hits')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']));ring=Ring(D);d=tuple(ring.decode(v) for v in range(U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    if not independent(I0,d) or not independent(X0,d):raise RuntimeError('base drift')
    obs=obs_witnesses(sum(1<<z for z in I0),nb,ring,d);seeds={'X':sorted(X0),'I0':sorted(I0)};checks=0;cases=0;winner=None;best=None;hist={}
    for seed_name,seed in seeds.items():
        for p in permutations(range(D)):
            for signs in product((1,-1),repeat=D):
                cases+=1;bits=0
                for x in seed:bits|=1<<transform(x,p,signs,d)
                if bits.bit_count()!=N:raise RuntimeError('automorphism collision')
                local=10**9;localw=None
                for dm,w in obs.items():
                    checks+=1;bad=(bits&dm).bit_count()
                    if bad<local:local=bad;localw=w
                    if bad==0:winner=(seed_name,p,signs,bits,w);break
                hist[str(local)]=hist.get(str(local),0)+1
                rec={'seed':seed_name,'perm':list(p),'signs':list(signs),'double_hits':local}
                if best is None or local<best['double_hits']:best=rec
                if winner:break
            if winner:break
        if winner:break
    status={'method':'bpz-t9-exact-aux-signed-coordinate-permutations','candidate':winner is not None,'automorphisms_per_seed':3840,'seeds':list(seeds),'cases_tested':cases,'obstruction_checks':checks,'unique_obstruction_masks':len(obs),'best':best,'min_hit_histogram':hist};args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    seed,p,signs,Xbits,w=winner;Ibits,pairs,o,PH,PV=w;pts,xp=build(Ibits,Xbits,pairs,PH,PV,ring);status.update({'score':len(pts),'winning_seed':seed,'winning_perm':list(p),'winning_signs':list(signs),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
