# Literature and method notes

## Scope

These notes support the length-100 LABS search in this topic. They distinguish public evidence from our own experiments; nothing here by itself is a novelty claim.

## Public baseline and verification

- Few Shots p006 defines the exact objective and ships the public energy-578 sequence: <https://github.com/few-shots/few-shots/tree/main/problems/p006-labs-100>.
- QOBLIB independently lists 578 as the best-known value for `labs100`: <https://github.com/ZIB-AOPT/QOBLIB/tree/main/02-labs>.
- The Few Shots verifier is the final judge for any shot. `code/verify.py` is intentionally much simpler and is only an independent cross-check.

## Exact-results boundary

Packebusch and Mertens proved exact LABS optima through length 66 using exhaustive branch-and-bound methods:
<https://arxiv.org/abs/1512.02475>.

Length 100 is outside that exact range. The public 578 value is therefore a best-known value, not a proven optimum.

## Historical unrestricted memetic/tabu search

Bošković, Brglez, Brest and collaborators published/open-sourced LABS solvers using self-avoiding walks, tabu search, and memetic search:

- Paper: <https://arxiv.org/abs/1406.5301>
- Solver archive: <https://github.com/borkob/git_labs>

Relevant implementation details inspected from the public archive:

- The unrestricted `lMAts` solver uses a population of 100 sequences.
- Uniform per-gene parent choice is used for crossover.
- Crossover probability is 0.9, mutation probability is `1/N`, and selection is a binary tournament.
- Each child is polished by a short tabu search; the historical implementation chooses a maximum local-search iteration count around `N/2 .. 3N/2` and uses a short tabu tenure derived from that count.
- A nonduplicate child replaces a random population member.

These details explain why a single very long tabu trajectory is not a faithful reproduction of the strongest historical method.

## 2025 massively parallel unrestricted memetic tabu

Zhang, Shen, Kumar and Pistoia, *New Improvements in Solving Large LABS Instances Using Massively Parallelizable Memetic Tabu Search*, arXiv:2504.00987:
<https://arxiv.org/abs/2504.00987>

Important facts for p006:

- The method is an unrestricted general LABS solver, not a skew-symmetric-only search.
- It uses a heavily optimized Nvidia A100 implementation of the memetic/tabu framework and reports up to 26x speedup over its 16-core CPU analogue.
- It improved twelve sizes between 92 and 118, including new odd-length records at 99 and 107.
- It did **not** improve N=100; the reported N=100 result remains the prior best `E=578`.
- It reports a new unrestricted `N=99, E=553` sequence and `N=98, E=529`. These are used by `code/cross_length.py` for targeted neighboring-length transfer experiments.

This is strong evidence that N=100 is unusually resistant even to a modern high-throughput unrestricted search: the same campaign improved several nearby lengths while matching, rather than beating, 578 at N=100.

## 2026 region-prioritization / two-stage search

Pšeničnik, Bošković, Popić and Brest, *Prioritizing Search Space Regions in the Low Autocorrelation Binary Sequences Problem*, arXiv:2607.09688:
<https://arxiv.org/abs/2607.09688>

The paper combines Thompson sampling with GPU-parallel self-avoiding walks and uses a two-stage strategy: search constrained partitioned skew-symmetric regions first, then refine selected candidates in the unrestricted space. It reports improvements for 35 lengths in `450 <= L <= 527` and for `L=573`, not for N=100.

Methodological lesson for p006: constrained spaces can be useful as proposal generators even when the final target is unrestricted. This is more promising than assuming the optimum itself must obey a restriction.

## 2026 isolated small-subsystem optimization

Lau and Gangat, *Competitive scaling of small-subsystem-optimization heuristics for LABS*, arXiv:2610.14361v2 (2026-10-14):
<https://arxiv.org/abs/2610.14361>

The paper optimizes very small subsystems after deleting their interactions with the rest of the sequence, then evaluates the resulting proposal in the full LABS objective. Key features:

- exact isolated-subsystem optimization in their simulations;
- testing both the proposed subsystem assignment and its complement in the full sequence;
- a `Kicked Descent` acceptance rule that permits a forced update after a run of failed global improvements;
- a stronger-scaling variant using tracked subsystem selection and multiple proposals;
- tuned `n=4` parameters `X=80` for Kicked Descent and `(X,Y)=(90,50)` for the multiple-proposal method;
- reported experiments through `N=60`, with the `n=4` multiple-proposal variant fitting a scaling base about `1.333` over `N=27..60`.

`code/isosubsys.cpp` is an independent N=100 probe of the simpler `n=4` kicked-descent idea. Its direct extrapolation was not competitive in our calibration; see `results/2026-10-27-search-benchmarks.md`. This does not contradict the paper, which does not report N=100 performance.

### Exact isolated-subsystem objective used in our probe

For a selected set of four spin indices, expand `E=sum_k C_k^2` into its Ising polynomial and delete every monomial containing any non-subsystem spin. The remaining assignment-dependent terms are:

- a two-body term `2 s_a s_b` for selected positions `a,b` whose distance is even (the two same-shift correlation edges share their midpoint, which cancels as `s_mid^2=1`);
- a four-body term `2 s_a s_b s_c s_d` for each pairing of the four selected positions into two equal-length edges.

We checked this formula independently on small N by averaging the full LABS energy over every assignment of the environment. For every tested subsystem assignment, the average full energy minus the formula was a subsystem-independent constant, as required.

## Current local search code

`code/search.cpp` is deliberately small and inspectable:

1. Maintain all 99 aperiodic correlations exactly.
2. Evaluate any one-bit flip in O(N) from the current correlation vector.
3. Use tabu tenure plus aspiration to cross shallow local minima.
4. Support random, incumbent-perturbed, or explicitly supplied starts.
5. Apply periodic random kicks after prolonged stagnation.
6. Parallelize independent runs with OpenMP.
7. In debug builds, periodically recompute energy from scratch and abort on any incremental mismatch.

Calibration shows that this long-walk design is much too weak to justify a large compute campaign unchanged; see `results/2026-10-27-search-benchmarks.md`.

## Exact local-neighborhood evidence

Two exact negative results are now established:

1. Public `E=578` incumbent: every Hamming-distance 1 through 5 edit was evaluated (79,375,495 candidates total), with no energy below 578.
2. Best `N=99 -> N=100` transferred sequence (`E=606`): every Hamming-distance 1 through 5 edit was evaluated, with no energy below 606.

`code/sphere.cpp` reproduces cumulative small-radius scans. `code/sphere_shell.cpp` parallelizes a single exact shell and is intended for larger radii.

## Neighboring-length transfer

`code/cross_length.py` reproduces simple insertion/deletion tests from strong public neighbors. Results are in `results/2026-10-27-cross-length.md`.

The strongest simple transfer is the new 2025 `N=99,E=553` sequence with one inserted sign, which reaches only `E=606`; historical N=102 and N=103 low-energy sequences degrade much more severely when deleted to N=100. Therefore raw insertion/deletion is not a promising route by itself.

## Compute policy for this topic

Large GitHub Actions campaigns should be reserved for methods that are either exact or locally calibrated into a competitive quality regime. Current long-tabu and direct isolated-subsystem probes fail that calibration. Exact Hamming-shell exclusion is suitable for Actions because every completed shell gives a deterministic reusable result even when no breakthrough is found.

Any candidate at energy `<=574` must be frozen immediately, rescored by `code/verify.py`, then scored by the Few Shots verifier before any record claim or submission.
