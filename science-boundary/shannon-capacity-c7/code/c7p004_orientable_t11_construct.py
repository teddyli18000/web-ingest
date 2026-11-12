#!/usr/bin/env python3
"""Construct an orientable 11-port C7^5 gadget, then a >134753 C7^10 code.

Starting from independently valid 14-private-owner C7^5 parents, modify the
parent itself using full adjacent-slice 4D MIS reoptimizations and private
neighbor neutral replacements. The true objective is 11 *simultaneously
orientable* private pairs, not the raw count of private owners.

For any t=11 parent, search translated 367-word auxiliaries for <=2 hits in
D=N[PH]∩N[PV]. This constructs (367-11)^2+22*(367-h)>=134766 points.
"""
import argparse,base64,hashlib,itertools,json,math,random,struct,time
from collections import Counter
from pathlib import Path
import numpy as np
from c7p5_two_layer_repair import solve_pair, independent, dump_certificate
from c7p5_port_aware_block_walk import PortGeometry,closed_neighborhood

P=(1,7,49,343,2401)
U=7**5
DIG=np.array([[(v//p)%7 for p in P] for v in range(U)],dtype=np.int16)

def conf(a,b):
    return all((int(DIG[a,k])-int(DIG[b,k]))%7 in (0,1,6) for k in range(5))

def load_code(parent):
    blob=base64.b64decode(parent['data'])
    h=hashlib.sha256(blob).hexdigest()
    assert h==parent.get('sha256',parent.get('sha256_decoded_bytes'))
    code=set(struct.unpack('<367H',blob))
    assert len(code)==367 and independent(sorted(code))
    return code

def profiles(g):
    owners={}
    for z in range(U):
        if z not in g.S and g.count[z]==1:
            owners.setdefault(g.xor[z]-1,[]).append(z)
    return owners

def orient(by,t):
    owners=sorted(by,key=lambda a:(len(by[a]),a))
    H=[];V=[];selected=[]
    def dfs(i):
        if len(selected)>=t:return selected.copy()
        if len(selected)+len(owners)-i<t:return None
        a=owners[i]
        for q in by[a]:
            if all(not conf(q,x) for x in H) and all(not conf(a,x) for x in V):
                H.append(q);V.append(a);selected.append((a,q,1))
                out=dfs(i+1)
                if out:return out
                selected.pop();V.pop();H.pop()
            if all(not conf(a,x) for x in H) and all(not conf(q,x) for x in V):
                H.append(a);V.append(q);selected.append((a,q,0))
                out=dfs(i+1)
                if out:return out
                selected.pop();V.pop();H.pop()
        return dfs(i+1)
    return dfs(0) if len(owners)>=t else None

def metric(by):
    for t in (11,10,9,8,7):
        wit=orient(by,t)
        if wit:return t,wit
    return 0,None

def arr(S):
    v=np.zeros((7,)*5,dtype=float)
    d=DIG[list(S)]
    v[tuple(d.T)]=1.
    return v

def encode(d):
    return sum(int(z)*P[i] for i,z in enumerate(d))

def shift_set(S,trans):
    delta=tuple(map(int,trans))
    return {sum((int(DIG[v,i])+delta[i])%7*P[i] for i in range(5)) for v in S}

def build(I,aux,pairs):
    t=11;R={a for a,b,c in pairs}
    assert len(R)==t
    B=I-R
    PH={b if color else a for a,b,color in pairs}
    PV={a if color else b for a,b,color in pairs}
    assert len(PH)==len(PV)==t and independent(sorted(PH)) and independent(sorted(PV))
    NH=set().union(*(set(closed_neighborhood(z)) for z in PH))
    NV=set().union(*(set(closed_neighborhood(z)) for z in PV))
    D=NH&NV
    assert not(D&aux)
    X0=aux-(NH|NV);XH=aux&NH;XV=aux&NV
    pts=set()
    for A,C in ((B,B),(R,X0),(PH,XH),(PV,XV),(X0,R),(XH,PV),(XV,PH)):
        pts.update((u,v) for u in A for v in C)
    expected=(367-t)**2+2*t*len(aux)
    assert len(pts)==expected
    words=sorted(''.join(str(int(x)) for x in list(DIG[u])+list(DIG[v])) for u,v in pts)
    assert len(words)==expected and len(set(words))==expected
    return words

def scan(I,pairs,sources):
    PH={b if color else a for a,b,color in pairs}
    PV={a if color else b for a,b,color in pairs}
    assert independent(sorted(PH)) and independent(sorted(PV))
    NH=set().union(*(set(closed_neighborhood(x)) for x in PH))
    NV=set().union(*(set(closed_neighborhood(x)) for x in PV))
    D=NH&NV
    FD=np.fft.fftn(arr(D))
    best=(367,None,None,None)
    for name,S in sources:
        corr=np.rint(np.fft.ifftn(np.conj(np.fft.fftn(arr(S)))*FD).real).astype(np.int16)
        m=int(corr.min())
        if m<best[0]:
            t=tuple(map(int,np.unravel_index(int(corr.argmin()),corr.shape)))
            for sign in (1,-1):
                delta=tuple(sign*x for x in t)
                X=shift_set(S,delta)
                hits=len(X&D)
                if hits<best[0]:
                    best=(hits,name,delta,X)
        if best[0]<=2:break
    return best,len(D)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('seed_file',type=Path);p.add_argument('tandon',type=Path)
    p.add_argument('family',type=Path);p.add_argument('out',type=Path)
    p.add_argument('--state',type=int,default=0)
    p.add_argument('--seed',type=int,default=20261112)
    p.add_argument('--moves',type=int,default=300)
    p.add_argument('--seconds',type=float,default=3.)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    raw=json.loads(a.seed_file.read_text())
    seeds=[(x['name'],load_code(x)) for x in raw['parents']]
    source_name,S=seeds[a.state]
    g=PortGeometry(S);rng=random.Random(a.seed)
    prior=profiles(g);curr_t,_=metric(prior)
    bestorient=curr_t;best_owners=len(prior);besthits=367;bestparent=None
    t11_found=0;neutral=0;completed=0;statuses=Counter()
    data=json.loads((a.tandon/'data/base_c7.json').read_text())
    fam=json.loads((a.family/'data/family-f.json').read_text())
    auxiliaries=[('I0',set(data['I0'])),('X',set(data['X']))]
    auxiliaries += [(f'F{i}',set(x)) for i,x in enumerate(fam['states'])]
    auxiliaries += seeds
    assert all(len(x)==367 and independent(sorted(x)) for name,x in auxiliaries)
    start=time.monotonic()
    for step in range(a.moves):
        before=g.S.copy()
        by=profiles(g)
        if rng.random()<.25 and by:
            owner=rng.choice(list(by))
            v=rng.choice(by[owner])
            cand=(before-{owner})|{v}
        else:
            axis=rng.randrange(5);layer=rng.randrange(7)
            cand,res=solve_pair(before,axis,layer,rng,a.seconds)
            statuses['block_'+str(res['solver_status'])]+=1
        if len(cand)>367:
            dump_certificate(cand,a.out/'certificate.json')
            print('FOUND_368',len(cand),flush=True)
            bestparent=list(sorted(cand));break
        assert len(cand)==367 and independent(sorted(cand))
        g.move(cand)
        newby=profiles(g)
        next_t,witness=metric(newby)
        bestorient=max(bestorient,next_t);best_owners=max(best_owners,len(newby))
        if witness is not None and next_t>=11:
            t11_found+=1
            best,ds=scan(g.S,witness,auxiliaries+[('new-parent',g.S)])
            if best[0]<besthits:
                besthits=best[0]
                bestparent={'points':sorted(g.S),'private_pairs':[[i,j] for i,j,c in witness],
                    'orientation':[c for i,j,c in witness],
                    'obstruction_size':ds,'best_auxiliary':best[1],'aux_shift':best[2],
                    'hits':best[0]}
                (a.out/'best_parent.json').write_text(json.dumps(bestparent,indent=2)+'\n')
                print('T11',json.dumps({'step':step,'hits':besthits,'obstruction':ds}),flush=True)
            if best[0]<=2:
                words=build(g.S,best[3]-set().union(*(set(closed_neighborhood(x)) for x in
                    ({j if c else i for i,j,c in witness})) & set().union(*(set(closed_neighborhood(x))
                    for x in ({i if c else j for i,j,c in witness})))),witness)
                (a.out/'certificate.json').write_text(json.dumps({'points':words},separators=(',',':'))+'\n')
                print('FOUND_P004',len(words),'step',step,flush=True)
                break
        temp=max(.18,1.2*(1-step/max(1,a.moves)))
        diff=(next_t-curr_t)*4 + (len(newby)-len(by))*.5
        accept=diff>=0 or rng.random()<math.exp(diff/temp)
        if not accept:
            g.move(before)
        elif cand!=before:neutral+=1;curr_t=next_t
        completed+=1
        if step%40==0:
            print('PROGRESS',json.dumps({'step':step,'best_orient':bestorient,
                'best_owners':best_owners,'best_hits':besthits,'accepted':neutral}),flush=True)
        if (a.out/'certificate.json').exists():break
    result={'method':'constructive-c7five-orientable-11-ports-and-365-auxiliary',
        'seed_name':source_name,'random_seed':a.seed,'moves':completed,
        'accepted_neutral':neutral,'best_orientable_pairs':bestorient,
        'best_private_owners':best_owners,'t11_parents_found':t11_found,
        'best_forbidden_hits':besthits if t11_found else None,
        'candidate':(a.out/'certificate.json').exists(),
        'elapsed_seconds':round(time.monotonic()-start,2),
        'solver_statuses':dict(statuses)}
    (a.out/'status.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps(result,sort_keys=True),flush=True)

if __name__=='__main__':main()
