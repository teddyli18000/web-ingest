#!/usr/bin/env python3
"""Use the public 2026 refutation-gap CaDiCaL SLP encoder on G103's 17->8 suffix.

This is an independent exact-SAT implementation path from the topic-local Z3
encodings.  The workflow clones a pinned public `Rohan-Pandey1729/refutation-gap`
commit and imports its unmodified `slp.optimal.exists_program` encoder.

We ask for a fixed XOR gate count K.  SAT is constructive evidence only: the
returned symbolic program is re-executed by the upstream verifier, converted to
XOR/XNOR gates with exact affine polarities, attached to the unchanged G103
32-AND/49-linear prefix, and independently checked on all 256 AES inputs.

A timeout is inconclusive.  An UNSAT result is recorded only as solver output,
not as a scientific lower bound here: a lower-bound claim would additionally
require the proof/certification route described in the research log.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf


def instance_data():
    c = ras.load_circuit('nist-g103')
    assert ras.independent_check(c)[0]
    _last, prefix, _orig_suffix, boundary = suf.split(c)
    m, C, _vals, targets, qtargets, _guide = suf.formal_suffix(
        _orig_suffix, boundary, c['outputs'])
    assert m == 17 and len(qtargets) == 8 and len(set(qtargets)) == 8
    assert all(q.bit_count() > 1 for q in qtargets)
    return c, prefix, boundary, m, C, targets, qtargets


def reconstruct(prefix, boundary, m, C, targets, qtargets, program):
    signals = [1 << i for i in range(m)]
    names = list(boundary)
    consts = [0] * m
    wanted_const = {q: (t >> m) & 1 for q, t in zip(qtargets, targets)}
    gates = []

    for gi, (a, b) in enumerate(program):
        idx = m + gi
        if not (0 <= a < idx and 0 <= b < idx and a != b):
            raise AssertionError(('bad SAT op', gi, a, b, idx))
        v = signals[a] ^ signals[b]
        desired = wanted_const.get(v, 0)
        xnor = desired ^ consts[a] ^ consts[b]
        out = f'__refgap_{gi}'
        gates.append({'op': 'XNOR' if xnor else 'XOR',
                      'a': names[a], 'b': names[b], 'out': out})
        signals.append(v); names.append(out); consts.append(desired)

    outs = []
    for q, t in zip(qtargets, targets):
        try:
            si = signals.index(q)
        except ValueError as e:
            raise AssertionError(('SAT program missing target', q)) from e
        if consts[si] != ((t >> m) & 1):
            raise AssertionError(('affine polarity mismatch', q, consts[si], t))
        outs.append(names[si])

    full = ras.prune({'gates': [dict(g) for g in prefix] + gates, 'outputs': outs})
    ok = ras.independent_check(full)
    if not ok[0]:
        raise AssertionError(('refgap SAT reattachment failed AES', ok))
    return full


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refgap', required=True)
    ap.add_argument('--k', type=int, required=True)
    ap.add_argument('--conf-budget', type=int, default=0)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)

    root = str(pathlib.Path(args.refgap).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    from slp.instance import SLPInstance, verify as refgap_verify
    from slp.optimal import exists_program

    c, prefix, boundary, m, C, targets, qtargets = instance_data()
    inst = SLPInstance(name='g103-suffix-17x8', n_inputs=m,
                       targets=tuple(qtargets),
                       meta={'source': 'normalized NIST G103 last-AND suffix'})
    t0 = time.time()
    res = exists_program(inst, args.k, conf_budget=args.conf_budget)
    summary = {
        'k': args.k,
        'sat': res.sat,
        'timed_out': res.timed_out,
        'solver_seconds': round(res.seconds, 3),
        'wall_seconds': round(time.time() - t0, 3),
        'n_vars': res.n_vars,
        'n_clauses': res.n_clauses,
        'conf_budget': args.conf_budget,
        'fingerprint': inst.fingerprint(),
        'upstream_repo': 'Rohan-Pandey1729/refutation-gap',
        'interpretation': ('SAT is independently replayed; timeout inconclusive; '
                           'UNSAT is not promoted to a lower-bound claim without certification'),
    }
    if res.sat:
        assert res.program is not None
        refgap_verify(inst, res.program)
        full = reconstruct(prefix, boundary, m, C, targets, qtargets, res.program)
        (out / 'program.json').write_text(json.dumps(res.program, indent=2) + '\n')
        (out / 'full.json').write_text(json.dumps(full, indent=2) + '\n')
        summary['program_gates'] = len(res.program)
        summary['full_gates'] = len(full['gates'])
        summary['verified_all_256'] = True
        summary['gate_counts'] = {
            op: sum(g['op'] == op for g in full['gates'])
            for op in ('AND', 'XOR', 'XNOR')
        }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
