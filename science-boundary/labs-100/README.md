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

The strongest exact progress is on the minimum odd-energy (`odd-perfect`) layer and on the first non-odd-perfect layer `O=58`. A separate constructive parity-half QUBO pilot (2026-11-06) reached O=58 repeatedly but had E>=5718 among those sampled states; full-energy paired swaps reached E=1030 (O=506/522), well above the incumbent.

**New conditional-repair finding (2026-11-08):** Holding correct exterior bits fixed, a 40/50-bit core tabu solver recovered hidden elite E218/E578/E606 targets in 54/120, 118/120, 115/120 trials versus 0/120 for matched-proposal unrestricted tabu. However, 1,840 genuine *unknown exterior* proposals with 1.3696 billion exact full-energy neighbor evaluations reached only E686 at best. This is a conditional-recovery advance, **not** a N100 record or a general solver victory. Future construction must jointly select outer bit patterns with interior cross-lag compensation; blind outer mutation followed by inner repair did not work. [Full evidence and exact source](results/2026-11-08-conditional-core-positive-controls.md).

**Constructive continuation (2026-11-08):** matched-work N40/60/80/100 exact-block/Tabu controls found no stable advantage, and alternative N99→100 movable-insertion plus N100 two-parent interval-stitching did not improve the independently published E606 target-class seed (32,360,000 lifted source-neighborhood evaluations and 32,663,400 two-interval inheritance evaluations). A genuine published N59→60 hidden-answer control also failed to recover the known E218 optimum (best E246). The next stage must introduce a qualitatively different signed-correlation-cut proposal mechanism rather than enlarge these fixed support families. [Full constructive audit and reproducible source](results/2026-11-08-constructive-controls-insertion-stitch.md).

**Additional constructive check (2026-11-06):** complete interval reversal and adjacent-block swap neighborhoods of the E578 incumbent (676,500 operations) return only its trivial symmetry images at or below E578; the best nonsymmetry single-step state is E686, but this is only a one-bit change. A 17-parent diverse two-step segment bridge also reaches no nontrivial E<=578. At symmetry-orbit distance >=8, the best single-step E722 state is a two-place rotation of an alternating-sign incumbent. Exact 14-bit block repair, O66 polishing, affine decimation and parity-block exchange produced no breakthrough. [Reproducible experiment](results/2026-11-06-exact-segment-bridges.md).

Current exact frontier:

- the entire standard N=100 near-skew manifold has exact minimum `578`;
- odd-perfect endpoint defect classes `d=0,1,2,3,4,5` contain no `E<=574` sequence;
- the sharp `(a,b)=(20,0), W=127` branch is completely excluded;
- the three remaining low11 `(20,0)` sparse near-NGP branches `W129-A`, `W131-A2`, `W131-B1` are closed after a full all-affine fibre audit;
- for normalized odd-perfect `(a,b)=(18,0)`, the complete order-25 compression layers `K=19`, `K=21`, and `K=23` are exactly excluded for `E<=570`; hence any surviving candidate on that line has `K>=25`;
- the first non-odd-perfect odd-energy layer `O=58` has been reduced exactly to canonical half sums `(a,b)=(2,2)`, a one-sparse paired odd-correlation defect, and only ten even center values `K=16,18,...,34`.
- on `O=58,K=16`, the four extreme compression splits `(1,15),(3,13),(13,3),(15,1)` and the six maximum-overlap subbranches of `(5,11),(7,9)` (and their swapped necessary-Q counterparts) are exactly excluded by periodic-cross + negacyclic fibre-Q checks (runs `41719753889`, `41851120769`); lower-overlap central cases remain;
- on `O=58,K=34`, both zero-fibre splits `(25,9)` and `(9,25)` are exactly excluded by the independent 4,113-support-orbit periodic spectral census (run `41853593511`), which proves `SG>=72` and hence `E>=670` in those two splits.
- on `O=58,K=34`, the two-sparse fibre splits `(23,11)` and `(11,23)` are also exactly closed: 240 normalized negacyclic systems leave 1,912 low-SH fibres, and an exhaustive support-constrained periodic join of 952 groups finds `Qpass=0` (clean run `41855726843`); only the five central K34 splits remain.
- **New support-defect formulation:** with overlap T and uncovered sites Z, set F=T union Z. Modulo 2 the periodic cross equation becomes `P F*+F P*=target`, and `|F|=25-K+2|T|`. Small F replaces huge raw compressed support scans.
- on `O=58,K=24`, balanced disjoint compression splits `(11,13)` and `(13,11)` at `t=0` are strictly excluded by exact reflection-support and negacyclic fibre-Q checks (clean run `42022471825`);
- on `O=58,K=26`, balanced `(13,13)` at `t=1` is strictly excluded by the same one-site support-defect kernel (clean run `42023022631`);
- on `O=58,K=28`, balanced `(13,15)` and swapped `(15,13)` at `t=3` are strictly excluded after 34 QHITs and all **66,000** induced binary affine-lift scorings (clean run `42025382319`; smallest full E=1310, smallest odd energy O=154). Other K28 overlaps/splits remain open.

The latest complete records are:

- [`results/2026-11-05-o58-k28-triple-overlap-allaffine.md`](results/2026-11-05-o58-k28-triple-overlap-allaffine.md)
- [`results/2026-11-05-o58-central-nearfull-k24-k26.md`](results/2026-11-05-o58-central-nearfull-k24-k26.md)
- [`results/2026-11-04-o58-k16-central-highoverlap-exclusion.md`](results/2026-11-04-o58-k16-central-highoverlap-exclusion.md)
- [`results/2026-11-04-o58-k34-two-sparse-fibre-closure.md`](results/2026-11-04-o58-k34-two-sparse-fibre-closure.md)
- [`results/2026-11-04-o58-k34-extreme-periodic-exclusion.md`](results/2026-11-04-o58-k34-extreme-periodic-exclusion.md)
- [`results/2026-11-04-o58-k16-extreme-splits-exact.md`](results/2026-11-04-o58-k16-extreme-splits-exact.md)
- [`results/2026-11-01-h18-k23-complete-exclusion.md`](results/2026-11-01-h18-k23-complete-exclusion.md)
- [`results/2026-11-01-odd-energy-defect-projection.md`](results/2026-11-01-odd-energy-defect-projection.md)
- [`results/2026-10-31-h18-k21-complete-exclusion.md`](results/2026-10-31-h18-k21-complete-exclusion.md)
- [`results/2026-10-31-h18-k19-complete-exclusion.md`](results/2026-10-31-h18-k19-complete-exclusion.md)
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

Write

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

On the odd-perfect layer the cyclic cross equation splits exactly into

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

The simultaneous `AGL(1,Z_25)` action on the two fibre supports is quotiented exactly before sign enumeration; final survivors are reconstructed to binary length-100 sequences and rescored in the original LABS objective. A compressed orbit representative alone is never treated as sufficient for aperiodic claims.

### `(18,0), K=19`

All six splits

```text
(19,0),(17,2),(15,4),(13,6),(11,8),(9,10)
```

are exactly empty through `E<=570`.

Record: [`results/2026-10-31-h18-k19-complete-exclusion.md`](results/2026-10-31-h18-k19-complete-exclusion.md).

### `(18,0), K=21`

Here

```text
m=-4,
W=16+2(Q+R),
E<=570 iff Q+R<=57.
```

All seven possible norm splits are exactly empty. Every Q-level survivor was expanded through matching compressed affine images, both required fibre signs, and all induced full-length affine transforms.

Record: [`results/2026-10-31-h18-k21-complete-exclusion.md`](results/2026-10-31-h18-k21-complete-exclusion.md).

### `(18,0), K=23`

Here

```text
m=-2,
W=4+2(Q+R),
E<=570 iff Q+R<=63,
SG+SH<=126.
```

All eight norm splits

```text
(23,0),(21,2),(19,4),(17,6),
(15,8),(13,10),(11,12),(9,14)
```

are exactly empty. The final three lower splits were verified by a support-orbit sharder that first reproduced the frozen `(15,8)` full-witness summary exactly and then performed independent final length-100 rescoring. Across the remaining Q-level survivors, no transform even met the residual `V` budget.

Record: [`results/2026-11-01-h18-k23-complete-exclusion.md`](results/2026-11-01-h18-k23-complete-exclusion.md).

Therefore

```text
odd-perfect (18,0), K in {19,21,23}, E<=570: impossible,
```

and the surviving odd-perfect frontier on this line is `K>=25`.

## First non-odd-perfect layer: `O=58`

Let

```text
D_r=C_(2r+1), r=0,...,49,
z_r=(D_r+D_(49-r))/4, r=0,...,24.
```

For every length-100 binary sequence, `z_r` is integral and

```text
O = sum_r D_r^2 >= 50 + 8 ||z||_2^2,
ab = 4 sum_r z_r.
```

Moreover `O-(50+8||z||^2)` is a nonnegative multiple of 16. Hence the first non-odd-perfect layer `O=58` forces

```text
||z||^2=1,
ab=+/-4.
```

Because the length-50 half sums are even, the only absolute half-sum class is `(2,2)`. Energy-preserving sign symmetries normalize this to

```text
(a,b)=(2,2),
z = one positive unit vector.
```

In the same order-25 decomposition the independent periodic/negacyclic cross coefficients become

```text
P_0=2 z_12,
M_0=0,
P_s=z_(12+s)+z_(12-s),
M_s=z_(12+s)-z_(12-s),  s=1,...,12.
```

Thus `O=58` is a one-sparse coupled cross-defect problem, not a generic relaxation of odd-perfectness.

The even-energy target gives

```text
W<=129,
K in {16,18,20,22,24,26,28,30,32,34}.
```

Exact per-center budgets `sum(U^2+V^2)<=B_K` are

```text
K:    16 18 20 22 24 26 28 30 32 34
B_K:  24 40 52 60 64 64 60 52 40 24
```

The existing `qmin(G)` and `SG+SH` even-energy machinery remains applicable; the new search must use the sparse nonzero cross right-hand sides above.

Derivation and sign/index audit: [`results/2026-11-01-odd-energy-defect-projection.md`](results/2026-11-01-odd-energy-defect-projection.md).

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

So any surviving odd-perfect breakthrough has `d>=6`. This hierarchy should not be extended mechanically; the compression/factorization route is stronger.

## Other exact / high-value evidence

- Ordinary Hamming radii **1 through 7** around the incumbent are completely exhausted: `17,278,988,695` non-center sequences, no improvement. See [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).
- Exact boundary+skew-core target searches exclude broad structured classes; see [`results/2026-10-28-skewcore-hierarchy.md`](results/2026-10-28-skewcore-hierarchy.md).
- Pairwise crossover among near-skew elites and parity-block descent were strongly negative; the exact near-skew proof supersedes those heuristics as a target route.
- Neighboring-length transfer and the tested Golay-52 deletion family were weak; see [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) and [`results/2026-10-28-golay52-deletion.md`](results/2026-10-28-golay52-deletion.md).

## Dead ends / constraints learned

- Do not spend further compute inside near-skew to beat 578; it is rigorously impossible.
- Do not repeat small ordinary incumbent edits; radius 7 is exact and strongly negative.
- Do not treat CP-SAT `UNKNOWN`, timeouts, SIGKILL, or unfinished Actions as exclusions.
- Do not mechanically extend the endpoint-defect hierarchy.
- Generic full-sequence and order-25 CP-SAT repeatedly timed out. Exact progress came from changing representation: GF(2) support kernels, modular sign solving, periodic/negacyclic splitting, `qmin`, affine support quotients, and final all-affine witness rescoring.
- For `kc>0`, fixing the compressed sign of `c` means `gamma -> -gamma` cannot be quotiented; both orientations must be scored.
- Three consecutive `(18,0)` center layers are now excluded with no candidate-quality improvement. Further K-layer scaling should be compared against the qualitatively different `O=58` defect family rather than treated as the default objective.

## Next steps

**Conditional boundary construction gate:** Candidate progress is now bottlenecked on choosing unknown outer variables jointly with interior compensatory changes, not on improving a known core. The tested two-end beam, fixed-mask swaps, and blind outer mutation are not yet reliable candidate generators; see [the 2026-11-08 positive controls](results/2026-11-08-conditional-core-positive-controls.md). Require held-out boundary-free positive recovery before extending N100 compute.

**2026-11-08 constructive gate:** the matched-work 8-spin LNS and source-movable insertion families failed to establish transferable gains even on known-answer N59→60 and N40/60 controls. Do not scale these unchanged. Coordinate any signed-correlation-cut construction with the independent [AI4S LABS search topic](../labs-ai4s-search/README.md), which has already examined pair-epistasis, native tabu, linkage-tree recombination and whole-solver controls. Seek a novel near-frontier *candidate* under matched total compute and an independent literal energy check before dispatching heavy Actions.

1. **Prioritize simultaneous odd/even target-profile construction rather than larger local moves.** The 2026-11-06 parity-half QUBO probe constructs O58 but has poor even energy; a 47-million-state exact-block pilot and exhaustive single-step segment moves likewise did not improve E578. Formulate coupled target even autocorrelations and odd cross terms jointly and assess full reconstructed E at every stage. See [the constructive QUBO pilot](results/2026-11-06-constructive-parity-qubo-joint-pilot.md) and [segment-bridge result](results/2026-11-06-exact-segment-bridges.md).
2. **Develop a real positive-control benchmark before scaling N100.** Hide independently superior solutions at nearby lengths, compare joint-repair, standard tabu/memetic, and exact-block/segment baselines under equal work; keep the target solution entirely out of the parents and candidate source. A mechanism that recovers withheld quality is a more credible N100 direction than another increasing exclusion.
3. **Use O58/O66 compressed solvers as structural oracles, not as the default objective.** Include the missing odd-pair residual conditions before all-affine lifts. Promote any candidate only after complete binary reconstruction and original 99-lag scoring; negative partial-branch results do not imply global optimality.
4. Re-check the live Few Shots record before claiming any advance. A candidate with E<=574 requires independent LABS verification, Few Shots verifier, certificate/SHOT preparation and submission.

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
- Lau & Gangat, small-subsystem LABS heuristic scaling (2026): <https://arxiv.org/abs/2610.14361>
- Wang & Zhu, base/normal/near-normal sequences (2025/2026): <https://arxiv.org/abs/2506.20296>

## Work log

- **2026-11-08 (conditional core):** 3×40 matched hidden-recovery tests on N60 E218/N100 E578/E606 demonstrated 54/118/115 successful core-only recoveries versus no matched unrestricted tabu recoveries. A prospective unknown-boundary test across 50–80 free-core sites (1,840 independent repair runs, 1.3696b candidate scores) did not produce E<=650. The two-ended partial-correlation beam and signed-correlation linear relaxation were also negative; code and audits are in [2026-11-08 study](results/2026-11-08-conditional-core-positive-controls.md). No new record.

- **2026-11-08 (constructive controls/insertion):** Matched proposal-count N40/60/80/100 tabu/exact-block/lag-graph/synergy pilots did not show reliable cross-length quality advantages. Tried all 32,360,000 source-radius≤3 mobile-insertion evaluations from verified N99 E553, all 54,615,120 source-radius-4 insertions from N59 E205, N98 dual insertion and 1-source-flip refinement, all N99 rotations/alternations and 32,663,400 E578/E606 two-parent interval stitches; no N100 E<606 candidate. Added exact reconstructable C++ generators and [negative/positive-control evidence](results/2026-11-08-constructive-controls-insertion-stitch.md); no shot.

- **2026-11-06 (nonlocal repair):** Enumerated 9,900 signed interval reversals and 666,600 signed adjacent-block swaps of the E578 incumbent; only six distinct, trivial-equivalent E578 states and best nontrivial E686. Expanded 17 diverse E<=950 intermediate states with 11,500,500 second-step operations; best nontrivial still E686. Tested 47,183,040 exact 14-bit block assignments, nonlocal O66 repair (8 valid O66 seeds; min E1318), 4,000 affine decimations and 10,200 aligned parity-block exchanges, all without a new record. [Details and source](results/2026-11-06-exact-segment-bridges.md).

- **2026-11-06:** Re-checked live Few Shots board (still 578); found exact conditional half-QUBO identity for odd aperiodic correlations and implemented alternating constructive search. In 100 seeded runs ×18 rounds, sampled 59 O58 states, best full E at O58 was 5718. Paired joint even/odd search with two schedules gave best E1030 (independent integer rescoring confirmed). Fixed-A odd-perfect swaps at the incumbent stayed within known near-skew freedom. Saved code and [full record](results/2026-11-06-constructive-parity-qubo-joint-pilot.md). No new record.

- **2026-10-27:** Reproduced the baseline; added independent scoring/search kernels; exhausted incumbent Hamming radii through 6; surveyed solver literature and neighboring-length records.
- **2026-10-28:** Exhausted radius 7; calibrated odd-perfect search; built exact skew-core and target-arithmetic decompositions; exhausted large near-skew local/crossover/block neighborhoods.
- **2026-10-29:** Proved exact N100 near-skew optimum 578; excluded endpoint defects 1 through 5; derived the global parity-polynomial factorization and norm identity; developed the order-25 compression program and closed W127.
- **2026-10-30:** Repaired affine-fibre coverage rigor; exactly closed the remaining low11 W129/W131 branches; derived and regression-tested the periodic/negacyclic fibre split; began the `(18,0)` center-layer program.
- **2026-10-31:** Completely excluded `(18,0)` `K=19` and `K=21` through `E<=570`, including direct final rescoring of all Q-level fibre survivors; generalized the compressed solver and moved to `K=23`.
- **2026-11-05:** Derived the global small support-defect identity F=T union Z and exhausted three balanced central minimal-overlap families with independent Actions: K24/t0, K26/t1 and K28/t3. K28 needed a complete 34-QHIT, 66,000 full binary affine-witness audit (none even reaches odd energy 58). Opened candidate-oriented F3 K24/t1 run 42026399358 and reassessed the next mechanism as early odd-pair residual constraints. No record candidate.
- **2026-11-04:** In the first non-odd-perfect O58 layer, closed four K16 extreme norm splits by uncapped compressed/fibre Q enumeration and four K34 edge norm splits by two independent exact pipelines: a 4,113-support-orbit periodic spectrum proof and a 240-system ternary-fibre plus 952-support-group periodic join. Clean Actions runs 41719753889, 41853593511 and 41855726843 verify the frozen counts. K16 central high-overlap Action subsequently finished with six more strict Q exclusions; best unrestricted E remains 578.
- **2026-11-01:** Exactly closed the full `(18,0),K=23` layer, including independent sharded final witness rescoring of all lower-split Q survivors. Reassessed the search space and derived the first non-odd-perfect layer `O=58` as a one-sparse coupled periodic/negacyclic defect problem with canonical half sums `(2,2)`.
