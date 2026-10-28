#!/usr/bin/env python3
"""Search new C7^5 auxiliaries from the Polak--Schrijver circular-code generator.

The published 367-set starts with the 382-word code
  t*(1,7,7^2,7^3,7^4) mod 382,
adds a coordinate shift, quantizes residue i by floor(2*i/109), deletes every
quantized word having a conflict with another quantized word, then extends the
remaining independent core.  The published shift (40,123,40,123,40) yields a
327-word core and an extension graph with 71 vertices, alpha 40.

Adding a multiple of the circular generator to the shift merely reindexes t, so
we normalize shift[0]=0 and search the remaining four coordinates.  The search
objective is tailored to the BPZ t=9 route: among all 160 obstruction masks,
prefer large conflict-free cores with few obstruction hits.  Promising shifts
are greedily extended inside C7^5 \ D.  Any 367-word obstruction-free extension
is exact-replayed and materialized as the 134770-point 10D construction.

This is a heuristic construction search.  Failure is not an impossibility result.
"""
import argparse,json,math,random,sys,time
from pathlib import Path

import bpz_t9_aux_translation_fft as f

MOD=382
GEN=(1,7,49,343,109)
PUBLISHED=(40,123,40,123,40)
TARGET=367


def normalize(a):
    z=a[0]
    return tuple((a[j]-z*GEN[j])%MOD for j in range(5))


def quantized(shift):
    out=set()
    for t in range(MOD):
        w=[]
        for j,g in enumerate(GEN):
            r=(t*g+shift[j])%MOD
            q=(2*r)//109
            if not 0<=q<7: raise RuntimeError('quantizer range drift')
            w.append(q)
        out.add(f.enc(tuple(w)))
    return out


def core_of(shift,nbmask):
    S=quantized(shift); bits=sum(1<<v for v in S); core=[]
    for v in S:
        if (nbmask[v]&bits)==(1<<v): core.append(v)
    return set(core),len(S)


def extension_candidates(core,Dset,nbmask):
    base=core-Dset; bb=sum(1<<v for v in base)
    return base,[v for v in range(f.U) if v not in Dset and not (nbmask[v]&bb)]


def greedy_extension(base,candidates,NB,rng,restarts=10):
    best=[]; C0=set(candidates)-set(base)
    for rr in range(restarts):
        C=set(C0); chosen=[]
        while C:
            sample=list(C) if len(C)<=80 else rng.sample(tuple(C),80)
            md=min(len(C.intersection(NB[v]))-1 for v in sample)
            opts=[v for v in sample if len(C.intersection(NB[v]))-1<=md+1]
            v=opts[rng.randrange(len(opts))]
            chosen.append(v); C.difference_update(NB[v])
        if len(chosen)>len(best): best=chosen
    return best


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path)
    ap.add_argument('--seed',type=int,default=1); ap.add_argument('--seconds',type=float,default=360); ap.add_argument('--iterations',type=int,default=1000000)
    args=ap.parse_args(); sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); I0=set(map(int,raw['I0']))
    ring=Ring(5); digits=tuple(ring.decode(v) for v in range(f.U)); NB=ring.NB; nbmask=[sum(1<<z for z in NB[v]) for v in range(f.U)]
    obs=f.obstruction_witnesses(I0,ring,digits,nbmask); obs_items=list(obs.items()); Dsets=[set(f.values(m)) for m,_ in obs_items]; Dbits=[sum(1<<v for v in D) for D in Dsets]

    pub=normalize(PUBLISHED); pcore,puniq=core_of(pub,nbmask); pbits=sum(1<<v for v in pcore)
    pub_cand=[v for v in range(f.U) if not (nbmask[v]&pbits)]
    # The paper's 71-vertex extension graph excludes the 327 core vertices automatically
    # because closed neighborhoods contain self.
    if puniq!=382 or len(pcore)!=327 or len(pub_cand)!=71:
        raise RuntimeError(f'published reconstruction drift unique={puniq} core={len(pcore)} candidates={len(pub_cand)}')

    rng=random.Random(args.seed^0xC7382); start=time.monotonic(); cur=list(pub); curcore=set(pcore)
    def metrics(core):
        bits=sum(1<<v for v in core); hits=[(bits&d).bit_count() for d in Dbits]; mh=min(hits); oi=hits.index(mh)
        return len(core),mh,oi
    cm=metrics(curcore); best_metric=cm; best_shift=tuple(cur); best_rows=[]; accepted=0; evaluated=1; promising=0; greedy_trials=0; best_total=0; winner=None
    best_rows.append({'shift':list(cur),'core':cm[0],'min_obstruction_hits':cm[1],'obstruction_index':cm[2]})

    temp0=2.5
    for it in range(args.iterations):
        if time.monotonic()-start>=args.seconds or winner: break
        prop=cur[:]
        nm=1 if rng.random()<0.8 else 2
        for _ in range(nm):
            j=rng.randrange(1,5)
            if rng.random()<0.75:
                delta=rng.choice((-7,-4,-3,-2,-1,1,2,3,4,7))
            else: delta=rng.randrange(-54,55)
            prop[j]=(prop[j]+delta)%MOD
        core,uniq=core_of(tuple(prop),nbmask); evaluated+=1
        m=metrics(core)
        # Prioritize retained independent core, then obstruction avoidance.
        oldscore=cm[0]*8-cm[1]; newscore=m[0]*8-m[1]
        T=temp0*max(0.05,1-it/max(1,args.iterations))
        if newscore>=oldscore or rng.random()<math.exp((newscore-oldscore)/max(T,1e-6)):
            cur,curcore,cm=prop,core,m; accepted+=1
        if (m[0],-m[1])>(best_metric[0],-best_metric[1]):
            best_metric=m; best_shift=tuple(prop); best_rows.append({'shift':list(prop),'core':m[0],'min_obstruction_hits':m[1],'obstruction_index':m[2]}); best_rows=best_rows[-100:]
        # Attempt actual extension only when the core survives well relative to D.
        if m[0]-m[1] < 315: continue
        promising+=1; oi=m[2]; base,cands=extension_candidates(core,Dsets[oi],nbmask)
        need=TARGET-len(base)
        if need<=0:
            X=set(list(base)[:TARGET])
        elif len(cands)<need:
            continue
        else:
            greedy_trials+=1; add=greedy_extension(base,cands,NB,rng,14); total=len(base)+len(add); best_total=max(best_total,total)
            if total<TARGET: continue
            X=set(base)|set(add[:need])
        if len(X)!=TARGET or X&Dsets[oi] or not f.independent(X,digits): continue
        witness=obs_items[oi][1]; Ibits,pairs,orient,PH,PV=witness; points,xp=f.build(Ibits,sum(1<<z for z in X),pairs,PH,PV,ring)
        if len(points)!=f.TARGET: raise RuntimeError(f'10D target drift {len(points)}')
        winner=(tuple(prop),m,oi,X,points,xp,witness); break

    status={'method':'polak-circular-code-obstruction-aware-shift-search','candidate':winner is not None,'seed':args.seed,'elapsed_seconds':time.monotonic()-start,'evaluated_shifts':evaluated,'accepted_moves':accepted,'promising_shifts':promising,'greedy_extension_trials':greedy_trials,'best_greedy_total':best_total,'published_normalized_shift':list(pub),'published_unique_quantized':puniq,'published_core_size':len(pcore),'published_extension_candidates':len(pub_cand),'best_core_size':best_metric[0],'best_core_min_obstruction_hits':best_metric[1],'best_core_obstruction_index':best_metric[2],'best_shift':list(best_shift),'improvement_trace':best_rows[-50:]}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753; args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True); return
    sh,m,oi,X,points,xp,w=winner; Ibits,pairs,o,PH,PV=w; status.update({'score':len(points),'winning_shift':list(sh),'winning_core_size':m[0],'winning_core_obstruction_hits':m[1],'winning_obstruction_index':oi,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}}); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n'); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
