#!/usr/bin/env python3
"""Exact Boolean/XOR feasibility model for the odd-perfect (20,0), W=127 branch.

This is the full (not projected) E=558 candidate problem in the normalized
half-sum class

    sum A = 20, sum B = 0,
    A_i=s_(2i), B_i=s_(2i+1), i=0..49.

At W=127 the convexity equality forces every even correlation C_(2r) to be
2 or 4, with exactly 26 values equal to 4.  Odd-perfectness forces every odd
correlation to be +/-1.  Opposite odd correlations have opposite signs, and
at W=127 opposite even correlations are equal.  In sign-bit variables all of
these become XOR cardinality equations; no quadratic objective or square table
is required.

The optional --ka shard fixes the number of equal endpoint-pairs
A_i=A_(i+25), i=0..24.  Since C_50=2 at W=127, the corresponding B count is
26-ka.  The only possible ka values are 10,12,...,24.

INFEASIBLE is an exact exclusion of that shard. FEASIBLE is independently
rescored and must have total LABS energy 558, in which case it is a genuine
record candidate and must be frozen/verified immediately.
"""
from __future__ import annotations

import argparse
import json
import sys
from ortools.sat.python import cp_model

N = 100


def exact(seq: str):
    s = [1 if ch == '+' else -1 for ch in seq]
    cs = [0] + [sum(s[i] * s[i + k] for i in range(N - k)) for k in range(1, N)]
    e = sum(c * c for c in cs[1:])
    odd = sum(cs[k] * cs[k] for k in range(1, N, 2))
    return e, odd, cs, sum(s[0::2]), sum(s[1::2])


def xor_var(model: cp_model.CpModel, x, y, name: str):
    """Return Boolean d = x XOR y."""
    d = model.NewBoolVar(name)
    # AddBoolXOr is true iff an odd number of literals are true.
    # x xor y xor (not d) == True  <=> d = x xor y.
    model.AddBoolXOr([x, y, d.Not()])
    return d


def build(ka: int | None):
    if ka is not None and ka not in range(10, 25, 2):
        raise ValueError('ka must be one of 10,12,...,24')

    m = cp_model.CpModel()
    # x[2*i] is A_i negative-bit; x[2*i+1] is B_i negative-bit.
    x = [m.NewBoolVar(f'x{i}') for i in range(N)]

    # Half sums (20,0) mean 15 negatives in A and 25 in B.
    m.Add(sum(x[0::2]) == 15)
    m.Add(sum(x[1::2]) == 25)

    # Global sign and reversal/alternation symmetries leave this class invariant.
    # A has positives, so fix A_0=+1 after a simultaneous cyclic rotation of the
    # parity halves only when ka is used as a periodic structural shard would be
    # unsafe for aperiodic LABS.  Therefore use only global sign symmetry here:
    # B has sum zero, while global sign maps A sum 20 -> -20, so normalization has
    # already consumed it.  No additional positional symmetry is imposed.

    corr = {}
    odd_sign = {}
    even4 = {}

    # Build each original LABS correlation directly as a disagreement count.
    for k in range(1, N):
        z = [xor_var(m, x[i], x[i + k], f'z_{k}_{i}') for i in range(N - k)]
        q = m.NewIntVar(0, N - k, f'q{k}')
        m.Add(q == sum(z))
        c = m.NewIntVar(-(N-k), N-k, f'c{k}')
        m.Add(c == (N - k) - 2 * q)
        corr[k] = c

        if k & 1:
            # k=2r+1, length=99-2r.  q=49-r gives C=+1,
            # q=50-r gives C=-1.
            r = (k - 1) // 2
            u = m.NewBoolVar(f'oddneg_{r}')
            m.Add(q == 49 - r + u)
            odd_sign[r] = u
        else:
            # k=2r.  At W=127 C is +2 or +4.
            r = k // 2
            t = m.NewBoolVar(f'even4_{r}')
            m.Add(q == 49 - r - t)
            even4[r] = t

    # Exactly 26 of the 49 even correlations are 4 (the other 23 are 2).
    m.Add(sum(even4.values()) == 26)

    # Odd-perfect plus ab=0: opposite odd correlations are opposite signs.
    for r in range(25):
        m.Add(odd_sign[r] + odd_sign[49 - r] == 1)

    # W=127 equality + opposite-even congruence: exact equality across r,50-r.
    for r in range(1, 25):
        m.Add(even4[r] == even4[50 - r])
    # The self-opposite middle lag must be C_50=2.
    m.Add(even4[25] == 0)

    # Optional order-25 compression support shard.  p_i=(A_i+A_i+25)/2
    # is nonzero iff the pair agrees.  The B compression has the same property.
    if ka is not None:
        ae = []
        be = []
        for i in range(25):
            da = xor_var(m, x[2*i], x[2*(i+25)], f'a25diff_{i}')
            db = xor_var(m, x[2*i+1], x[2*(i+25)+1], f'b25diff_{i}')
            ea = m.NewBoolVar(f'a25eq_{i}')
            eb = m.NewBoolVar(f'b25eq_{i}')
            m.Add(ea + da == 1)
            m.Add(eb + db == 1)
            ae.append(ea); be.append(eb)
        m.Add(sum(ae) == ka)
        m.Add(sum(be) == 26 - ka)

    return m, x, corr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ka', type=int)
    ap.add_argument('--seconds', type=float, default=900.0)
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()

    model, x, corr = build(args.ka)
    err = model.Validate()
    if err:
        raise SystemExit('MODEL_INVALID ' + err)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.randomize_search = True
    solver.parameters.cp_model_presolve = True
    solver.parameters.symmetry_level = 2
    st = solver.Solve(model)
    out = {
        'ka': args.ka,
        'status': solver.StatusName(st),
        'wall_time': solver.WallTime(),
        'branches': solver.NumBranches(),
        'conflicts': solver.NumConflicts(),
    }

    if st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        seq = ''.join('-' if solver.Value(v) else '+' for v in x)
        e, odd, cs, asum, bsum = exact(seq)
        out.update(sequence=seq, energy=e, odd_energy=odd, asum=asum, bsum=bsum,
                   even_values=sorted(cs[k] for k in range(2,100,2)))
        ok = (e == 558 and odd == 50 and asum == 20 and bsum == 0
              and all(abs(cs[k]) == 1 for k in range(1,100,2))
              and all(cs[k] in (2,4) for k in range(2,100,2)))
        out['independent_check'] = ok
        print(json.dumps(out, sort_keys=True))
        if not ok:
            raise SystemExit('independent exact LABS check failed')
        return 0

    print(json.dumps(out, sort_keys=True))
    if st == cp_model.INFEASIBLE:
        return 0
    return 2


if __name__ == '__main__':
    sys.exit(main())
