# O=58, K=34: exact exclusion of both zero-fibre norm splits

Date: 2026-11-04

## Statement

In the length-100 LABS O=58 layer, normalize the parity-half sums to (a,b)=(2,2). Let K=||p||^2+||c||^2=34, hence m=d_25=9. The extreme norm splits are

    (kp,kc)=(25,9) or (9,25).

Both are excluded at E<=574. In fact, any full binary sequence in either split with O=58 obeys E>=670.

This is a **complete** exclusion of these two norm splits, not a statement about the other seven K34 splits.

## Reduction

For O=58, the one-sparse odd-defect projection has periodic and negacyclic requirements

    p c* + c p* = one-sparse periodic RHS,
    alpha gamma* - gamma alpha* = one-sparse negacyclic RHS.

If kp=25, then alpha=0. If kc=25, then gamma=0. Thus the negacyclic commutator is identically zero, and the noncenter defect types (unit and five) are algebraically impossible. Only the centered defect remains, with

    p c* + c p* = 2 delta_0   modulo x^25-1,
    sum p = sum c = 1.

By the exact norm split, p is a full 25-entry binary sequence and c is a 9-sparse ternary sequence in the (25,9) orientation. Swapping p,c preserves this centered periodic equation and its PAF sum-of-squares, covering (9,25) as well.

At K34 the full even target has

    E = 382 + 8(Q+R),
    2Q = SG+SH,
    SG = sum_{r=1}^{12} (PAF_p(r)+PAF_c(r))^2,
    SH = sum_{r=1}^{12} (NPAF_alpha(r)+NPAF_gamma(r))^2 >=0,
    R >=0.

Thus every E<=574 would require SG<=48. We prove a stronger exact minimum SG=72 under the centered periodic equation.

## Exact finite calculation

Durable code:

    science-boundary/labs-100/code/o58_k34_extreme_periodic_exact.cpp

Algorithm:

1. Enumerate all 9-point supports of c in Z/25. The count is C(25,9)=2,042,975. Quotient only the simultaneous 500-element AGL(1,Z25) action, which preserves the centered periodic equation and SG. There are exactly **4,113** support orbits.
2. For each support representative enumerate **all** 126 signed c vectors with sum c=1 (five + and four -), for 4,113*126=518,238 signed tests.
3. For each c solve the 13 independent periodic-cross equations plus sum p=1 using exact GF(3) row reduction, enumerate all +/-1 assignments on the free columns, recover the pivots, reject zero residues, then check all original integer equations, sum p=1, and every entry of p is binary.
4. Score every resulting p,c in the original exact integer periodic correlation definition. Only the spatial support is symmetry-reduced; every sign pattern and every GF3-consistent binary p is enumerated. Any SG<=48 is written in full.

The GF(3) step is exhaustive, not a relaxation used to claim impossibility: every binary solution defines a GF3 solution and occurs among the finite free +/-1 assignments. Exact integer checks are performed afterward.

## Independently reproduced transcript

- Local exhaustive build: 2026-11-04, 4 OpenMP threads, same counts.
- Clean GitHub Actions: run **41853593511**, job **126656101094**, outcome **success**.
- Artifact: `labs100-o58-k34-extreme-periodic`.
- Workflow `.github/workflows/temp-labs100-o58-k34-extreme-periodic.yml`.
- The runner first smoke-tested 15 support orbits and then exhausted all 4,113.

Frozen full summary:

    K34_PERIODIC_EXACT reps_tested=4113 reps_total=4113
    c_sign_tests=518238 systems=512700
    p_exact=115353 minSG=72 SG_le_48=0

A 15-orbit smoke prefix independently prints `c_sign_tests=1890 systems=1866 p_exact=1055 minSG=110 SG_le_48=0`.

Since SG>=72 and SH,R>=0,

    Q+R >= SG/2 >= 36,
    E >= 382+8*36 = 670.

This is a necessary lower bound (not a claim that E=670 is attained).

## Scope and next direction

The result closes the zero-fibre corners of O58/K34. The remaining seven K34 norm splits have two nonzero fibres and require the coupled sparse negacyclic commutator; the K16 central four splits are also being independently enumerated. Do **not** extrapolate the K34 lower bound to those unsearched splits.

Current unrestricted LABS best verified energy remains 578, and no E<=574 candidate has been found.
