#!/usr/bin/env python3
"""Exact unrestricted C7^5 MIS for a size-ranked BPZ t=9 obstruction mask.

All 160 distinct same-side-valid obstruction masks D=N(PH) cap N(PV) from the
complete 243-state private-swap component of the BPZ main set are reconstructed.
They are ranked by (|D|, number of published-X hits, witness data).  The chosen
rank asks whether C7^5\D has an independent 367-set using the exact binary-cube
clique cover and a native global cardinality constraint.  SAT materializes the
corresponding 134770-point Gao construction.
"""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path
from pysat.solvers import Minicard
Q=7;DIM=5;U=Q**DIM;N=367;T=9;TARGET=N*N+T*T

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
def values(bits):
    while bits:
        z=bits&-bits;yield z.bit_length()-1;bits^=z
def private(bits,nb):
    out=[]
    for q in range(U):
        if (bits>>q)&1:continue
        h=nb[q]&bits
        if h.bit_count()==1:out.append((h.bit_length()-1,q))
    return sorted(out)
def component(start,nb):
    seen={start};front=[start];pm={};parent={start:None}
    while front:
        nxt=[]
        for b in front:
            pp=private(b,nb);pm[b]=pp
            for a,q in pp:
                c=b^(1<<a)^(1<<q)
                if c not in seen:seen.add(c);parent[c]=(b,a,q);nxt.append(c)
        front=nxt
    return seen,pm,parent
def path(b,parent):
    out=[]
    while parent[b] is not None:
        p,a,q=parent[b];out.append([a,q]);b=p
    return list(reversed(out))
def all_masks(I0,X,ring,digits,nb):
    comp,pm,parent=component(sum(1<<z for z in I0),nb)
    if len(comp)!=243:raise RuntimeError(f'component drift {len(comp)}')
    masks={};raw=0
    for ib in comp:
        pp=pm[ib]
        if len({a for a,q in pp})<T:continue
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T:continue
            for o in product((0,1),repeat=T):
                PH=[q if s else a for (a,q),s in zip(pairs,o)];PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,digits) or not independent(PV,digits):continue
                raw+=1;Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));mask=sum(1<<z for z in Dset)
                if mask not in masks:masks[mask]={'mask':mask,'size':len(Dset),'published_X_hits':len(X&Dset),'published_X_hit_points':sorted(X&Dset),'Ibits':ib,'I_path':path(ib,parent),'pairs':pairs,'orientation':o,'PH':PH,'PV':PV}
    if raw!=640 or len(masks)!=160:raise RuntimeError(f'mask drift raw={raw} unique={len(masks)}')
    rows=list(masks.values());rows.sort(key=lambda r:(r['size'],r['published_X_hits'],r['I_path'],r['orientation']))
    return rows
def enc(w):
    v=0;m=1
    for x in w:v+=x*m;m*=Q
    return v
def cube(a):
    for b in product((0,1),repeat=DIM):yield enc(tuple((a[j]+b[j])%Q for j in range(DIM)))
def build(row,X,ring):
    I=set(values(row['Ibits']));pairs=row['pairs'];PH=row['PH'];PV=row['PV'];R={a for a,q in pairs};B=I-R;NH=ring.nbhd(set(PH));NV=ring.nbhd(set(PV));X=set(X)
    if X&NH&NV:raise RuntimeError('SAT X still hits D')
    X0=X-(NH|NV);XH=X&NH;XV=X&NV;P=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:P.add((a,c))
    if len(P)!=TARGET:raise RuntimeError(f'score drift {len(P)}')
    return sorted(''.join(map(str,ring.decode(a)+ring.decode(b))) for a,b in P),(len(X0),len(XH),len(XV))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--rank',type=int,required=True);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));Xpub=set(map(int,raw['X']));ring=Ring(DIM);digits=tuple(ring.decode(v) for v in range(U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    rows=all_masks(I0,Xpub,ring,digits,nb)
    if not 0<=args.rank<len(rows):raise SystemExit('rank out of range')
    row=rows[args.rank];Dmask=row['mask'];obstruction=set(values(Dmask));allowed=[v for v in range(U) if not ((Dmask>>v)&1)];aset=set(allowed);var={v:i+1 for i,v in enumerate(allowed)}
    s=Minicard();nc=0;lt=0;mx=0
    for a in range(U):
        lits=[var[v] for v in cube(digits[a]) if v in aset]
        if len(lits)>=2:s.add_atmost(lits,1);nc+=1;lt+=len(lits);mx=max(mx,len(lits))
    s.add_atmost([-var[v] for v in allowed],len(allowed)-N)
    setup={'rank_by_size':args.rank,'obstruction_size':row['size'],'published_X_hits':row['published_X_hits'],'published_X_hit_points':row['published_X_hit_points'],'allowed_vertices':len(allowed),'cube_constraints':nc,'cube_literal_total':lt,'max_allowed_per_cube':mx,'target_auxiliary_size':N,'target_10d_score':TARGET,'I_path':row['I_path'],'private_pairs':[list(z) for z in row['pairs']],'orientation':list(row['orientation'])};print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=s.solve();model=s.get_model() if sat else None;s.delete();args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        st={'candidate':False,'sat':False,'method':'bpz-t9-size-ranked-obstruction-MIS-exact','score':134753,'setup':setup};args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(st,sort_keys=True),flush=True);return
    pos={z for z in model if z>0};X=[v for v in allowed if var[v] in pos][:N]
    if len(X)!=N or not independent(X,digits) or set(X)&obstruction:raise RuntimeError('SAT replay failed')
    pts,xp=build(row,X,ring);st={'candidate':True,'sat':True,'method':'bpz-t9-size-ranked-obstruction-MIS-exact','score':len(pts),'auxiliary_points':X,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]},'setup':setup};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps({k:v for k,v in st.items() if k!='auxiliary_points'},sort_keys=True),flush=True)
if __name__=='__main__':main()
