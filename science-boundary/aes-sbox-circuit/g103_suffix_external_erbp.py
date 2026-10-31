#!/usr/bin/env python3
"""Run the public CHES-2025 Extended-BP eRNBP on the G103 17->8 suffix.

This is intentionally an independent implementation path from the topic-local
RNBP ports.  The public `lemontrr/Extended-BP-Framework` is cloned externally by
the workflow and its unmodified `Optimizer_RNBP.Optimizer_with_RNBP` is called on
the exact 17-bit linear quotient map after the final G103 AND.

The framework searches only the linear parts.  Once it returns an XOR SLP, this
wrapper independently reattaches exact affine polarities using XOR/XNOR at unit
cost, attaches the unchanged 32-AND/49-linear G103 prefix, and checks all 256 AES
inputs with `released_and_skeleton.independent_check`.  Thus an upstream result
of 19 XORs gives a 100-gate complete circuit; 20 or 21 XORs are still useful
structurally diverse 101/102 seeds.

The optimizer is randomized.  `--seed-start/--seeds` enumerate independent RNG
seeds and `--workers` uses separate processes so the framework's module globals
cannot interfere across searches.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import pathlib
import re
import sys
import time

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf


def suffix_instance():
    c = ras.load_circuit('nist-g103')
    assert ras.independent_check(c)[0]
    last, prefix, orig_suffix, boundary = suf.split(c)
    m, C, vals, targets, qtargets, _guide = suf.formal_suffix(
        orig_suffix, boundary, c['outputs'])
    assert m == 17 and len(qtargets) == 8 and len(set(qtargets)) == 8
    assert all(q.bit_count() > 1 for q in qtargets)
    XORs = {}
    NOTs = []
    for i, (q, t) in enumerate(zip(qtargets, targets)):
        XORs[f'y[{i}]'] = [f'x[{j}]' for j in range(m) if (q >> j) & 1]
        if (t >> m) & 1:
            NOTs.append(f'y[{i}]')
    return c, prefix, boundary, m, C, targets, qtargets, XORs, NOTs


def worker(payload):
    framework, seed, XORs, NOTs = payload
    os.chdir(framework)
    if framework not in sys.path:
        sys.path.insert(0, framework)
    import Optimizer_RNBP as opt
    opt.random.seed(seed)
    t0 = time.time()
    circuit, xor_num = opt.Optimizer_with_RNBP(
        17, 8, XORs, [], NOTs, log_filename=f'g103suffix_seed{seed:06d}')
    return {
        'seed': seed,
        'xor_num': xor_num,
        'elapsed_s': round(time.time() - t0, 3),
        'circuit': circuit,
    }


def reconstruct(prefix, boundary, C, targets, qtargets, rec):
    m = len(boundary)
    vec = {f'x[{i}]': 1 << i for i in range(m)}
    name = {f'x[{i}]': boundary[i] for i in range(m)}
    const = {f'x[{i}]': 0 for i in range(m)}
    target_const = {q: (t >> m) & 1 for q, t in zip(qtargets, targets)}
    gates = []
    t_lines = []
    for raw in rec['circuit']:
        line = raw.replace(' ', '')
        if not line.startswith('t['):
            continue
        lhs, rhs = line.split('=', 1)
        parts = rhs.split('^')
        if len(parts) != 2 or '1' in parts:
            raise AssertionError(('unexpected eRNBP helper line', raw))
        a, b = parts
        if a not in vec or b not in vec:
            raise AssertionError(('non-topological eRNBP output', raw, sorted(vec)))
        v = vec[a] ^ vec[b]
        desired = target_const.get(v, 0)
        neg = desired ^ const[a] ^ const[b]
        out = f'__erbp_{len(gates)}'
        gates.append({'op': 'XNOR' if neg else 'XOR',
                      'a': name[a], 'b': name[b], 'out': out})
        vec[lhs] = v; name[lhs] = out; const[lhs] = desired
        t_lines.append(raw)
    if len(gates) != rec['xor_num']:
        raise AssertionError(('framework count/parsed helpers disagree',
                              rec['xor_num'], len(gates), rec['circuit']))

    by_vec = {}
    for ext, v in vec.items():
        by_vec.setdefault(v, ext)
    outs = []
    for q, t in zip(qtargets, targets):
        ext = by_vec.get(q)
        if ext is None:
            raise AssertionError(('framework did not materialize target', q, rec))
        if const[ext] != ((t >> m) & 1):
            raise AssertionError(('target polarity mismatch', q, const[ext], t))
        outs.append(name[ext])

    full = ras.prune({'gates': [dict(g) for g in prefix] + gates, 'outputs': outs})
    ok = ras.independent_check(full)
    if not ok[0]:
        raise AssertionError(('eRNBP reattachment failed AES', ok, rec['seed']))
    return full


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--framework', required=True)
    ap.add_argument('--seed-start', type=int, default=0)
    ap.add_argument('--seeds', type=int, default=32)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    framework = str(pathlib.Path(args.framework).resolve())
    if not pathlib.Path(framework, 'Optimizer_RNBP.py').exists():
        raise FileNotFoundError(framework)

    c, prefix, boundary, m, C, targets, qtargets, XORs, NOTs = suffix_instance()
    seeds = list(range(args.seed_start, args.seed_start + args.seeds))
    payloads = [(framework, s, XORs, NOTs) for s in seeds]
    t0 = time.time()
    with mp.Pool(processes=max(1, args.workers)) as pool:
        rows = list(pool.imap_unordered(worker, payloads))
    rows.sort(key=lambda r: (r['xor_num'], r['seed']))

    best_count = None
    verified = []
    for r in rows:
        full = reconstruct(prefix, boundary, C, targets, qtargets, r)
        r['full_gates'] = len(full['gates'])
        r['verified_all_256'] = True
        if best_count is None or r['xor_num'] < best_count:
            best_count = r['xor_num']
            (out / 'best-full.json').write_text(json.dumps(full, indent=2) + '\n')
            (out / 'best-framework-circuit.json').write_text(json.dumps(r, indent=2) + '\n')
        if len(full['gates']) <= 100:
            p = out / f'candidate-{r["seed"]}.json'
            p.write_text(json.dumps(full, indent=2) + '\n')
            verified.append({'seed': r['seed'], 'gates': len(full['gates']),
                             'xor_num': r['xor_num'], 'path': p.name})

    summary = {
        'framework_repo': 'lemontrr/Extended-BP-Framework',
        'seed_start': args.seed_start, 'seeds': args.seeds,
        'workers': args.workers, 'best_suffix_xors': best_count,
        'best_full_gates': None if best_count is None else len(prefix) + best_count,
        'count_hist': {}, 'verified_le_100': verified,
        'elapsed_s': round(time.time() - t0, 3),
        'rows': rows,
    }
    from collections import Counter
    summary['count_hist'] = dict(sorted(Counter(str(r['xor_num']) for r in rows).items()))
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
