# 2026-10-28 exact exclusion of the 3-bit-boundary + skew97 family

## Statement

Consider normalized length-100 sequences whose suffix at positions `3..99` is a length-97 skew-symmetric sequence. Up to the standard LABS global-sign and alternating-sign symmetries, **no odd-perfect sequence in this complete structural family has total LABS energy `E <= 574`.**

This is now an exact computational exclusion, not a heuristic observation.

The family was motivated by the reproducible `E=1162` odd-perfect basin found in every shard of the outside-near-skew audit. That basin has exactly this `3 + skew97` structure.

## Coordinates

Normalize `s_0=+1`. Write the first three signs as

```text
(s_0,s_1,s_2) = (1,b,c).
```

Let

```text
u_j = s_{2j+1},  j=0,...,49,
v_j = s_{2j+2},  j=0,...,48.
```

The skew97 suffix implies the mirror relations

```text
u_{50-r} = u_r,
v_{49-r} = -v_r.
```

Odd-perfectness means every odd-lag correlation has magnitude one. Pairing each odd lag with its skew97 mirror reduces that condition to local constraints on the boundary triple. The two values of `c=s_2` produce two very different finite spaces.

## Branch 1: `c=+1`

For `c=+1`, the mirrored odd-perfect constraints force

```text
u_1 = -u_0,
u_{r+1} = -u_r,  r=1,...,24,
```

while `v_1,...,v_24` are arbitrary. Thus the entire branch has exactly

```text
2 * 2^24 = 2^25 = 33,554,432
```

sequences: one free sign `b=u_0` and 24 free `v` signs.

`code/skewcore_d3_cplus_exact.cpp` enumerates this complete space with exact incremental scoring. GitHub Actions run `40637378032` checked all `33,554,432` states in 2.90 seconds and independently rescored the optimum with `code/verify.py`.

Result:

```text
tested = 33,554,432
best E = 38,906
odd energy = 50
count E<=578 = 0
```

Best sequence in this branch:

```text
+++--+---++--+---+--++---+--+++--++-++--+++--+---+--+++-+++--+--++---++--+--+++-++--+++-+++--++-+++-
```

Independent verifier output: `38906`.

## Branch 2: `c=-1`

For `c=-1`, use alternating-sign symmetry to fix `s_1=+1` without changing `s_0` or `s_2`. The remaining odd-perfect constraints reduce every mirrored transition `r=1,...,24` to exactly three possibilities:

```text
F  : u_{r+1} = -u_r,  v_r = -u_r
S+ : u_{r+1} =  u_r,  v_r = +1
S- : u_{r+1} =  u_r,  v_r = -1
```

There is also the initial free sign `u_1`. Therefore the complete normalized branch has

```text
2 * 3^24
```

states.

`code/skewcore_d3_cminus_bnb.cpp` performs an exact outer-in branch-and-bound over this ternary tree. It uses only a rigorous fixed-product correlation lower bound; no heuristic pruning is used.

The workflow first performed a positive control under even-energy cap `1112` and recovered the known `E=1162` structural basin. It then searched the Few Shots target even-energy cap `524` (`50+524=574`).

GitHub Actions run `40637624589` target result:

```text
prefix split depth = 8
tasks = 13,122 / 13,122
nodes = 566,892,784
pruned = 377,932,871
leaves = 0
seconds = 137.54
complete = 1
found = 0
```

Because every prefix task completed and every unexplored subtree was removed only by a rigorous lower bound, this is a complete exclusion of `E<=574` in the `c=-1` branch.

## Conclusion

The two branches exhaust the complete normalized `3-bit boundary + skew97 tail` odd-perfect family. Hence:

```text
E <= 574 is impossible in the entire d=3 skew-core family.
```

This is stronger than the preceding heuristic result that eight independent odd-perfect shards all converged to the same `E=1162` outside-near-skew basin. The `E=1162` state is a genuine strong local attractor, but its whole structural class cannot contain the desired record.

## Implication

The low-energy odd-perfect landscape now has a sharper hierarchy:

- `d=1`, `1 + skew99`: contains the public `E=578` record and remains the primary exact target;
- `d=3`, `3 + skew97`: **exactly excluded for `E<=574`**;
- larger odd boundaries `d=5,7,...`: current heuristic calibration is substantially worse (`1194`, `1406`, `1682`, ...), but not exactly excluded.

This strengthens the case for concentrating exact work on the direct near-skew `d=1` family and for treating transitions through higher odd-energy layers as a separate problem rather than scaling the strict odd-perfect local graph.
