#!/usr/bin/env python3
"""Compare current low-AND AES S-box families with the near-100 seed families.

The point is architectural triage, not record claiming.  NIST now contains a
28-AND / 124-gate circuit and a 29-AND / 137-gate circuit, both substantially
farther from the gate-count record than A32/G103 but with different nonlinear
budgets.  This script independently parses and verifies those public circuits,
then compares exact nonlinear truth functions and recursive AND-dependency
fingerprints against G103, A34/G110, and the Few Shots 101 circuit.

Exact-function overlap is only a coordinate-dependent diversity signal.  Zero
overlap does not prove affine inequivalence; the recursive shape hash provides a
second structural descriptor.
"""
from __future__ import annotations

import json
import pathlib

import seed_family_census as sf

SEEDS={
    'nist-a28-g124':'https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt',
    'nist-a29-g137':'https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-sbox/aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt',
    'nist-a32-g103':sf.DEFAULTS['nist-a32-g103'],
    'nist-a34-g110':sf.DEFAULTS['nist-a34-g110'],
    'fs-101':sf.DEFAULTS['fs-101'],
}


def main():
    seeds={n:sf.load(n,u) for n,u in SEEDS.items()}
    out={'seeds':{},'pairs':{}}
    for n,s in seeds.items():
        sm=dict(s['summary'])
        sm['and_functions']=len(s['and_functions'])
        sm['wire_functions']=len(s['wire_functions'])
        out['seeds'][n]=sm
    names=list(seeds)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            A=seeds[a];B=seeds[b]
            aa=A['and_functions'];bb=B['and_functions']
            wa=A['wire_functions'];wb=B['wire_functions']
            out['pairs'][f'{a}__{b}']={
                'shared_and_functions':len(aa&bb),
                'and_union':len(aa|bb),
                'and_jaccard':round(len(aa&bb)/len(aa|bb),6),
                'shared_wire_functions':len(wa&wb),
                'wire_union':len(wa|wb),
                'same_and_shape_hash':A['summary']['and_shape_hash']==B['summary']['and_shape_hash'],
                'same_recursive_and_shape_hash':A['summary']['recursive_and_shape_hash']==B['summary']['recursive_and_shape_hash'],
            }
    pathlib.Path('low-and-family-census.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':
    main()
