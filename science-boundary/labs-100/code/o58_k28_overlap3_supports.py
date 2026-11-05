#!/usr/bin/env python3
"""Complete GF(2) support census for O58/K28, kp=13,kc=15, overlap t=3.

Every common-support triple is considered up to the simultaneous AGL(1,25)
action. For a triple T, all P=supp(p) containing T with |P|=13 and
P*T^*+T*P^*=0 (mod2) are enumerated. C=supp(c)=complement(P) union T.
"""
from itertools import combinations
import argparse

N = 25
UNITS = [a for a in range(1, N) if a % 5 != 0]
ALL = (1 << N) - 1


def affine(T, a, b):
    return frozenset((a * i + b) % N for i in T)


def triple_orbits():
    seen = set()
    representatives = []
    for triple in combinations(range(N), 3):
        T = frozenset(triple)
        if T in seen:
            continue
        orbit = {affine(T, a, b) for a in UNITS for b in range(N)}
        seen.update(orbit)
        representatives.append((T, len(orbit)))
    assert len(representatives) == 6
    assert len(seen) == 2300
    return representatives


def supports(T):
    positions = [j for j in range(N) if j not in T]
    matrix = []
    for r in range(1, 13):
        row = 0
        rhs = 0
        for j in positions:
            if ((j + r) % N in T) != ((j - r) % N in T):
                row |= 1 << j
        for j in T:
            rhs ^= ((j + r) % N in T) != ((j - r) % N in T)
        matrix.append([row, rhs])

    pivot = []
    rank = 0
    for j in positions:
        candidate = next((i for i in range(rank, 12) if matrix[i][0] >> j & 1), None)
        if candidate is None:
            continue
        matrix[candidate], matrix[rank] = matrix[rank], matrix[candidate]
        for i in range(12):
            if i != rank and (matrix[i][0] >> j & 1):
                matrix[i][0] ^= matrix[rank][0]
                matrix[i][1] ^= matrix[rank][1]
        pivot.append(j)
        rank += 1

    assert all(not row and not rhs for row, rhs in matrix[rank:])
    free = [j for j in positions if j not in pivot]
    base = sum(1 << j for i, j in enumerate(pivot) if matrix[i][1])
    Tmask = sum(1 << j for j in T)
    answers = []
    for setting in range(1 << len(free)):
        P = base
        for i, f in enumerate(free):
            if setting >> i & 1:
                P ^= 1 << f
                for r, j in enumerate(pivot):
                    if matrix[r][0] >> f & 1:
                        P ^= 1 << j
        P |= Tmask
        if P.bit_count() != 13:
            continue
        C = (ALL ^ P) | Tmask
        assert P.bit_count() == 13 and C.bit_count() == 15
        assert (P & C) == Tmask
        for r in range(1, 13):
            parity = sum(
                ((P >> i & 1) * (C >> ((i + r) % N) & 1))
                + ((C >> i & 1) * (P >> ((i + r) % N) & 1))
                for i in range(N)
            ) & 1
            assert parity == 0
        answers.append(P)
    return answers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="CSV filename with triple_mask,P_mask rows")
    args = ap.parse_args()

    orbits = triple_orbits()
    counts = []
    with open(args.out, "w", encoding="utf-8") as out:
        for T, orbital_size in orbits:
            choices = supports(T)
            counts.append(len(choices))
            Tmask = sum(1 << j for j in T)
            for P in choices:
                out.write(f"{Tmask},{P}\n")
            print("SUPPORT_CLASS", sorted(T), "orbit_size=", orbital_size, "P_count=", len(choices))
    assert counts == [462, 311, 324, 311, 324, 462]
    assert sum(counts) == 2194
    print("K28_SUPPORT_COMPLETE triple_orbits=6 support_pairs=2194")


if __name__ == "__main__":
    main()
