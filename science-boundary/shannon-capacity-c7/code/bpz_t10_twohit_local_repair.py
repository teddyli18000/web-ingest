#!/usr/bin/env python3
"""Exact local +1 repair through remove-2/add-3 for all BPZ t=10 two-hit alignments.

After deleting the two forced obstruction hits from a translated 367-set we
have an allowed independent retained set L of size 365.  To recover |X|=366 we
seek, exhaustively:

  remove 0 / add 1,
  remove 1 / add 2,
  remove 2 / add 3.

For every allowed outside vertex v, its owner support S(v) is the subset of L
confusable with v.  A repair removing owner set R may use exactly the vertices
with S(v) subset R.  This makes the radius-2 search finite and exhaustive.
"""
import argparse,json,sys
from itertools import combinations
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def compatible(a,b,digits): return not t10.conflict(a,b,digits)

def find_pair(pool,digits):
    for i,a in enumerate(pool):
        for b in pool[i+1:]:
            if compatible(a,b,digits): return [a,b]
    return None

def find_triple(pool,digits):
    n=len(pool)
    for i in range(n):
        a=pool[i]
        for j in range(i+1,n):
            b=pool[j]
            if not compatible(a,b,digits): continue
            for k in range(j+1,n):
                c=pool[k]
                if compatible(a,c,digits) and compatible(b,c,digits): return [a,b,c]
    return None

def support_groups(retained,Dset,ring):
    owners={v:i for i,v in enumerate(retained)}
    supp=[0]*t10.U
    for i,u in enumerate(retained):
        bit=1<<i
        for v in ring.NB[u]: supp[v]|=bit
    groups={}
    rset=set(retained)
    for v in range(t10.U):
        if v in Dset or v in rset: continue
        s=supp[v]
        if s.bit_count()<=2: groups.setdefault(s,[]).append(v)
    return groups

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    obs,ostats=t10.obstruction_witnesses(I0,ring,digits,nb); fam=json.loads((args.family_root/'data'/'family-f.json').read_text()); states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    Fobs=[(mask,w,np.fft.fftn(t10.arr(t10.values(mask),digits))) for mask,w in obs.items()]
    alignments=0; replays=0; tested=0; winner=None; stats={'r0':0,'r1_owner_sets':0,'r2_owner_sets':0,'max_pool_r1':0,'max_pool_r2':0}
    seen_align=set()
    for name,S in seeds:
        FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=2: continue
            Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==2):
                tr=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    Xfull=set(t10.shift_set(S,tr,digits,sign)); hits=Xfull&Dset; replays+=1
                    if len(hits)!=2: continue
                    key=(name,oi,tuple(sorted(Xfull)))
                    if key in seen_align: continue
                    seen_align.add(key); alignments+=1
                    retained=sorted(Xfull-Dset)
                    if len(retained)!=365 or not t10.independent(retained,digits): raise RuntimeError('retained replay failed')
                    groups=support_groups(retained,Dset,ring); tested+=1
                    # r=0
                    if groups.get(0):
                        add=[groups[0][0]]; rem=[]; method='remove0-add1'; stats['r0']+=1
                        winner=(name,oi,tr,sign,retained,rem,add,w,mask,method); break
                    # r=1
                    found=None
                    for a in range(len(retained)):
                        pool=list(groups.get(1<<a,()))
                        stats['r1_owner_sets']+=1; stats['max_pool_r1']=max(stats['max_pool_r1'],len(pool))
                        z=find_pair(pool,digits)
                        if z is not None: found=([a],z,'remove1-add2'); break
                    if found is not None:
                        remidx,add,method=found; winner=(name,oi,tr,sign,retained,remidx,add,w,mask,method); break
                    # r=2: pool contains single-owner groups and exact double-owner group.
                    for a in range(len(retained)):
                        ga=groups.get(1<<a,())
                        for b in range(a+1,len(retained)):
                            pool=list(ga); pool.extend(groups.get(1<<b,())); pool.extend(groups.get((1<<a)|(1<<b),()))
                            if len(pool)<3: continue
                            stats['r2_owner_sets']+=1; stats['max_pool_r2']=max(stats['max_pool_r2'],len(pool))
                            z=find_triple(pool,digits)
                            if z is not None:
                                found=([a,b],z,'remove2-add3'); break
                        if found is not None: break
                    if found is not None:
                        remidx,add,method=found; winner=(name,oi,tr,sign,retained,remidx,add,w,mask,method); break
                if winner: break
            if winner: break
        if winner: break

    status={'method':'bpz-t10-two-hit-exact-local-plus1-through-r2','candidate':winner is not None,'score':134753 if winner is None else 134769,'obstruction_stats':ostats,'two_hit_alignments':alignments,'explicit_replays':replays,'alignments_locally_tested':tested,'search_stats':stats}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    name,oi,tr,sign,retained,remidx,add,w,mask,method=winner; rem={retained[i] for i in remidx}; X=(set(retained)-rem)|set(add)
    if len(X)!=366 or X&set(t10.values(mask)) or not t10.independent(X,digits): raise RuntimeError('winning local repair replay failed')
    Ibits,pairs,o,PH,PV=w; pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=134769: raise RuntimeError(f'10D score replay {len(pts)}')
    status.update({'score':len(pts),'repair_method':method,'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(tr),'translation_sign':sign,'removed_retained_points':sorted(rem),'added_auxiliary_points':add,'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
