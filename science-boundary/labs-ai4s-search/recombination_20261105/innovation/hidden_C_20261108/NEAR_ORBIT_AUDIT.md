# Frozen posthoc quality/diversity audit of history-retention searches — 2026-11-09

**Question:** Beyond recovering known C, do the completed A/B-blind search trajectories generate *new structurally distinct near-optimal LABS orbits* at equal full compute? This may reveal positive search instances where exact C hits are scarce. This audit does **not** change any policy or candidate and does not re-train an ML model.

**Inputs already immutable:** exact-verified gzip event traces for N46, N47 and N50, classic one-incumbent vs alternating-X, plus the N50 all-X classical baseline; source-parent input, a hidden target vault and the independently scored [29-orbit corpus](../../data/combined/combined10.tsv). All target and source-corpus lookups are *post-hoc* only. The solver had no C vault.

**Predeclared endpoints, each per source-pair/seed and policy, excluding the common initial direct repair when judging incremental action success:**
- Any **non-A and non-B** eightfold symmetry orbit with exact E≤1.05×known optimum and separately ≤1.10×known optimum. This includes known target C but does not privilege it during scoring.
- Number of distinct canonical high-quality non-A/B orbits, exact first hit time and minimum E.
- Stronger diversity screen: each candidate orbit must be at minimum symmetry-aware Hamming distance **at least ceil(N/5)** from **both** supplied A and B. This excludes close parent clones and is frozen rather than tuned after viewing outputs.
- New relative to the **entire** frozen 29-source-orbit corpus, not just A/B, at near5/near10. This excludes known target C and other already archived source optima and avoids calling a rediscovered published solution novel.
- Distinguish AB_blind from C_shell; record each C orbit lineage separately, because AB_blind is the real source-independent intervention and C_shell is privileged target-conditioned.
- Compare paired hits, costs and source-orbit coverage between original single incumbent, alternating-X and (N50 only) classical always-X. Do not treat repeated trajectory events as independent sample units. Model/history policy must beat simple X-only classical restarts for architecture to be justified.

**Important:** A near5/near10 orbit is not automatically a distinct attraction basin. These are **structural-proxy** outcome labels; exact basin identity requires reproducible convergence/relaxation or transition analyses. Report both minimum orbit Hamming and energy to prevent false novel-structure claims.

No further search evaluation is commissioned here; this is strictly an analysis of the prior full-cost verified archives with independent exact checks of every retained high-quality candidate.
