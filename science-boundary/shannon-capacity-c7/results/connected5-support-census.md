# Connected five-owner support-graph census

Pinned source: Tandon/BPZ commit `c753408492dde92a239708986d16c15dbf6c3235`.  Supports are measured against the pinned 359-point set `B=I0\R`.

`code/bpz_connected5_c5_census.py` enumerates every five-owner set connected in the observed support hypergraph, reconstructs the complete pool

`Y_C = {z : empty != N[z] intersect B subseteq C}`,

computes `alpha(Y_C)` exactly, and checks for an induced `C5` in the conflict graph.

Exact result:

- connected five-owner sets: **121,192**;
- `alpha(Y_C)=5`: **121,191**;
- `alpha(Y_C)=6`: **1**;
- the unique alpha-6 set is exactly the previously known raw +1 defect `C={1644,13347,13600,13692,14040}`;
- connected alpha-5 sets containing an induced `C5`: **2,003**;
- largest complete pool among all connected five-owner sets: 21 vertices;
- largest pool among the induced-C5 alpha-5 cases: 20 vertices.

The unique-alpha6 replay is a hard self-check against the independently obtained row-support search.

Scientific implication: raw one-dimensional replacement value is flat on a large **nonperfect neutral layer**.  These 2,003 cases do not improve `C7^5` by themselves, but they are qualitatively different from the perfect pair/triple support graphs and are legitimate strong-product supermultiplicativity candidates.

Reproduction: GitHub Actions run `40989172669`, job `123847148166`; workflow completed successfully.  Four worker processes used about 268% aggregate CPU; elapsed time about 36 s; peak RSS about 509 MB.

The immediate follow-up is an exact Hall relaxation over all `68 x 2003 = 136,204` products between the known nonperfect connected four-owner types and these neutral five-owner induced-C5 types.  Candidate conflicts are dropped in that screen, so Hall saturation is a rigorous exclusion; only Hall-positive cases need conflict-aware MaxSAT.
