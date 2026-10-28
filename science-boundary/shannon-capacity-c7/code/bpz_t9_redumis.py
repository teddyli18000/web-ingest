#!/usr/bin/env python3
"""Replay a ReduMIS solution on the BPZ t=9 obstruction graph."""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_obstruction_mis as mis
import bpz_t9_kamis as bridge


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path)
    ap.add_argument('mapping',type=Path)
    ap.add_argument('solution',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('status',type=Path)
    args=ap.parse_args()
    I,_,pairs,PH,PV,ring,digits,obstruction,lower=bridge.reconstruct(args.tan_root)
    allowed=list(map(int,json.loads(args.mapping.read_text())['allowed']))
    bits=[int(x.strip()) for x in args.solution.read_text().splitlines() if x.strip()]
    if len(bits)!=len(allowed) or any(x not in (0,1) for x in bits):
        raise RuntimeError(f'unexpected ReduMIS vector: {len(bits)} entries for {len(allowed)} vertices')
    X=[v for v,take in zip(allowed,bits) if take]
    if set(X)&obstruction or not mis.independent(X,digits):
        raise RuntimeError('ReduMIS solution replay failed')
    status={'method':'bpz-t9-redumis','auxiliary_size':len(X),'known_lower_bound':len(lower),'candidate':len(X)>=mis.N}
    if len(X)>=mis.N:
        X=X[:mis.N]
        points,xp=mis.build(I,X,pairs,PH,PV,ring)
        if len(points)!=mis.TARGET: raise RuntimeError(f'10D target drift {len(points)}')
        status.update({'score':len(points),'auxiliary_size_used':len(X),'private_pairs':[list(z) for z in pairs],'orientation':list(mis.ORIENTATION),'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n')
        print('FOUND',json.dumps(status,sort_keys=True))
    else:
        status.update({'score':134753,'conclusion':'no-breakthrough-in-this-heuristic-run'})
        print('NONE',json.dumps(status,sort_keys=True))
    args.status.parent.mkdir(parents=True,exist_ok=True)
    args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': main()
