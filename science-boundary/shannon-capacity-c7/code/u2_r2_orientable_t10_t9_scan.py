#!/usr/bin/env python3
"""Exact t=10/t=9 orientability + obstruction scan on the U2 radius<=2 neighborhood.

The frozen U2 depth-2 parent has maximum orientable private-pair subset 8, but
its exact neutral radius<=2 neighborhood contains states with 9,10,11,12
distinct private pairs.  The previous t=11 search only asked for orientable 11.
This program closes the important gap: enumerate the same exact 59-state
neighborhood, enumerate every size-10 and size-9 private-pair subset and binary
orientation, deduplicate exact obstruction masks, then scan every translation
of the public 367-point auxiliary catalog.

For t=10 a record improvement permits at most one auxiliary obstruction hit;
for t=9 it permits zero.  Any promising FFT shift is replayed exactly and a
Few-Shots-ready 10D certificate is materialized.
"""
import argparse,json,runpy,sys
from itertools import combinations,product
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as base
from bpz_t9_funsearch_fft import funsearch_seed

N=367; BASELINE=134753; TS=(10,9)


def exact_states(P,ring,digits):
    P=sorted(P); pset=set(P); supp=[0]*base.U
    for i,u in enumerate(P):
        bit=1<<i
        for v in ring.NB[u]: supp[v]|=bit
    one={}; two={}
    for v,s in enumerate(supp):
        if v in pset: continue
        bc=s.bit_count()
        if bc==1:
            i=(s&-s).bit_length()-1; one.setdefault(i,[]).append(v)
        elif bc==2:
            ids=[i for i in range(len(P)) if (s>>i)&1]; two.setdefault((ids[0],ids[1]),[]).append(v)
    seen=set(); states=[]
    def add(Y,move):
        k=tuple(sorted(Y))
        if k in seen:return
        seen.add(k)
        if len(k)!=N or not base.independent(k,digits):raise RuntimeError(f'state replay {move}')
        states.append((k,move))
    add(P,{'radius':0})
    for a in sorted(one):
        for u in sorted(one[a]):
            Y=list(P);Y[a]=u;add(Y,{'radius':1,'remove_indices':[a],'add':[u]})
    ownerpairs=set(two)
    for a,b in combinations(sorted(one),2):ownerpairs.add((a,b))
    trials=0;maxpool=0
    for a,b in sorted(ownerpairs):
        pool=sorted(set(one.get(a,[])+one.get(b,[])+two.get((a,b),[])));maxpool=max(maxpool,len(pool))
        for u,v in combinations(pool,2):
            trials+=1
            if base.conflict(u,v,digits):continue
            Y=list(P);Y[a]=u;Y[b]=v
            if len(set(Y))==N:add(Y,{'radius':2,'remove_indices':[a,b],'add':[u,v]})
    return states,{'states':len(states),'support1_groups':len(one),'support2_pairs':len(two),'owner_pairs':len(ownerpairs),'candidate_pair_trials':trials,'max_pool':maxpool}


def private_pairs(state,ring):
    S=set(state); out=[]
    for q in range(base.U):
        if q in S:continue
        hits=[a for a in S if q in ring.NB[a]]
        if len(hits)==1:out.append((hits[0],q))
    return out


def orientable_obstructions(state,ring,digits):
    pp=private_pairs(state,ring); by={}
    for a,q in pp:by.setdefault(a,[]).append(q)
    owners=sorted(by)
    Ibits=sum(1<<z for z in state); out={t:{} for t in TS}; stats={}
    for t in TS:
        raw=0;subsets=0
        if len(owners)>=t:
            for osub in combinations(owners,t):
                choices=[by[a] for a in osub]; anyvalid=False
                for qs in product(*choices):
                    ps=tuple(zip(osub,qs))
                    for orient in product((0,1),repeat=t):
                        PH=[q if s else a for (a,q),s in zip(ps,orient)]
                        PV=[a if s else q for (a,q),s in zip(ps,orient)]
                        if not base.independent(PH,digits) or not base.independent(PV,digits):continue
                        raw+=1;anyvalid=True
                        D=ring.nbhd(set(PH))&ring.nbhd(set(PV)); mask=sum(1<<z for z in D)
                        out[t].setdefault(mask,(Ibits,ps,orient,PH,PV))
                if anyvalid:subsets+=1
        stats[str(t)]={'private_pairs':len(pp),'private_owners':len(owners),'raw_valid_orientations':raw,'orientable_owner_subsets':subsets,'distinct_obstructions':len(out[t])}
    return out,stats


def extract_367(ns,digits):
    out=[]
    for name,v in ns.items():
        if name.startswith('__'):continue
        try:
            if len(v)!=N:continue
        except Exception:continue
        try:
            S=frozenset(base.enc(tuple(map(int,w))) for w in v)
            if len(S)==N and base.independent(S,digits):out.append((name,set(S)))
        except Exception:pass
    uniq={}
    for name,S in out:uniq.setdefault(frozenset(S),name)
    return [(name,set(S)) for S,name in uniq.items()]


def build(Ibits,X,pairs,PH,PV,ring):
    t=len(pairs);I=set(base.values(Ibits));R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('auxiliary hits obstruction')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    expected=(N-t)**2+2*t*len(X)
    if len(P)!=expected:raise RuntimeError(f'score drift {len(P)} != {expected}')
    pts=sorted(''.join(map(str,ring.decode(a)+ring.decode(c))) for a,c in P)
    return pts,(len(X0),len(XH),len(XV))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('c7five_root',type=Path);ap.add_argument('parent_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    ring=Ring(base.D);digits=tuple(ring.decode(v) for v in range(base.U))
    frozen=json.loads(args.parent_json.read_text());P=sorted(map(int,frozen['points']));
    if len(P)!=N or not base.independent(P,digits):raise RuntimeError('parent invalid')
    states,nstat=exact_states(P,ring,digits);print('STATES',json.dumps(nstat,sort_keys=True),flush=True)
    allobs={t:{} for t in TS};state_stats=[];best_orient=0
    for si,(S,move) in enumerate(states):
        obs,st=orientable_obstructions(S,ring,digits);mx=max((t for t in TS if obs[t]),default=8);best_orient=max(best_orient,mx)
        rec={'state_index':si,'move':move,'stats':st,'max_relevant_orientable':mx};state_stats.append(rec)
        for t in TS:
            for mask,w in obs[t].items():allobs[t].setdefault(mask,(si,w))
        print('STATE_DONE',json.dumps(rec,sort_keys=True),flush=True)
    ocounts={str(t):len(allobs[t]) for t in TS};print('OBSTRUCTIONS',json.dumps(ocounts,sort_keys=True),flush=True)

    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']))
    fam=json.loads((args.c7five_root/'data'/'family-f.json').read_text());seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',set(map(int,s))) for i,s in enumerate(fam['states'])]
    for fn,label in (('u1.py','u1'),('u2.py','u2')):
        ns=runpy.run_path(str(args.c7five_root/'verify'/fn));seeds += [(f'{label}:{n}',S) for n,S in extract_367(ns,digits)]
    seeds.append(('funsearch',set(funsearch_seed(digits))))
    dedup={}
    for name,S in seeds:
        if len(S)!=N or not base.independent(S,digits):raise RuntimeError(f'invalid seed {name}')
        dedup.setdefault(frozenset(S),name)
    seeds=[(name,set(S)) for S,name in dedup.items()]

    winner=None;best=None;cases=0;hist={}
    for t in TS:
        allowed=1 if t==10 else 0
        if not allobs[t]:continue
        Fobs=[(mask,si,w,np.fft.fftn(base.arr(base.values(mask),digits))) for mask,(si,w) in allobs[t].items()]
        for name,A in seeds:
            FA=np.fft.fftn(base.arr(A,digits));sbest=999
            for oi,(mask,si,w,FD) in enumerate(Fobs):
                cases+=1;corr=np.rint(np.fft.ifftn(np.conj(FA)*FD).real).astype(np.int16);mn=int(corr.min());sbest=min(sbest,mn);hist[f'{t}:{mn}']=hist.get(f'{t}:{mn}',0)+1
                rec={'t':t,'seed':name,'obstruction_index':oi,'parent_state_index':si,'min_hits':mn,'allowed_hits':allowed,'obstruction_size':mask.bit_count()}
                if best is None or (mn-allowed,-t,mn)<(best['min_hits']-best['allowed_hits'],-best['t'],best['min_hits']):best=rec;print('NEW_BEST',json.dumps(best,sort_keys=True),flush=True)
                if mn>allowed:continue
                D=set(base.values(mask));
                for idx in np.argwhere(corr<=allowed):
                    tr=tuple(int(z) for z in idx)
                    for sign in (1,-1):
                        Xfull=set(base.shift_set(A,tr,digits,sign));hits=Xfull&D
                        if len(Xfull)!=N or not base.independent(Xfull,digits):raise RuntimeError('translation replay')
                        if len(hits)>allowed:continue
                        X=Xfull-D;Ibits,pairs,orient,PH,PV=w;pts,xp=build(Ibits,X,pairs,PH,PV,ring);score=len(pts)
                        if score<=BASELINE:continue
                        winner=(t,name,oi,si,tr,sign,X,hits,w,score,xp,pts);break
                    if winner:break
                if winner:break
            print('SEED_DONE',json.dumps({'t':t,'seed':name,'best_hits':sbest},sort_keys=True),flush=True)
            if winner:break
        if winner:break
    status={'method':'u2-radius2-orientable-t10-t9-all-obstructions-public367-translations','candidate':winner is not None,'score':BASELINE if winner is None else winner[8],'neighborhood':nstat,'states_scored':len(states),'max_relevant_orientable':best_orient,'distinct_obstructions':ocounts,'seed_count':len(seeds),'cases':cases,'best':best,'histogram':hist,'state_stats':state_stats}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    t,name,oi,si,tr,sign,X,hits,w,score,xp,pts=winner;Ibits,pairs,orient,PH,PV=w
    status.update({'score':score,'winning_t':t,'winning_seed':name,'winning_obstruction_index':oi,'winning_parent_state_index':si,'winning_translation':list(tr),'translation_sign':sign,'deleted_auxiliary_hits':sorted(hits),'auxiliary_size':len(X),'private_pairs':[list(p) for p in pairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
