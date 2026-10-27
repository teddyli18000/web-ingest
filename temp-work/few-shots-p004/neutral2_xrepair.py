#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import generalized9 as g

MODS={267:15083,294:16388}
PORTS=[
    (11283,13677,0),(15083,14733,1),(13108,13158,0),
    (15953,15910,1),(14328,12277,0),(16388,16046,0),
    (1321,15685,1),(8601,6494,0),(3660,6110,1),
]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('r367',type=Path);ap.add_argument('out',type=Path);args=ap.parse_args()
    digits=tuple(g.dec5(v) for v in range(g.U)); r0=g.load_r(args.r367); x=g.make_x(r0,digits); r=list(r0)
    for i,v in MODS.items(): r[i]=v
    hs=[a if s==0 else b for a,b,s in PORTS]
    vs=[b if s==0 else a for a,b,s in PORTS]
    bad=[i for i,z in enumerate(x) if any(g.conflict(z,h,digits) for h in hs) and any(g.conflict(z,v,digits) for v in vs)]
    print('bad companion indices',bad,'points',[x[i] for i in bad],flush=True)
    if len(bad)!=1:
        args.out.write_text(json.dumps({'kind':'none','method':'neutral2-single-x-repair','reason':'expected one bad X','bad':bad})+'\n');return
    bi=bad[0]; retained=x[:bi]+x[bi+1:]; retained_set=set(retained)
    candidates=[]
    for q in range(g.U):
        if q in retained_set: continue
        if any(g.conflict(q,h,digits) for h in hs) and any(g.conflict(q,v,digits) for v in vs): continue
        if any(g.conflict(q,z,digits) for z in retained): continue
        candidates.append(q)
    print('replacement candidates',candidates,flush=True)
    if not candidates:
        args.out.write_text(json.dumps({'kind':'none','method':'neutral2-single-x-repair','bad_index':bi,'bad_point':x[bi],'replacement_candidates':0})+'\n');return
    q=candidates[0]; xp=list(x);xp[bi]=q
    result={'kind':'coupled-found','method':'neutral2-single-x-repair','score':134770,'depth':2,'best_overlap_seen':1,'bad_index':bi,'bad_point':x[bi],'replacement':q,'replacement_candidates':candidates,'independent_set':r,'companion_set':xp,'ports':[{'center':a,'alt':b,'side':s} for a,b,s in PORTS]}
    args.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print('FOUND',json.dumps({k:result[k] for k in ('score','bad_index','bad_point','replacement','replacement_candidates')},sort_keys=True),flush=True)
if __name__=='__main__':main()
