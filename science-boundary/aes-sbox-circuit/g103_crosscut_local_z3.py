#!/usr/bin/env python3
"""Exact local affine synthesis across the late G103 nonlinear/output boundary.

Fix the complete G103 circuit before a chosen AND-release interval, then replace
everything from that interval through the outputs by a new straight-line program
with the same remaining ordered AND atoms.  Linear XOR/XNOR slots may use either
all fixed-prefix signals (the broad family), or only the original window live-in
interface (a smaller exactly checkable family), plus any earlier local helper and
already released local AND atom.  Each AND operand and final AES output is
constrained by its exact affine form in the released-AND basis.

For start=31 there is one remaining AND and two linear intervals: immediately
before the final AND and after it.  Removing three slots across those intervals
directly asks for a 32-AND + 68-linear = 100-gate circuit while allowing linear
sharing to cross the old last-AND cut.  For a fixed source scope and slot schedule
this is an exact QF_BV/Int-selector model; SAT yields a fully reconstructed
circuit, UNSAT excludes only that represented family, and timeout is not evidence
of impossibility.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import released_and_skeleton as ras
import temporal_window_resynth as tw

try:
    import z3
except ImportError as e:
    raise SystemExit('z3-solver is required') from e


def parse_ints(s):
    return [int(x) for x in s.split(',') if x != '']


def bv(v, D):
    return z3.BitVecVal(v, D)


def select_expr(sel, sources):
    e = sources[-1]
    for i in range(len(sources) - 2, -1, -1):
        e = z3.If(sel == i, sources[i], e)
    return e


def source_names_for_scope(c, vals, prefix, lo, scope):
    all_prefix = [f'x{i}' for i in range(8)] + [g['out'] for g in prefix]
    if scope == 'all':
        return all_prefix
    if scope != 'live':
        raise ValueError(scope)

    window = c['gates'][lo:]
    win_outputs = {g['out'] for g in window}
    names = []
    seen_names = set()
    for g in window:
        for w in (g['a'], g['b']):
            if w not in win_outputs and w not in seen_names:
                seen_names.add(w); names.append(w)
    for w in c['outputs']:
        if w not in win_outputs and w not in seen_names:
            seen_names.add(w); names.append(w)

    # Equal affine values are interchangeable as source wires for this local
    # synthesis problem.  Deduplicate them to remove pure selector symmetry.
    out = []
    seen_vals = set()
    for w in names:
        v = vals[w]
        if v in seen_vals:
            continue
        seen_vals.add(v); out.append(w)
    return out


def local_problem(c, start, removals, timeout_ms, source_scope='all'):
    sk = ras.extract_skeleton(c)
    sched0 = tw.original_schedule(c)
    n = sk['n_and']
    if not (0 <= start <= n):
        raise ValueError((start, n))
    local0 = sched0[start:]
    if len(removals) != len(local0):
        raise ValueError(('removal length', len(removals), len(local0), local0))
    if any(r < 0 or r > k for r, k in zip(removals, local0)):
        return None, {'status': 'invalid_plan', 'start': start,
                      'schedule_local_original': local0, 'removals': removals,
                      'source_scope': source_scope}
    local = [k - r for k, r in zip(local0, removals)]

    vals, _out_vec, const_bit = tw.vectorize(c)
    C = 1 << const_bit
    D = const_bit + 1
    starts = tw.interval_boundaries(c)
    lo = starts[start]
    prefix = [dict(g) for g in c['gates'][:lo]]
    source_names = source_names_for_scope(c, vals, prefix, lo, source_scope)
    source_vals = [vals[w] for w in source_names]
    if not source_names:
        raise AssertionError(('empty source interface', start, source_scope))

    s = z3.Solver(); s.set(timeout=timeout_ms)
    sources = [bv(v, D) for v in source_vals]
    meta = []
    and_selectors = []
    lin_no = 0
    remaining_ands = n - start

    for stage in range(remaining_ands + 1):
        for _ in range(local[stage]):
            p = z3.Int(f'p_{lin_no}'); q = z3.Int(f'q_{lin_no}')
            neg = z3.Bool(f'n_{lin_no}')
            # p<=q includes same-input XOR/XNOR, so the represented family also
            # permits explicit 0/1 affine constants if they are worth one gate.
            s.add(p >= 0, q >= 0, p <= q, q < len(sources))
            v = z3.BitVec(f'L_{lin_no}', D)
            pv = select_expr(p, sources); qv = select_expr(q, sources)
            s.add(v == (pv ^ qv ^ z3.If(neg, bv(C, D), bv(0, D))))
            sources.append(v)
            meta.append(('linear', lin_no, p, q, neg))
            lin_no += 1
        if stage < remaining_ands:
            ai = start + stage
            sels = []
            for side in ('a', 'b'):
                target = sk['ands'][ai][side]
                q = z3.Int(f'and_{ai}_{side}')
                s.add(q >= 0, q < len(sources), select_expr(q, sources) == bv(target, D))
                sels.append(q)
            and_selectors.append((ai, sels[0], sels[1]))
            sources.append(bv(1 << (8 + ai), D))
            meta.append(('and', ai))

    out_selectors = []
    for oi, target in enumerate(sk['outputs']):
        q = z3.Int(f'out_{oi}')
        s.add(q >= 0, q < len(sources), select_expr(q, sources) == bv(target, D))
        out_selectors.append(q)

    data = {
        'solver': s, 'meta': meta, 'and_selectors': and_selectors,
        'out_selectors': out_selectors, 'prefix': prefix,
        'source_names': source_names, 'schedule_original': sched0,
        'schedule_local_original': local0, 'schedule_local_tested': local,
        'start': start, 'n_and': n, 'target_local_linear': sum(local),
        'removed_linear': sum(removals), 'const_bit': const_bit,
        'source_scope': source_scope, 'source_count': len(source_names),
    }
    return data, None


def reconstruct(model, data):
    names = list(data['source_names'])
    gates = [dict(g) for g in data['prefix']]
    and_map = {ai: (qa, qb) for ai, qa, qb in data['and_selectors']}
    for rec in data['meta']:
        if rec[0] == 'linear':
            _, _lin_no, p, q, neg = rec
            pi = model.eval(p, model_completion=True).as_long()
            qi = model.eval(q, model_completion=True).as_long()
            nv = z3.is_true(model.eval(neg, model_completion=True))
            out = f'__lz_{len(gates)}'
            gates.append({'op': 'XNOR' if nv else 'XOR',
                          'a': names[pi], 'b': names[qi], 'out': out})
            names.append(out)
        else:
            _, ai = rec
            qa, qb = and_map[ai]
            ia = model.eval(qa, model_completion=True).as_long()
            ib = model.eval(qb, model_completion=True).as_long()
            out = f'__lz_{len(gates)}'
            gates.append({'op': 'AND', 'a': names[ia], 'b': names[ib], 'out': out})
            names.append(out)
    outs = [names[model.eval(q, model_completion=True).as_long()]
            for q in data['out_selectors']]
    return ras.prune({'gates': gates, 'outputs': outs})


def solve(start, removals, timeout_ms, outdir, source_scope='all'):
    c = ras.load_circuit('nist-g103')
    assert ras.independent_check(c)[0]
    data, early = local_problem(c, start, removals, timeout_ms, source_scope)
    if early is not None:
        return early
    t0 = time.time()
    r = data['solver'].check()
    elapsed = time.time() - t0
    res = {
        'status': str(r), 'start': start, 'removals': removals,
        'elapsed_s': round(elapsed, 3),
        'base_gates': len(c['gates']), 'base_linear': len(c['gates']) - data['n_and'],
        'n_and': data['n_and'], 'removed_linear': data['removed_linear'],
        'schedule_original': data['schedule_original'],
        'schedule_local_original': data['schedule_local_original'],
        'schedule_local_tested': data['schedule_local_tested'],
        'target_linear': (len(c['gates']) - data['n_and']) - data['removed_linear'],
        'source_scope': source_scope, 'source_count': data['source_count'],
        'family_scope': ('fixed prefix before start; fixed ordered remaining AND functions; '
                         'fixed local slot schedule; selected prefix-source scope'),
    }
    if r == z3.sat:
        cand = reconstruct(data['solver'].model(), data)
        ok = ras.independent_check(cand)
        if not ok[0]:
            raise AssertionError(('local Z3 candidate failed AES', ok))
        out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=True)
        (out / 'candidate.json').write_text(json.dumps(cand, indent=2) + '\n')
        res['candidate_gates'] = len(cand['gates'])
        res['verified_all_256'] = True
        res['gate_counts'] = {op: sum(g['op'] == op for g in cand['gates'])
                              for op in ('AND', 'XOR', 'XNOR')}
    elif r == z3.unknown:
        res['reason_unknown'] = data['solver'].reason_unknown()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=31)
    ap.add_argument('--removals', type=parse_ints, required=True)
    ap.add_argument('--source-scope', choices=['all', 'live'], default='all')
    ap.add_argument('--timeout-ms', type=int, default=300000)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    res = solve(args.start, args.removals, args.timeout_ms, args.out, args.source_scope)
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(res, indent=2, sort_keys=True) + '\n')
    print(json.dumps(res, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
