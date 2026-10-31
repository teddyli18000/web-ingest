#!/usr/bin/env python3
"""Exact one-new-helper neighborhood around the 22-gate G103 suffix guide set.

Search 20-gate suffixes containing 19 functions from the transformed original
22-gate suffix plus exactly one new linear function.  For every three-function
deletion set we first compute the full monotone closure of the retained guides.
Any useful single new helper must then be the XOR of two signals in that closure;
otherwise its parents themselves would require another new helper.  Enumerating
all such pair-XORs is therefore exact for this represented one-new-function family.

After inserting the new helper, close the remaining retained guides again.  A
successful closure is reconstructed as an XOR/XNOR SLP, attached to the explicit
cut-basis prefix when available, and verified on all 256 AES inputs.

This exactness is family-scoped: it does not exclude 20-gate suffixes containing
two or more genuinely new intermediate linear functions.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez
import g103_explicit_cut_basis as xp
import g103_suffix_guide_subset as gs


def close_from(S, remaining, order, parents):
    S = set(S)
    rem = set(remaining)
    order = list(order)
    parents = dict(parents)
    while rem:
        ready = []
        for v in sorted(rem):
            ab = gs.pair_witness(S, v)
            if ab is not None:
                ready.append((v, ab))
        if not ready:
            break
        for v, ab in ready:
            if v not in rem:
                continue
            parents[v] = ab
            order.append(v)
            S.add(v)
            rem.remove(v)
    return S, rem, order, parents


def pair_candidates(S):
    xs = sorted(S)
    out = {}
    for i, a in enumerate(xs):
        for b in xs[i + 1:]:
            v = a ^ b
            if v and v not in S:
                out.setdefault(v, (a, b))
    return out


def search(c, rows, target_gates=20):
    if target_gates != 20:
        raise ValueError('current exact family is defined for 20 gates')
    m, C, boundary, extras, guide, target_q, affine_targets = gs.ordered_guide_vectors(c, rows)
    if len(guide) != 22 or len(set(guide)) != 22:
        raise AssertionError(('unexpected guide set', len(guide), len(set(guide))))
    target_set = set(target_q)
    by_value = {v: i for i, v in enumerate(guide)}
    target_indices = {by_value[q] for q in target_q}

    tested_drop = 0
    tested_helpers = 0
    best_remaining = None
    best_record = None

    # 19 retained old functions + one new helper = 20 gates.
    for dropped in itertools.combinations(range(22), 3):
        dset = set(dropped)
        dropped_targets = [guide[i] for i in dropped if i in target_indices]
        if len(dropped_targets) > 1:
            continue
        tested_drop += 1
        selected = [v for i, v in enumerate(guide) if i not in dset]
        S0 = {1 << i for i in range(m)}
        S, rem, order, parents = close_from(S0, selected, [], {})
        if not rem:
            # This would already be a 19-guide realization; the retained-guide
            # census is responsible for reporting it.  No new helper is needed.
            continue

        # If an output guide was deleted, the unique new helper must be exactly
        # that missing output vector.  Otherwise enumerate every one-gate value
        # reachable from the maximal old-guide closure.
        WD = pair_candidates(S)
        candidates = dropped_targets if dropped_targets else sorted(WD)
        for h in candidates:
            if h in S or h in selected or h not in WD:
                continue
            tested_helpers += 1
            hab = WD[h]
            S1 = set(S); S1.add(h)
            order1 = list(order) + [h]
            parents1 = dict(parents); parents1[h] = hab
            S2, rem2, order2, parents2 = close_from(S1, rem, order1, parents1)
            missing_outputs = [q for q in target_q if q not in S2]
            score = (len(missing_outputs), len(rem2))
            if best_remaining is None or score < best_remaining:
                best_remaining = score
                best_record = {'dropped_indices': list(dropped), 'helper': h,
                               'remaining_guides': len(rem2),
                               'missing_outputs': len(missing_outputs)}
            if rem2 or missing_outputs:
                continue
            if len(order2) != 20:
                raise AssertionError(('wrong order length', len(order2)))
            net = gs.build_net(m, C, order2, parents2, target_q, affine_targets)
            return net, {
                'status': 'found', 'gates': 20,
                'dropped_indices': list(dropped), 'new_helper': h,
                'tested_drop_sets': tested_drop, 'tested_helpers': tested_helpers,
                'target_indices': sorted(target_indices), 'boundary_count': m,
                'extras': extras,
            }

    return None, {
        'status': 'exhausted', 'gates': 20,
        'tested_drop_sets': tested_drop, 'tested_helpers': tested_helpers,
        'target_indices': sorted(target_indices),
        'best_residual': best_remaining, 'best_record': best_record,
        'family_scope': '19 original transformed guide functions plus one new pair-XOR helper',
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--basis-rows', type=ez.parse_rows, default=(1, 2, 4))
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    c = ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    t0 = time.time()
    net, meta = search(c, args.basis_rows, 20)
    print(json.dumps(meta, sort_keys=True), flush=True)

    prec, pmeta = xp.synthesize_at_cut(c, args.basis_rows)
    summary = {'basis_rows': list(args.basis_rows), 'search': meta,
               'prefix': pmeta, 'elapsed_s': round(time.time() - t0, 3)}
    if net is not None:
        (out / 'suffix.json').write_text(json.dumps(net, indent=2) + '\n')
        if prec is not None:
            full = xp.attach_suffix(c, prec, net)
            if not ras.independent_check(full)[0]:
                raise AssertionError('reattached one-new-helper suffix failed AES')
            (out / 'full.json').write_text(json.dumps(full, indent=2) + '\n')
            summary['full_gates'] = len(full['gates'])
            summary['verified_all_256'] = True
            summary['gate_counts'] = {op: sum(g['op'] == op for g in full['gates'])
                                      for op in ('AND', 'XOR', 'XNOR')}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('search', 'prefix')},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
