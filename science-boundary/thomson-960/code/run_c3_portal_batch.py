#!/usr/bin/env python3
"""Batch C3 portal classification and first downward solution-landscape expansion.

Designed for congested GitHub Actions queues: acquire one runner, force numerical
libraries to one thread per subprocess, and use all available runner CPUs across
independent portal calculations.  Stage 1 classifies all requested C3-constrained
stationary states in parallel.  Stage 2 automatically selects the lowest-energy
modest-index portals and runs index-k -> index-(k-1) CHiSD reconnaissance for
both signs of their softest unstable mode, again in parallel.

This deliberately avoids a GitHub Actions job matrix: one queued runner slot
performs a whole scientific batch.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import shlex
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Portal:
    seed: int
    trial: int
    tag: str
    expected: float


def parse_spec(s: str) -> Portal:
    try:
        seed, trial, tag, expected = s.split(':', 3)
        return Portal(int(seed), int(trial), tag, float(expected))
    except Exception as e:
        raise argparse.ArgumentTypeError('spec must be seed:trial:tag:expected_energy') from e


def run_logged(cmd: list[str], log_path: pathlib.Path, env: dict[str, str]) -> dict:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w') as f:
        f.write('$ ' + shlex.join(cmd) + '\n')
        f.flush()
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, text=True)
    return {'cmd': cmd, 'returncode': p.returncode, 'log': str(log_path)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('few_shots')
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--spec', action='append', type=parse_spec, required=True)
    ap.add_argument('--k', type=int, default=24)
    ap.add_argument('--max-workers', type=int, default=0, help='0 => os.cpu_count()')
    ap.add_argument('--downward-portals', type=int, default=4)
    ap.add_argument('--downward-outer', type=int, default=8)
    ap.add_argument('--downward-k', type=int, default=18)
    ap.add_argument('--max-parent-index', type=int, default=12,
                    help='skip downward search if classification suggests a larger/uncertain index')
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    code = pathlib.Path(__file__).resolve().parent
    env = os.environ.copy()
    # Independent Python processes own the parallelism.  Prevent nested BLAS/OpenMP
    # oversubscription, which is especially harmful for the dense 960x960 kernels.
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
        env[key] = '1'
    ncpu = os.cpu_count() or 2
    workers = args.max_workers if args.max_workers > 0 else ncpu
    workers = max(1, min(workers, ncpu, len(args.spec)))
    print(f'runner_cpus={ncpu} workers={workers} portals={len(args.spec)}', flush=True)

    stage1: list[tuple[Portal, pathlib.Path, pathlib.Path, list[str]]] = []
    for p in args.spec:
        out = outdir / f'portal-{p.tag}.json'; log = outdir / f'portal-{p.tag}.log'
        cmd = [sys.executable, str(code/'harvest_classify_c3_portal.py'), args.few_shots,
               '--seed', str(p.seed), '--trial', str(p.trial), '--k', str(args.k),
               '--expected-energy', repr(p.expected), '--out', str(out)]
        stage1.append((p, out, log, cmd))

    results1 = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_logged, cmd, log, env):(p,out,log) for p,out,log,cmd in stage1}
        for fut in cf.as_completed(futs):
            p,out,log = futs[fut]; r = fut.result(); r['tag'] = p.tag
            print(f'classification {p.tag}: rc={r["returncode"]}', flush=True)
            results1.append(r)
    failed = [r for r in results1 if r['returncode'] != 0]
    if failed:
        pathlib.Path(outdir/'batch-summary.json').write_text(json.dumps({'stage1':results1,'failed':failed},indent=2)+'\n')
        raise SystemExit(f'{len(failed)} portal classifications failed')

    portals = []
    for p,out,log,cmd in stage1:
        d = json.loads(out.read_text())
        portals.append({'spec':p,'path':out,'data':d})
        print(f'PORTAL {p.tag} E={d["full_energy"]:.12f} grad={d["full_gradient_rms"]:.3g} '
              f'neg={d["negative_modes_among_k"]} lows={d["lowest_eigenvalues"][:6]}', flush=True)

    eligible = [x for x in portals
                if 2 <= int(x['data']['negative_modes_among_k']) <= args.max_parent_index]
    eligible.sort(key=lambda x: float(x['data']['full_energy']))
    eligible = eligible[:args.downward_portals]
    stage2 = []
    for x in eligible:
        p = x['spec']
        for sign in (-1, 1):
            tag = f'{p.tag}-m0-s{sign:+d}'
            out = outdir / f'down-{tag}.json'; log = outdir / f'down-{tag}.log'
            cmd = [sys.executable, str(code/'downward_indexk.py'), str(x['path']),
                   '--escape-mode','0','--sign',str(sign),'--escape-amp','0.0003',
                   '--outer',str(args.downward_outer),'--k-search',str(args.downward_k),
                   '--perp-maxiter','500','--out',str(out)]
            stage2.append((tag,out,log,cmd))

    results2 = []
    if stage2:
        workers2 = max(1, min(args.max_workers if args.max_workers>0 else ncpu, ncpu, len(stage2)))
        print(f'downward_tasks={len(stage2)} workers={workers2}', flush=True)
        with cf.ThreadPoolExecutor(max_workers=workers2) as ex:
            futs = {ex.submit(run_logged, cmd, log, env):(tag,out,log) for tag,out,log,cmd in stage2}
            for fut in cf.as_completed(futs):
                tag,out,log = futs[fut]; r=fut.result(); r['tag']=tag
                if r['returncode']==0 and out.exists():
                    d=json.loads(out.read_text())
                    r.update(final_energy=d.get('final_energy'), final_gradient_rms=d.get('final_gradient_rms'),
                             final_index=d.get('negative_internal_modes_below_-1e-3'), status=d.get('status'))
                    print(f'DOWN {tag} rc=0 E={r["final_energy"]:.12f} grad={r["final_gradient_rms"]:.3g} '
                          f'index={r["final_index"]} status={r["status"]}', flush=True)
                else:
                    print(f'DOWN {tag} rc={r["returncode"]}', flush=True)
                results2.append(r)

    summary = {
        'runner_cpus': ncpu, 'classification_workers': workers,
        'portals': [{
            'tag': x['spec'].tag, 'seed': x['spec'].seed, 'trial': x['spec'].trial,
            'expected_energy': x['spec'].expected,
            'energy': x['data']['full_energy'], 'gradient_rms': x['data']['full_gradient_rms'],
            'negative_modes_among_k': x['data']['negative_modes_among_k'],
            'lowest_eigenvalues': x['data']['lowest_eigenvalues'][:12],
            'coord_counts': x['data']['coord_counts'],
        } for x in portals],
        'eligible_downward_tags': [x['spec'].tag for x in eligible],
        'stage1': results1, 'stage2': results2,
    }
    (outdir/'batch-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if any(r['returncode'] != 0 for r in results2):
        raise SystemExit('one or more downward tasks failed; classification results remain valid')


if __name__ == '__main__':
    main()
