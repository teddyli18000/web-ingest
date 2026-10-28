# 2026-10-28 odd-perfect manifold search

## Structure

For `N=100`, every odd-lag aperiodic autocorrelation has odd parity, so the minimum possible odd-lag contribution is `50`. Call a sequence **odd-perfect** when every odd `|C_k|=1`, equivalently when the odd-lag energy is exactly `50`.

The general binary-sequence congruence

```text
C_k + C_{100-k} ≡ 0 (mod 4)
```

has a particularly strong consequence here: if the sequence is odd-perfect and `k` is odd, both terms are `±1`, hence

```text
C_{100-k} = -C_k.
```

Thus the 50 odd correlations cancel in opposite pairs.

Writing the sequence as two length-50 halves by parity,

```text
A_i = s_{2i},   B_i = s_{2i+1},   i=0..49,
```

and setting `a=sum A_i`, `b=sum B_i`, the identity `sum_{k odd} C_k = ab` gives the necessary condition

```text
ab = 0
```

for every odd-perfect length-100 sequence.  Also

```text
C_{2r} = C_A(r) + C_B(r),
sum_{r=1}^{49} C_{2r} = (a^2+b^2-100)/2.
```

A target `E<=574` inside this manifold therefore requires even-lag energy at most `524`.

## Search kernel

`code/oddperfect_walk.cpp` uses two phases:

1. random one-bit tabu descent on odd-lag energy until it reaches the exact minimum `50`;
2. a tabu walk using only exact one- and two-bit moves that preserve `|C_k|=1` at every odd lag, while minimizing full LABS energy.

The implementation maintains correlations incrementally and has independent full-energy checks in debug builds.

## First parallel calibration

GitHub Actions run `40612938897` launched 8 shards, each with 128 random starts and 100,000 odd-perfect walk steps, for 1,024 random starts total.  Tenure ranges `5..15` and `10..30` were both tested.

The strongest observations were:

- at least two shards independently rediscovered energy `578` from random starts;
- both `E=578` outputs checked so far are standard symmetry images of the public Knauer incumbent, not new record basins;
- the best verified inequivalent basin captured from the run is `E=622`, with odd energy `50`, at minimum Hamming distance `47` from the eight incumbent symmetry images;
- several other shards reached `638`, `650`, `662`, `678`, etc., showing that this method samples a much stronger quality regime than the earlier unrestricted CPU tabu prototypes.

Verified `E=622` sequence (artifact `labs100-oddperfect-4`, run `40612938897`):

```text
++--+--+++++++++++++++-------++++--+--+--+--+++--+---++-++---+++---++-+--+-+-+--+-+-+-+-+-+-+--+++--
```

Independent exact score:

```text
E = 622
odd-lag energy = 50
even-lag energy = 572
minimum distance to incumbent symmetry orbit = 47
```

One shard's workflow post-check failed only because its best sequence began with `-` and the verification command omitted the `--` option separator; the search result itself was still present in the log.  The scaled follow-up workflow fixes this quoting issue.

## Interpretation

This is the first home-grown search kernel in this project that passes the calibration criterion of returning from genuinely random starts to the public `E=578` regime.  It therefore deserves scaling.  It does **not** yet show a second inequivalent `E=578` solution, and it has not found `E<=574`.

The result also shows that odd-perfect is a useful search manifold beyond merely making small edits of the incumbent: competitive states such as the `E=622` sequence can lie nearly half the cube away from every incumbent symmetry image.

## Exact / CP-SAT probes

Several exact-feasibility models were also tested.  Current completed limited-time results are all **UNKNOWN**, not infeasibility proofs:

- unrestricted odd-perfect target `574`: 600 s, no certificate, status `UNKNOWN`;
- exact Hamming distance 8 + target `574`, both general and odd-perfect variants: 600 s each, `UNKNOWN`;
- fixing either parity half of the incumbent and solving the other half with a reduced 50-variable model: 600 s each, `UNKNOWN`.

Do not cite any of these as exclusions.

## Current next step

A scaled odd-perfect campaign was launched from the calibrated kernel with 8 independent shards, 256 random starts per shard, 250,000 manifold steps per start, and several tabu-tenure ranges.  The first candidate at `E<=574`, if any, must be frozen and independently verified before any record claim.
