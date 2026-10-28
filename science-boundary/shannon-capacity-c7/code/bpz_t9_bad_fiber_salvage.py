#!/usr/bin/env python3
"""Salvage natural 10D points involving the deleted one-hit auxiliary vertex.

A t=9 one-hit construction becomes a valid 134752 certificate after deleting
its unique bad auxiliary point x.  The nominal t=9 product template would have
used x in fibers involving PH/PV, but x lies in both neighborhood unions.  This
script ignores the template assignment and simply tests the natural 10D points

    PH×{x}, PV×{x}, {x}×PH, {x}×PV

against the entire valid 134752 seed.  Any two individually safe candidates
that are mutually nonconfusable give an unrestricted 134754 certificate.
"""
import argparse,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_representative_case import cases


def conflict10(a,b):
    return all(((x-y)%7) in (0,1,6) for x,y in zip(a,b))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);ap.add_argument('--case',type=int,required=True);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    c=cases(I0,ring,digits,nb)[args.case];X=set(c['S'])-{c['bad']};Ibits,pairs,orient,PH,PV=c['witness'];pts,_=f.build(Ibits,sum(1<<q for q in X),pairs,PH,PV,ring)
    if len(pts)!=134752:raise RuntimeError(f'base score drift {len(pts)}')
    base=[tuple(map(int,p)) for p in pts];x=digits[c['bad']]
    cand=set()
    for u in set(PH)|set(PV):
        q=digits[u];cand.add(q+x);cand.add(x+q)
    safe=[]
    for z in sorted(cand):
        if all(not conflict10(z,p) for p in base):safe.append(z)
    pair=None
    for i,a in enumerate(safe):
        for b in safe[i+1:]:
            if not conflict10(a,b):pair=(a,b);break
        if pair:break
    st={'method':'bpz-t9-bad-fiber-natural-10d-salvage','case_index':args.case,'obstruction_index':c['obstruction_index'],'bad':c['bad'],'natural_candidates':len(cand),'individually_safe':len(safe),'safe_points':[''.join(map(str,z)) for z in safe],'candidate':pair is not None,'score':134754 if pair else 134752}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if pair:
        out=set(pts);out.update(''.join(map(str,z)) for z in pair)
        if len(out)!=134754:raise RuntimeError('salvage score drift')
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':sorted(out)},separators=(',',':'))+'\n');st['added_points']=[''.join(map(str,z)) for z in pair]
    args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(('FOUND' if pair else 'NONE'),json.dumps(st,sort_keys=True))

if __name__=='__main__':main()
