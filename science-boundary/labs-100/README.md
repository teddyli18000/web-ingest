# LABS length 100

## Question

Can we find a binary sequence of length 100 with LABS energy below the public best-known value `578`?

For signs `s_i in {-1,+1}`,

```text
C_k = sum_i s_i s_{i+k},
E = sum_{k=1}^{99} C_k^2.
```

Length-100 energies are `2 (mod 4)`, so the first nominal improvement is `574`, followed by `570, 566, ...`.

Few Shots problem: `few-shots/few-shots`, `problems/p006-labs-100`.

## Current state

**Active; no unrestricted breakthrough yet. Current best verified energy remains 578.**

Public incumbent:

```text
++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-
```

The strongest exact progress is now on the minimum odd-energy (`odd-perfect`) layer. The sharp `(20,0), W=127` corner has been reduced to an order-25 ternary projection with eight support splits; the four high-support splits `ka=18,20,22,24` are now exactly excluded, leaving only `ka=10,12,14,16` in that branch.

### Exact near-skew result

The entire standard N=100 near-skew manifold has exact minimum energy `578`.

For canonical near-skew `s`, deleting one endpoint gives a skew-symmetric length-99 sequence `t`, while appending the matching endpoint gives a skew-symmetric length-101 sequence `u`. Exact correlation algebra gives

```text
E99(t) + E101(u) = 2 E100(s) - 1.
```

Packebusch-Mertens exhaustively proved the skew-symmetric optima through N=119; `E_skew(99)=577` and `E_skew(101)=578`. Hence `E100(s)>=578`, and the public incumbent attains equality.

Proof: [`results/2026-10-29-nearskew-optimum-proof.md`](results/2026-10-29-nearskew-optimum-proof.md).

### Exact odd-perfect endpoint exclusions

Every odd-lag correlation of a length-100 sequence is odd. The minimum possible odd-lag energy is therefore 50. Call a sequence **odd-perfect** when every odd `|C_k|=1`.

For the two length-99 endpoint deletions, let `d_L,d_R` be the number of nonzero odd deletion correlations, and define the invariant endpoint defect

```text
d = min(d_L,d_R).
```

The current exact picture for an odd-perfect `E<=574` candidate is

```text
d=0   near-skew manifold: exact minimum E=578
d=1   no E<=574
d=2   no E<=574
d=3   no E<=574
d=4   no E<=574
d=5   no E<=574
```

Thus any surviving odd-perfect breakthrough must satisfy

```text
d >= 6.
```

Durable endpoint records:

- [`results/2026-10-29-endpoint-support-reflection-inversion.md`](results/2026-10-29-endpoint-support-reflection-inversion.md)
- [`results/2026-10-29-endpoint-support-linearization.md`](results/2026-10-29-endpoint-support-linearization.md)
- [`results/2026-10-29-endpoint-support-path.md`](results/2026-10-29-endpoint-support-path.md)
- [`results/2026-10-29-endpoint-defect-class-coverage.md`](results/2026-10-29-endpoint-defect-class-coverage.md)
- [`results/2026-10-29-endpoint-defect2-modular-exhaustion.md`](results/2026-10-29-endpoint-defect2-modular-exhaustion.md)
- [`results/2026-10-29-endpoint-defect3-modular-exhaustion.md`](results/2026-10-29-endpoint-defect3-modular-exhaustion.md)
- [`results/2026-10-29-endpoint-defect4-modular-exhaustion.md`](results/2026-10-29-endpoint-defect4-modular-exhaustion.md)
- [`results/2026-10-29-endpoint-defect5-mod4-exhaustion.md`](results/2026-10-29-endpoint-defect5-mod4-exhaustion.md)

The final defect-5 computation covers all `C(49,5)=1,906,884` supports. A new mod-4/GF(2) representation reduced the old `666,348,057` anchor-system formulation to `4,498,643,306` affine assignments, of which `1,190,683,248` satisfy every original integer odd-perfect equation exactly. No target had even energy `<=520`.

Implementation: [`code/oddperfect_endpoint_mod4.cpp`](code/oddperfect_endpoint_mod4.cpp).

## Global odd-perfect polynomial reformulation

The endpoint hierarchy is useful evidence, but it should not be extended mechanically. A more global representation has now been derived.

Split the sequence into parity halves and form Littlewood polynomials

```text
A(x) = sum_{i=0}^{49} s_{2i} x^i,
B(x) = sum_{i=0}^{49} s_{2i+1} x^i.
```

Let `A^R(x)=x^49 A(x^-1)` and similarly for `B`. Odd-perfectness is equivalent to the exact cross factorization

```text
A B^R + x B A^R = (x^50 - 1) Q,                 (1)
```

where `Q` is a length-50 Littlewood polynomial satisfying

```text
Q_j = -Q_{49-j}.
```

So `Q` has only 25 independent signs.

Define

```text
D(x) = A(x)^2 - x B(x)^2.
```

A Lagrange identity plus Parseval gives the exact objective identity on the odd-perfect layer

```text
||D||_2^2 = 9900 + 2 V,
V = sum_{r=1}^{49} C_{2r}^2.
```

Therefore

```text
E<=574  <=>  ||D||_2^2 <= 10948,
E<=570  <=>  ||D||_2^2 <= 10940.
```

The E578 incumbent has `||D||_2^2=10956`, only 8 above the nominal E574 threshold.

Moreover every coefficient `d_n` of `D` lies in a fixed residue lattice:

```text
d_n == +1 (mod 4),   n=0,...,49,
d_n == -1 (mod 4),   n=50,...,99,
```

and

```text
D(x^2) = S(x) S(-x)
```

for the original length-100 Littlewood polynomial `S`.

Full derivation: [`results/2026-10-29-oddperfect-polynomial-factorization.md`](results/2026-10-29-oddperfect-polynomial-factorization.md).

This factorization/norm-gap formulation is now the preferred first-principles route to the whole odd-perfect layer.

### Sharp `(20,0), W=127` order-25 branch

For half sums `(20,0)`, integer convexity gives `W>=127`. At equality the even-correlation multiset is forced, and the parity halves form an NGP50 subject to the additional odd-perfect cross condition. Compressing opposite positions gives ternary length-25 sequences `p,c` with

```text
sum p = 10,
sum c = 0,
||p||^2+||c||^2 = 26,
p c* + c p* = 0  in Z[x]/(x^25-1),
PAF_p(r)+PAF_c(r) in {2,3,4},
sum_{r=1}^{12}[PAF_p(r)+PAF_c(r)] = 37.
```

Writing `ka=||p||^2`, the only possible splits are

```text
ka = 10,12,14,16,18,20,22,24.
```

Exact non-CP-SAT computations now give

```text
ka=18  impossible
ka=20  impossible
ka=22  impossible
ka=24  impossible
```

so W127 survives only at

```text
ka = 10,12,14,16.
```

The `ka=18` computation is the strongest new representation step: for fixed `c`, write `p=1-z-2n`. The cross equation becomes `Mz+2Mn=0`; reducing modulo 2 restricts the 7-zero mask `z` to a small GF(2) kernel before an exact base-17 integer MITM. It exhausts 2,191 support orbits and 75,987 signed `c` orbits, finds 3,675,345 exact cross-compatible pairs, and no W127 target. An independent four-core GitHub Actions reproduction returned the same counts.

Durable records:

- [`results/2026-10-29-h20-ngp50-paley-exclusion.md`](results/2026-10-29-h20-ngp50-paley-exclusion.md)
- [`results/2026-10-29-h20-w127-order10-ngp-projection.md`](results/2026-10-29-h20-w127-order10-ngp-projection.md)
- [`results/2026-10-29-w127-order25-ka24-exclusion.md`](results/2026-10-29-w127-order25-ka24-exclusion.md)
- [`results/2026-10-29-w127-order25-ka20-ka22-exclusion.md`](results/2026-10-29-w127-order25-ka20-ka22-exclusion.md)
- [`results/2026-10-29-w127-order25-ka18-kernel-mitm-exclusion.md`](results/2026-10-29-w127-order25-ka18-kernel-mitm-exclusion.md)

## Target arithmetic

Split by parity:

```text
A_i=s_{2i}, B_i=s_{2i+1},
a=sum A_i, b=sum B_i.
```

Then

```text
C_{2r} = C_A(r)+C_B(r),
sum_{k odd} C_k = ab,
sum_{r=1}^{49} C_{2r} = (a^2+b^2-100)/2.
```

Odd-perfectness plus the opposite-lag congruence forces `ab=0`.

The global product controls energy mod 8:

```text
global product +1 => E == 6 (mod 8),
global product -1 => E == 2 (mod 8).
```

Thus exact E574 and E570 belong to different product classes; never use the E574 product condition to exclude lower energies.

Target-specific records:

- [`results/2026-10-28-exact574-arithmetic.md`](results/2026-10-28-exact574-arithmetic.md)
- [`results/2026-10-28-exact570-structure.md`](results/2026-10-28-exact570-structure.md)

## Other exact / high-value evidence

- Ordinary Hamming radii **1 through 7** around the incumbent are completely exhausted: `17,278,988,695` non-center sequences, no improvement. Radius-6 minimum `978`; radius-7 minimum `974`. See [`results/2026-10-27-incumbent-shells.md`](results/2026-10-27-incumbent-shells.md).
- The calibrated odd-perfect walk repeatedly rediscovers the near-skew E578 basin. Outside every near-skew symmetry orientation, 1,024 starts reproducibly reached the same E1162 orbit, a `3-bit boundary + skew97` structure. See [`results/2026-10-28-oddperfect-outside-nearskew.md`](results/2026-10-28-oddperfect-outside-nearskew.md).
- Exact boundary+skew-core target searches exclude broad structured classes; see [`results/2026-10-28-skewcore-hierarchy.md`](results/2026-10-28-skewcore-hierarchy.md).
- Pairwise crossover among eight near-skew elites exhausted `265,814,016` recombination states with no synergy; parity-block descent exhausted `1,258,291,200` states and stalled far above the record. Historical near-skew evidence is preserved under [`results/`](results/), but the exact near-skew proof supersedes it as a target route.
- Neighboring-length transfer and the tested Golay-52 deletion family are weak: see [`results/2026-10-27-cross-length.md`](results/2026-10-27-cross-length.md) and [`results/2026-10-28-golay52-deletion.md`](results/2026-10-28-golay52-deletion.md).

## Dead ends / constraints learned

- Do not spend further compute inside near-skew to beat 578; it is rigorously impossible.
- Do not repeat small ordinary incumbent edits; radius 7 is exact and strongly negative.
- Do not treat CP-SAT `UNKNOWN`, process timeout, or killed jobs as exclusions.
- The generic order-25 CP-SAT W127 model timed out with `UNKNOWN` in every `ka` shard; the exact high-`ka` exclusions came only after changing representation to orbit/MITM and GF(2)-kernel/MITM.
- Do not scale the old endpoint anchor/RREF formulation to higher defect; defect 5 required a representation change to mod-4 affine linearization.
- Do not mechanically continue defect-by-defect merely because d=0..5 are now closed. Candidate quality has not improved; the global factorization (1) is a better search space.
- The failed d4 `[150000,172000)` SIGKILL run is not evidence; that interval was later fully rerun in four successful subranges, as recorded in the clean d4 transcript.

## Next steps

1. **Close the four remaining W127 order-25 splits `ka=10,12,14,16`.** Prefer a joint representation over four unrelated enumerations. The identity `X=p+c`, `Y=p-c` turns the cross equation into periodic homometry `PAF_X=PAF_Y`; every W127 candidate has `sum X=sum Y=10`, `||X||^2=||Y||^2=26`, and nonzero autocorrelations in `{2,3,4}` with independent-lag sum 37.
2. If the homometric route does not close W127, extend the GF(2)-kernel/MITM only where its kernel/support counts remain demonstrably small; do not return to the timed-out generic CP-SAT model.
3. Then use the already-derived sparse near-NGP classification for W129/W131 rather than restarting from generic LABS search.
4. In parallel, continue attacking the global odd-perfect factorization and the norm threshold `||A^2-xB^2||_2^2 >= 10956`, which would eliminate the whole `O=50` layer at once.
5. Continue higher odd-energy target layers (`O=58`, `O=66`, ...) only with target-specific arithmetic and exact verification; keep E574 and E570 product classes separate.
6. Re-check Few Shots/public record immediately before any claim. If `E<=574` is found, freeze the sequence, independently rescore with `code/verify.py`, verify with the Few Shots verifier, create only `certificate.json` and `SHOT.md`, run `tools/check.py`, then publish under `teddyli18000` as authorized.

## Durable artifacts

- [`code/`](code/) — independent scorer; exact shell scanners; endpoint modular solvers; odd-perfect search kernels; target arithmetic models; skew-core and neighboring-length tools.
- [`results/`](results/) — exact exclusions, proof transcripts, negative searches and structural derivations.
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

- **2026-10-27:** Reproduced the baseline; added independent scoring/search kernels; exhausted incumbent Hamming radii through 6; surveyed current solver literature and neighboring-length records.
- **2026-10-28:** Exhausted incumbent radius 7. Derived/corrected near-skew representation. Calibrated odd-perfect search; found reproducible outside-near-skew E1162 boundary+skew97 basin. Built exact skew-core and target-arithmetic decompositions. Exhausted large near-skew local, crossover and block neighborhoods.
- **2026-10-29:** Proved the exact N100 near-skew optimum 578. Developed reflection-support endpoint linearization and exactly excluded odd-perfect endpoint defects 1 through 5. Defect 5 required a new mod-4/GF(2) affine reformulation and a 1.9-million-support exhaustive search. Derived the global parity-polynomial factorization `A B^R+x B A^R=(x^50-1)Q` and exact norm identity `||A^2-xB^2||^2=9900+2V`. In the sharp `(20,0),W127` branch, reduced to an order-25 ternary projection, exactly excluded `ka=18,20,22,24`, and independently reproduced the `ka=18` GF(2)-kernel/MITM count on a four-core GitHub runner.
