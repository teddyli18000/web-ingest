#!/usr/bin/env python3
"""Maximum-closure frontier around the 63-factor support-3 obstruction.

The minimal owner-clique obstruction uses 59 core owners.  This program enlarges
its factor universe in two nested, structurally motivated ways while retaining
support size <=3:

  subset   : S(z) is nonempty and entirely contained in the 59 owner set;
  overlap2 : |S(z) cap O| >= 2.

For every BPZ terminal scenario it forms all ordered outside-outside pairs from
the selected factor universe and computes the exact maximum-closure relaxation
of true score gain: each selected new point has reward +1 and forces deletion
of every conflicting old BxB/periphery point, charged once globally.  New-new
conflicts are deliberately ignored, so closure optimum 0 is a rigorous upper
bound closing that entire factor shell.

Positive closure is only a signal for a later exact conflict-aware solve; this
script never claims a breakthrough from a relaxation.
"""
from __future__ import annotations
import argparse,json,os,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery

PINNED_COMMIT='c753408492dde92a239708986d16c15dbf6c3235'
OWNERS=frozenset((1393,1485,1577,1644,1985,2053,2695,3079,3781,3862,3873,3940,4014,4025,4106,4440,4768,5132,5466,5852,6012,6218,6236,6249,6310,6321,6462,6545,6828,7156,7519,7847,7912,8195,8231,8321,8399,8491,8606,8666,8758,8875,8888,9216,9593,9907,10217,10284,10551,10612,10879,10960,11054,11305,11653,12344,12573,12672,13266))

def closure(losses):
    touched=sorted(set().union(*losses)) if losses else [];bi={p:i for i,p in enumerate(touched)};n=len(losses);m=len(touched);s=n+m;t=s+1;g=Dinic(t+1);inf=n+m+10
    for i,ls in enumerate(losses):
        g.add(s,i,1)
        for p in ls:g.add(i,n+bi[p],inf)
    for j in range(m):g.add(n+j,t,1)
    cut=g.flow(s,t);side=g.source_side(s);chosen=[i for i in range(n) if i in side];lost=set()
    for i in chosen:lost.update(losses[i])
    gain=len(chosen)-len(lost)
    if gain!=n-cut:raise RuntimeError(('closure mismatch',gain,n-cut))
    return gain,len(chosen),len(lost),len(touched)

def select_factors(ring,B,mode):
    F=[];supports={};hist={}
    for z in range(ring.n):
        if z in B:continue
        S=frozenset(ring.NB[z]&B)
        if not S or len(S)>3:continue
        ok=(S<=OWNERS) if mode=='subset' else (len(S&OWNERS)>=2)
        if ok:F.append(z);supports[z]=S;hist[len(S)]=hist.get(len(S),0)+1
    return F,supports,hist

def solve(task):
    root_s,mode,q,r,o,pair_limit=task;root=Path(root_s);_base,ring,B,fam=load_geometry(root);B=set(B);F,supports,hist=select_factors(ring,B,mode);P=terminal_periphery(fam,q,r,o);baseline={(a,b) for a in B for b in B}|P
    raw_pairs=len(F)*len(F);row={'mode':mode,'q':q,'r':r,'terminal_orientation':o,'factor_count':len(F),'support_histogram':hist,'raw_pair_count':raw_pairs,'candidate_count':None,'closure_gain':None,'closure_selected':None,'closure_deleted':None,'touched_blockers':None,'status':'counted'}
    if raw_pairs>pair_limit:row['status']='pair-limit';return row
    candidates=[(x,y) for x in F for y in F if (x,y) not in baseline];row['candidate_count']=len(candidates)
    by_first={}
    for p in P:by_first.setdefault(p[0],[]).append(p)
    keys=set(by_first);losses=[]
    for x,y in candidates:
        hit={(a,b) for a in supports[x] for b in supports[y]}
        for a in ring.NB[x]&keys:
            for p in by_first[a]:
                if p[1] in ring.NB[y]:hit.add(p)
        if not hit<=baseline:raise RuntimeError(('loss outside baseline',x,y))
        losses.append(hit)
    t=time.time();g,ns,nd,nt=closure(losses);row.update({'closure_gain':g,'closure_selected':ns,'closure_deleted':nd,'touched_blockers':nt,'closure_seconds':time.time()-t,'status':'closed' if g<=0 else 'positive'});return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--modes',default='subset,overlap2');ap.add_argument('--pair-limit',type=int,default=300000);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args();root=a.tan_root.resolve();modes=[x.strip() for x in a.modes.split(',') if x.strip()]
    tasks=[(str(root),m,q,r,o,a.pair_limit) for m in modes for q in ('O','H','V') for r in ('O','H','V') for o in (0,1)];workers=max(1,min(4,a.workers,len(tasks)));rows=[]
    if workers==1:rows=[solve(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve,t) for t in tasks]
            for f in as_completed(fs):rows.append(f.result())
    rows.sort(key=lambda x:(x['mode'],x['q'],x['r'],x['terminal_orientation']))
    summary={}
    for m in modes:
        rr=[x for x in rows if x['mode']==m];summary[m]={'factor_count':rr[0]['factor_count'] if rr else None,'support_histogram':rr[0]['support_histogram'] if rr else None,'max_raw_pairs':max((x['raw_pair_count'] for x in rr),default=0),'max_closure_gain':max((x['closure_gain'] for x in rr if x['closure_gain'] is not None),default=None),'positive_scenarios':sum((x['closure_gain'] or 0)>0 for x in rr),'pair_limit_scenarios':sum(x['status']=='pair-limit' for x in rr)}
    out={'method':'support3-obstruction-owner-shell-closure','source_commit':PINNED_COMMIT,'owner_count':len(OWNERS),'modes':modes,'pair_limit':a.pair_limit,'workers':workers,'summary':summary,'rows':rows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='rows'},sort_keys=True))
if __name__=='__main__':main()
