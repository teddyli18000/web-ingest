#!/usr/bin/env python3
"""Exact simultaneous 2-for-2 bridge search from the BPZ C7^5 main set.

The complete component reachable by sequential one-point private swaps has 243
states and contains no t=9 Definition-2 gadget with the published X.  This
program enumerates every valid simultaneous two-point replacement of the
published I0 whose added vertices have I0-conflict support contained in the two
removed owners.  Such moves include bridges that cannot be decomposed into
single private swaps.  States already in the 243-state component are skipped.

Every genuinely new 367-set is tested exactly: all its private pairs are
recomputed from the ambient C7^5 graph; every 9-subset of distinct owners and
all 2^9 complementary transversal orientations are checked against the fixed
published X.  A hit materializes the 134770-point Gao product.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path

Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def vals(bits):
    while bits:
        z=bits&-bits;yield z.bit_length()-1;bits^=z

def private(bits,nbmask):
    pp=[];zero=[]
    for q in range(U):
        if (bits>>q)&1:continue
        h=nbmask[q]&bits;bc=h.bit_count()
        if bc==0:zero.append(q)
        elif bc==1:pp.append((h.bit_length()-1,q))
    return sorted(pp),zero

def one_swap_component(start,nbmask):
    seen={start};front=[start]
    while front:
        nxt=[]
        for bits in front:
            pp,_=private(bits,nbmask)
            for r,q in pp:
                b=bits^(1<<r)^(1<<q)
                if b not in seen:seen.add(b);nxt.append(b)
        front=nxt
    return seen

def first_t9(bits,X,ring,digits,nbmask):
    pp,zero=private(bits,nbmask)
    owners=len({r for r,q in pp})
    if owners<T:return None,pp,zero,0,0
    subsets=0;orients=0
    for pairs in combinations(pp,T):
        if len({r for r,q in pairs})<T:continue
        subsets+=1
        for o in product((0,1),repeat=T):
            orients+=1
            PH=[q if s else r for (r,q),s in zip(pairs,o)];PV=[r if s else q for (r,q),s in zip(pairs,o)]
            if not independent(PH,digits) or not independent(PV,digits):continue
            if not (set(X)&ring.nbhd(set(PH))&ring.nbhd(set(PV))):return (pairs,o,PH,PV),pp,zero,subsets,orients
    return None,pp,zero,subsets,orients

def build(Ibits,X,pairs,PH,PV,ring):
    I=set(vals(Ibits));R={r for r,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV));X=set(X)
    if X&NH&NV:raise RuntimeError('double hit')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U));nbmask=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    if len(I0)!=N or len(X)!=N or not independent(I0,digits) or not independent(X,digits):raise RuntimeError('base drift')
    start=sum(1<<z for z in I0);component=one_swap_component(start,nbmask)
    if len(component)!=243:raise RuntimeError(f'one-swap component drift {len(component)}')
    ilist=sorted(I0)
    # Candidates whose conflict support against I0 has size 1 or 2, represented
    # by actual owner vertices rather than ordering-dependent indices.
    cand=[];support_hist={1:0,2:0}
    for q in range(U):
        if q in I0:continue
        h=[z for z in ring.NB[q] if z in I0]
        if 1<=len(h)<=2:
            fs=frozenset(h);cand.append((q,fs));support_hist[len(h)]+=1
    # Map every possible removed owner-pair to all candidates whose support is a
    # nonempty subset of that pair.  Singleton candidates belong to 366 pairs.
    pools={}
    for q,s in cand:
        if len(s)==2:
            key=tuple(sorted(s));pools.setdefault(key,[]).append(q)
        else:
            a=next(iter(s))
            for b in ilist:
                if b==a:continue
                key=(a,b) if a<b else (b,a);pools.setdefault(key,[]).append(q)
    states=set();owner_pairs=0;candidate_pairs=0;component_skips=0
    for owners,pool in pools.items():
        pool=sorted(set(pool))
        if len(pool)<2:continue
        owner_pairs+=1;a,b=owners
        for i in range(len(pool)):
            x=pool[i]
            for y in pool[i+1:]:
                candidate_pairs+=1
                if conflict(x,y,digits):continue
                bits=start^(1<<a)^(1<<b)|(1<<x)|(1<<y)
                if bits.bit_count()!=N:raise RuntimeError('two-swap cardinality drift')
                if bits in component:component_skips+=1;continue
                states.add(bits)
    print('ENUM',json.dumps({'support1':support_hist[1],'support2':support_hist[2],'owner_pairs':owner_pairs,'candidate_pairs':candidate_pairs,'new_states':len(states),'component_skips':component_skips},sort_keys=True),flush=True)
    tested=0;eligible=0;subsets=0;orients=0;max_private=0;max_owners=0;winner=None;best=[]
    for si,bits in enumerate(states):
        tested+=1;sol,pp,zero,ns,no=first_t9(bits,X,ring,digits,nbmask);subsets+=ns;orients+=no;pc=len(pp);po=len({r for r,q in pp});max_private=max(max_private,pc);max_owners=max(max_owners,po)
        if po>=T:eligible+=1
        rec={'state_index':si,'private_candidates':pc,'private_owners':po,'zero_conflict':len(zero)}
        if not best or (po,pc)>(best[0]['private_owners'],best[0]['private_candidates']):best=[rec]
        elif (po,pc)==(best[0]['private_owners'],best[0]['private_candidates']) and len(best)<20:best.append(rec)
        if sol is not None:
            pairs,o,PH,PV=sol;winner=(bits,pairs,o,PH,PV,rec);break
    status={'method':'bpz-t9-exact-simultaneous-two-swap-bridge','candidate':winner is not None,'one_swap_component_states':len(component),'support1_candidates':support_hist[1],'support2_candidates':support_hist[2],'owner_pairs_with_pool':owner_pairs,'candidate_add_pairs':candidate_pairs,'component_state_skips':component_skips,'new_two_swap_states':len(states),'states_tested':tested,'eligible_t9_states':eligible,'nine_pair_subsets_tested':subsets,'orientations_tested':orients,'max_private_candidates':max_private,'max_private_owners':max_owners,'best_states':best}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    bits,pairs,o,PH,PV,rec=winner;pts,xp=build(bits,X,pairs,PH,PV,ring);status.update({'score':len(pts),'winning_state':rec,'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
