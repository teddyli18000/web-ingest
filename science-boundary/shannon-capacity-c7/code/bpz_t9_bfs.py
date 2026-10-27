#!/usr/bin/env python3
"""Exact breadth-first search of the BPZ C7^5 private-swap state graph.

A state is a 367-point independent set I with the published BPZ auxiliary set X
held fixed.  An edge replaces r in I by q outside I when q has r as its unique
I-neighbour.  This is exactly every one-point replacement that preserves the
cardinality and independence of I (zero-neighbour points are detected
separately).  Every visited state is tested exactly for a Definition-2 t=9
orientation using MiniCard.

The 16807-vertex ambient space is represented by Python integer bitsets, so
neighbour counting and state de-duplication are exact and cheap enough for a
multi-level BFS.
"""

import argparse,json,sys
from itertools import combinations
from pathlib import Path
from pysat.solvers import Minicard

Q=7;D=5;U=Q**D;N=367;TARGET=9;TARGET_SCORE=N*N+TARGET*TARGET


def conflict(a,b,digits):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(digits[a],digits[b]))

def values(bits):
    while bits:
        z=bits&-bits;yield z.bit_length()-1;bits^=z

def solve_t9(Ibits,X,nbmask,digits,xmask):
    priv=[];zero=0
    for q in range(U):
        if (Ibits>>q)&1:continue
        z=nbmask[q]&Ibits;bc=z.bit_count()
        if bc==0:zero+=1
        elif bc==1:priv.append((z.bit_length()-1,q))
    owners=len({r for r,_ in priv})
    if owners<TARGET:return None,priv,{"private_candidates":len(priv),"private_owners":owners,"zero_conflict":zero,"oriented_options":0,"incompatible_pairs":None}
    opts=[];selfbad=0
    for r,q in priv:
        if xmask[r]&xmask[q]:selfbad+=1;continue
        opts.append((r,q,r,q,0));opts.append((r,q,q,r,1))
    if len({r for r,_,_,_,_ in opts})<TARGET:return None,priv,{"private_candidates":len(priv),"private_owners":owners,"zero_conflict":zero,"oriented_options":len(opts),"self_invalid":selfbad,"incompatible_pairs":None}
    s=Minicard();inc=0;m=len(opts)
    for i,(ri,qi,hi,vi,si) in enumerate(opts):
        for j in range(i+1,m):
            rj,qj,hj,vj,sj=opts[j]
            if (ri==rj or conflict(hi,hj,digits) or conflict(vi,vj,digits) or (xmask[hi]&xmask[vj]) or (xmask[hj]&xmask[vi])):
                s.add_clause([-(i+1),-(j+1)]);inc+=1
    s.add_atmost([-(i+1) for i in range(m)],m-TARGET)
    sat=s.solve();model=s.get_model() if sat else None;s.delete();chosen=None
    if sat:
        pos={z for z in model if z>0};ids=[i for i in range(m) if i+1 in pos][:TARGET]
        if len(ids)!=TARGET:raise RuntimeError('short SAT model')
        chosen=[opts[i] for i in ids]
    return chosen,priv,{"private_candidates":len(priv),"private_owners":owners,"zero_conflict":zero,"oriented_options":m,"self_invalid":selfbad,"incompatible_pairs":inc}

def build(Ibits,X,chosen,ring,digits):
    I=set(values(Ibits));owners=[z[0] for z in chosen];PH=[z[2] for z in chosen];PV=[z[3] for z in chosen]
    if len(set(owners))!=TARGET:raise RuntimeError('owner replay')
    for A in (PH,PV):
        for a,b in combinations(A,2):
            if conflict(a,b,digits):raise RuntimeError('transversal replay')
    R=set(owners);B=I-R;NH=set().union(*(ring.NB[h] for h in PH));NV=set().union(*(ring.NB[v] for v in PV))
    if set(X)&NH&NV:raise RuntimeError('X double-hit replay')
    X0=set(X)-(NH|NV);XH=set(X)&NH;XV=set(X)&NV;pairs=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:pairs.add((a,c))
    if len(pairs)!=TARGET_SCORE:raise RuntimeError(f'bad score {len(pairs)}')
    pts=[]
    for a,b in pairs:pts.append(''.join(map(str,ring.decode(a)+ring.decode(b))))
    return sorted(pts),owners,PH,PV,(len(X0),len(XH),len(XV))

def path_to(state,parent):
    out=[]
    while parent[state][0] is not None:
        p,r,q,d=parent[state];out.append((r,q));state=p
    out.reverse();return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--max-depth',type=int,default=6);ap.add_argument('--max-states',type=int,default=500000);args=ap.parse_args()
    root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U))
    if len(I0)!=N or len(X)!=N:raise RuntimeError('base drift')
    nbmask=[sum(1<<z for z in ring.NB[q]) for q in range(U)]
    xmask=[0]*U
    for xi,x in enumerate(sorted(X)):
        bit=1<<xi
        for v in ring.NB[x]:xmask[v]|=bit
    start=sum(1<<z for z in I0);front=[start];seen={start};parent={start:(None,None,None,0)};depth_rows=[];best=[];winner=None;truncated=False
    for depth in range(args.max_depth+1):
        next_front=[];n_sat_test=0;max_priv=0;max_owners=0;zero_states=0
        print(f'DEPTH_START {depth} frontier={len(front)} seen={len(seen)}',flush=True)
        for si,Ibits in enumerate(front):
            chosen,priv,st=solve_t9(Ibits,X,nbmask,digits,xmask);max_priv=max(max_priv,st['private_candidates']);max_owners=max(max_owners,st['private_owners']);zero_states+=bool(st['zero_conflict'])
            if st['private_owners']>=TARGET:n_sat_test+=1
            rec={"depth":depth,"state_index":si,**st,"path":[list(z) for z in path_to(Ibits,parent)]}
            if not best or (st['private_owners'],st['private_candidates'])>(best[0]['private_owners'],best[0]['private_candidates']):best=[rec]
            elif (st['private_owners'],st['private_candidates'])==(best[0]['private_owners'],best[0]['private_candidates']) and len(best)<20:best.append(rec)
            if chosen is not None:
                winner=(Ibits,chosen,rec);break
            if depth<args.max_depth:
                for r,q in priv:
                    J=Ibits^(1<<r)^(1<<q)
                    if J in seen:continue
                    if len(seen)>=args.max_states:truncated=True;continue
                    seen.add(J);parent[J]=(Ibits,r,q,depth+1);next_front.append(J)
        depth_rows.append({"depth":depth,"states":len(front),"new_states":len(next_front),"sat_test_states":n_sat_test,"max_private_candidates":max_priv,"max_private_owners":max_owners,"zero_conflict_states":zero_states})
        print('DEPTH',json.dumps(depth_rows[-1],sort_keys=True),flush=True)
        if winner is not None:break
        if depth==args.max_depth or not next_front:break
        front=next_front
    status={"method":"bpz-definition2-exact-private-swap-bfs","candidate":winner is not None,"max_depth_requested":args.max_depth,"max_states":args.max_states,"states_seen":len(seen),"truncated":truncated,"depths":depth_rows,"best_states":best}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=N*N+8*8;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    Ibits,chosen,rec=winner;pts,owners,PH,PV,xp=build(Ibits,X,chosen,ring,digits);status.update({"score":len(pts),"winning_state":rec,"owners":owners,"PH":PH,"PV":PV,"X_partition":{"X0":xp[0],"XH":xp[1],"XV":xp[2]}});args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({"points":pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
