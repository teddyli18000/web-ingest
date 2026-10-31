#!/usr/bin/env python3
"""Exact retained-guide deletion census for the G103 pure-linear suffix.

The normalized NIST G103 circuit has a 22-gate linear suffix after its last AND.
Rather than synthesize an arbitrary 17->8 SLP from scratch, test the restricted
family in which a shorter suffix uses only a subset of the 22 existing suffix
linear functions, but may regenerate every retained function from any two
currently available retained functions / cut inputs.

For a chosen subset this reachability test is exact: starting from the 17 cut
basis inputs, repeatedly add every retained guide vector that is the XOR of two
available vectors.  The monotone closure is independent of generation order, so
failure proves that exact retained-function subset cannot form an SLP; success
reconstructs one.  We enumerate every deletion set compatible with the requested
gate count.  This is a restricted-family result, never a global lower bound.

The three non-atomic cut coordinates may be transformed by any GL(3,2) basis.
Affine output polarities are recovered afterwards with XOR/XNOR choices, and any
reattached full AES circuit is independently checked on all 256 inputs.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf
import g103_suffix_exact_z3 as ez
import g103_cut_basis_census as cb
import g103_explicit_cut_basis as xp


def ordered_guide_vectors(c, rows):
    _last, _prefix, suffix, boundary = suf.split(c)
    m, C, _vals, targets, qtargets, _guide = suf.formal_suffix(
        suffix, boundary, c['outputs'])
    extras, _ = cb.semantic_cut_extras(c, boundary)
    extra_idx = [boundary.index(w) for w in extras]
    cmap = cb.coeff_map(rows)

    qvals = {w: 1 << i for i, w in enumerate(boundary)}
    guides = []
    for g in suffix:
        q = qvals[g['a']] ^ qvals[g['b']]
        qvals[g['out']] = q
        guides.append(cb.transform_mask(q, extra_idx, cmap))

    tq = [cb.transform_mask(q, extra_idx, cmap) for q in qtargets]
    at = [q | (C if ((t >> m) & 1) else 0) for q, t in zip(tq, targets)]
    return m, C, boundary, extras, guides, tq, at


def pair_witness(S, target):
    xs = sorted(S)
    have = set(S)
    for a in xs:
        b = a ^ target
        if b in have and a != b:
            return (a, b) if a < b else (b, a)
    return None


def close_subset(m, selected):
    S = {1 << i for i in range(m)}
    remaining = set(selected)
    order = []
    parents = {}
    while remaining:
        progress = []
        for v in sorted(remaining):
            ab = pair_witness(S, v)
            if ab is not None:
                progress.append((v, ab))
        if not progress:
            break
        # Adding every currently reachable value is safe because reachability is
        # monotone; deterministic ordering only fixes the reconstructed witness.
        for v, ab in progress:
            if v not in remaining:
                continue
            parents[v] = ab
            order.append(v)
            S.add(v)
            remaining.remove(v)
    return not remaining, order, parents, sorted(remaining)


def build_net(m, C, order, parents, target_q, affine_targets):
    names = {1 << i: f'b{i}' for i in range(m)}
    const = {1 << i: 0 for i in range(m)}
    req = {}
    for q, t in zip(target_q, affine_targets):
        c = (t >> m) & 1
        if q in req and req[q] != c:
            raise AssertionError(('conflicting target polarity', q))
        req[q] = c

    gates = []
    exact = {1 << i: 1 << i for i in range(m)}
    for j, v in enumerate(order):
        a, b = parents[v]
        if a not in names or b not in names:
            raise AssertionError(('parent not ready', j, v, a, b))
        cv = req.get(v, 0)
        xn = cv ^ const[a] ^ const[b]
        out = f's{j}'
        gates.append({'op': 'XNOR' if xn else 'XOR',
                      'a': names[a], 'b': names[b], 'out': out})
        names[v] = out
        const[v] = cv
        exact[v] = exact[a] ^ exact[b] ^ (C if xn else 0)
        if (exact[v] & (C - 1)) != v or ((exact[v] >> m) & 1) != cv:
            raise AssertionError(('exact reconstruction mismatch', j, v))

    for q, t in zip(target_q, affine_targets):
        if q not in names:
            raise AssertionError(('missing output', q))
        if exact[q] != t:
            raise AssertionError(('target affine mismatch', q, exact[q], t))
    return {'gates': gates, 'outputs': [names[q] for q in target_q]}


def search(c, rows, gates):
    m, C, boundary, extras, guide, target_q, affine_targets = ordered_guide_vectors(c, rows)
    if len(guide) != 22:
        raise AssertionError(('expected 22 suffix guides', len(guide)))
    if len(set(guide)) != len(guide):
        raise AssertionError('guide vectors are not unique; subset indexing must be generalized')
    if len(set(target_q)) != len(target_q):
        raise AssertionError('targets unexpectedly duplicate')

    by_value = {v: i for i, v in enumerate(guide)}
    mandatory = sorted(by_value[q] for q in target_q)
    optional = [i for i in range(len(guide)) if i not in set(mandatory)]
    drop_n = len(guide) - gates
    if drop_n < 0 or drop_n > len(optional):
        return None, {'status': 'invalid_bound', 'gates': gates,
                      'mandatory_count': len(mandatory), 'optional_count': len(optional)}

    total = 0
    best_remaining = None
    best_drop = None
    for dropped in itertools.combinations(optional, drop_n):
        total += 1
        dset = set(dropped)
        selected = [v for i, v in enumerate(guide) if i not in dset]
        ok, order, parents, remaining = close_subset(m, selected)
        if best_remaining is None or len(remaining) < best_remaining:
            best_remaining = len(remaining)
            best_drop = list(dropped)
        if not ok:
            continue
        net = build_net(m, C, order, parents, target_q, affine_targets)
        if len(net['gates']) != gates:
            raise AssertionError(('wrong reconstructed gate count', len(net['gates']), gates))
        return net, {
            'status': 'found', 'gates': gates, 'tested_subsets': total,
            'total_subsets': None, 'dropped_indices': list(dropped),
            'mandatory_indices': mandatory, 'optional_count': len(optional),
            'boundary_count': m, 'extras': extras,
        }

    return None, {
        'status': 'exhausted', 'gates': gates, 'tested_subsets': total,
        'dropped': drop_n, 'mandatory_indices': mandatory,
        'optional_count': len(optional), 'best_unreachable_count': best_remaining,
        'best_drop_indices': best_drop, 'boundary_count': m, 'extras': extras,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--basis-rows', type=ez.parse_rows, default=(1, 2, 4))
    ap.add_argument('--min-gates', type=int, default=19)
    ap.add_argument('--max-gates', type=int, default=21)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    c = ras.load_circuit('nist-g103')
    assert ras.independent_check(c)[0]

    t0 = time.time()
    rows = []
    winner = None
    for k in range(args.min_gates, args.max_gates + 1):
        net, meta = search(c, args.basis_rows, k)
        rows.append(meta)
        print(json.dumps(meta, sort_keys=True), flush=True)
        if net is not None:
            winner = (k, net, meta)
            break

    prec, pmeta = xp.synthesize_at_cut(c, args.basis_rows)
    summary = {
        'basis_rows': list(args.basis_rows),
        'results': rows,
        'prefix': pmeta,
        'best_sat_gates': None if winner is None else winner[0],
        'elapsed_s': round(time.time() - t0, 3),
        'family_scope': 'retained subset of the 22 transformed original suffix guide functions',
    }
    if winner is not None:
        k, net, _ = winner
        (out / 'suffix.json').write_text(json.dumps(net, indent=2) + '\n')
        if prec is not None:
            full = xp.attach_suffix(c, prec, net)
            if not ras.independent_check(full)[0]:
                raise AssertionError('reattached retained-guide suffix failed AES')
            (out / 'full.json').write_text(json.dumps(full, indent=2) + '\n')
            summary['full_gates'] = len(full['gates'])
            summary['verified_all_256'] = True
            summary['gate_counts'] = {op: sum(g['op'] == op for g in full['gates'])
                                      for op in ('AND', 'XOR', 'XNOR')}

    (out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('results', 'prefix')},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
