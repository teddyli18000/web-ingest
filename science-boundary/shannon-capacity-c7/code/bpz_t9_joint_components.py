#!/usr/bin/env python3
"""Exact joint search over private-swap components of both BPZ base sets.

Enumerate the complete one-point-replacement component of the published main
367-set I and, independently, the component of the auxiliary 367-set X.
For every I-state with at least nine private pairs, enumerate every 9-subset
and all transversal orientations.  For each orientation with independent
P^H/P^V, ask whether any X-state in its component avoids
N(P^H) cap N(P^V).  Such a pair of states is a Definition-2 t=9 gadget and
materializes Gao's 134770-point C7^10 construction.

The component enumerations use exact 16807-bit integer states.  A cap is only a
resource guard; the status records whether either enumeration was truncated.
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

def component(start,nbmask,cap):
    seen={start};front=[start];parent={start:(None,None,None)};depths=[];privmap={};zeros={};truncated=False
    depth=0
    while front:
        nxt=[];mx=0
        for bits in front:
            pp,z=private(bits,nbmask);privmap[bits]=pp
            if z:zeros[bits]=z
            mx=max(mx,len(pp))
            for r,q in pp:
                nxtbits=bits^(1<<r)^(1<<q)
                if nxtbits in seen:continue
                if len(seen)>=cap:truncated=True;continue
                seen.add(nxtbits);parent[nxtbits]=(bits,r,q);nxt.append(nxtbits)
        depths.append({'depth':depth,'states':len(front),'new_states':len(nxt),'max_private':mx})
        if truncated:break
        front=nxt;depth+=1
    return list(seen),parent,privmap,zeros,depths,truncated

def path(bits,parent):
    out=[]
    while parent[bits][0] is not None:
        p,r,q=parent[bits];out.append([r,q]);bits=p
    return list(reversed(out))

def build(Ibits,Xbits,pairs,PH,PV,ring):
    I=set(vals(Ibits));X=set(vals(Xbits));R={r for r,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV))
    if X&NH&NV:raise RuntimeError('winning X still double-hits')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    pts=sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P)
    return pts,(len(X0),len(XH),len(XV))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--cap',type=int,default=500000);args=ap.parse_args()
    root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X0=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U));nbmask=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    if len(I0)!=N or len(X0)!=N or not independent(I0,digits) or not independent(X0,digits):raise RuntimeError('base drift')
    ib=sum(1<<z for z in I0);xb=sum(1<<z for z in X0)
    Istates,Ipar,Ipriv,Izero,Idepth,Itr=component(ib,nbmask,args.cap);print('I_COMPONENT',len(Istates),'truncated',Itr,flush=True)
    Xstates,Xpar,Xpriv,Xzero,Xdepth,Xtr=component(xb,nbmask,args.cap);print('X_COMPONENT',len(Xstates),'truncated',Xtr,flush=True)
    if Izero or Xzero:
        print('DIRECT_ADD_STATES',len(Izero),len(Xzero),flush=True)
    # If truncated we can still report a found candidate, but cannot call absence exact.
    xsets=[(b,set(vals(b))) for b in Xstates]
    eligible=0;subsets=0;orientations=0;sameside=0;checks=0;winner=None;best_bad=None;best_rec=None
    for si,Ibits in enumerate(Istates):
        pp=Ipriv[Ibits]
        if len({r for r,q in pp})<T:continue
        eligible+=1
        for pairs in combinations(pp,T):
            if len({r for r,q in pairs})<T:continue
            subsets+=1
            for orient in product((0,1),repeat=T):
                orientations+=1;PH=[q if s else r for (r,q),s in zip(pairs,orient)];PV=[r if s else q for (r,q),s in zip(pairs,orient)]
                if not independent(PH,digits) or not independent(PV,digits):continue
                sameside+=1;Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));dbits=sum(1<<z for z in Dset)
                # Track how close the best X-state gets, even if no exact repair exists.
                local_best=10**9;local_x=None
                for Xbits,X in xsets:
                    checks+=1;bad=(Xbits&dbits).bit_count()
                    if bad<local_best:local_best=bad;local_x=Xbits
                    if bad==0:
                        winner=(Ibits,Xbits,pairs,PH,PV,orient,si);break
                if best_bad is None or local_best<best_bad:
                    best_bad=local_best;best_rec={'I_state':si,'I_path':path(Ibits,Ipar),'X_path':path(local_x,Xpar) if local_x is not None else None,'private_pairs':[list(z) for z in pairs],'orientation':list(orient),'min_double_hits':local_best}
                if winner:break
            if winner:break
        if winner:break
    status={'method':'bpz-t9-joint-private-swap-components','candidate':winner is not None,'cap':args.cap,'I_component_states':len(Istates),'X_component_states':len(Xstates),'I_truncated':Itr,'X_truncated':Xtr,'I_depths':Idepth,'X_depths':Xdepth,'I_direct_add_states':len(Izero),'X_direct_add_states':len(Xzero),'eligible_I_states':eligible,'nine_pair_subsets':subsets,'orientations':orientations,'same_side_valid':sameside,'I_X_checks':checks,'best_min_double_hits':best_bad,'best_near':best_rec}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not winner:
        status['score']=134753;status['absence_exact_over_components']=not Itr and not Xtr;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    Ibits,Xbits,pairs,PH,PV,orient,si=winner;pts,xp=build(Ibits,Xbits,pairs,PH,PV,ring);status.update({'score':len(pts),'winning_I_path':path(Ibits,Ipar),'winning_X_path':path(Xbits,Xpar),'private_pairs':[list(z) for z in pairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)
if __name__=='__main__':main()
