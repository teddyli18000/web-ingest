#!/usr/bin/env python3
"""Exact t=9 + one-X-swap search over the full BPZ private-swap I component.

Starting from the published 367-point I, exhaust the complete connected
component under one-point private swaps.  For every state with at least nine
private pairs, enumerate every 9-subset and all 2^9 orientations.  Whenever
P^H and P^V are independent and exactly one published X vertex lies in both
closed neighbourhoods, exhaust every one-point replacement of that bad X
vertex.  A successful repair materializes Gao's 134770-point C7^10 set.
"""

import argparse,json,sys
from itertools import combinations,product
from pathlib import Path

Q=7;D=5;U=Q**D;N=367;T=9;TARGET=N*N+T*T

def conflict(a,b,d): return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def vals(bits):
    while bits:
        z=bits&-bits;yield z.bit_length()-1;bits^=z

def private(Ibits,nbmask):
    out=[];zero=0
    for q in range(U):
        if (Ibits>>q)&1:continue
        h=nbmask[q]&Ibits;bc=h.bit_count()
        if bc==0:zero+=1
        elif bc==1:out.append((h.bit_length()-1,q))
    return sorted(out),zero

def path(state,parent):
    p=[]
    while parent[state][0] is not None:
        prev,r,q=parent[state];p.append((r,q));state=prev
    return list(reversed(p))

def build(Ibits,X,pairs,PH,PV,ring):
    I=set(vals(Ibits));R={r for r,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if set(X)&NH&NV:raise RuntimeError('double hit survived')
    X0=set(X)-(NH|NV);XH=set(X)&NH;XV=set(X)&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    pts=[''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P]
    return sorted(pts),(len(X0),len(XH),len(XV))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args()
    root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U))
    if len(I0)!=N or len(X0)!=N or not independent(I0,digits) or not independent(X0,digits):raise RuntimeError('base drift')
    nbmask=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    xlist=sorted(X0);xpos={x:i for i,x in enumerate(xlist)};xhits=[0]*U
    for x,i in xpos.items():
        bit=1<<i
        for y in ring.NB[x]:xhits[y]|=bit

    start=sum(1<<z for z in I0);seen={start};front=[start];parent={start:(None,None,None)};states=[]
    while front:
        nxt=[]
        for Ibits in front:
            pp,zero=private(Ibits,nbmask);states.append((Ibits,pp,zero))
            for r,q in pp:
                J=Ibits^(1<<r)^(1<<q)
                if J not in seen:
                    seen.add(J);parent[J]=(Ibits,r,q);nxt.append(J)
        front=nxt
    if len(states)!=235:raise RuntimeError(f'I-component drift: {len(states)} states')

    eligible_states=0;subsets=0;orientations=0;sameside=0;onebad=0;repair_trials=0;near=[];winner=None
    for si,(Ibits,pp,zero) in enumerate(states):
        if zero:raise RuntimeError('unexpected direct-add state')
        if len({r for r,q in pp})<T:continue
        eligible_states+=1
        for chosen_pairs in combinations(pp,T):
            if len({r for r,q in chosen_pairs})<T:continue
            subsets+=1
            for orient in product((0,1),repeat=T):
                orientations+=1
                PH=[q if s else r for (r,q),s in zip(chosen_pairs,orient)];PV=[r if s else q for (r,q),s in zip(chosen_pairs,orient)]
                if not independent(PH,digits) or not independent(PV,digits):continue
                sameside+=1;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV));bad=sorted(X0&NH&NV)
                if len(bad)!=1:continue
                onebad+=1;badx=bad[0];badbit=1<<xpos[badx];repairs=[]
                for y in range(U):
                    if y in X0:continue
                    repair_trials+=1
                    if xhits[y]&~badbit:continue
                    if y in NH and y in NV:continue
                    repairs.append(y)
                if repairs:
                    rec={'state_index':si,'I_path':[list(z) for z in path(Ibits,parent)],'private_pairs':[list(z) for z in chosen_pairs],'orientation':list(orient),'bad_X':badx,'X_replacements':repairs[:50],'replacement_count':len(repairs)};near.append(rec)
                    if winner is None:winner=(Ibits,chosen_pairs,PH,PV,badx,repairs[0],rec)
                elif len(near)<20:
                    near.append({'state_index':si,'I_path':[list(z) for z in path(Ibits,parent)],'private_pairs':[list(z) for z in chosen_pairs],'orientation':list(orient),'bad_X':badx,'X_replacements':[],'replacement_count':0})
        if winner is not None:break
    status={'method':'bpz-full-I-component-t9-one-X-swap','candidate':winner is not None,'I_component_states':len(states),'eligible_I_states':eligible_states,'nine_pair_subsets':subsets,'orientations_tested':orientations,'same_side_valid':sameside,'one_bad_X_orientations':onebad,'ambient_repair_trials':repair_trials,'near_examples':near[:20]}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=134753;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    Ibits,pairs,PH,PV,badx,y,rec=winner;X=set(X0);X.remove(badx);X.add(y)
    if len(X)!=N or not independent(X,digits):raise RuntimeError('X repair replay failed')
    pts,xpart=build(Ibits,X,pairs,PH,PV,ring);status.update({'score':len(pts),'winning':rec,'X_swap':{'remove':badx,'add':y},'PH':PH,'PV':PV,'X_partition':{'X0':xpart[0],'XH':xpart[1],'XV':xpart[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
