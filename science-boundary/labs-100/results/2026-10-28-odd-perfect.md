# 2026-10-28 odd-perfect manifold search

## Structure

For `N=100`, every odd-lag aperiodic autocorrelation has odd parity, so the minimum possible odd-lag contribution is `50`. Call a sequence **odd-perfect** when every odd `|C_k|=1`, equivalently when the odd-lag energy is exactly `50`.

The general binary-sequence congruence

```text
C_k + C_{100-k} ≡ 0 (mod 4)
```

has a strong consequence here: if the sequence is odd-perfect and `k` is odd, both terms are `±1`, hence

```text
C_{100-k} = -C_k.
```

Writing the sequence as two length-50 parity halves

```text
A_i = s_{2i},   B_i = s_{2i+1},   i=0..49,
```

and setting `a=sum A_i`, `b=sum B_i`, the identity `sum_{k odd} C_k = ab` gives the necessary condition

```text
ab = 0.
```

Also

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

GitHub Actions run `40612938897` launched 8 shards, each with 128 random starts and 100,000 odd-perfect walk steps, for 1,024 random starts total. Tenure ranges `5..15` and `10..30` were tested.

The strongest observations were:

- multiple shards independently rediscovered energy `578` from random starts;
- checked `E=578` outputs were standard symmetry images of the public Knauer incumbent;
- the best verified inequivalent energy captured from this run was `E=622`, with odd energy `50`, at minimum ordinary Hamming distance `47` from the incumbent symmetry orbit;
- several other shards reached `638`, `650`, `662`, `678`, etc., materially stronger than the earlier unrestricted CPU tabu probes.

Verified `E=622` sequence:

```text
++--+--+++++++++++++++-------++++--+--+--+--+++--+---++-++---+++---++-+--+-+-+--+-+-+-+-+-+-+--+++--
```

Exact score:

```text
E = 622
odd-lag energy = 50
even-lag energy = 572
minimum ordinary Hamming distance to incumbent symmetry orbit = 47
```

### Structural reclassification of the E=622 state

The large ordinary Hamming distance does **not** mean this state leaves the near-skew structural family. Direct checking shows

```text
s_p s_{100-p} = (-1)^p,  p=1,...,49,
```

so its positions `1..99` form the same length-99 skew tail representation used by the incumbent. In the corrected 50 near-skew free coordinates it is only radius `24` from the incumbent (the corresponding ordinary Hamming distance is `47`).

This matters for interpretation: `E=622` is an inequivalent LABS state, but it is not evidence for a distinct non-near-skew low-energy component.

## Scaled campaign

GitHub Actions run `40627045447` scaled the same calibrated kernel to 8 independent shards, each with 256 random starts and 250,000 odd-perfect walk steps, for **2,048 random starts total**. Several tabu-tenure ranges were used.

Result:

- all 8 shards independently reached `E=578`;
- no shard found `E<=574`;
- final `E=578` sequences checked from the run are symmetry images of the incumbent;
- shard medians were roughly in the mid-700s, so reaching 578 is a rare but repeatedly reproducible basin capture rather than the typical endpoint.

Inspecting monotone `BEST` traces also showed intermediate states such as `E=690`, `694`, `698`, `710`, etc. Some do not satisfy the canonical near-skew reflection in their printed orientation, but after applying the standard LABS 8-element symmetry orbit the checked low-energy examples do have a near-skew representative. This observation is empirical, not a theorem.

To measure the genuinely different regime instead of allowing a final near-skew `578` to hide earlier states, `code/oddperfect_outside_nss.cpp` was added. It records the best odd-perfect state whose entire 8-element LABS symmetry orbit avoids the canonical near-skew manifold. A dedicated calibration campaign was launched as Actions run `40634532205`.

## Exact / CP-SAT probes

Several earlier exact-feasibility models were tested. Completed limited-time results were `UNKNOWN`, not infeasibility proofs:

- unrestricted odd-perfect target `574`: 600 s, no certificate;
- exact ordinary Hamming distance 8 + target `574`, general and odd-perfect variants: 600 s each;
- fixing either parity half of the incumbent and solving the other half: 600 s each.

A later 50-free-variable exact near-skew formulation is documented separately in the current handoff. It fixes the skew reflection directly, makes odd energy identically `50`, and asks only whether even energy can be at most `524`.

## Interpretation

The odd-perfect representation is the first home-grown search space in this project that repeatedly rediscovers the record regime from genuinely random starts. Scaling the same strict 1/2-bit walk unchanged, however, repeatedly returns to the incumbent symmetry orbit and has not produced 574.

The strongest next question is therefore structural: how low can an odd-perfect state go **outside every near-skew orientation**? If that floor is substantially above 578 in calibrated search, effort should shift toward global search inside the near-skew manifold or toward controlled excursions through higher odd-energy layers rather than simply adding more strict odd-perfect starts.
