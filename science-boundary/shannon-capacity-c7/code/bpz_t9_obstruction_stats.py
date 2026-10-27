#!/usr/bin/env python3
"""Rank all distinct t=9 BPZ obstruction masks from the complete I component."""
import argparse,json,sys
from itertools import combinations,product
from pathlib import Path
Q=7;D=5;U=Q**D;N=367;T=9

def conflict(a,b,d):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(d[a],d[b]))
def independent(v,d):
    a=list(v);return all(not conflict(x,y,d) for x,y in combinations(a,2))
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
def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(U)]
    comp,pm,parent=component(sum(1<<z for z in I0),nb)
    if len(comp)!=243:raise RuntimeError(f'component drift {len(comp)}')
    masks={};raw_orient=0
    for ib in comp:
        pp=pm[ib]
        if len({a for a,q in pp})<T:continue
        for pairs in combinations(pp,T):
            if len({a for a,q in pairs})<T:continue
            for o in product((0,1),repeat=T):
                PH=[q if s else a for (a,q),s in zip(pairs,o)];PV=[a if s else q for (a,q),s in zip(pairs,o)]
                if not independent(PH,digits) or not independent(PV,digits):continue
                raw_orient+=1;Dset=ring.nbhd(set(PH))&ring.nbhd(set(PV));mask=sum(1<<z for z in Dset)
                rec=masks.get(mask)
                witness={'I_path':path(ib,parent),'private_pairs':[list(z) for z in pairs],'orientation':list(o),'PH':PH,'PV':PV}
                if rec is None:masks[mask]={'size':len(Dset),'published_X_hits':len(X&Dset),'published_X_hit_points':sorted(X&Dset),'witness':witness,'multiplicity':1}
                else:rec['multiplicity']+=1
    if raw_orient!=640 or len(masks)!=160:raise RuntimeError(f'mask drift raw={raw_orient} unique={len(masks)}')
    rows=list(masks.values())
    by_size=sorted(rows,key=lambda r:(r['size'],r['published_X_hits']))
    by_hits=sorted(rows,key=lambda r:(r['published_X_hits'],r['size']))
    size_hist={};hit_hist={}
    for r in rows:size_hist[str(r['size'])]=size_hist.get(str(r['size']),0)+1;hit_hist[str(r['published_X_hits'])]=hit_hist.get(str(r['published_X_hits']),0)+1
    out={'I_component_states':len(comp),'raw_same_side_orientations':raw_orient,'unique_obstruction_masks':len(masks),'min_size':by_size[0]['size'],'max_size':by_size[-1]['size'],'min_published_X_hits':by_hits[0]['published_X_hits'],'size_histogram':size_hist,'published_X_hit_histogram':hit_hist,'top_by_size':by_size[:20],'top_by_published_X_hits':by_hits[:20]};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True),flush=True)
if __name__=='__main__':main()
