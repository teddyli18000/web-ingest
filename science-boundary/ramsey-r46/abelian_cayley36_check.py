#!/usr/bin/env python3
"""Independent exhaustive checker for all abelian Cayley graphs on 36 vertices."""
from itertools import product
from time import perf_counter


def coords(mods):
    return list(product(*[range(m) for m in mods]))


def idx(c, mods):
    x = 0
    for a, m in zip(c, mods):
        x = x * m + a
    return x


def add(a, b, mods):
    return tuple((x + y) % m for x, y, m in zip(a, b, mods))


def neg(a, mods):
    return tuple((-x) % m for x, m in zip(a, mods))


def clique_k(adj, cand, need):
    if need == 0:
        return True
    while cand.bit_count() >= need:
        b = cand & -cand
        v = b.bit_length() - 1
        cand ^= b
        if clique_k(adj, cand & adj[v], need - 1):
            return True
    return False


def has_k4_edgewise(adj):
    # Deliberately different from the C++ K4 path: inspect common neighbourhoods of edges.
    for u in range(36):
        nu = adj[u] & ~((1 << (u + 1)) - 1)
        vv = nu
        while vv:
            b = vv & -vv
            v = b.bit_length() - 1
            vv ^= b
            common = adj[u] & adj[v] & ~((1 << (v + 1)) - 1)
            cc = common
            while cc:
                q = cc & -cc
                w = q.bit_length() - 1
                cc ^= q
                if adj[w] & cc:
                    return True
    return False


def has_i6(adj):
    full = (1 << 36) - 1
    comp = [full ^ adj[i] ^ (1 << i) for i in range(36)]
    return clique_k(comp, full, 6)


def scan(mods):
    cs = coords(mods)
    mp = {c: i for i, c in enumerate(cs)}
    seen = {0}
    orbits = []
    for d in range(1, 36):
        if d in seen:
            continue
        e = mp[neg(cs[d], mods)]
        seen.add(d)
        seen.add(e)
        orbits.append((d,) if e == d else (d, e))

    orbit_rows = []
    for orbit in orbits:
        rows = [0] * 36
        for x, c in enumerate(cs):
            for d in orbit:
                rows[x] |= 1 << mp[add(c, cs[d], mods)]
        orbit_rows.append(rows)

    adj = [0] * 36
    prev = 0
    k4free = valid = 0
    t0 = perf_counter()
    for t in range(1 << len(orbit_rows)):
        gray = t ^ (t >> 1)
        if t:
            d = gray ^ prev
            o = (d & -d).bit_length() - 1
            rows = orbit_rows[o]
            for v in range(36):
                adj[v] ^= rows[v]
        prev = gray
        if not has_k4_edgewise(adj):
            k4free += 1
            if not has_i6(adj):
                valid += 1
                print("FOUND", mods, gray)
                return
    print(
        "DONE", mods, "orbits", len(orbits), "total", 1 << len(orbits),
        "k4free", k4free, "valid", valid, "sec", perf_counter() - t0
    )


if __name__ == "__main__":
    # Classification: C4 or C2xC2 on the 2-part, C9 or C3xC3 on the 3-part.
    for group in [(36,), (4, 3, 3), (2, 2, 9), (2, 2, 3, 3)]:
        scan(group)
