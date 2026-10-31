# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value `578`?

For signs `s_i in {-1,+1}`,

```text
C_k = sum_i s_i s_{i+k},
E = sum_{k=1}^{99} C_k^2.
```

Length-100 energies are `2 (mod 4)`, so the first nominal improvement is `574`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Current state

**Active; no unrestricted breakthrough yet. Current best verified energy remains `578`.**

Public incumbent:

```text
++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-
```

The strongest exact progress is on the minimum odd-energy (`odd-perfect`) layer, where every odd-lag correlation has magnitude one and the odd energy is `50`.

Current exact frontier:

- the entire standard N=100 near-skew manifold has exact minimum `578`;
- odd-perfect endpoint defect classes `d=0,1,2,3,4,5` contain no `E<=574` sequence;
- the sharp `(a,b)=(20,0), W=127` branch is completely excluded;
- the three remaining low11 `(20,0)` sparse near-NGP branches `W129-A`, `W131-A2`, `W131-B1` are closed after a full all-affine fibre audit;
- for `(a,b)=(18,0)`, the complete order-25 compression layers `K=19` and `K=21` are exactly excluded for `E<=570`;
- the active next layer is `K=23`.

The latest complete records are:

- [`results/2026-10-31-h18-k19-complete-exclusion.md`](results/2026-10-31-h18-k19-complete-exclusion.md)
- [`results/2026-10-31-h18-k21-complete-exclusion.md`](results/2026-10-31-h18-k21-complete-exclusion.md)
- [`results/2026-10-30-low11-affine-fibre-closure.md`](results/2026-10-30-low11-affine-fibre-closure.md)
- [`results/2026-10-29-w127-complete-exclusion.md`](results/2026-10-29-w127-complete-exclusion.md)

## Exact near-skew result

For canonical near-skew `s`, deleting one endpoint gives a skew-symmetric length-99 sequence `t`, while appending the matching endpoint gives a skew-symmetric length-101 sequence `u`. Exact correlation algebra gives

```text
E99(t) + E101(u) = 2 E100(s) - 1.
```

Packebusch-Mertens proved the skew-symmetric optima through N=119; `E_skew(99)=577` and `E_skew(101)=578`. Hence every N=100 near-skew sequence has `E>=578`, and the public incumbent attains equality.

Proof: [`results/2026-10-29-nearskew-optimum-proof.md`](results/2026-10-29-nearskew-optimum-proof.md).

## Odd-perfect global formulation

Split the sequence into parity halves

```text
A_i=s_(2i), B_i=s_(2i+1),
a=sum A_i, b=sum B_i.
```

Odd-perfectness plus the opposite-lag congruence forces `ab=0`.

With Littlewood polynomials

```text
A(x)=sum A_i x^i,
B(x)=sum B_i x^i,
```

odd-perfectness is equivalent to

```text
A B^R + x B A^R = (x^50-1) Q,
```

where `Q_j=-Q_(49-j)`. Defining

```text
D(x)=A(x)^2-x B(x)^2
```

gives the exact objective identity

```text
||D||_2^2 = 9900 + 2 V,
V = sum_{r=1}^{49} C_(2r)^2.
```

Thus

```text
E<=574  <=>  ||D||_2^2<=10948,
E<=570  <=>  ||D||_2^2<=10940.
```

Full derivation: [`results/2026-10-29-oddperfect-polynomial-factorization.md`](results/2026-10-29-oddperfect-polynomial-factorization.md).

## Order-25 compression / fibre interface

For the current `(18,0)` line write

```text
d_r = C_(2r)/2,
U_r = (d_r+d_(50-r))/2,
V_r = (d_r-d_(50-r))/2,
m=d_25,
K=25+m.
```

Decompose the parity halves as

```text
A=(1+x^25)p+(1-x^25)alpha,
B=(1+x^25)q+(1-x^25)beta,
c=x^13 q,
gamma=x^13 beta.
```

The odd-perfect cyclic cross equation splits exactly into two independent order-25 equations:

```text
p c* + c p* = 0                    mod x^25-1,
alpha gamma* - gamma alpha* = 0    mod x^25+1.
```

For

```text
G_j = PAF_p(j)+PAF_c(j) = U_j+U_(25-j),
```

the sharp compressed lower bound is

```text
qmin(G)=sum_j ceil(G_j^2/2) <= sum U_r^2.
```

If

```text
SG=sum G_j^2,
H_j=NPAF_alpha(j)+NPAF_gamma(j),
SH=sum H_j^2,
```

then the full fibre identity is

```text
2 sum U_r^2 = SG+SH.
```

This is now the preferred representation for the `(18,0)` center layers. The simultaneous `AGL(1,Z_25)` action on the two fibre supports is quotiented exactly before sign enumeration; any final survivors are reconstructed to binary length-100 sequences and rescored in the original LABS objective.

### `K=19`

Here `m=-6` and `E<=570` forces an extremely sparse near-NGP spectrum. All six possible splits

```text
(kp,kc)=(19,0),(17,2),(15,4),(13,6),(11,8),(9,10)
```

are exactly empty.

Record: [`results/2026-10-31-h18-k19-complete-exclusion.md`](results/2026-10-31-h18-k19-complete-exclusion.md).

### `K=21`

Here

```text
m=-4,
W=16+2(Q+R),
E<=570 iff Q+R<=57.
```

All seven possible norm splits `kp=9,11,13,15,17,19,21` are exactly empty. The last four fibre-Q survivors were expanded through every matching compressed affine image, both independent fibre signs, and all 500 induced full-length affine transforms; none even met the residual `V` budget.

Record: [`results/2026-10-31-h18-k21-complete-exclusion.md`](results/2026-10-31-h18-k21-complete-exclusion.md).

### Active `K=23` layer

For `K=23`,

```text
m=-2,
sum U=29,
W=4+2(Q+R),
E<=570 iff Q+R<=63.
```

The same `qmin` and fibre-Q identities apply unchanged. A generic exact compressed solver, [`code/oddperfect_h18_k_compressed.cpp`](code/oddperfect_h18_k_compressed.cpp), is regression-checked against frozen `K=21` counts before use on the new layer.

## Endpoint exclusions

For the two length-99 endpoint deletions let `d_L,d_R` count nonzero odd deletion correlations and define `d=min(d_L,d_R)`. Exact computations give

```text
d=0  near-skew: minimum E=578
d=1  no E<=574
d=2  no E<=574
d=3  no E<=574
d=4  no E<=574
d=5  no E<=574
```

So any surviving odd-perfect breakthrough has `d>=6`. This hierarchy should not be extended mechanically; the compression/factorization route is currently stronger.

Durable endpoint records are under [`results/`](results/), including [`results/2026-10-29-endpoint-defect5-mod4-exhaustion.md`](results/2026-10-29-endpoint-defect5-mod4-exhaustion.md).

## Other exact / high-value evidence

- Ordinary Hamming radii **1 through 7** around the incumbent are completely exhausted: `17,278,988,695` non-center sequences, no improvement. See [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).
- Exact boundary+skew-core target searches exclude broad structured classes; see [`results/2026-10-28-skewcore-hierarchy.md`](results/2026-10-28-skewcore-hierarchy.md).
- Pairwise crossover among eight near-skew elites and parity-block descent were strongly negative; the exact near-skew proof supersedes those heuristics as a target route.
- Neighboring-length transfer and the tested Golay-52 deletion family were weak; see [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) and [`results/2026-10-28-golay52-deletion.md`](results/2026-10-28-golay52-deletion.md).

## Dead ends / constraints learned

- Do not spend further compute inside near-skew to beat 578; it is rigorously impossible.
- Do not repeat small ordinary incumbent edits; radius 7 is exact and strongly negative.
- Do not treat CP-SAT `UNKNOWN`, timeouts, SIGKILL, or unfinished Actions as exclusions.
- Do not mechanically extend the endpoint-defect hierarchy; candidate quality stayed flat while only the excluded region grew.
- Generic full-sequence and order-25 CP-SAT repeatedly timed out. The successful exact progress came from changing representation: GF(2) support kernels, modular sign solving, periodic/negacyclic fibre splitting, `qmin`, and affine support quotients.
- A compressed affine orbit representative is not automatically sufficient for aperiodic fibre properties. All relevant affine images must be covered or an invariant must be proved; this issue was explicitly repaired in the low11 and K19/K21 work.

## Next steps

1. **Complete the `(18,0), K=23` exact census** with the generic compressed solver and the affine-canonical fibre-Q solver. Any surviving Q-level fibres must be reconstructed and directly rescored at length 100.
2. If K23 closes, continue the same representation through the remaining convex-feasible center layers `K=25,27,29,31,33`, reassessing the search space if compressed/fibre survivor counts stop shrinking effectively.
3. In parallel, seek a global lower bound on `||A^2-xB^2||_2^2` or an algebraic classification of the periodic/negacyclic pair that would eliminate the whole odd-perfect layer at once.
4. Only after the odd-perfect frontier is materially exhausted should higher odd-energy layers (`O=58,66,...`) receive major exact compute; derive their own target arithmetic first.
5. Re-check Few Shots/public records immediately before any record claim. If `E<=574` is found, freeze the exact sequence, independently rescore it, run the Few Shots verifier/check, create the required certificate/SHOT, and publish as authorized.

## Durable artifacts

- [`code/`](code/) — exact scorers, compression/fibre solvers, endpoint solvers, target arithmetic and witness verifiers.
- [`results/`](results/) — exact exclusions, proofs, transcripts and structural derivations.
- [`notes/literature-and-methods.md`](notes/literature-and-methods.md) — literature and method decisions.

## Sources

- Few Shots p006 problem/verifier: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>
- Few Shots procedure: <https://github.com/few-shots/few-shots/blob/main/skills/take-a-shot/SKILL.md>
- QOBLIB LABS benchmark/solutions: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>
- Knauer record table / historical solver mirror: <https://github.com/borkob/git_labs>
- Packebusch & Mertens, exact LABS and skew-symmetric enumeration: <https://arxiv.org/abs/1512.02475>
- Prestwich, improved LABS branch-and-bound: <https://arxiv.org/abs/1305.6187>
- Bošković, Brglez & Brest, heuristic LABS search: <https://arxiv.org/abs/1406.5301>
- Zhang et al., massively parallel memetic tabu (2025): <https://arxiv.org/abs/2504.00987>
- Pšeničnik et al., search-space region prioritization (2026): <https://arxiv.org/abs/2607.09688>
- Wang & Zhu, base/normal/near-normal sequences (2025/2026): <https://arxiv.org/abs/2506.20296>

## Work log

- **2026-10-27:** Reproduced the baseline; added independent scoring/search kernels; exhausted incumbent Hamming radii through 6; surveyed solver literature and neighboring-length records.
- **2026-10-28:** Exhausted radius 7; calibrated odd-perfect search; built exact skew-core and target-arithmetic decompositions; exhausted large near-skew local/crossover/block neighborhoods.
- **2026-10-29:** Proved exact N100 near-skew optimum 578; excluded endpoint defects 1 through 5; derived the global parity-polynomial factorization and norm identity; developed the order-25 compression program and closed W127.
- **2026-10-30:** Repaired affine-fibre coverage rigor; exactly closed the remaining low11 W129/W131 branches; derived and regression-tested the periodic/negacyclic fibre split; began the `(18,0)` center-layer program.
- **2026-10-31:** Completely excluded `(18,0)` `K=19` and `K=21` through `E<=570`, including direct final rescoring of all Q-level fibre survivors; generalized the compressed solver and moved to `K=23`.
