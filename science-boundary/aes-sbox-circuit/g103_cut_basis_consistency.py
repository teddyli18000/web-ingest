#!/usr/bin/env python3
"""Audit transformed G103 cut coordinates gate-by-gate.

A genuine GL(3,2) change of the three non-atomic cut coordinates must preserve
all XOR relations in the pure-linear suffix.  This diagnostic checks that the
transformed output vector of every original suffix gate equals the XOR of the
transformed parent vectors, then independently checks retained-guide monotone
closure.  Any mismatch is an implementation bug, not a circuit lower bound.
"""
from __future__ import annotations
import argparse,json
import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf
import g103_suffix_exact_z3 as ez
import g103_cut_basis_census as cb
import g103_suffix_guide_subset as gs


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--basis-rows',type=ez.parse_rows,required=True)
    a=ap.parse_args(); c=ras.load_circuit('nist-g103')
    _last,_pre,suffix,boundary=suf.split(c)
    extras,_=cb.semantic_cut_extras(c,boundary); idx=[boundary.index(w) for w in extras]
    cmap=cb.coeff_map(a.basis_rows)
    q={w:1<<i for i,w in enumerate(boundary)}
    tq={w:cb.transform_mask(1<<i,idx,cmap) for i,w in enumerate(boundary)}
    mism=[]; guides=[]
    for j,g in enumerate(suffix):
        old=q[g['a']]^q[g['b']]; q[g['out']]=old
        new=cb.transform_mask(old,idx,cmap)
        parent=tq[g['a']]^tq[g['b']]
        if new!=parent: mism.append({'gate':j,'out':g['out'],'new':new,'parent_xor':parent})
        tq[g['out']]=new; guides.append(new)
    ok,order,parents,remaining=gs.close_subset(len(boundary),guides)
    # Also report transformed images of the three old coordinate unit vectors;
    # in a correct coordinate change these need not themselves be unit vectors,
    # because they are old e_i expressed in the new y basis.
    coord_images=[cb.transform_mask(1<<i,idx,cmap) for i in idx]
    print(json.dumps({'basis_rows':list(a.basis_rows),'extras':extras,'extra_idx':idx,
                      'coord_images':coord_images,'gate_relation_mismatches':mism,
                      'closure_ok':ok,'closure_order':len(order),
                      'remaining_count':len(remaining),'remaining':remaining},sort_keys=True))

if __name__=='__main__': main()
