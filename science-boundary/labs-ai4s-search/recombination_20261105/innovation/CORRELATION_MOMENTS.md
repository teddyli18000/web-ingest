# Exact cross-parent autocorrelation moments: a new representation, not yet a better solver (2026-11-05)

## Why the old per-parent spectrum encoder cannot solve alignment

For LABS sequence s and symmetry generators reversal R, global sign reversal −I, and alternating sign A_i=(-1)^i:

- C_k(Rs)=C_k(s)
- C_k(−s)=C_k(s)
- C_k(As)=(-1)^k C_k(s)

Thus the energy/unsigned power spectrum C_k² is **identical under all eight LABS symmetry actions**, and even the complete signed correlation profile C_k distinguishes **at most two** symmetry subfamilies. If the odd-lag C_k are all zero (as can happen for skew specializations), the signed spectrum cannot distinguish *any* of the eight.

The previous prospective [2070-source-pair alignment study](SYMMETRY_ALIGNMENT.md) finds the signed-C minimizing orientation equals the minimum-Hamming orientation on **8/9** preselected source pairs, showing limited actionable alignment differentiation from signed spectra. Different arm RNG streams mean nonzero observed mean-E differences between such mathematically identical choices are **Monte Carlo noise**, not representation quality.

This does *not* prove a dual neural encoder is useless: it proves **separate per-parent C² branches cannot identify the relative spatial orientation of the parents**, even though the direct joint recombination feasibility changes. Future policies need explicit cross-parent bit/lag products or joint interaction features.

## Exact expected energy of random *joint inheritance + consensus innovation*

Hold source A fixed and choose a symmetry-oriented B. Define D={i:A_i≠B_i}, Q={i:A_i=B_i}. Choose exactly k positions from D and r positions from Q, independently and uniformly, and flip A at the selected positions.

Let X_i be −1 when site i is flipped and +1 otherwise. The recombinant sequence is S_i=A_i X_i and its lag correlation is

\[
C_\ell(S)=\sum_{i=0}^{N-\ell-1} A_i A_{i+\ell} X_i X_{i+\ell}.
\]

Squaring creates pairs of lag edges (i,i+ell) and (j,j+ell). Because X_i²=1, the random sign product contains only vertices that occur an **odd number of times** in the two edges, at most four distinct sites.

For any fixed-size group of n sites where exactly K are flipped uniformly, and any *m distinct* sites in that group,

\[
M_m(n,K) = \mathbb E\left[\prod_{a=1}^{m}X_a\right]
  = \sum_{h=0}^{m} {m\choose h}(-2)^h
    \frac{(K)_{\underline h}}{(n)_{\underline h}},
\]
where the falling factorial at h=0 equals 1. For a pair of lag edges, partition its odd-degree vertex set U into U∩D and U∩Q. By independence of the two fixed-cardinality group samples,

\[
\mathbb E\left[\prod_{u\in U} X_u\right]
 = M_{|U\cap D|}(|D|,k)\,
   M_{|U\cap Q|}(|Q|,r).
\]

Consequently, the **exact unconditional expected raw LABS E** of a specified two-parent mask distribution is

\[
\mathbb E[E(S)]
 =\sum_{\ell=1}^{N-1}\sum_{i,j=0}^{N-\ell-1}
 A_i A_{i+\ell} A_j A_{j+\ell}
 M_{|U_{i,j,\ell}\cap D|}(|D|,k)
 M_{|U_{i,j,\ell}\cap Q|}(|Q|,r).
\]

This is an exact O(N³) *classical analytic feature* of **joint parent structure**, with no neural training and no Monte Carlo. It is more informative than either parent's own C_k² because D/Q depends on the relative source alignment.

## Independent check and source-corpus results

The [standalone executable math derivation/selftest](expected_raw_recombination.py) includes two short instances whose mask distributions can be exhaustively enumerated. An independent JavaScript implementation also brute-force-checked two instances (30 and 36 masks): analytic expectations 24.8 and 47.2222222222 equal direct averaged integer LABS E within 1e−13.

For the **nine frozen elite source pairs**, all eight B orientations were scored analytically with identical physical proposal Hamming distance k+r. [Exact expected values for all eight orientations](results/expected_raw_alignment_v1.json):

| Source pair | N | Min-Hamming orientation: expected raw E | Best-expectation orientation: expected raw E | Expected gain | Different orientation? |
| --- | ---: | ---: | ---: | ---: | --- |
|c60_1-c60_4|60|1690.81|1690.81|0|No|
|c60_0-c60_3|60|1746.03|1727.43|18.59|Yes|
|c60_2-c60_5|60|1758.45|1733.35|25.10|Yes|
|c59_0-c59_2|59|1674.64|1674.64|~0|Numerical tie|
|c46_0-c46_1|46|940.05|940.05|0|No|
|c47_0-c47_2|47|1022.58|1022.58|0|No|
|c50_0-c50_1|50|1231.39|1225.12|6.26|Yes|
|c92_0-c92_1|92|3905.96|3905.96|0|No|
|c99_0-c99_1|99|4580.41|4544.75|35.66|Yes|

The 0.000000000000454 numerical tie at N59 is floating-point summation, **not an exact structural gain**. At N99, all signed individual B correlation profiles are invariant under all eight relevant representations (see source corpus), yet expected *recombinant* E varies by about 35.7 energy units. That demonstrates structural information exists in **cross-parent spatial correlations** which is absent from separate per-parent autocorrelation spectra.

**Critical limit:** the predicted raw offspring energies are often 5–8 times the sources' elite energies. Improving an expectation by 0.8–1.4% of the large raw damage is **not** proof of a meaningful improvement in postrepair elite-generation rate. The 2070-run prospective alignment panel directly found no consistent near-elite advantage. This new exact joint-parent feature is a *possible input to a future constructive, repair-aware* policy, not a neural model license or a solver improvement.

## Go/no-go for future learning

Do not predict raw E from C² with a large transformer: this exact formula already gives that answer deterministically. To justify neural models, a conditional policy must predict or generate **postrepair source-new basin entries**, outperforming this analytical joint score, true-E masked optimization, classical full GOMEA, and same-compute strong original memetic Tabu on distinct elite source families. The proper future object is the interaction among relative symmetry orientation, donor/consensus cut, and **stateful repair dynamics**.

Sources: 2009 LABS memetic recombination; 2024 fitness-based gray-box GOMEA linkage; 2026 GOMEA linkage learning from static templates. No claim of priority or first publication is made without separate novelty review.
