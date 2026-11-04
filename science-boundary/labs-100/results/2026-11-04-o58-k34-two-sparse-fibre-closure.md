# O=58, K=34: exact closure of both two-sparse-fibre norm splits

Date: 2026-11-04

## Claim and scope

For length-100 binary LABS in the first non-odd-perfect layer O=58, normalized to parity-half sums (a,b)=(2,2), the entire order-25 norm splits

    (kp,kc)=(23,11) and (11,23)

have no E<=574 sequence.

Combined with the previously completed (25,9)/(9,25) exact exclusion, **four of nine** possible K34 norm splits are now closed; the unsearched middle five remain. No unrestricted record is claimed.

## Exact identities and budget

With K=||p||²+||c||²=34, m=K-25=9 and

    E=382+8(Q+R),        Q=sum U_r², R=sum V_r²>=0,
    2Q=SG+SH,
    SG=sum_{r=1}^{12} (PAF_p(r)+PAF_c(r))²,
    SH=sum_{r=1}^{12} (NPAF_alpha(r)+NPAF_gamma(r))²,

the target requires

    SG+SH<=48.

Also sum p=sum c=1 and K=34 imply sum_{r=1}^{12} G_r=-16, G_r integer, so by exact integer convexity

    SG>=4*2²+8*1²=24.

At (kp,kc)=(23,11), the complementary fibre supports have norms (||alpha||²,||gamma||²)=(2,14). The reversed norm split is covered by swapping p,c and alpha,gamma. This preserves SG and SH, preserves the symmetric periodic cross equation, and reverses only the negacyclic commutator sign; both orientations of the O58 noncenter defect are explicitly enumerated.

## Exhaustive two-sparse fibre census

The order-25 negacyclic commutator is

    alpha gamma* - gamma alpha* = M modulo x^25+1.

Every alpha with two nonzero coordinates can be transformed by a common negacyclic shift (applied to both alpha and gamma, preserving M and SH) and common global sign into

    alpha=1+epsilon*x^d,     d=1,...,24, epsilon in {-1,1}.

The O58 one-sparse defect has three cyclic-location classes: center M=0, unit (gcd(s,25)=1), and five (gcd(s,25)=5). An odd-power negacyclic ring automorphism x->x^a with gcd(a,25)=1 maps noncenter positions to s=1 or s=5; both signs of the resulting M_s=M_(25-s)=+/-1 are retained. Hence the complete normalized families consist of 48 center cases and 192 noncenter cases, **240 exact systems** total.

For fixed alpha and RHS, the commutator is an integer-linear map in 25 ternary variables gamma_j in {-1,0,+1}. Its GF(3) reduction is exact as an enumeration interface: every ternary assignment corresponds to a unique GF(3) vector; enumerate all 3^d free-coordinate assignments after RREF, recover the pivot variables, and then check the original 25 integer commutator coefficients exactly. Require ||gamma||²=14 and compute SH from its exact negacyclic PAF. Thus there is no SAT/CP timeout or sign-solution omission.

Durable code:

    code/o58_k34_fibre2_exact.cpp

The 240 systems yield:

| Defect | normalized cases | exact commutator solutions, weight 14 | SH<=24 fibre hits | minimum SH |
|---|---:|---:|---:|---:|
| center | 48 | 4,973,888 | 0 | 26 |
| unit, orientation - | 48 | 875,520 | 336 | 6 |
| unit, orientation + | 48 | 875,520 | 336 | 6 |
| five, orientation - | 48 | 1,145,680 | 620 | 16 |
| five, orientation + | 48 | 1,145,680 | 620 | 16 |
| **total** | **240** | **9,016,288** | **1,912** | — |

Center is immediately excluded: SG>=24 and SH>=26 imply SG+SH>=50>48.

The 1,912 noncenter low-SH fibres collapse, without loss for a necessary-Q exclusion, to **952 groups** keyed by (d,epsilon,s,support(gamma)), retaining the minimum SH in each group. Exact fibre signs are not discarded when claiming existence: taking the minimum across all signs is a conservative relaxation for exclusion.

## Exact periodic join for noncenter defects

For each of these 952 groups, the compressed supports are fully determined:

    support(p)=complement(support(alpha)),  |support(p)|=23,
    support(c)=complement(support(gamma)),  |support(c)|=11.

Enumerate every signed c with sum c=1: choose five negative among the 11 nonzero positions (C(11,5)=462). For each c solve the 13 independent integer periodic-cross equations plus sum p=1 via exact GF(3) RREF, enumerate all +1/-1 free assignments, recover pivots, and check the complete original integer equations and sums. The one-sparse noncenter periodic RHS is P_s=P_(25-s)=1. Score each exact p,c pair's SG.

Because the lower-bound test uses the minimum SH over *all* fibre signs sharing that support, any actual full candidate would satisfy SG+minSH<=48 and be detected. No such support/periodic pair exists.

Durable code:

    code/o58_k34_fibre2_join.cpp

Frozen exact summary:

    K34_FIBRE2_JOIN hits=1912 groups=952
    c_signs=439824 systems=433168
    periodic=20416 minSG=88 min_margin=60 Qpass=0

The closest necessary-budget margin is +60 in SG+minSH-48. In particular, none of the 20,416 periodic solutions shares a complement support with a low-SH fibre capable of meeting the energy target.

## Clean independent Actions verification

The local 4-thread execution first generated one file per normalized case (avoiding interleaved stdout), concatenated the 240 complete logs, and fed them to the join solver.

A separate clean GitHub Actions run did the same without using local binaries:

- run **41855726843**, job **126663702203**, status **success**;
- artifact `labs100-o58-k34-fibre2-join`;
- temporary workflow `.github/workflows/temp-labs100-o58-k34-fibre2-join.yml`;
- exhaustive producer asserted 240 summaries, 1,912 HIT rows, 48 center cases, center minSH=26, and 0 center SH<=24 survivors;
- join asserted the exact frozen 952/439824/433168/20416/88/60/0 summary above.

The complete emitter deliberately has **no 10,000-candidate truncation cap**; every low-SH fibre is represented in the exact join artifact.

## Proof boundary / future work

This closes the K34 two-sparse corner in both component orientations. The remaining K34 splits are

    (21,13),(19,15),(17,17),(15,19),(13,21).

The solver architecture generalizes to 4-sparse fibres, but scaling the same enumeration is not automatically an efficient path to a record. Before extending it, compare the sizes of exact low-SH survivor classes with the unrelated O58/K16 central-split campaign and reassess whether the frontier should instead target central K24/26 for better candidate quality.

Current verified unrestricted best is still E=578.
