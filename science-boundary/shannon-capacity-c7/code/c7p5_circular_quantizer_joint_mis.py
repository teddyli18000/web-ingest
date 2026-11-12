#!/usr/bin/env python3
"""Exact construction of C7^5 codes from jointly variable circular quantizers.

A 382-word circular template is quantized coordinatewise. Unlike the
fixed 7-bin quantizer, each of five coordinates may shift every one of six
bin boundaries independently by up to J residues. Each of the 382 original
template positions consequently has several candidate five-dimensional
quantizations; their union relaxes cross-position threshold consistency.
We add all 5D words nonconfusable with the original quantizer's conflict-free
subcore, then solve exact MIS over the entire combined universe.

The resulting witness, if >367, squares to an immediate p004 candidate.
Otherwise a 367-word witness can serve as a genuinely distinct auxiliary in
the exact 16807-translation Hall-gluing campaign.
"""
import argparse,itertools,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

P=(1,7,49,343,2401)
GEN=(1,7,49,343,109)
MOD=382
CUTS=(55,109,164,218,273,327)
STEPS=tuple(itertools.product((-1,0,1),repeat=5))

def digits(v):return tuple(v//p%7 for p in P)
def integer(d):return sum(int(d[j])*P[j] for j in range(5))
def neighbors(v):
    d=digits(v)
    return tuple(integer(tuple((d[j]+s[j])%7 for j in range(5))) for s in STEPS)

def independent(S):
    L=list(S)
    return len(set(L))==len(L) and all(
        any((a//p-b//p)%7 not in (0,1,6) for p in P)
        for i,a in enumerate(L) for b in L[i+1:])

def circular(phase):
    return {
        integer(tuple(sum(((t*GEN[j]+phase[j])%MOD)>=b for b in CUTS)
                      for j in range(5)))
        for t in range(MOD)
    }

def candidate_pool(phase,jitter):
    raw=circular(phase)
    assert len(raw)==382
    isolated={x for x in raw if not (set(neighbors(x))&raw-{x})}
    forbidden={z for v in isolated for z in neighbors(v)}
    pool=set(range(7**5))-forbidden
    assert len(isolated)>=300
    for t in range(MOD):
        choices=[]
        for j in range(5):
            residue=(t*GEN[j]+phase[j])%MOD
            q=sum(residue>=b for b in CUTS)
            allowed={q}
            for k,b in enumerate(CUTS):
                if b-jitter<=residue<b:allowed.add(k+1)
                if b<=residue<b+jitter:allowed.add(k)
            choices.append(sorted(allowed))
        for d in itertools.product(*choices):pool.add(integer(d))
    return isolated,pool

def solve(phase,jitter,seconds):
    isolated,U=candidate_pool(phase,jitter)
    V=sorted(U);n=len(V);index={v:i for i,v in enumerate(V)}
    rows=[];cols=[]
    for i,v in enumerate(V):
        for z in neighbors(v):
            j=index.get(z)
            if j is not None and j>i:
                rows.append(i);cols.append(j)
    e=len(rows)
    edges=coo_matrix((np.ones(2*e),(
        np.repeat(np.arange(e),2),
        np.column_stack((rows,cols)).ravel())),shape=(e,n)).tocsr()
    t0=time.monotonic()
    opt=milp(-np.ones(n),integrality=np.ones(n),
             bounds=Bounds(np.zeros(n),np.ones(n)),
             constraints=LinearConstraint(edges,-np.inf,np.ones(e)),
             options={'time_limit':seconds,'mip_rel_gap':0})
    selected=sorted(V[i] for i in range(n) if opt.x is not None and opt.x[i]>.5)
    assert independent(selected)
    return selected,{'phase':list(phase),'jitter':jitter,
                     'isolated_raw_core':len(isolated),'candidate_vertices':n,
                     'candidate_conflicts':e,'solver_status':int(opt.status),
                     'score':len(selected),'optimal':opt.status==0,
                     'bound':float(-opt.mip_dual_bound) if opt.mip_dual_bound is not None else None,
                     'solver_seconds':time.monotonic()-t0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('output',type=Path)
    ap.add_argument('--phase',required=True)
    ap.add_argument('--jitter',type=int,default=7)
    ap.add_argument('--seconds',type=float,default=45)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    phase=tuple(int(x) for x in a.phase.split(','))
    assert len(phase)==5 and all(0<=x<MOD for x in phase) and 0<=a.jitter<=21
    selected,stats=solve(phase,a.jitter,a.seconds)
    assert stats['optimal']
    (a.output/'parent.ids').write_text(''.join(f'{v}\n' for v in selected))
    (a.output/'status.json').write_text(json.dumps(stats,indent=2,sort_keys=True)+'\n')
    if len(selected)>=368:
        S=selected[:368]
        w=[''.join(str(v//p%7) for p in P) for v in S]
        points=sorted(a+b for a in w for b in w)
        assert len(points)==135424
        (a.output/'certificate.json').write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
    print('FINAL',json.dumps(stats,sort_keys=True),flush=True)

if __name__=='__main__':
    main()
