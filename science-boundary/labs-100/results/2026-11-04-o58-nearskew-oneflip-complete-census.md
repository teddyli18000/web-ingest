# O=58 near-skew one-bit bridge: exact finite energy census

Date: 2026-11-04

## Claim and scope

Take a length-100 near-skew sequence obtained by prepending one sign to a skew-symmetric length-99 sequence. Normalize the parity-half sums to (a,b)=(2,0). Flip exactly one negative sign in the odd-position parity half B to get (a,b)=(2,2), and require the first non-odd-perfect odd energy O=58. Reversal and whole-half sign symmetries cover equivalent orientations.

**Local exhaustive result: the minimum full LABS energy in this precise family is E=1694 (O=58, even energy=1636).** It does not cover arbitrary O58 sequences, unrestricted non-near-skew sequences, or multi-bit departures.

## Exact reduction to 9352 A cases

Let A_i=s_(2i), B_i=s_(2i+1). The skew99 core forces

    A_i=A_(50-i), for i=1,...,24;
    B_r=-B_(49-r), for r=0,...,49;
    D_r=C_(2r+1)=A_0 B_r.

Fix the flipped B coordinate j with initial B_j=-1. Define

    w_r = [r<=j] A_(j-r) + [r<=48-j] A_(j+r+1),
    D'_r = A_0 B_r + 2 w_r.

Opposite odd correlations then obey

    D'_r + D'_(49-r) = 2(w_r+w_(49-r)).

For (a,b)=(2,2) and O=58, the exact odd-defect projection says exactly one opposite odd-lag pair must sum to +4, all others sum to zero. For each r=0,...,24, w_r+w_(49-r) is the sum of exactly two distinct A coordinates, and the 25 coordinate pairs partition all 50 A positions. Thus all ordinary matched A pairs have opposite signs, and one exceptional pair h is (+1,+1).

Combining those matching constraints with near-skew mirror equality A_i=A_(50-i) yields a finite parity-union-find system. The committed generator exhausts j=0,...,49, h=0,...,24 and every free sign component. The output contains exactly **9352 (j,h,A) cases**.

## Independent B-pair choices

For each (j,h,A), before flipping B_j, let b=B_r and B_(49-r)=-b. The new two odd correlations are

    A_0*b + 2w_r,
    -A_0*b + 2w_(49-r).

For the exceptional pair r=h their squared sum must be 10 (one magnitude 3, one magnitude 1). For every other pair the squared sum is 2. These exact conditions admit zero, one, or two b choices independently for each r; B_j=-1 fixes its containing pair. The consistency-checked 9352 A cases all have at least one admissible B, with free dimension f in 0,...,24. Every resulting full sequence has O=58.

The even autocorrelation identity

    C_(2r) = C_A(r) + C_B(r), r=1,...,49,

turns every B-pair Gray-code toggle into an exact O(50) correlation update. The scanner independently recomputes all 99 correlations whenever a new within-case minimum is reported, verifying odd energy 58 and complete energy.

These counts describe encoded configurations, not necessarily unique sequences; overlapping encodings do not affect exhaustive coverage.

## Frozen local exhaustive summary

| Freedom shard | A cases | Encoded full sequences | Minimum E |
|---|---:|---:|---:|
| f=0..16 | 8980 | 39,720,648 | 1694 |
| f=17..20 | 216 | 105,381,888 | 5310 |
| f=21 | 42 | 88,080,384 | 5390 |
| f=22 | 60 | 251,658,240 | 6270 |
| f=23, j=23 | 1 | 8,388,608 | 34310 |
| f=23, j=24 | 24 | 201,326,592 | 8278 |
| f=23, j=25 | 24 | 201,326,592 | 8278 |
| f=23, j=26 | 1 | 8,388,608 | 34310 |
| f=24 | 4 | 67,108,864 | 14694 |
| **Total** | **9352** | **971,380,424** | **1694** |

Durable generator: code/o58_oneflip_nearskew_cases.py

Durable exact scanner: code/o58_oneflip_even_exact.cpp

Local exhaustions used four/five CPU threads and independent original-correlation assertions. A separate clean GitHub Actions run, 41876572961, was launched to reproduce the nine frozen shard summaries and independently score every shard winner through code/verify.py. Only call this clean-run verified after the run succeeds.

## Next representation: exact conditional A/B repair

This family is structurally too rigid to approach E=578. Do not simply extend one-flip shells.

For any fixed half A (without any near-skew assumption), all 50 odd autocorrelations are **linear in the 50 binary B signs**:

    D_r = sum_{j=0}^{49} B_j [
        (j>=r ? A_(j-r) : 0)
      + (j+r+1<50 ? A_(j+r+1) : 0)
    ].

For a selected exceptional lag t, impose half sum sum B_j=2, the 49 absolute linear inequalities |D_r|<=1 for r!=t, and |D_t|<=3. Since every D_r is odd and the paired projection forces O>=58 whenever a=b=2, these constraints imply O=58 and are an exact integer-linear conditional repair interface.

A local HiGHS MILP probe found, for the E1694 A and fixed exceptional lag, another feasible B at Hamming distance 24 with O58 and E5918. Preliminary trust-region surrogate repair did not improve E1694. This shows the near-skew oneflip subclass is not the whole fixed-A slice, but it is not an improved LABS candidate.

Prefer jointly changing A and B and optimizing even energy within the exact odd-feasible polytope; any search without that coupling has repeatedly generated correct odd projections but poor original even energy.

## References

- results/2026-10-29-nearskew-optimum-proof.md
- results/2026-11-01-odd-energy-defect-projection.md
- code/verify.py
