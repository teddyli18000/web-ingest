"""Exact finite regression for projecting expanded LABS energy onto four spins.

The projected Hamiltonian is the assignment-dependent part of E averaged
uniformly over all exterior sign assignments. This is not the same operator
as deleting cross-boundary autocorrelation edges before squaring.
"""
from itertools import combinations, product


def energy(s):
    return sum(sum(s[i] * s[i + k] for i in range(len(s) - k)) ** 2
               for k in range(1, len(s)))


def projected(p, v):
    h = sum(2 * v[i] * v[j] for i, j in combinations(range(4), 2)
            if (p[j] - p[i]) % 2 == 0)
    for a, b, c, d in ((0, 1, 2, 3), (0, 2, 1, 3), (0, 3, 1, 2)):
        if p[b] - p[a] == p[d] - p[c]:
            h += 2 * v[0] * v[1] * v[2] * v[3]
    return h


def exterior_sum(n, p, v):
    other = [i for i in range(n) if i not in p]
    total = 0
    for env in product((-1, 1), repeat=n - 4):
        s = [1] * n
        for i, sign in zip(p, v):
            s[i] = sign
        for i, sign in zip(other, env):
            s[i] = sign
        total += energy(s)
    return total


def main():
    tests = 0
    for n in range(5, 9):
        factor = 2 ** (n - 4)
        for positions in combinations(range(n), 4):
            ref = (1, 1, 1, 1)
            ref_total = exterior_sum(n, positions, ref)
            ref_h = projected(positions, ref)
            for signs in product((-1, 1), repeat=4):
                assert exterior_sum(n, positions, signs) - ref_total == (
                    factor * (projected(positions, signs) - ref_h)
                ), (n, positions, signs)
                tests += 1
    p = (0, 1, 2, 4)
    assert projected(p, (1, 1, 1, 1)) == 6
    print(f"PASS {tests} assignment checks, n=5..8, outside midpoint retained")


if __name__ == "__main__":
    main()
