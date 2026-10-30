# R(4,6,36) frontier after row-CSP audit — 2026-10-30

## Trust boundary

Commit `e99119cc3a862be239e8d6d99a325dc64ccd70bc` found that the old row-domain `tf()` predicate rejected length-2 paths as if they were triangles. Any UNSAT result depending on that predicate is withdrawn unless independently re-proved.

Withdrawn for current reasoning:

- `results/m219-r34-binary-csp.json` and the old `m219-final-two-sequences.json` conclusion;
- m220 r2/r3 row-CSP results produced from the same core;
- the old m220 r4 A25/B117 row-CSP result.

Unaffected by this specific bug include the 216–218 edge exclusions, the independently solved d12 fixed-pair closure, and solver-free / low-graph / column-only arguments that do not call the faulty row predicate.

## Restored sound m=219 closure

The two degree sequences that had depended on the withdrawn row CSP are now re-closed by `m219_final_two_sound_verify.py` and `results/m219-final-two-sound-post-audit.json`.

### `11^7 12^16 13^13`

- r=3 is fully excluded by the post-audit t=3/5/6 transversal verifier and t=4 exact size-2-column verifier.
- Therefore every degree-11 vertex has r>=4.
- If no r=4 vertex existed, sum r>=35, while the seven low vertices are K4-free so sum t<=2 ex(7,K4)=32 and r<=t pointwise. Hence an r=4 anchor exists.
- For r=4, the only local edge strata are A25/B116 and A26/B117. Complete sound B-class-label scans give zero contexts for t=4 and t=5.
- For t=6, the six other low vertices inside A form a triangle-free graph of minimum degree at least 3, hence K3,3. This forces no low-high edges; T-mid contributes at most 9 edges and the remaining five A vertices at most 6, so e(A)<=24, contradicting the r=4 requirement e(A)>=25.

### `11^8 12^14 13^14`

- For r=3, t=3 and t=4 have zero sound B-label contexts.
- t=5 has exactly the same A26/B116 local class data as the already-audited seq0 r=3,t=4 certificate, so that six-run exact size-2-column proof applies verbatim.
- t=6 reduces to a unique B116 low vertex q with d_B(q)=8 and no high B neighbour. Its three A-cross edges must all go to low A vertices, making q itself t=3,r=3, already impossible.
- t=7 is excluded by complete enumeration of the two A26 types: the 7-low/4-high partition support counts are `[0,0]`.
- Thus all eight low vertices have r>=4. The exact degree-class relaxation has 210 feasible class matrices and max sum r=32, forcing every low vertex to have r=4.
- Sound B-label scans exclude t=4,5,6 for any r=4 vertex. Hence all eight lows would need t=7, inducing K8, impossible in a K4-free graph.

`m219_complete_exclusion.py` now requires the post-audit replacement result and explicitly refuses the old final-two result. `results/m219-complete-exclusion-post-audit.json` records the restored 23/23 structural coverage. Consequently any hypothetical `(4,6,36)` graph must have at least 220 edges.

## Next frontier

Proceed at m=220 from the structural reduction only. Treat every prior m220 result based on the faulty row-domain predicate as withdrawn. Prefer the now-successful pattern:

1. degree-class / local-edge identities;
2. complete small A/B strata;
3. sound class-label necessary conditions;
4. low-graph finite enumeration and extremal arguments;
5. exact column CSP only after the above reductions.

Do not return to broad whole-graph SAT unless these structural interfaces stop reducing the candidate space.
