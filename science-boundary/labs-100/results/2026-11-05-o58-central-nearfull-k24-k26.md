# O=58: two exact central minimal-defect exclusions at K24 and K26

Date: 2026-11-05

## Scope and criterion

The full N=100 LABS energy target is E<=574. In the O=58 layer normalize the parity-half sums to (2,2). At K24 (m=-1) and K26 (m=+1) the exact even-energy budget is Q+R<=64, with Q=sum U_r^2 and R=sum V_r^2>=0. The coupled periodic-compression and negacyclic-fibre spectra obey

    2Q=SG+SH,

so every target candidate must satisfy SG+SH<=128.

This document proves only the two named balanced, near-full support cases; it does **not** close every K24 or K26 norm/overlap class.

## A unified GF(2) support identity

Let P=supp(p) and C=supp(c) be masks over the cyclic group Z25. Let

    T=P intersect C (overlap),
    Z=Z25 minus (P union C) (holes),
    F=T union Z.

Since the compression coefficients are in {-1,0,+1}, reduction of the periodic cross equation modulo 2 uses only masks. We have C=P xor J xor F, where J is the all-ones mask. Therefore

    H=P C* + C P* = P F* + F P*      (mod 2),

because P J*+J P*=0 over GF(2). The size of this **support-defect set** is

    |F|=25-K+2|T|.

The old interface directly enumerated a P/C support pair. The new interface first chooses a small F and solves a linear GF(2) correlation equation for P.

### K24, disjoint supports

Set (kp,kc)=(11,13), overlap t=0. Then |Z|=1 and |F|=1. A common translation places the unique hole at 0. Center defect P0=2 is impossible because H0=2 sum p_i c_i=0. For either noncenter defect, an order-25 unit multiplier normalizes its symmetric lag pair to s=1 (unit) or s=5 (five).

The mask identity becomes P+P*=x^s+x^-s. Hence P0=0, P is reflection-symmetric except at the pair ±s, and precisely five of the remaining eleven opposite pairs have both sites in P. There are exactly

    2*C(11,5)=924

possible supports for each of s=1,5. Sign p with sum p=1 (C(11,5)=462 choices), solve the 13 periodic equations and sum c=1 by exact GF(3) RREF and exhaust every free ternary coordinate, then check the complete original integer equation. Retain all compressed pairs with qmin(G)<=64 and test all complementary negacyclic fibre signs against SG+SH<=128.

Clean run **42022471825**, job **127228375620**, outcome **success**; artifact `labs100-o58-k24-disjoint`.

| defect | signed p tests | exact compressed pairs | qmin<=64 | exact fibre support groups | Q passes | min SG+SH-128 |
|---|---:|---:|---:|---:|---:|---:|
| s=1 unit | 426,888 | 4,024 | 132 | 61 | 0 | +34 |
| s=5 five | 426,888 | 5,590 | 260 | 22 | 0 | +30 |

The negacyclic oracle evaluates all admissible fibre signs; no 10,000-HIT cap applies. Swapping p,c preserves SG and SH while reversing the negacyclic commutator sign, which is enumerated both ways. Therefore the (13,11) split at t=0 is also excluded at the necessary-Q level.

Durable code:
- `code/o58_k24_disjoint_compressed_exact.cpp`
- `code/o58_qgroup_budget_exact.cpp`

### K26, minimal overlap

Set (kp,kc)=(13,13), overlap t=1 and no holes. Translate the unique common position to 0. Again F={0}; the centered defect requires H0=2, so p0*c0=+1, whereas the noncenter defect would require 0 and is impossible at odd overlap.

Modulo 2, the center equation is P+P*=0; the 13-site support P must contain 0 and exactly six opposite pairs:

    C(12,6)=924 supports.

For each support, enumerate all C(13,6)=1,716 signed p with sum p=1. Set c0=p0, solve all 12 remaining c signs using exact GF(3) row reduction, check all integer cross equations, and then test qmin<=64 and the full negacyclic fibre-Q oracle.

Clean run **42023022631**, job **127230235084**, outcome **success**; artifact `labs100-o58-k26-oneoverlap`.

    SUPPORTS=924
    SIGNED_P=1,585,584
    MOD3_CONSISTENT=1,102,664
    EXACT_COMPRESSED=4,280
    MIN_SG=108
    MIN_QMIN=60
    QMIN<=64=120

The exact fibre oracle reports:

    SUMMARY budget=128 groups=4 outer=8192 half=16408
            qpass=0 minSH=36 minmargin=16

Thus no target in the (13,13), t=1 centered class exists.

Durable code:
- `code/o58_k26_overlap1_compressed_exact.cpp`
- `code/o58_qgroup_budget_exact.cpp`

## Reproducibility and conclusion

Both actions compile their C++ solvers from a clean checkout on the recorded main commit and assert the actual number of emitted HIT records equals the exact producer summary before passing all hits to the fibre oracle. All subsequent Q failures are strict necessary-condition exclusions. These runs are **not** unrestricted E<=574 exclusions, nor do they claim any new LABS record.

The useful new representation is the small set F=T union Z. It exposes reflection rigidity whenever |F|=1 and generalizes to a fixed, small 3-site GF(2) kernel across K22/24/26/28, allowing a different search organization from fixed-K brute-force support scans.
