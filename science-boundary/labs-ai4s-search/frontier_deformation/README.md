# Frontier-state curation and directed objective deformation — 2026-10-29

## Verdict and hard gate

**Do not train a neural intervention selector yet.** Six independently integer-verified public QOBLIB anchors at N=64/80/92/96/99/100 are real boundary data, but there is only **one public anchor per length** in this collection. A reproducible 12-seed dual-origin local Tabu diagnostic generated 28 extra symmetry-distinct states across those lengths; **none** is within 20% of its length's QOBLIB reference energy (at N100, best new E=810 vs reference E578). Fourteen of these non-anchor states were used for a small controlled direction-versus-placebo trial with no robust advantage. A separate N100 E578 experiment of periodic, directed correlation-lag deformation also found **no E<578**. The only apparent downstream direction signal is relative to a shuffled placebo on an *unavailable, high-energy non-near-skew quench endpoint*: its superiority to ordinary fixed-goal Tabu is not statistically supported.

This is a **data-quality failure for the intended frontier-conditioned learner**, not evidence against all target-deformation methods. We should not silently relabel E≈800–1100 states as near-record LABS100 elites. A published *unrestricted* memetic Tabu solver, not our diagnostic Tabu, is now being used separately for prospective corpus collection; no final result or threshold pass is claimed until its exact checks succeed.

Current source files:
- [anchors.tsv](anchors.tsv) — QOBLIB snapshot, sequences in 0/1 notation and exact recomputed energies;
- [deform.cpp](deform.cpp) — exact one-bit incremental evaluator, trajectory history, lag/parity weight perturbation, local quenching, symmetry tracking, fixed-step control;
- [skew_harvest.cpp](skew_harvest.cpp) — exhaustive restriction-family pair-group radius 1..5 scanner;
- [curate.py](curate.py) — independent integer scorer, canonicalization and near-skew audit;
- [strong_collect.py](strong_collect.py) — actual published unrestricted memetic Tabu corpus collector.

## Curation and structural diversity

Frozen primary sources, independently rescored with \(\sum_{k>0} C_k^2\):

| N | QOBLIB source file | E in snapshot | structural class |
|---:|---|---:|---|
| 64 | labs064.opt.sol | 208 | non-near-skew; known exhaustive optimum |
| 80 | labs080.bst.sol | 352 | non-near-skew |
| 92 | labs092.bst.sol | 498 | non-near-skew |
| 96 | labs096.bst.sol | 520 | non-near-skew |
| 99 | labs099.bst.sol | 577 | skew (odd N); **QOBLIB snapshot, not necessarily 2026 live record** |
| 100 | labs100.bst.sol | 578 | near-skew |

QOBLIB files: https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs/solutions . The officially validated Few Shots N100 E578 equals the source. Treat provenance as **QOBLIB snapshot** and recheck the actual 2026 public best before record statements.

Near-skew classification for even N: deletion of either endpoint produces a length-(N−1) skew-symmetric word; for odd N: the word itself obeys \(s_{m+j}=(-1)^j s_{m-j}\). Reverse, global sign, alternation are canonically identified. **Different search seeds or Hamming perturbations of the *same* anchor do not constitute independent record families.**

Generate corpus:

\`\`\`sh
cd science-boundary/labs-ai4s-search/frontier_deformation
g++ -O3 -std=c++17 deform.cpp -o /tmp/labs_deform
/tmp/labs_deform --selftest
/tmp/labs_deform --harvest anchors.tsv corpus.tsv 12 20000
{ head -n1 corpus.tsv; grep $'\tpublic_anchor\t' corpus.tsv; } > anchors_corpus.tsv
python3 curate.py
\`\`\`

The local producer ran 12 seeded branches from each public anchor and 12 seeded independent random starts per N, each for 20,000 exact single-flip Tabu iterations, retaining canonical-unique solutions with E≤1.55×reference. This deliberately **does not** reproduce published MTS; the strong published MTS collector is a separate source. In the current run there were 34 entries in \`corpus.tsv\`: 6 public anchors plus 28 new distinct orbits. Eight one-/two-paired-near-skew derived states were appended for each of N99 and N100 as labeled perturbation diagnostics, yielding **50 total rows**. Their provenance remains \`near_skew_manifold\`, never \`independent_random_start\`.

| N | reference | best generated (all origins) | generated/reference | near-skew rows in expanded corpus |
|---:|---:|---:|---:|---:|
|64|208|none|n/a|0|
|80|352|528|1.500|0|
|92|498|730|1.466|0|
|96|520|780|1.500|0|
|99|577|813|1.409|9 incl. anchor|
|100|578|810|1.401|9 incl. anchor|

**No generated candidate reaches a proposed E≤1.20×reference near-elite gate**. This is the primary obstacle for user-requested frontier-level data. The current corpus is fit for negative control and debugging, not for learning near-record intervention policies.

## Exact restricted structural barrier at N99 / N100

For each public odd-skew N99 or near-skew N100 source, identify 49 constrained paired spin coordinates about the skew center, and enumerate *all* one-, two-, three-, four- and five-pair flips, retaining the proper skew constraint. Number per length: \(49+1176+18424+211876+1906884 = 2,138,409\). The scorer uses exact correlations; independent selftests check 27,200 one-bit deltas against fresh O(N²) energy recomputation.

Minimum energies at exactly d pair-groups changed:

| d | N99 E min | N100 E min |
|---:|---:|---:|
|1|833|834|
|2|961|994|
|3|1001|1058|
|4|929|962|
|5|865|882|

**These are exact restricted-neighborhood minima only** (under the specified near-skew parametric pair flips), not a global exclusion for N100. Since the initial N100 near-skew is E578 and the entire near-skew N100 manifold has optimum E578 (proved by the independent labs-100 owner), we should not spend record-seeking compute repeatedly reoptimizing within that manifold. The high one-pair barrier also explains why "near-skew children" from a record do not automatically yield additional near-record basins.

Reproduce:
\`\`\`sh
g++ -O3 -std=c++17 skew_harvest.cpp -o /tmp/labs_skew
/tmp/labs_skew /tmp/skew_candidates.tsv anchors.tsv 5 760
\`\`\`
It emits only E≤760 non-center hits (none) and prints exact depth-specific minima.

## Directional deformation hypothesis, pre-experimental status

Instead of predicting the energy formula with a neural network, temporarily alter the **search objective** and then restore the exact LABS objective:

\[
E_\lambda(s;w)=\sum_{k=1}^{N-1}(1+\lambda w_k)\,C_k(s)^2,\qquad w_k\in\{-1,0,+1\}.
\]

The direction is chosen from the correlation-lag pressure \(0.7 C_k^2/(N-k)+0.3\,\overline{C_k^2/(N-k)}_\text{recent}\) and re-evaluated once per 600-iteration epoch. For top/bottom 20% of lags:
0. Original-goal Tabu (no weighting);
1. **Focus:** positive weight for high-stress lags and negative for calm lags;
2. **Permutation placebo:** the same number of \(+\lambda\) and \(-\lambda\) weights assigned at random;
3. **Release:** negative weight for high-stress lags, positive for calm lags;
4. Odd-lag release/even-lag focus (for challenging odd-perfect structure);
5. Reverse odd/even emphasis;
6. Randomized odd/even-sized assignment placebo.

Use \(\lambda=0.65\) (all lag weights remain positive), fixed Tabu tenure 9; the first 300 moves of each 600-step epoch are deformed, the next 300 use the exact original objective. At both transition boundaries, a *counterfactual* exact steepest single-flip quench records the resulting LABS local minimum; the quench is **not fed back into the Tabu trajectory**. This measures whether direction produces better reachable true-objective basins rather than merely better distorted-objective scores. The quench evaluation costs are equal in count, though trajectory-dependent in work. The step-based comparison is **not a wall-time-matched published-solver benchmark**, and neither focused weighting nor parity release is claimed historically novel.

### Public anchors: no improvement

All 6 anchored lengths, 8 independent streams × methods 0–3, 5,000 iterations per run: **zero strictly improved true LABS solutions**. That is consistent with public quality and does not prove optimum except at N64.

From the true N100 E578 anchor, 20 independent RNG streams × seven arms × 6,000 move iterations and 20 exact steepest-descent quench samples per run: **no E<578**, total 140 treatment runs, 2,800 quenched endpoints (not independent starting states). Independent rechecking of the 140 retained best non-near-skew quench sequences confirms both exact energies and one-bit local optimality. Raw unquenched non-near-skew intermediate states as low as E686 should **never** be counted as independent elite basins; they are usually one move from the record and fall back on descent.

| Arm | Mean best quenched non-near-skew E over 20 streams | Best observed E |
|---|---:|---:|
| Original Tabu | 1056.2 | 958 |
| Focus high-stress lags | 1082.6 | 1022 |
| Permuted lag placebo | 1082.2 | 1018 |
| **Release high-stress lags** | **1046.4** | **862** |
| Release odd lags | 1083.8 | 938 |
| Focus odd lags | 1083.0 | 938 |
| Random parity placebo | 1085.2 | 978 |

For release minus lag permutation placebo, lower is better: **−35.8**, paired 95% bootstrap interval **[−69.0,−3.8]** (20 streams, exploratory and uncorrected for seven-arm multiple testing). Against unmodified Tabu, it is **−9.8 [−54.2,+28.4]**, so **no demonstrated gain over a familiar solver**. Even the best return E862 remains far from E578; there is no proof this will transfer to distinct elite N100 states.

### Nonrecord generated states: null / insufficient positives

A frozen subset of 14 canonically distinct nonrecord candidate states (lengths 80/92/96/99/100, 4 repeats each, 4000 moves, arms 0–3) was compared. None of those states is within 20% of reference energy. Out of **56 paired state×repeat contrasts**, mean *actual positive energy gain* from focusing minus shuffled weighting was **−0.43 [−1.29,0.00]**, from releasing minus shuffled was **−0.21 [−1.29,+0.64]**, bootstrap over state×repeat pairs. Most trials never improved, yielding sparse feedback; these intervals ignore same-state repeat correlation and therefore are exploratory, not strict cluster-robust discovery claims.

A larger earlier attempted batch was terminated by execution timeout and produced a **partial file**, which is excluded from inference.

## Scientific interpretation

This first study established **why better boundary data are prerequisite**. Near-record anchors of different lengths are available but mostly only one orbit per size; the attempted 20k-step homemade Tabu yielded zero independently near-record orbits and cannot stand in for the public 2025 GPU memetic search. The apparent effect of selective lag release on quenched non-skew energy is worth one independent confirmatory test **only if** a proper elite corpus exists and a tuned classical comparator is reproduced.

The next step should first run a published source-level solver, validate every sequence by direct energy and symmetry, retain independent lineages, and predeclare a state-quality threshold (suggest relative gap ≤20%, stratified near-skew/non-near-skew). **Do not hide corpus failure by widening the label "elite".** Train/test splits must be by source lineage and length, never randomized symmetry copies or perturbations of the same public parent.

Further direct target deformation should address escaping *specific exact structural restrictions*, not generic weighted lag rearrangements alone. It must beat a tuned historical-memory controller / published memetic Tabu or self-avoiding walk in equal full compute on held-out genuine elite states. If not, stop training and reformulate the search space.

## Public sources and existing boundary evidence

- QOBLIB anchors and reference coordinates: https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs/solutions
- Zhang et al., GPU memetic tabu: https://arxiv.org/abs/2504.00987 (2025; **not reproduced in this preliminary experiment**)
- Pšeničnik et al., Thompson sampling / GPU self-avoiding walk: https://arxiv.org/abs/2607.09688 (2026)
- Bošković et al. archive and original code: https://github.com/borkob/git_labs , \`solvers/lMAts-lRRts/src\`
- Packebusch/Mertens LABS exact enumeration and skew symmetries: https://arxiv.org/abs/1512.02475
- Exact near-skew N100 lower bound and higher-defect research, maintained by the independent owner: https://github.com/teddyli18000/web-ingest/blob/main/science-boundary/labs-100/README.md (read only)
- Official N100 certificate verifier: https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100

## Handoff

- \`anchors.tsv\`, \`deform.cpp\`, \`curate.py\`, \`skew_harvest.cpp\` committed on main in this topic.
- Build: GNU g++14.2, \`g++ -O3 -std=c++17 deform.cpp -o deform && ./deform --selftest\`; 27,200 randomized independent exact-delta checks passed.
- Reconstruct the raw corpus: \`./deform --harvest anchors.tsv corpus.tsv 12 20000\`, then extract its anchor rows into \`anchors_corpus.tsv\` and run \`python3 curate.py\`.
- Run principal record experiment: \`./deform --compare anchors_corpus.tsv record_trial.tsv 20 6000 600 0.65 9 6\` (to select N100 only, filter by column N first; see user's downloadable raw evidence archive).
- Strong published solver source collector: \`strong_collect.py\`, orchestrated in disposable workflow \`.github/workflows/temp-labs-ai4s-strong-harvest.yml\`; confirm workflow result and independently validate the committed output before declaring stronger elite data available. Use GitHub run status, not a promise of background completion.
- SHA256 from validated local source: \`deform.cpp\` original local run \`e72c9bab8a70ced5920ae38d773a64dbc02e9fd8c768533f2d4d68ce5c0a013a\`; the repo copy is semantically equivalent with only comments trimmed and may have a different SHA. Experimental records and raw CSV files are provided as the companion downloadable archive, and the topic contains complete regeneration commands.
- No edits to \`science-boundary/labs-100/\`; no p006 submission or claimed record.

