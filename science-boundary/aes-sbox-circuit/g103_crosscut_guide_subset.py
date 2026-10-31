#!/usr/bin/env python3
"""Exact cross-cut retained-guide census for the final G103 AND/output region.

Take the original NIST G103 circuit at AND-release interval 31.  The remaining
region contains the final AND atom plus 25 linear XOR/XNOR gates: some linear
functions are produced before the final AND and the rest after it.  The old
pre/post split is not treated as fixed here.

For a selected subset of those 25 original linear *functions*, repeatedly:
  * materialize every retained function that is XOR/XNOR of two available
    affine values;
  * when both exact operands of the final ordered AND are available, release its
    nonlinear atom;
then continue to monotone closure.  Because retained function values and the AND
function are fixed, this closure is independent of scheduling choices.  Thus
exhausting all 22-of-25 subsets exactly answers whether this retained-guide family
contains a 22-linear local realization, i.e. a complete 100-gate AES circuit.

Two prefix-source scopes are supported.  `all` permits tapping any signal from
the fixed prefix; `live` permits only signals used by the original late region.
A miss is exact only for the represented retained-guide family, never a global
100-gate lower bound.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_crosscut_local_z3 as lz


def pair_witness(S, target, C):
    xs = sorted(S)
    have = set(S)
    for a in xs:
        bx = a ^ target
        if bx in have and bx != a:
            return ('XOR', a, bx)
        bn = a ^ target ^ C
        if bn in have and bn != a:
            return ('XNOR', a, bn)
    return None


def close(c, start, selected, source_scope, reconstruct=False):
    sk = ras.extract_skeleton(c)
    vals, _out, const_bit = tw.vectorize(c)
    C = 1 << const_bit
    starts = tw.interval_boundaries(c)
    lo = starts[start]
    prefix = [dict(g) for g in c['gates'][:lo]]
    source_names = lz.source_names_for_scope(c, vals, prefix, lo, source_scope)
    names = {}
    for w in source_names:
        names.setdefault(vals[w], w)
    S = set(names)
    rem = set(selected)
    ai = start
    events = []

    while True:
        progress = False
        # Release ordered nonlinear atoms as soon as their exact affine operands
        # exist.  For start=31 this loop has only the final AND, but keeping it
        # generic makes the closure semantics explicit.
        while ai < sk['n_and']:
            a = sk['ands'][ai]['a']; b = sk['ands'][ai]['b']
            if a not in S or b not in S:
                break
            atom = 1 << (8 + ai)
            if atom not in S:
                S.add(atom); events.append(('AND', ai, a, b, atom)); progress = True
            ai += 1

        ready = []
        for v in sorted(rem):
            hit = pair_witness(S, v, C)
            if hit is not None:
                ready.append((v, hit))
        for v, hit in ready:
            if v not in rem:
                continue
            S.add(v); rem.remove(v); events.append(('LIN', v, *hit)); progress = True

        if not progress:
            break

    outputs = set(sk['outputs'])
    missing_outputs = sorted(outputs - S)
    success = (ai == sk['n_and'] and not rem and not missing_outputs)
    meta = {
        'success': success, 'released_ands': ai - start,
        'remaining_guides': len(rem), 'missing_outputs': len(missing_outputs),
        'source_count': len(source_names), 'source_scope': source_scope,
    }
    if not success or not reconstruct:
        return None, meta

    # Replay the monotone witness into a concrete circuit.
    gates = [dict(g) for g in prefix]
    vec_name = dict(names)
    lino = 0
    for ev in events:
        if ev[0] == 'AND':
            _, gi, a, b, atom = ev
            out = f'__cg_and_{gi}'
            gates.append({'op': 'AND', 'a': vec_name[a], 'b': vec_name[b], 'out': out})
            vec_name[atom] = out
        else:
            _, v, op, a, b = ev
            out = f'__cg_lin_{lino}'; lino += 1
            gates.append({'op': op, 'a': vec_name[a], 'b': vec_name[b], 'out': out})
            vec_name[v] = out
    full = ras.prune({'gates': gates, 'outputs': [vec_name[v] for v in sk['outputs']]})
    ok = ras.independent_check(full)
    if not ok[0]:
        raise AssertionError(('retained-guide witness failed AES', ok))
    return full, meta


def search(c, start, keep, source_scope):
    vals, _out, _const = tw.vectorize(c)
    lo = tw.interval_boundaries(c)[start]
    local = c['gates'][lo:]
    guides = [vals[g['out']] for g in local if g['op'] != 'AND']
    if len(guides) != 25:
        raise AssertionError(('expected 25 late linear guides', len(guides)))
    if len(set(guides)) != len(guides):
        raise AssertionError('late guide vectors are not unique')
    if not (0 <= keep <= len(guides)):
        raise ValueError(keep)

    drop_n = len(guides) - keep
    tested = 0
    best = None; best_drop = None; best_meta = None
    for dropped in itertools.combinations(range(len(guides)), drop_n):
        tested += 1
        dset = set(dropped)
        selected = [v for i, v in enumerate(guides) if i not in dset]
        _full, meta = close(c, start, selected, source_scope, False)
        score = (meta['missing_outputs'], meta['remaining_guides'],
                 (ras.extract_skeleton(c)['n_and'] - start) - meta['released_ands'])
        if best is None or score < best:
            best = score; best_drop = list(dropped); best_meta = dict(meta)
        if not meta['success']:
            continue
        full, meta2 = close(c, start, selected, source_scope, True)
        return full, {
            'status': 'found', 'start': start, 'keep': keep,
            'drop_n': drop_n, 'dropped_indices': list(dropped),
            'tested_subsets': tested, **meta2,
        }
    return None, {
        'status': 'exhausted', 'start': start, 'keep': keep,
        'drop_n': drop_n, 'tested_subsets': tested,
        'best_residual': best, 'best_drop_indices': best_drop,
        'best_meta': best_meta, 'source_scope': source_scope,
        'family_scope': 'subset of original 25 late linear functions, arbitrary cross-AND rescheduling/rewiring',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=31)
    ap.add_argument('--keep', type=int, default=22)
    ap.add_argument('--source-scope', choices=['all','live'], default='all')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(); out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    c = ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    t0 = time.time(); full, meta = search(c, args.start, args.keep, args.source_scope)
    meta['elapsed_s'] = round(time.time() - t0, 3)
    if full is not None:
        (out/'candidate.json').write_text(json.dumps(full, indent=2)+'\n')
        meta['candidate_gates'] = len(full['gates'])
        meta['verified_all_256'] = True
        meta['gate_counts'] = {op: sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
    (out/'summary.json').write_text(json.dumps(meta, indent=2, sort_keys=True)+'\n')
    print(json.dumps(meta, sort_keys=True), flush=True)

if __name__ == '__main__':
    main()
