# O=58, K=28, (kp,kc)=(13,15), overlap three: exact all-affine exclusion

Date: 2026-11-05

## Statement

In length-100 LABS with O=58 and normalized half sums (a,b)=(2,2), no E<=574 sequence has order-25 compressed norm split

    (kp,kc)=(13,15) or (15,13)

and overlap size t=3 (the smallest possible overlap because kp+kc=28>25).

The proof does **not** exclude other norm splits or overlap sizes at K28.

## The support-defect reformulation

Write binary support masks P=supp(p), C=supp(c), T=P∩C, Z=Z25\(P∪C), and F=T∪Z. Over GF(2),

    P C* + C P* = P F* + F P*.

For K28 and t3, all 25 positions are covered, Z is empty and F=T has size 3. Because H0=2 sum p_i c_i, an odd overlap cannot give noncenter defect (which requires H0=0). Thus only the **center** defect can occur:

    H0=2, H_r=0 for r=1..12,
    P T* + T P* =0 mod2.

There are C(25,3)=2,300 overlap triples. The full AGL(1,Z25) symmetry partitions them into six complete orbits of sizes

    250, 500, 500, 500, 500, 50.

Choose one triple per orbit and fix its three P bits to 1. The 12 independent GF(2) cross equations are linear in the other 22 P bits. Exhaust every free GF(2) assignment, constrain |P|=13, define C=(J xor P) union T, and independently check all 12 support parity equations. The six representatives have respectively

    462, 311, 324, 311, 324, 462

allowed P masks; **2,194 complete support representatives** remain.

The simultaneous affine action is used only for periodic/fibre necessary tests at this stage. No aperiodic record claim treats an orbit representative as equivalent without all-affine rescoring.

## Exact signed periodic stage

For each support representative sign every p with sum p=1: C(13,6)=1,716 assignments. The overlap has three positions; H0=2 forces two p_i c_i products +1 and one -1, exactly three choices. Once the three overlap c signs are fixed, the remaining 12 c signs solve a 13×12 linear system over GF(3) (12 periodic-cross lags and sum c=1). Enumerate all ternary free variables, recover pivots, require nonzero entries, and independently check every original integer equation.

At K28, m=3 and B_K=60, so E<=574 implies Q+R<=60 and qmin(G)<=60.

Clean full run:

    support representatives     2,194
    signed periodic systems     11,294,712
    modular consistent systems   7,730,197
    exact periodic pairs             3,772
    min SG                            49
    min qmin                          29
    qmin<=60 survivors               53

Code:
- `code/o58_k28_overlap3_supports.py`
- `code/o58_k28_overlap3_compressed_exact.cpp`

## Exact negacyclic fibre-Q stage

The 53 compressed survivors are matched to complementary fibre supports, with both overall fibre signs accounted for. The exact negacyclic cross requirement is M=0 for this centered defect. By

    2Q=SG+SH

the target requires SG+SH<=120.

The exact fibre oracle returns **34** preliminary QHITs among 32 support groups:

    SUMMARY budget=120 groups=32 outer=16384
            half=18570 qpass=34 minSH=27 minmargin=-18

This is a nonempty necessary-filter result. It is not itself a length-100 candidate and cannot be used to claim exclusion.

## Complete all-affine binary witness audit

The independent witness checker `code/o58_k28_overlap3_allaffine_witness.py`:

1. Parses all 53 compressed signed pairs and all 34 QHIT fibre patterns.
2. Expands every compressed pair by the complete 500-element affine group and joins exactly matching pairs of canonical zero-support masks. There are 5 canonical support groups with QHITs.
3. Keeps only the matched signed pairs that actually satisfy SG+SH<=120. This gives 66 pair/fibre combinations, because the Q oracle conservatively used each support group's minimal SG.
4. Reinstates both global fibre signs and applies **all 500 simultaneous cyclic/negacyclic affine transformations** to every matching pair. Periodic transforms act by i↦ai+b (mod25); negacyclic transforms use the odd representative of each multiplier in Z50 so that the required wrap signs are retained.
5. Reconstructs the original binary parity halves from

       A_i=p_i+alpha_i,      A_(i+25)=p_i-alpha_i,
       q_i=c_(i+13 mod25),
       beta_i=gamma_(i+13)   for 0<=i<12,
       beta_i=-gamma_(i-12)  for 12<=i<25,
       B_i=q_i+beta_i,       B_(i+25)=q_i-beta_i,

   and then interleaves A,B into the 100-entry binary sequence.
6. Scores all 99 **aperiodic** correlations in the original LABS objective. The best sequence is independently checked using the literal double sum, not the compressed score.

Frozen summary:

    K28_FULL_AFFINE_AUDIT compressed=53 QHIT=34
    mapped_Q=66 transforms=66000 O58=0 minE=1310 minO=154

The minimum original energy anywhere in these 66,000 images is E=1310, with O=586. The minimum odd energy is O=154, attained by an E=1702 sequence. No image reaches even O=58, let alone E<=574. The minimum odd-energy excess corresponds to six extra odd-correlation defect units, O=58+6*16.

This full expansion is essential: the aperiodic objective is not invariant under the full order-25 affine action, so checking QHIT representatives alone would have been unsound.

## Independent clean reproduction

- Initial exact producer/fibre run **42024146030**, job **127234019421** succeeded and preserved its complete output artifact `labs100-o58-k28-threeoverlap`.
- Final clean run **42025382319**, job **127238169878** completed **success**. It re-executed the complete support, signed periodic, fibre and all-affine stages, checked frozen counts, and independently rescored the best original binary sequence.
- The temporary runner workflow was `.github/workflows/temp-labs100-o58-k28-threeoverlap.yml`.

No E<=574 candidate or unrestricted record was found.

## Mechanistic lesson

The Q-budget relaxation is not enough: 34 QHITs pass, but all 500 affine image orientations retain at least six extra odd defects. A more candidate-oriented successor should couple the anti-paired odd-correlation residual e_r=(D_r-D_(49-r))/2, requiring each |e_r|=1, to support and fibre selection **before** or during the lift. Increasing exact exclusion coverage within fixed K without improving these residuals is unlikely to find an N100 record.
