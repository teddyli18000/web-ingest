#!/usr/bin/env python3
"""Audit whether the known q1->q2->q3 R->A scar walk creates new remote glides.

Compares the complete same-count legal Delaunay event catalog at live R against
q3-fixed and a modest-restraint q3 probe. Persistent root glides, inverses of
already-flipped root glides, and genuinely emergent remote events are separated.
"""
from __future__ import annotations
import argparse,json,pathlib,math
import numpy as np

import diagnose_soft_modes as sm
import search_dynamic_scar_walk_beam as base
from search_from_seed_modes import load_seed
from search_e564_defect_flip_parallel import threshold,perturb
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax

Q3=(511,599,282,502)
SUPPORT={108,282,511,599,502}

def catalog(label,x,support,root_rows,remote_distance):
    ef,rows=base.legal_rows(x); dist=base.graph_distances(ef,support,len(x))
    root={base.key(r):r for r in root_rows}
    inv={(r['add'],r['delete']):r for r in root_rows}
    persistent=[]; inverse=[]; emergent=[]
    for r in rows:
        d=min(dist[v] for v in r['quad'])
        if d<remote_distance: continue
        k=base.key(r); item={'quad':list(r['quad']),'delete':list(r['delete']),'add':list(r['add']),
            'threshold':float(r['threshold']),'graph_distance':int(d)}
        if k in root:
            t0=float(root[k]['threshold']); item['root_threshold']=t0
            item['fractional_drop']=max(0.0,1.0-float(r['threshold'])/max(t0,1e-15))
            persistent.append(item)
        elif k in inv:
            item['root_forward_threshold']=float(inv[k]['threshold']); inverse.append(item)
        else:
            emergent.append(item)
    persistent.sort(key=lambda z:(-z['fractional_drop'],z['threshold']))
    inverse.sort(key=lambda z:z['threshold']); emergent.sort(key=lambda z:z['threshold'])
    out={'label':label,'remote_persistent_count':len(persistent),'remote_inverse_count':len(inverse),
         'remote_emergent_count':len(emergent),'top_softened_root':persistent[:12],
         'top_inverse_root':inverse[:12],'top_emergent':emergent[:20],
         'emergent_below_0p002':sum(z['threshold']<0.002 for z in emergent),
         'emergent_below_0p005':sum(z['threshold']<0.005 for z in emergent),
         'emergent_below_0p01':sum(z['threshold']<0.01 for z in emergent)}
    print('CAT',label,'persistent',len(persistent),'inverse',len(inverse),'emergent',len(emergent),
          '<.002',out['emergent_below_0p002'],'<.005',out['emergent_below_0p005'],'<.01',out['emergent_below_0p01'],flush=True)
    print('EMERGENT',[(z['delete'],z['add'],round(z['threshold'],8),z['graph_distance']) for z in emergent[:12]],flush=True)
    print('SOFTROOT',[(z['delete'],z['add'],round(z['root_threshold'],8),round(z['threshold'],8),round(z['fractional_drop'],4)) for z in persistent[:8]],flush=True)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('live_json'); ap.add_argument('two_flip_result')
    ap.add_argument('--third-multiplier',type=float,default=1.04)
    ap.add_argument('--probe-kappa',type=float,default=100.0); ap.add_argument('--remote-distance',type=int,default=2)
    ap.add_argument('--fixed-maxiter',type=int,default=2600); ap.add_argument('--probe-maxiter',type=int,default=2200)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    _,xroot=load_seed(args.live_json); _,root_rows=base.legal_rows(xroot)
    rec=json.load(open(args.two_flip_result)); st=rec.get('last_both_flipped_state')
    if not st or 'points' not in st: raise RuntimeError('two-flip result lacks last_both_flipped_state.points')
    x0=np.asarray(st['points'],dtype=float); t3=threshold(x0,Q3,'balanced')
    if t3 is None or not math.isfinite(t3): raise RuntimeError('q3 unavailable')
    start=perturb(x0,Q3,float(t3)*args.third_multiplier,'balanced')
    Efix,raw,qfix,xfix,nfix,okfix,msgfix=fixed_relax(sm.xyz_to_vars(start),sorted(SUPPORT),args.fixed_maxiter)
    q3cat=catalog('q3-fixed',xfix,SUPPORT,root_rows,args.remote_distance)
    Ep,rawp,qp,xp,nprobe,okp,msgp,arms,pen=restraint_relax(qfix.copy(),xfix.copy(),sorted(SUPPORT),args.probe_kappa,args.probe_maxiter)
    probecat=catalog('probe',xp,SUPPORT,root_rows,args.remote_distance)
    out={'q3_threshold':float(t3),'q3_fixed_energy':float(Efix),'q3_fixed_ok':bool(okfix),
         'probe_kappa':args.probe_kappa,'probe_energy':float(Ep),'probe_anchor_rms':float(arms),
         'probe_nit':int(nprobe),'probe_ok':bool(okp),'q3_fixed':q3cat,'probe':probecat}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
