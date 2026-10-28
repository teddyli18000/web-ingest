#!/usr/bin/env python3
"""Exact CP-SAT target model for the LABS-100 odd-energy O=66 layer.

For N=100 the 50 odd-lag correlations split into 25 opposite pairs
(C_k, C_{100-k}) with C_k + C_{100-k} divisible by 4. The pairwise minimum
energy is 2. Writing O=50+8D, O=66 means D=2, so exactly one of these two
structures occurs:

1. single18: one pair is (3,-3) or (-3,3), all others are (1,-1)/(-1,1);
2. two10: two pairs have energy 10 and all others have energy 2.
   Up to standard LABS symmetries this splits into:
   * double-same: both defects have positive pair sum, forcing half sums (2,4);
   * double-mixed: one positive and one negative defect, forcing half product 0.

The zero-product cases are normalized by reversal/sign symmetry to A_sum=0,
0<=B_sum<=20. The upper bound 20 is rigorous for target <=574 from the even
energy budget 508 and Cauchy applied to the 49 even correlations.

Any feasible solution is independently rescored before being printed. UNKNOWN
is reported separately from an exact INFEASIBLE proof.
"""

from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N = 100
SMOKE_SINGLE18 = (
    "-++++----+-+-++++-+++--++--++--++--++---+--++--++--++--++--++---+--++--++--++--++--+---+-++++++-+--+"
)


def exact(seq: str) -> tuple[int, int, list[int], int, int]:
    s = [1 if ch == "+" else -1 for ch in seq]
    cs = [0] + [sum(s[i] * s[i + k] for i in range(N - k)) for k in range(1, N)]
    energy = sum(c * c for c in cs[1:])
    odd = sum(cs[k] * cs[k] for k in range(1, N, 2))
    asum = sum(s[0::2])
    bsum = sum(s[1::2])
    return energy, odd, cs, asum, bsum


def add_square_table(model: cp_model.CpModel, v, name: str, lo: int, hi: int):
    q = model.NewIntVar(0, max(lo * lo, hi * hi), name)
    model.AddAllowedAssignments([v, q], [(x, x * x) for x in range(lo, hi + 1)])
    return q


def pair_class(cs: list[int]) -> tuple[list[int], list[int], list[int]]:
    e18, pos10, neg10 = [], [], []
    for k in range(1, 50, 2):
        x, y = cs[k], cs[N - k]
        pe = x * x + y * y
        if pe == 18:
            e18.append(k)
        elif pe == 10:
            if x + y == 4:
                pos10.append(k)
            elif x + y == -4:
                neg10.append(k)
            else:
                raise ValueError("energy-10 pair has impossible sum")
        elif pe != 2:
            raise ValueError(f"unexpected odd-pair energy at k={k}: {pe}")
    return e18, pos10, neg10


def build(case: str, target: int, hint: str | None):
    if case not in {"single18", "double-same", "double-mixed"}:
        raise ValueError("bad case")
    if target < 66:
        raise ValueError("target must be at least 66")

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x{i}") for i in range(N)]  # 0 => +1, 1 => -1

    asum = model.NewIntVar(-50, 50, "asum")
    bsum = model.NewIntVar(-50, 50, "bsum")
    model.Add(asum == 50 - 2 * sum(x[0::2]))
    model.Add(bsum == 50 - 2 * sum(x[1::2]))

    if case == "double-same":
        model.Add(asum == 2)
        model.Add(bsum == 4)
    else:
        model.Add(asum == 0)
        model.Add(bsum >= 0)
        if target <= 574:
            model.Add(bsum <= 20)

    corr: dict[int, cp_model.IntVar] = {}
    even_q = []
    even_corr = []

    for k in range(1, N):
        length = N - k
        z = []
        for i in range(length):
            d = model.NewBoolVar(f"z_{k}_{i}")
            model.AddBoolXOr([x[i], x[i + k], d.Not()])
            z.append(d)
        m = model.NewIntVar(0, length, f"m{k}")
        model.Add(m == sum(z))
        c = model.NewIntVar(-length, length, f"c{k}")
        model.Add(c == length - 2 * m)
        corr[k] = c

        if k % 2 == 0:
            q = model.NewIntVar(0, target - 66, f"q{k}")
            rows = [
                (value, value * value)
                for value in range(-length, length + 1, 2)
                if value * value <= target - 66
            ]
            model.AddAllowedAssignments([c, q], rows)
            even_q.append(q)
            even_corr.append(c)

    if case == "single18":
        flags = []
        for k in range(1, 50, 2):
            j = N - k
            h = model.NewBoolVar(f"d18_{k}")
            model.AddAllowedAssignments(
                [corr[k], corr[j], h],
                [(-1, 1, 0), (1, -1, 0), (-3, 3, 1), (3, -3, 1)],
            )
            flags.append(h)
        model.Add(sum(flags) == 1)
    elif case == "double-same":
        flags = []
        for k in range(1, 50, 2):
            j = N - k
            h = model.NewBoolVar(f"d10_{k}")
            model.AddAllowedAssignments(
                [corr[k], corr[j], h],
                [(-1, 1, 0), (1, -1, 0), (1, 3, 1), (3, 1, 1)],
            )
            flags.append(h)
        model.Add(sum(flags) == 2)
    else:
        states = []
        for k in range(1, 50, 2):
            j = N - k
            st = model.NewIntVar(-1, 1, f"d10state_{k}")
            model.AddAllowedAssignments(
                [corr[k], corr[j], st],
                [
                    (-1, 1, 0), (1, -1, 0),
                    (1, 3, 1), (3, 1, 1),
                    (-1, -3, -1), (-3, -1, -1),
                ],
            )
            states.append(st)
        nonzero = []
        for idx, st in enumerate(states):
            nz = model.NewBoolVar(f"d10nz_{idx}")
            model.AddAllowedAssignments([st, nz], [(-1, 1), (0, 0), (1, 1)])
            nonzero.append(nz)
        model.Add(sum(states) == 0)
        model.Add(sum(nonzero) == 2)

    model.Add(sum(even_q) <= target - 66)

    if case == "double-same":
        model.Add(sum(even_corr) == -40)
    else:
        b2 = add_square_table(model, bsum, "bsum_sq", 0, 20 if target <= 574 else 50)
        model.Add(2 * sum(even_corr) == b2 - 100)

    a_alt = model.NewIntVar(-50, 50, "a_alt")
    b_alt = model.NewIntVar(-50, 50, "b_alt")
    a_terms = []
    b_terms = []
    for j in range(50):
        coeff = 1 if j % 2 == 0 else -1
        a_terms.append(coeff * (1 - 2 * x[2 * j]))
        b_terms.append(coeff * (1 - 2 * x[2 * j + 1]))
    model.Add(a_alt == sum(a_terms))
    model.Add(b_alt == sum(b_terms))
    a2 = add_square_table(model, a_alt, "a_alt_sq", -50, 50)
    b2 = add_square_table(model, b_alt, "b_alt_sq", -50, 50)
    alternating_even = sum(
        (1 if r % 2 == 0 else -1) * corr[2 * r] for r in range(1, 50)
    )
    model.Add(a2 + b2 == N + 2 * alternating_even)

    if hint is not None:
        if len(hint) != N or any(ch not in "+-" for ch in hint):
            raise ValueError("bad hint")
        for var, ch in zip(x, hint):
            model.AddHint(var, 0 if ch == "+" else 1)

    return model, x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=["single18", "double-same", "double-mixed"], required=True)
    ap.add_argument("--target", type=int, default=574)
    ap.add_argument("--seconds", type=float, default=600.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        e, o, cs, a, b = exact(SMOKE_SINGLE18)
        cls = pair_class(cs)
        print(f"SMOKE energy={e} odd={o} asum={a} bsum={b} classes={cls}")
        if e != 33562 or o != 66 or a != 0 or b != 2 or cls != ([17], [], []):
            raise SystemExit("smoke structural check failed")

    hint = SMOKE_SINGLE18 if args.case == "single18" and args.target >= 33562 else None
    model, x = build(args.case, args.target, hint)
    validation = model.Validate()
    if validation:
        raise SystemExit(f"MODEL_INVALID {validation}")

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.randomize_search = True
    solver.parameters.cp_model_presolve = True
    solver.parameters.symmetry_level = 2

    start = time.time()
    status = solver.Solve(model)
    print(
        "STATUS",
        f"case={args.case}",
        solver.StatusName(status),
        f"wall={time.time()-start:.3f}",
        f"branches={solver.NumBranches()}",
        f"conflicts={solver.NumConflicts()}",
    )
    if status == cp_model.INFEASIBLE:
        print(f"PROVED_INFEASIBLE case={args.case}")
        return
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print(f"UNRESOLVED case={args.case}")
        return

    seq = "".join("-" if solver.Value(v) else "+" for v in x)
    e, o, cs, a, b = exact(seq)
    cls = pair_class(cs)
    print(
        f"FOUND case={args.case} energy={e} odd={o} even={e-o} "
        f"asum={a} bsum={b} classes={cls} seq={seq}"
    )
    if e > args.target or o != 66:
        raise SystemExit("independent exact score check failed")
    e18, pos10, neg10 = cls
    if args.case == "single18":
        ok = len(e18) == 1 and not pos10 and not neg10 and a == 0 and b >= 0
        if args.target <= 574:
            ok = ok and b <= 20
    elif args.case == "double-same":
        ok = not e18 and len(pos10) == 2 and not neg10 and (a, b) == (2, 4)
    else:
        ok = not e18 and len(pos10) == 1 and len(neg10) == 1 and a == 0 and b >= 0
        if args.target <= 574:
            ok = ok and b <= 20
    if not ok:
        raise SystemExit("independent structural check failed")


if __name__ == "__main__":
    main()
