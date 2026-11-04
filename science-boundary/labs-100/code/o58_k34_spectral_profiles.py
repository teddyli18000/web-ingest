from functools import lru_cache
from collections import Counter

VALUES = (-3, -2, -1, 0, 1, 2)


def multiset_counts(j=0, count=0, total=0, defect=0, counts=()):
    if j == len(VALUES):
        if count == 24 and total == -16:
            yield defect, counts
        return
    value = VALUES[j]
    penalty = value * (value + 1) // 2
    for k in range(25 - count):
        if defect + k * penalty > 4:
            break
        yield from multiset_counts(j + 1, count + k, total + k * value,
                                   defect + k * penalty, counts + (k,))


@lru_cache(None)
def paired_spectra(counts):
    if not sum(counts):
        return frozenset({()})
    i = next(i for i, n in enumerate(counts) if n)
    rem = list(counts)
    rem[i] -= 1
    out = set()
    for j, n in enumerate(rem):
        if n:
            rem2 = rem.copy()
            rem2[j] -= 1
            for tail in paired_spectra(tuple(rem2)):
                out.add(tuple(sorted((VALUES[i] + VALUES[j],) + tail)))
    return frozenset(out)


if __name__ == '__main__':
    counts = Counter()
    spectra = {d: set() for d in range(5)}
    for d, multiset in multiset_counts():
        counts[d] += 1
        for G in paired_spectra(multiset):
            SH = 2 * (16 + 2 * d) - sum(g * g for g in G)
            if SH >= 0:
                spectra[d].add((G, SH))
    assert [counts[d] for d in range(5)] == [1, 2, 3, 6, 9]
    assert [len(spectra[d]) for d in range(5)] == [5, 13, 34, 56, 105]
    for d in range(5):
        hist = Counter(sh for _, sh in spectra[d])
        print(f'd={d} U_multisets={counts[d]} G_profiles={len(spectra[d])} SH={dict(sorted(hist.items()))}')
    print('total_G_profiles=', sum(map(len, spectra.values())))
