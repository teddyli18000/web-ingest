# 2026-10-29 odd-perfect endpoint-defect frontier

## Purpose

The N=100 near-skew / pseudo-skew manifold is now rigorously known to have exact optimum 578, so any improvement must leave it. To measure *how* odd-perfect (`odd energy = 50`) states leave that manifold, define an endpoint-deletion defect.

For an odd-perfect length-100 sequence `s`, let

```text
L = s[1..99]   # delete the first sign
R = s[0..98]   # delete the last sign.
```

For every odd `k <= 97`,

```text
C_k(L) = C_k(s) - s_0 s_k,
C_k(R) = C_k(s) - s_{99-k} s_99.
```

Since `C_k(s)=+/-1`, every odd autocorrelation of `L` or `R` is in `{0,+/-2}`. Define

```text
d_L = number of nonzero odd autocorrelations of L,
d_R = number of nonzero odd autocorrelations of R,
d   = min(d_L,d_R).
```

The quantity `d` is invariant under the standard LABS symmetry orbit: global sign and alternating sign preserve each mismatch, while reversal swaps `d_L,d_R`.

Pseudo-/near-skew states have `d=0` for the corresponding skew endpoint deletion. The public E578 incumbent has `(d_L,d_R)=(0,25)`.

## Heuristic frontier campaign

`code/oddperfect_defect_walk.cpp` instruments the already calibrated strict odd-perfect 1/2-bit walk and records the best full N=100 energy observed at every invariant defect `d`.

GitHub Actions run `40740837849` used eight independent shards. Each shard used 64 random odd-perfect starts, 60,000 strict odd-perfect phase-2 steps, and one of four tabu-tenure ranges. Total: 512 odd-perfect starts.

The best observed energy by defect was:

| d | best E | raw `(d_L,d_R)` of that representative |
| ---: | ---: | ---: |
| 0 | **578** | (0,25) |
| 1 | not observed | — |
| 2 | 39130 | (2,25) |
| 3 | 38890 | (28,3) |
| 4 | 38722 | (21,4) |
| 5 | 38690 | (5,26) |
| 6 | 7178 | (11,6) |
| 7 | 38602 | (7,28) |
| 8 | 3014 | (14,8) |
| 9 | 2466 | (9,12) |
| 10 | 1514 | (10,13) |
| 11 | 1586 | (14,11) |
| 12 | 1326 | (14,12) |
| 13 | 1346 | (13,18) |
| 14 | 1246 | (30,14) |
| 15 | **1162** | (20,15) |
| 16 | 1206 | (16,20) |
| 17 | 1266 | (17,24) |
| 18 | 1214 | (20,18) |
| 19 | 1338 | (20,19) |
| 20 | 1306 | (20,29) |
| 21 | 1514 | (21,32) |
| 22 | 1422 | (28,22) |
| 23 | 1538 | (30,23) |
| 24 | 1622 | (24,24) |
| 25 | 1650 | (26,25) |
| 26 | 1898 | (26,27) |
| 27 | 1922 | (27,28) |
| 28 | 2134 | (30,28) |
| 29 | 2546 | (29,30) |
| 30 | 1978 | (33,30) |
| 31 | 1802 | (31,32) |
| 32 | 3262 | (32,32) |

The raw `left/right` labels above come from unnormalized heuristic trajectories and should not be assigned the parity properties derived below. Only `d=min(d_L,d_R)` is being used as a symmetry-invariant layer label.

The qualitative signal is strong but remains heuristic: the walk finds the record only at defect zero; the best nonzero-defect basin is the previously identified E1162 `3-bit boundary + skew97` orbit at `d=15`; the low layers `d=1..5` are either absent or visited only at extremely high energy.

## Exact defect arithmetic after safe symmetry normalization

Odd-perfect implies `a*b=0` for the parity-half sums

```text
A_i=s_{2i}, B_i=s_{2i+1},
a=sum A_i, b=sum B_i.
```

A safe symmetry normalization is:

1. use reversal if necessary so `b=0`;
2. use the independent even-half sign symmetry to make `a>=0`;
3. use the independent odd-half sign symmetry to set `B_0=s_1=+1`.

**Do not also fix `A_0=s_0=+1` when `a>0`; that would over-fix the LABS symmetry group.**

In this normalized orientation, deleting `s_0` gives a length-99 sequence whose two parity sums are `b=0` and `a-s_0`. Hence

```text
sum_{k odd} C_k(L) = 0.
```

Every nonzero odd correlation of `L` is `+2` or `-2`, so the positive and negative defects occur equally often. Therefore

```text
d_L is even.
```

Deleting `s_99` gives parity sums `a` and `-s_99`, hence

```text
sum_{k odd} C_k(R) = -a s_99.
```

If `d_R` terms are nonzero, each is `+/-2`. Therefore exactly

```text
d_R >= a/2,
d_R == a/2 (mod 2).
```

These are exact constraints, independent of the heuristic campaign.

### Consequence for defect 1

If `d=1`, the left side cannot realize the minimum because `d_L` is even. Therefore `d_R=1`. The exact right-defect bound then forces

```text
a = 2.
```

Thus **the entire odd-perfect defect-1 target space collapses to one canonical half-sum class** `(a,b)=(2,0)` (with `B_0=+1` and `A_0` free). This makes defect 1 suitable for a complete outer-in branch-and-bound proof rather than generic CP-SAT.

More generally, an odd defect `d` can only be realized by the right deletion and therefore requires

```text
a <= 2d,
a/2 == d (mod 2).
```

For example defect 3 permits only `a=2` or `a=6`.

## Generic CP-SAT calibration

An earlier generic A/B CP-SAT formulation was split by fixed defect `d=0,1,2,3` for representative half-sum classes. The low-defect coordinate is mathematically valid, but the generic XOR model remained poorly calibrated: representative `d=2` runs at `a=0,10,20` all ended `UNKNOWN` after 90 seconds, with no certificate and no proof.

Those CP runs must not be treated as exclusions. In addition, the first version over-fixed the symmetry by imposing both `A_0=B_0=+1` and `a>=0`; all of its results were `UNKNOWN`, so no exact claim depended on that mistake. New exact search uses the safe normalization above.

## Exact outer-in search

`code/oddperfect_outer_bnb.cpp` implements a specialized exact branch-and-bound:

- assign signs from both ends toward the center;
- every partial odd correlation must still be able to reach `+/-1`;
- even correlations use the rigorous fixed-product / unknown-product lower bound against even-energy cap `524`;
- the exact even-correlation sum `(a^2-100)/2` is enforced as an interval constraint;
- parity-half sums are enforced incrementally;
- fixed endpoint-defect layers use the exact parity/minimum rules above.

The first complete target is defect 1, which needs only `a=2`. The search is sharded by a deterministic outer prefix so independent Actions jobs cover disjoint parts of the exact state space.

## Interpretation

The endpoint defect is currently the most useful coordinate for leaving the now-solved pseudo-skew manifold. It has three advantages:

1. it is invariant at the level `d=min(d_L,d_R)` under the standard LABS symmetry orbit;
2. it has exact arithmetic constraints after normalization;
3. an outer-in search determines high-lag defect contributions early, unlike a generic full-sequence SAT encoding.

The heuristic cliff around low nonzero defect is not a proof. The immediate scientific goal is to convert the first few defect layers into exact exclusions, beginning with defect 1.
