#!/usr/bin/env python3
"""Exact remove-3/add-4 repair for all BPZ t=10 two-hit alignments.

After deleting the two obstruction hits, each alignment gives an allowed
independent set L of size 365.  Earlier exact search proved support-zero absent,
single-owner pools have size at most one, and no two-owner pool contains three
candidate vertices.  To recover |X|=366 at radius 3, choose four pairwise
compatible outside vertices whose union of conflict owners in L has size <=3.

Any successful four-set cannot consist solely of support-1 vertices: with at
most one candidate per singleton owner, three owners provide at most three such
vertices.  Hence every success contains a realized support of size 2 or 3.  We
generate exactly all owner triples containing every realized size-2 support,
plus all realized size-3 supports, then test the complete candidate pool for
that triple.  This is exhaustive for remove-3/add-4 under the verified
single-owner sparsity condition.
"""
import argparse,json,sys
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
                    if (not t10.conflict(a,d,digits) and not t10.conflict(b,d,digits)
                            and not t10.conflict(c,d,digits)):
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
        if bc<=3: groups.setdefault(s,[]).append(v)
    return groups


def pool_for(T,groups):
    out=[]
    for s,vs in groups.items():
        if s and (s & ~T)==0: out.extend(vs)
    return sorted(set(out))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    fam=json.loads((args.family_root/'data'/'family-f.json').read_text()); states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    obs,ostats=t10.obstruction_witnesses(I0,ring,digits,nb)
    Fobs=[(mask,w,np.fft.fftn(t10.arr(t10.values(mask),digits))) for mask,w in obs.items()]

    seen_align=set(); alignments=0; explicit=0; triples_tested=0; eligible=0; max_pool=0; winner=None; per=[]
    for name,S in seeds:
        FS=np.fft.fftn(t10.arr(S,digits))
        for oi,(mask,w,FD) in enumerate(Fobs):
            corr=np.rint(np.fft.ifftn(np.conj(FS)*FD).real).astype(np.int16)
            if int(corr.min())!=2: continue
            Dset=set(t10.values(mask))
            for idx in np.argwhere(corr==2):
                tr=tuple(int(z) for z in idx)
                for sign in (1,-1):
                    explicit+=1; Xfull=set(t10.shift_set(S,tr,digits,sign)); hits=Xfull&Dset
                    if len(hits)!=2: continue
                    key=(name,oi,tuple(sorted(Xfull)))
                    if key in seen_align: continue
                    seen_align.add(key); alignments+=1
                    retained=sorted(Xfull-Dset)
                    if len(retained)!=365 or not t10.independent(retained,digits): raise RuntimeError('retained replay failed')
                    groups=support_groups(retained,Dset,ring)
                    if groups.get(0): raise RuntimeError('r0 drift: free vertex exists')
                    max_single=max((len(vs) for s,vs in groups.items() if s.bit_count()==1),default=0)
                    if max_single>1: raise RuntimeError(f'singleton sparsity drift {max_single}')
                    s2=[s for s in groups if s.bit_count()==2]; s3=[s for s in groups if s.bit_count()==3]
                    Ts=set(s3)
                    allowners=(1<<len(retained))-1
                    for s in s2:
                        rest=allowners ^ s
                        while rest:
                            b=rest & -rest; rest^=b; Ts.add(s|b)
                    local_tested=local_eligible=0; local_max=0
                    for T in sorted(Ts):
                        p=pool_for(T,groups); triples_tested+=1; local_tested+=1; local_max=max(local_max,len(p)); max_pool=max(max_pool,len(p))
                        if len(p)<4: continue
                        eligible+=1; local_eligible+=1
                        add=find4(p,digits)
                        if add is None: continue
                        owners=[i for i in range(len(retained)) if (T>>i)&1]
                        if len(owners)!=3: raise RuntimeError('owner triple drift')
                        winner=(name,oi,tr,sign,retained,owners,add,w,mask); break
                    per.append({'seed':name,'obstruction_index':oi,'support2_groups':len(s2),'support3_groups':len(s3),'owner_triples_tested':local_tested,'eligible_pools_at_least4':local_eligible,'max_pool':local_max})
                    print('ALIGN_DONE',json.dumps(per[-1],sort_keys=True),flush=True)
                    if winner: break
                if winner: break
            if winner: break
        if winner: break

    status={'method':'bpz-t10-two-hit-exact-remove3-add4','candidate':winner is not None,'score':134753 if winner is None else 134769,'obstruction_stats':ostats,'two_hit_alignments':alignments,'explicit_replays':explicit,'owner_triples_tested':triples_tested,'eligible_pools_at_least4':eligible,'max_pool':max_pool,'per_alignment':per}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    name,oi,tr,sign,retained,owners,add,w,mask=winner
    rem={retained[i] for i in owners}; X=(set(retained)-rem)|set(add)
    if len(X)!=366 or X&set(t10.values(mask)) or not t10.independent(X,digits): raise RuntimeError('winning r3 replay failed')
    Ibits,pairs,o,PH,PV=w; pts,xp=t10.build(Ibits,X,pairs,PH,PV,ring)
    if len(pts)!=134769: raise RuntimeError(f'10D score replay {len(pts)}')
    status.update({'score':len(pts),'winning_seed':name,'winning_obstruction_index':oi,'winning_translation':list(tr),'translation_sign':sign,'removed_retained_points':sorted(rem),'added_auxiliary_points':add,'auxiliary_size':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
