#!/usr/bin/env python3
"""Compute exact symmetry orbits of the 20 representative FunSearch one-hit cases.

The public FunSearch priority is invariant under cyclic rotation of its five
coordinates.  The reconstructed seed is therefore checked for the C5 rotation
stabilizer.  We conjugate that stabilizer through the signed-coordinate map and
translation defining representative image 330, then replay its action on the
20 exact t=9 one-hit obstruction states.

If the obstruction collection is closed, deep automorphism-invariant searches
need only one representative per resulting orbit.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_fft import funsearch_seed
from bpz_t9_funsearch_representative_case import PERM, NEGMASK, TRANSLATION, cases, representative_set


def rot(w, k):
    return tuple(w[(j + k) % f.D] for j in range(f.D))


def A(w):
    return tuple(((-w[PERM[j]]) % f.Q) if ((NEGMASK >> j) & 1) else w[PERM[j]] for j in range(f.D))


def Ainv(w):
    out = [0] * f.D
    for j in range(f.D):
        z = (-w[j]) % f.Q if ((NEGMASK >> j) & 1) else w[j]
        out[PERM[j]] = z
    return tuple(out)


def Ttuple(w, k):
    # S = A(seed) + t, so stabilizer is t + A R_k A^{-1}(w-t).
    q = tuple((w[j] - TRANSLATION[j]) % f.Q for j in range(f.D))
    q = Ainv(q)
    q = rot(q, k)
    q = A(q)
    return tuple((q[j] + TRANSLATION[j]) % f.Q for j in range(f.D))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('tan_root', type=Path); ap.add_argument('output', type=Path); args = ap.parse_args()
    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring
    raw = json.loads((args.tan_root / 'data' / 'base_c7.json').read_text())
    I0 = set(map(int, raw['I0']))
    ring = Ring(f.D); digits = tuple(ring.decode(v) for v in range(f.U)); nb = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]

    seed = funsearch_seed(digits)
    for k in range(5):
        rr = {f.enc(rot(digits[v], k)) for v in seed}
        if rr != seed: raise RuntimeError(f'base seed not C5-invariant at k={k}')

    S = representative_set(digits)
    cc = cases(I0, ring, digits, nb)
    if len(cc) != 20: raise RuntimeError('case count drift')
    key_to_case = {(frozenset(c['S']), frozenset(c['D'])): i for i, c in enumerate(cc)}
    perms = []
    for k in range(5):
        p = []
        for i, c in enumerate(cc):
            ts = frozenset(f.enc(Ttuple(digits[v], k)) for v in c['S'])
            td = frozenset(f.enc(Ttuple(digits[v], k)) for v in c['D'])
            if ts != S: raise RuntimeError(f'representative set stabilizer drift k={k} case={i}')
            j = key_to_case.get((ts, td))
            if j is None: raise RuntimeError(f'obstruction family not closed k={k} case={i}')
            tb = f.enc(Ttuple(digits[c['bad']], k))
            if tb != cc[j]['bad']: raise RuntimeError(f'bad-point action drift k={k} {i}->{j}')
            p.append(j)
        if sorted(p) != list(range(20)): raise RuntimeError(f'not permutation k={k}')
        perms.append(p)

    unseen = set(range(20)); orbits = []
    while unseen:
        i = min(unseen); orb = sorted({perms[k][i] for k in range(5)})
        # Close defensively under all generators/actions.
        changed = True
        while changed:
            changed = False
            for a in list(orb):
                for p in perms:
                    b = p[a]
                    if b not in orb: orb.append(b); changed = True
            orb.sort()
        for a in orb: unseen.discard(a)
        orbits.append(orb)
    status = {
        'method': 'FunSearch-representative-C5-stabilizer-onehit-case-orbits',
        'group_order': 5,
        'case_count': 20,
        'permutations': perms,
        'orbits': orbits,
        'orbit_sizes': [len(o) for o in orbits],
        'representatives': [o[0] for o in orbits],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(status, indent=2, sort_keys=True)+'\n'); print(json.dumps(status, sort_keys=True))

if __name__ == '__main__': main()
