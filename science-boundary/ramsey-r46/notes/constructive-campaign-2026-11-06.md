# p003 construction-first work log — 2026-11-06

## Outcome (no new record)

Few Shots p003 still has a 35-vertex record. No verified 36-vertex graph was found. The retained best 36-vertex near-miss remains 14 forbidden sets (10 K4 and 4 independent 6-sets), stored in `results/algorithm22-calibration-best-14.json`.

### 192 joint-regrowth SAT attempts

- Actions: https://github.com/teddyli18000/web-ingest/actions/runs/42255847873 (completed successfully on both seeds).
- 96 attempts from the public 35-vertex baseline and 96 from the 14-defect 36-vertex near-miss, each regenerating all edges incident on a randomized block of 10–14 vertices.
- Each parent: 95 solver TIMEOUT/UNKNOWN, one local-core UNSAT, **zero SAT/witness**. Exact jobs and output are available in that run's two artifacts.
- This is a test of the specific fixed-core conditional search, not a global exclusion; the 190 unknowns supply no proof.

### Nonabelian Cayley to subgroup-orbit construction

A new distinct family uses vertices `S3 x S3`, with all 630 possible unordered pairs assembled in full-Cayley inverse-pair orbits (25 variables), then orbits of its normal order-nine subgroup (70 variables) and finally an order-three subgroup (210 variables).

All three retained seeds were independently reconstructed from their orbit masks and recounted over the full 36-vertex adjacency matrix:

| symmetry | edge count | K4 | I6 | total defects |
| --- | ---: | ---: | ---: | ---: |
| full Cayley | 252 | 45 | 0 | 45 |
| C3 x C3 | 270 | 36 | 0 | 36 |
| C3 | 267 | 33 | 0 | 33 |

Reproduction: `python science-boundary/ramsey-r46/nonabelian_orbit_seeds.py --level cayley`, then `h9`, then `h3`. Use `--out <file>.json` to emit a whole-graph near-miss, but **none is a valid (4,6)-graph**.

Constructive mechanisms tested: full-Cayley stochastic orbit flips, progressive 9- and 3-orbit relaxation, unrestricted 1- and 2-edge conflict-guided local repair, and SAT thinning of the 45-defect Cayley seed (also with prioritized additions of 20–80 edges). Orbit relaxation did improve its own starting score 45→36→33, but unrestricted repair did not beat 33; the independent 14-defect incumbent also did not improve in a short retest. The local SAT thinning of the 45-defect graph was UNSAT only under its fixed allowed-edge sets, or timed out. These are not broad impossibility claims.

**Reassessment:** An orbit-flip changes 9 or 3 edges at once, maintaining strong global symmetry; the best 3-fold model is still 19 defects worse than the incumbent. Do not scale this same orbit basis for many more hours without a qualitatively better cross-family recombination mechanism.

### New constructive reformulation: 32-core/four-tail multi-parent fusion

A known valid 35-vertex parent can be reduced to a valid 32-vertex core plus three legal single-vertex extensions. The repository already contains exhaustive three-vertex regeneration work on published 35-core deletions, so freezing a 33-core is not a fresh constructive family. We therefore compare **canonical 32-vertex cores across all 37 public Exoo graphs**, collect the distinct legal tail neighbor masks on each core, and create graphs with **four** jointly chosen tails.

The four tail-tail vertices have six free pair bits. For any choice of four legal tails, the exact defects can be calculated as follows:

- For two tails x,y: if xy=1, K4 defects equal the number of base edges among their common neighbors; if xy=0, I6 defects equal the number of independent fours in their common nonneighbors.
- For triples: a tail triangle contributes one K4 per shared core neighbor; a tail independent triple contributes one I6 per independent core triple in their common nonneighbors.
- For four tails: all six tail edges present contributes one K4; all six absent contributes one I6 per nonedge pair among common core nonneighbors.
- There are no other forbidden configurations: the core is valid and each individual tail is a valid addition to it.

All 64 choices of the six tail-tail edges are explored. The formula was compared with independent full-graph clique/independent-set recount on explicit 35-parent-derived synthetic test cases, and agreed. A score below 15 is independently recounted and saved; a zero would additionally require the Few Shots verifier.

Reproduction: `core32_multiparent_fusion.py` downloads `r46_35some.g6`, uses Python igraph/Bliss to canonicalize sampled cores and runs the exact four-tail recombination. Its currently launched Action: https://github.com/teddyli18000/web-ingest/actions/runs/42266493452 (two separate sampling seeds; consume artifacts and look for a confirmed sub-14 candidate).

## Decision

Optimize discovery of a legal 36-vertex graph or a **verified improvement below 14 defects**. Do not treat new class exclusions, UNSAT at a fixed core, or timeouts as the target metric. A credible breakthrough requires a full certificate and the authoritative Few Shots verifier.
