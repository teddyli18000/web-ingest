#!/usr/bin/env python3
"""Census private-neighbour owners of the 38 public C7^5 367-point seeds.

The Gao/BPZ t-construction needs t private pairs with distinct old owners.  The
I0 private-neighbour component reaches t=10 but not t=11.  This script checks
whether any of the other public 367-point basins already exposes >=11 distinct
private owners at the seed itself, which would open a much more tolerant t>=11
construction family.
"""
import argparse, json, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('family_root',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text())
    I0=set(map(int,raw['I0'])); X0=set(map(int,raw['X']))
    fam=json.loads((args.family_root/'data'/'family-f.json').read_text())
    states=[set(map(int,s)) for s in fam['states']]
    seeds=[('bpz-X',X0),('bpz-I0',I0)]+[(f'family-f-{i}',s) for i,s in enumerate(states)]
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    rows=[]
    for name,S in seeds:
        if len(S)!=367 or not t10.independent(S,digits): raise RuntimeError(f'invalid seed {name}')
        pp=t10.private(sum(1<<z for z in S),nb)
        owners=sorted({a for a,q in pp})
        rows.append({'seed':name,'private_pairs':len(pp),'private_owners':len(owners)})
    rows.sort(key=lambda r:(-r['private_owners'],-r['private_pairs'],r['seed']))
    hist={}
    for r in rows: hist[str(r['private_owners'])]=hist.get(str(r['private_owners']),0)+1
    status={'method':'public-367-private-owner-census','seed_count':len(rows),'max_private_owners':max(r['private_owners'] for r in rows),'max_private_pairs':max(r['private_pairs'] for r in rows),'owner_histogram':hist,'top':rows[:20],'t11_seed_exists':any(r['private_owners']>=11 for r in rows)}
    args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print(json.dumps(status,sort_keys=True))

if __name__=='__main__': main()
