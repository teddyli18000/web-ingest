"""Reproducible p006 hidden-improvement pilot (Python stdlib only)."""
import argparse
import json
import random

def energy(seq):
    n = len(seq)
    return sum(sum(seq[i] * seq[i + k] for i in range(n - k)) ** 2 for k in range(1, n))

def flip(seq, indexes):
    s = seq.copy()
    for i in indexes:
        s[i] *= -1
    return s

def descent(seq, allowed=None):
    s, e = seq.copy(), energy(seq)
    sites = range(len(s)) if allowed is None else sorted(allowed)
    while True:
        best_e, best_i = e, -1
        for i in sites:
            s[i] *= -1
            ei = energy(s)
            s[i] *= -1
            if ei < best_e:
                best_e, best_i = ei, i
        if best_i < 0:
            return s, e
        s[best_i] *= -1
        e = best_e

def repair(candidate, width, rounds, rng, mode):
    s, score = candidate.copy(), energy(candidate)
    n = len(s)
    for _ in range(rounds):
        if mode == 'random':
            indices = rng.sample(range(n), width)
        else:
            corr = [sum(s[i] * s[i + k] for i in range(n-k)) for k in range(1,n)]
            pressure = [sum(abs(corr[k-1]) for k in range(1,n) if (i < n-k or i >= k)) for i in range(n)]
            center = max(range(n), key=lambda i: (pressure[i], -i))
            indices = [(center + j) % n for j in range(-width//2, -width//2+width)]
        chosen = rng.sample(indices, min(3, len(indices)))
        cand, ce = descent(flip(s, chosen))
        if ce < score:
            s, score = cand, ce
    return s, score

def run(seed, n, cases, width, rounds):
    rng = random.Random(seed)
    records = []
    for case in range(cases):
        teacher, teacher_e = descent([rng.choice((-1,1)) for _ in range(n)])
        parent = flip(teacher, rng.sample(range(n), max(3, n//4)))
        parent, initial = descent(parent)
        results = {}
        for mode in ('random', 'pressure'):
            local_rng = random.Random(seed * 100000 + case)
            _, e = repair(parent, width, rounds, local_rng, mode)
            results[mode] = e
        records.append(dict(case=case, teacher=teacher_e, initial=initial,
                            random=results['random'], pressure=results['pressure'],
                            random_recovers=results['random'] <= teacher_e,
                            pressure_recovers=results['pressure'] <= teacher_e))
    return records

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=20261107)
    p.add_argument('--n',type=int,default=40)
    p.add_argument('--cases',type=int,default=12)
    p.add_argument('--width',type=int,default=10)
    p.add_argument('--rounds',type=int,default=16)
    args=p.parse_args()
    records=run(args.seed,args.n,args.cases,args.width,args.rounds)
    print(json.dumps(dict(config=vars(args),cases=records,aggregate={
        'random_recovered':sum(r['random_recovers'] for r in records),
        'pressure_recovered':sum(r['pressure_recovers'] for r in records),
        'random_mean':sum(r['random'] for r in records)/len(records),
        'pressure_mean':sum(r['pressure'] for r in records)/len(records),
    }),indent=2))
