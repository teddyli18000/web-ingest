#!/usr/bin/env python3
"""Exact remove-3/add-4 repair for every BPZ t=10 two-hit alignment.

The preceding exact radius<=2 search established that every singleton owner
support group has size at most one.  Hence four selected additions whose owner
union has size at most three cannot all have singleton supports: at least one
selected vertex has support size 2 or 3.  We therefore generate every relevant
owner triple from the actually realized support-2/3 groups, collect all outside
vertices whose support is a nonempty subset of that triple, and exactly test
for an independent 4-set.
"""
import argparse,json,sys
from itertools import combinations
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def find4(pool,digits):
    n=len(pool)
    for i in range(n):
        a=pool[i]
        for j in range(i+1,n):
            b=pool[j]
            if t10.conflict(a,b,digits): continue
            for k in range(j+1,n):
                c=pool[k]
                if t10.conflict(a,c,digits) or t10.conflict(b,c,digits): continue
                for l in range(k+1,n):
                    d=pool[l]
                    if not t10.conflict(a,d,digits) and not t10.conflict(b,d,digits) and not t10.conflict(c,d,digits):
                        return [a,b,c,d]
    return None

def support_groups(retained,Dset,ring):
    supp=[0]*t10.U
    for i,u in enumerate(retained):
        bit=1<<i
        for v in ring.NB[u]: supp[v]|=bit
    groups={}; rset=set(retained)
    for v in range(t10.U):
        if v in Dset or v in rset: continue
        s=supp[v]; bc=s.bit_count()
        if 1<=bc<=3: groups.setdefault(s,[]).append(v)
    return groups

def bits(mask):
    while mask:
        b=mask&-mask; yield b.bit_length()-1; mask^=b

def pool_for(T,groups):
    out=[]; sub=T
    while sub:
        out.extend(groups.get(sub,())); sub=(sub-1)&T
    return sorted(set(out))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    obs,ostats=t10.obstruction_witnesses(I0,ring,digits,nb); fam=json.loads((args.family_root/'data'/'family-f.json').read_text()); states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]; Fobs=[(m,w,np.fft.fftn(t10.arr(t10.values(m),digits))) for m,w in obs.items()]
    seen_align=set(); alignments=0; triples_scanned=0; eligible=0; maxpool=0; winner=None; per=[]
    for name,S in seeds:
        FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=2: continue
            Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==2):
                tr=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    Xfull=set(t10.shift_set(S,tr,digits,sign)); hits=Xfull&Dset
                    if len(hits)!=2: continue
                    key=(name,oi,tuple(sorted(Xfull)))
                    if key in seen_align: continue
                    seen_align.add(key); alignments+=1; retained=sorted(Xfull-Dset); groups=support_groups(retained,Dset,ring)
                    singles={m for m in groups if m.bit_count()==1}; doubles={m for m in groups if m.bit_count()==2}; triples={m for m in groups if m.bit_count()==3}
                    if max((len(groups[m]) for m in singles),default=0)>1: raise RuntimeError('singleton-group assumption drift')
                    owner_triples=set(triples)
                    for dm in doubles:
                        own=set(bits(dm))
                        for c in range(len(retained)):
                            if c not in own: owner_triples.add(dm|(1<<c))
                    local_eligible=0; local_max=0
                    for T in owner_triples:
                        pool=pool_for(T,groups); triples_scanned+=1; local_max=max(local_max,len(pool)); maxpool=max(maxpool,len(pool))
                        if len(pool)<4: continue
                        eligible+=1; local_eligible+=1; add=find4(pool,digits)
                        if add is None: continue
                        owners=list(bits(T)); winner=(name,oi,tr,sign,retained,owners,add,w,mask); break
                    per.append({'seed':name,'obstruction_index':oi,'support_groups_1':len(singles),'support_groups_2':len(doubles),'support_groups_3':len(triples),'owner_triples':len(owner_triples),'eligible_pools':local_eligible,'max_pool':local_max})
                    print('ALIGN_DONE',json.dumps(per[-1],sort_keys=True),flush=True)
                    if winner: break
                if winner: break
            if winner: break
        if winner: break
    status={'method':'bpz-t10-two-hit-exact-remove3-add4','candidate':winner is not None,'score':134753 if winner is None else 134769,'obstruction_stats':ostats,'two_hit_alignments':alignments,'owner_triples_scanned':triples_scanned,'eligible_pools':eligible,'max_pool':maxpool,'alignment_summaries':per}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    name,oi,tr,sign,retained,owners,add,w,mask=winner; rem={retained[i] for i in owners}; X=(set(retained)-rem)|set(add)
    if len(X)!=366 or X&set(t10.values(mask)) or not t10.independent(X,digits): raise RuntimeError('winner replay failed')
    Ibits,pairs,o,PH,PV=w; pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=134769: raise RuntimeError(f'score replay {len(pts)}')
    status.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(tr),'translation_sign':sign,'removed_retained_points':sorted(rem),'added_auxiliary_points':add,'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
