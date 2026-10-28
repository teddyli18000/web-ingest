#!/usr/bin/env python3
"""Exact radius<=3 repair over BPZ-X signed-coordinate t=10 two-hit basins.

The full signed-coordinate orbit scan found 50 image/obstruction cases whose
best translated overlap with a valid t=10 obstruction is exactly two.  After
forced deletion of those two hits, L has size 365.  Any repair reaching 366
already gives a 134769-point C7^10 construction.

For every assigned signed image and every exact two-hit translated alignment,
this program exhausts:
  r=0: add one support-zero vertex;
  r=1: remove <=1 owner, add two compatible vertices;
  r=2: remove <=2 owners, add three compatible vertices;
  r=3: remove <=3 owners, add four compatible vertices.
Candidate pools are exact support-subset pools.  Owner sets are generated from
all realized support masks and singleton combinations, so no sparsity
assumption from the identity BPZ-X alignment is required.
"""
import argparse,json,sys
from itertools import combinations,permutations
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def support_groups(retained,Dset,ring,maxr=3):
    supp=[0]*t10.U
    for i,u in enumerate(retained):
        bit=1<<i
        for v in ring.NB[u]: supp[v]|=bit
    groups={}; rset=set(retained)
    for v in range(t10.U):
        if v in Dset or v in rset: continue
        s=supp[v]; bc=s.bit_count()
        if bc<=maxr: groups.setdefault(s,[]).append(v)
    return groups


def pool_for(T,groups):
    out=[]; sub=T
    while sub:
        out.extend(groups.get(sub,())); sub=(sub-1)&T
    return sorted(set(out))


def find_independent(pool,digits,need):
    chosen=[]
    def dfs(start):
        if len(chosen)==need: return list(chosen)
        if len(pool)-start < need-len(chosen): return None
        for i in range(start,len(pool)):
            v=pool[i]
            if any(t10.conflict(v,u,digits) for u in chosen): continue
            chosen.append(v); z=dfs(i+1)
            if z is not None: return z
            chosen.pop()
        return None
    return dfs(0)


def owners_of(add,retained,digits):
    own=set()
    for v in add:
        for i,u in enumerate(retained):
            if t10.conflict(v,u,digits): own.add(i)
    return own


def owner_sets(groups,r,nowners):
    singles=sorted(m for m in groups if m and m.bit_count()==1)
    if r==1: return set(singles)
    if r==2:
        out={m for m in groups if m.bit_count()==2}
        for a,b in combinations(singles,2): out.add(a|b)
        return out
    if r==3:
        out={m for m in groups if m.bit_count()==3}
        doubles=[m for m in groups if m.bit_count()==2]
        for d in doubles:
            for i in range(nowners):
                b=1<<i
                if not (d&b): out.add(d|b)
        for a,b,c in combinations(singles,3): out.add(a|b|c)
        return out
    raise ValueError(r)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path)
    ap.add_argument('--shard',type=int,default=0); ap.add_argument('--shards',type=int,default=1)
    args=ap.parse_args()
    if args.shards<1 or not 0<=args.shard<args.shards: raise SystemExit('bad shard')
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    obs,ostats=t10.obstruction_witnesses(I0,ring,digits,nb); Fobs=[(m,w,np.fft.fftn(t10.arr(t10.values(m),digits))) for m,w in obs.items()]

    images={}
    for perm in permutations(range(t10.D)):
        for negmask in range(1<<t10.D):
            S=frozenset(t10.enc(tuple(((-digits[v][perm[j]])%t10.Q if ((negmask>>j)&1) else digits[v][perm[j]]) for j in range(t10.D))) for v in X0)
            images.setdefault(S,(perm,negmask))
    if len(images)!=3840: raise RuntimeError(f'signed orbit drift {len(images)}')

    seen=set(); min2_cases=0; alignments=0; stats={str(r):{'owner_sets':0,'eligible_pools':0,'max_pool':0} for r in range(4)}; winner=None; per=[]
    for ii,(Sfro,meta) in enumerate(images.items()):
        if ii%args.shards != args.shard: continue
        S=set(Sfro); perm,negmask=meta; FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=2: continue
            min2_cases+=1; Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==2):
                tr=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    Xfull=set(t10.shift_set(S,tr,digits,sign)); hits=Xfull&Dset
                    if len(hits)!=2: continue
                    key=(mask,tuple(sorted(Xfull)))
                    if key in seen: continue
                    seen.add(key); alignments+=1
                    retained=sorted(Xfull-Dset)
                    if len(retained)!=365 or not t10.independent(retained,digits): raise RuntimeError('retained replay failed')
                    groups=support_groups(retained,Dset,ring,3)
                    free=groups.get(0,[])
                    local={'image':ii,'perm':list(perm),'negmask':negmask,'obstruction_index':oi,'translation':list(tr),'sign':sign,'free':len(free)}
                    if free:
                        add=[free[0]]; owner=set(); winner=(retained,add,owner,w,mask,local); break
                    for r in (1,2,3):
                        O=owner_sets(groups,r,len(retained)); local[f'r{r}_owner_sets']=len(O); stats[str(r)]['owner_sets']+=len(O)
                        localmax=localeligible=0
                        for T in O:
                            p=pool_for(T,groups); localmax=max(localmax,len(p)); stats[str(r)]['max_pool']=max(stats[str(r)]['max_pool'],len(p))
                            if len(p)<r+1: continue
                            localeligible+=1; stats[str(r)]['eligible_pools']+=1
                            add=find_independent(p,digits,r+1)
                            if add is None: continue
                            own=owners_of(add,retained,digits)
                            if len(own)>r: raise RuntimeError('owner replay drift')
                            winner=(retained,add,own,w,mask,local); break
                        local[f'r{r}_eligible']=localeligible; local[f'r{r}_max_pool']=localmax
                        if winner: break
                    per.append(local); print('ALIGN_DONE',json.dumps(local,sort_keys=True),flush=True)
                    if winner: break
                if winner: break
            if winner: break
        if winner: break
        if ii%128==args.shard: print('PROGRESS',json.dumps({'image':ii,'min2_cases':min2_cases,'alignments':alignments},sort_keys=True),flush=True)

    status={'method':'bpz-t10-signed-two-hit-exact-radius0-3','candidate':winner is not None,'score':t10.BASELINE if winner is None else None,'shard':args.shard,'shards':args.shards,'distinct_signed_images':len(images),'min2_image_obstruction_cases':min2_cases,'two_hit_alignments':alignments,'radius_stats':stats,'alignment_summaries':per,'obstruction_stats':ostats}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=t10.BASELINE; args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    retained,add,own,w,mask,local=winner; X=(set(retained)-{retained[i] for i in own})|set(add)
    if len(X)<366 or X&set(t10.values(mask)) or not t10.independent(X,digits): raise RuntimeError(f'winner replay failed size={len(X)}')
    Ibits,pairs,o,PH,PV=w; pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring); score=len(pts)
    if score<=t10.BASELINE: raise RuntimeError(f'not a breakthrough {score}')
    status.update({'score':score,'winning_alignment':local,'actual_removed_owners':sorted(own),'added_auxiliary_points':add,'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
