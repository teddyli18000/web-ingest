# W127 order-25 projection: exact exclusion of `ka=18` by GF(2)-kernel MITM

Date: 2026-10-29

## Scope

For the odd-perfect `(20,0)` W127 branch, the established order-25 compression gives ternary length-25 sequences `p,c` satisfying

```text
sum p = 10,
sum c = 0,
||p||^2 + ||c||^2 = 26,
p c* + c p* = 0  in Z[x]/(x^25-1),
PAF_p(r)+PAF_c(r) in {2,3,4}, r=1,...,12,
sum_{r=1}^{12} [PAF_p(r)+PAF_c(r)] = 37.
```

Write

```text
ka=||p||^2,
kc=||c||^2=26-ka.
```

This note exactly excludes

```text
(ka,kc)=(18,8).
```

Together with the previously exact `ka=20,22,24` exclusions, only `ka=10,12,14,16` remain in W127.

## Composition

At `ka=18,kc=8`, the ternary compositions are forced:

```text
p: 14 entries +1, 4 entries -1, 7 entries 0,
c:  4 entries +1, 4 entries -1, 17 entries 0.
```

Let `z` be the zero indicator of `p` and `n` its negative indicator. Then

```text
p = 1-z-2n,
|z|=7,
|n|=4,
z n = 0.
```

For fixed `c`, use the 13 independent cyclic cross coefficients `r=0,...,12` and define

```text
M[r,j] = c_(j-r)+c_(j+r).
```

Since `sum c=0`, `M 1=0`, so the exact cross equation becomes

```text
M z + 2 M n = 0.                                  (1)
```

## GF(2) kernel reduction

Reducing (1) modulo 2 gives the necessary condition

```text
M z = 0  (mod 2).                                  (2)
```

Modulo 2, `M` depends only on the support of `c`, not on its signs. Therefore the nullspace is computed once per support orbit.

All 8-subsets of `Z_25` are partitioned exactly under the affine group

```text
i -> a i+b,  gcd(a,25)=1,
```

of size 500. Explicit orbit marking verifies

```text
C(25,8) = 1,081,575 raw supports,
2,191 affine support orbits.
```

For every support representative, Gaussian elimination over GF(2) constructs the full nullspace of (2), and only nullspace vectors of Hamming weight 7 are retained. The kernel dimension is 13 or 15 in this search. The weight-7 list has about 142 elements per support orbit on average, versus the unfiltered

```text
C(25,7)=480,700
```

zero masks.

This is the key representation change that makes the `ka=18` shard small.

## Complete c-orbit coverage

For each support representative, every choice of four positive positions among its eight support positions is enumerated. The stabilizer of the support and the independent global sign flip `c -> -c` are used only as exact symmetries.

The implementation explicitly checks that all 70 signings on every representative support are covered by these sign orbits. Across the 2,191 support orbits this gives exactly

```text
75,987 c affine/sign orbit representatives.
```

No generic orbit-size assumption is used.

## Exact integer MITM

For each fixed `c`, enumerate all

```text
C(25,4)=12,650
```

negative masks `n` and compute `Mn`.

Every coordinate of `Mn` lies in `[-8,8]`. The complete 13-coordinate integer vector is encoded injectively as a base-17 integer:

```text
key(Mn) = sum_{r=0}^{12} (Mn_r+8) 17^r.
```

`17^13` fits safely in 64 bits, so this is an exact encoding, not a probabilistic hash. For each weight-7 GF(2)-kernel mask `z`, equation (1) requires

```text
Mn = -Mz/2.
```

The exact base-17 key is looked up, disjointness `z & n = 0` is checked, and every hit is reconstructed as a ternary `p`.

Every reconstructed candidate is then independently rechecked against:

1. the 13 integer equations used by the MITM;
2. all 25 original cyclic cross coefficients;
3. all 12 independent combined periodic autocorrelations;
4. the exact W127 target range `{2,3,4}` and sum 37.

Thus the orbit reduction, GF(2) filter, and table lookup cannot silently create an exclusion.

## Exact result

Implementation:

```text
code/oddperfect_w127_ka18_kernel_mitm.cpp
```

A local full run on 5 CPU threads returned

```text
supports=2191
c_reps=75987
cross-compatible p/c pairs=3,675,345
W127 target survivors=0
```

An independent GitHub Actions reproduction used all four CPUs of one hosted runner and returned exactly the same counts:

```text
SUMMARY supports=2191 c_reps=75987 cross=3675345 target=0
```

Workflow run:

```text
40998739009
```

The exact search step took about 5.23 seconds on that runner. Runtime is not part of the proof.

Therefore

```text
boxed: (ka,kc)=(18,8) is impossible in the W127 order-25 projection.
```

## Additional projection diagnostic

Before this exact search, the committed order-10 cross + NGP projection was independently regenerated and then mapped to possible `+25` support sizes. All 4,220 order-10 profile pairs remain compatible with at least one order-25 support layer, but the counts by `ka` are

```text
ka=10: 3376
ka=12: 4080
ka=14: 4220
ka=16: 4220
ka=18: 2988
ka=20:  868
ka=22:  384
ka=24:   96
```

This projection is useful for prioritization, but the `ka=18` exclusion above does not depend on it: the exact kernel/MITM sweep covers the complete `ka=18,kc=8` projected space.

## Consequence

The W127 support split began with

```text
ka = 10,12,14,16,18,20,22,24.
```

Exact solver-independent order-25 searches have now removed

```text
ka = 18,20,22,24.
```

The remaining W127 shards are

```text
ka = 10,12,14,16.
```

The next useful move is not to return to the timed-out generic CP-SAT model. Either generalize the GF(2)-kernel representation carefully to the lower `ka` shards, or exploit the equivalent homometric reformulation `X=p+c`, `Y=p-c` to attack all four remaining shards jointly.
