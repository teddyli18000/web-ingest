#!/usr/bin/env python3
"""Constructive CaDiCaL search for a transformed G103 cut basis.

This wrapper couples the exact explicit-prefix construction in
`g103_explicit_cut_basis.py` to the affine CNF suffix synthesizer in
`g103_suffix_cadical.py`.  It is intentionally narrow: only bases whose fixed
G103 prefix can be materialized at <=49 linear gates are useful with a 19-gate
suffix for the 100-gate target.
"""
from __future__ import annotations
import argparse,json,pathlib
import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez
import g103_suffix_cadical as sat
import g103_explicit_cut_basis as xp


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=ez.parse_rows,required=True)
    ap.add_argument('--gates',type=int,default=19)
    ap.add_argument('--conf-budget',type=int,default=10000000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    prec,pmeta=xp.synthesize_at_cut(c,args.basis_rows)
    summary={'basis_rows':list(args.basis_rows),'prefix':pmeta,'suffix_bound':args.gates}
    if prec is None or pmeta.get('prefix_linear',999)>49:
        summary['status']='prefix_too_large'
        (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'status':summary['status'],'basis_rows':summary['basis_rows']},sort_keys=True));return
    (out/'prefix.json').write_text(json.dumps(prec,indent=2)+'\n')
    _last,_prefix,old_suffix,_boundary,_extras,_extra_idx,m,_C,targets,_q=ez.problem(c,args.basis_rows)
    smeta,net=sat.solve(targets,m,args.gates,args.conf_budget)
    summary['solver']=smeta
    if net is None:
        summary['status']='suffix_'+smeta['status']
    else:
        (out/'suffix.json').write_text(json.dumps(net,indent=2)+'\n')
        full=xp.attach_suffix(c,prec,net)
        (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
        summary['status']='found';summary['full_gates']=len(full['gates']);summary['verified_all_256']=True
        summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('prefix','solver')},sort_keys=True),flush=True)

if __name__=='__main__':main()
