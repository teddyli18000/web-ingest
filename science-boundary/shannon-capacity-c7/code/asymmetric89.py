#!/usr/bin/env python3
"""Exact asymmetric 8x9 port search for the C7^10 construction.

The published construction uses the same eight deleted R-centres on both
coordinates.  Here the square block is B_L x B_R with |K_L|=8, |K_R|=9
(or the transpose), and the H/V fibers choose 8 and 9 square-safe endpoints
respectively.  A full solution has

  359*358 + (8+9)*367 = 134761

vertices, eight above the current 134753 record.
"""

import argparse, json
from itertools import combinations
from pathlib import Path
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Minisat22

import generalized9 as g

TARGET=134761
BASELINE=134753


def solve(kl,kr,r,x,digits,supports):
    ml=sum(1<<i for i in kl); mr=sum(1<<i for i in kr)
    sl=tuple(g.safe_vertices(ml,supports)); sr=tuple(g.safe_vertices(mr,supports))
    pl,pr=len(kl),len(kr)
    if len(sl)<pl or len(sr)<pr:
        return None,{'safe_l':len(sl),'safe_r':len(sr),'active_h':0,'active_v':0}
    pool=IDPool(); cnf=CNF()
    H=lambda i,e: pool.id(('H',i,e)); V=lambda i,e: pool.id(('V',i,e))
    el=[(a,b) for a,b in combinations(range(len(sl)),2) if g.conflict(sl[a],sl[b],digits)]
    er=[(a,b) for a,b in combinations(range(len(sr)),2) if g.conflict(sr[a],sr[b],digits)]
    for i in range(g.R_SIZE):
        cnf.extend(CardEnc.equals([H(i,e) for e in range(len(sl))],bound=pl,vpool=pool,encoding=EncType.seqcounter).clauses)
        cnf.extend(CardEnc.equals([V(i,e) for e in range(len(sr))],bound=pr,vpool=pool,encoding=EncType.seqcounter).clauses)
        for a,b in el: cnf.append([-H(i,a),-H(i,b)])
        for a,b in er: cnf.append([-V(i,a),-V(i,b)])
    # H(i,e) conflicts V(j,f) iff e~X_j and X_i~f.
    hit_l=[[ei for ei,e in enumerate(sl) if g.conflict(e,xj,digits)] for xj in x]
    hit_r=[[ei for ei,e in enumerate(sr) if g.conflict(e,xi,digits)] for xi in x]
    ah=[j for j,z in enumerate(hit_l) if z]; av=[i for i,z in enumerate(hit_r) if z]
    cross=0
    for i in av:
        for j in ah:
            for e in hit_l[j]:
                h=H(i,e)
                for f in hit_r[i]: cnf.append([-h,-V(j,f)]); cross+=1
    st={'safe_l':len(sl),'safe_r':len(sr),'active_h_targets':len(ah),'active_v_sources':len(av),'endpoint_edges_l':len(el),'endpoint_edges_r':len(er),'cross_clauses':cross,'vars':pool.top,'clauses':len(cnf.clauses)}
    with Minisat22(bootstrap_with=cnf.clauses) as s:
        if not s.solve(): return None,st
        pos={z for z in s.get_model() if z>0}
    hs=[[sl[e] for e in range(len(sl)) if H(i,e) in pos] for i in range(g.R_SIZE)]
    vs=[[sr[e] for e in range(len(sr)) if V(i,e) in pos] for i in range(g.R_SIZE)]
    if any(len(z)!=pl for z in hs) or any(len(z)!=pr for z in vs): raise RuntimeError('cardinality replay failed')
    return (hs,vs),st


def build(kl,kr,model,r,x,digits):
    hs,vs=model; KL=set(kl); KR=set(kr)
    bl=[z for i,z in enumerate(r) if i not in KL]; br=[z for i,z in enumerate(r) if i not in KR]
    C={a*g.U+b for a in bl for b in br}
    for i,xi in enumerate(x):
        C.update(e*g.U+xi for e in hs[i]); C.update(xi*g.U+e for e in vs[i])
    exp=len(bl)*len(br)+len(x)*(len(kl)+len(kr))
    if len(C)!=exp: raise RuntimeError(f'duplicate candidate {len(C)} != {exp}')
    if exp!=TARGET: raise RuntimeError(f'target arithmetic drift {exp}')
    # exact structural replay
    for z in hs:
        for a,b in combinations(z,2):
            if g.conflict(a,b,digits): raise RuntimeError('H fiber conflict')
    for z in vs:
        for a,b in combinations(z,2):
            if g.conflict(a,b,digits): raise RuntimeError('V fiber conflict')
    for i in range(g.R_SIZE):
        for j in range(g.R_SIZE):
            if any(g.conflict(e,x[j],digits) for e in hs[i]) and any(g.conflict(x[i],f,digits) for f in vs[j]):
                raise RuntimeError('cross conflict')
    return C


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('r367',type=Path); ap.add_argument('baseline',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U)); r=g.load_r(args.r367); x=g.make_x(r,digits); supports,_=g.support_masks(r,digits)
    idx={v:i for i,v in enumerate(r)}; k8=tuple(sorted(idx[g.enc5(w)] for w in g.OLD_DELETED)); K=set(k8)
    if len(k8)!=8: raise RuntimeError('K8 drift')
    # Rank extras by square-safe endpoint count; test both orientations because X is not symmetric.
    extras=[]
    for e in range(g.R_SIZE):
        if e in K: continue
        k9=tuple(sorted((*k8,e))); m=sum(1<<i for i in k9); extras.append((len(g.safe_vertices(m,supports)),e))
    extras.sort(reverse=True)
    tested=0; sat=0; best=[]
    for safe9,e in extras:
        k9=tuple(sorted((*k8,e)))
        for orient in ('L8R9','L9R8'):
            kl,kr=(k8,k9) if orient=='L8R9' else (k9,k8)
            tested+=1; model,st=solve(kl,kr,r,x,digits,supports)
            if len(best)<20: best.append({'extra':e,'orientation':orient,**st})
            if model is None: continue
            sat+=1; C=build(kl,kr,model,r,x,digits)
            base={int(p,7) for p in json.loads(args.baseline.read_text())['points']}
            status={'candidate':True,'score':len(C),'method':'asymmetric-8x9-exact-sat','orientation':orient,'k_left':list(kl),'k_right':list(kr),'extra_index':e,'extra_word':''.join(map(str,digits[r[e]])),'tested':tested,'safe9_rank_value':safe9,'solver':st,'removed_vs_baseline':len(base-C),'added_vs_baseline':len(C-base)}
            args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({'points':[g.dec10(z) for z in sorted(C)]},separators=(',',':'))+'\n')
            args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('FOUND',json.dumps(status,sort_keys=True),flush=True); return
    status={'candidate':False,'score':BASELINE,'method':'asymmetric-8x9-exact-sat','tested':tested,'sat':sat,'best_diagnostics':best}
    args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print('NONE',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__': main()
