#!/usr/bin/env python3
"""Integer-only verifier for bpz_t9_obstruction_cover_lp.py output."""
import argparse,json,sys
from pathlib import Path
import bpz_t9_obstruction_mis as mis

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('certificate',type=Path);args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I=set(map(int,raw['I0']));X=set(map(int,raw['X']));ring=Ring(mis.D);digits=tuple(ring.decode(v) for v in range(mis.U))
    for a,b in mis.I_SWAPS:I.remove(a);I.add(b)
    pairs=list(mis.PRIVATE_PAIRS);PH=[q if s else a for (a,q),s in zip(pairs,mis.ORIENTATION)];PV=[a if s else q for (a,q),s in zip(pairs,mis.ORIENTATION)];obs=ring.nbhd(set(PH))&ring.nbhd(set(PV));hits=sorted(X&obs)
    if len(obs)!=1098 or hits!=[10665]:raise RuntimeError('obstruction drift')
    obj=json.loads(args.certificate.read_text());den=int(obj['denominator']);entries=obj['cube_units'];units={int(a):int(u) for a,u in entries}
    if den<=0 or any(not 0<=a<mis.U or u<=0 for a,u in units.items()) or len(units)!=len(entries):raise RuntimeError('bad certificate entries')
    total=sum(units.values());cov=[0]*mis.U
    for a,u in units.items():
        for v in mis.cube(digits[a]):
            if v not in obs:cov[v]+=u
    allowed=[v for v in range(mis.U) if v not in obs];minimum=min(cov[v] for v in allowed);valid=minimum>=den
    result={'valid_cover':valid,'denominator':den,'total_units':total,'total_weight':total/den,'minimum_coverage_units':minimum,'proves_alpha_le_366':valid and total<367*den,'obstruction_size':len(obs),'allowed_vertices':len(allowed),'nonzero_cubes':len(units)}
    print(json.dumps(result,sort_keys=True))
    if not valid:raise SystemExit('invalid fractional cover')
if __name__=='__main__':main()
