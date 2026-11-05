# Official full CWI discrete GOMEA LABS baseline — 2026-11-05

## Verified experiment

The previous linkage-tree operator implemented in this research was deliberately only a **GOMEA-style single pass**, not the full published optimizer. This experiment runs [official CWI discrete GOMEA](https://github.com/CWI-EvolutionaryIntelligence/GOMEA), PyPI version 1.1.0 (2025-07-12), using its published binary black-box fitness interface. We compare its real univariate and filtered mutual-information linkage-tree models, both in the fully functioning DiscreteGOMEA population optimizer.

Seven lengths (N46/47/50/59/60/92/99), four seed-matched runs, two linkage choices, two seconds each, totaling **56 independently exact integer verified complete solver runs**. Fitness maximizes negative LABS energy. The best sequence and full eightfold canonical symmetry orbit in every row were independently recomputed.

[Verified successful computation](https://github.com/teddyli18000/web-ingest/actions/runs/42046841158) | [Adapter and exact scorer](benchmark.py) | [All 56 terminal best certificates and evaluation counts](results/full_v1.tsv) | [Full SHA/provenance](results/official_provenance.json).

| N | Best known E | Univariate: mean E (best) | Filtered MI-LT: mean E (best) |
|---:|---:|---:|---:|
|46|131|223 (211)|209 (195)|
|47|135|238 (231)|221 (215)|
|50|153|271 (257)|281 (273)|
|59|205|412 (385)|411 (401)|
|60|218|432 (406)|426 (394)|
|92|490|1114 (990)|1160 (1058)|
|99|553|1371 (1329)|1353 (1305)|

None reached known optimum or current best source. The original pilot Action 42046456585 completed four 0.7s solver calls but failed only the postrun metadata formatting; it was **not counted** as independent scientific replication.

## Crucial scope limitation

This benchmark is **random population cold-start full GOMEA**, not elite-parent-initialized recombination. Its public Python interface did not provide a supported direct initialization from the archived independent near-optimal parents, so **it cannot resolve the requested high-quality-parent recombination experiment**. Nor is it a fair direct native-runtime comparison to compiled classical memetic Tabu or GPU-MTS: the exact objective is an O(N²) **Python callback**, and no external Tabu repair was applied to these GOMEA outputs. Within two seconds the algorithm evaluates ~23k strings at N46 and ~6k at N99. This is useful baseline calibration only, not evidence full optimized/GOMEA/CGOMEA fails in the LABS problem.

A decisive future comparison would add legitimate elite population seeding through the open-source GOMEA C++ optimizer, include the same true LABS incremental scoring and postvariation Tabu repair as competing methods, and hold total solver compute constant.

The current project-level decision remains: see [the independently costed genuine-versus-virtual second-parent ablation](../innovation/SOURCE_ABLATION.md). Elite B provides limited quality-preserving value relative to an equally sized fake B on some N, but not a reproducible source-novel <=5% elite yield. No neural model or new N100 record is justified.
