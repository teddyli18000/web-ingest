# AES S-box p008 research log — 2026-10-30

This note records the current durable frontier after takeover work on the 101-gate Few Shots AES S-box circuit. It distinguishes exact exclusions from heuristic search misses; none of the negative results below is a global lower bound unless explicitly scoped.

## Baseline

- Live Few Shots record audited at takeover: 101 gates in the `{AND, XOR, XNOR}` basis.
- Released-AND representation of that circuit: 33 AND atoms + 68 linear gates.
- Goal: find and officially verify a circuit with at most 100 gates.

## Search families exhausted or deprioritized

### Mutate one AND root, then strict shave

Run `40997311108` tested 33 representative 102-gate architecture mutations with exact strict resubstitution. Aggregate work was 48,486,897 gate tests + 437,089 alias tests. Every seed returned only to 101; no 100 was found.

This is evidence only against that local mutation/shave family.

### One shared helper across two AND roots

`pair_shared_helper_search.py`, Run `41040810148`:

- FS101: 74 pair candidates, 70 distinct verified circuits, 3 nonworsening 101s, no 100.
- care53: 74 / 70, 5 nonworsening 101s, no 100.
- NIST G103 remained 103; NIST A34/G110 remained 110.

This exactly enumerates the represented one-helper/two-root family.

### Temporal local-window resynthesis

`temporal_window_resynth.py` jointly rewrites linear helpers across several fixed AND-release intervals while preserving exact live-ins/live-outs and internal AND semantics.

Broad Run `41042194646` searched 165 overlapping windows spanning up to six AND boundaries, each targeting one fewer linear gate. All 165 were `not_found`; total generated states: **29,706,547**. This is a beam-search miss, not an exact exclusion, but it makes further scaling of the same local-window representation unattractive.

## Global released-AND prefix search

### Shallow RNBP / projected future targets

`temporal_rnbp_synth.py` found a prefix releasing all 33 AND atoms with 61 linear helpers. Exact Z3 output tails of 6, 7, and 8 gates were UNSAT (Run `41043193985`; K8 UNSAT in 34.043s). K9 timed out/unknown.

`rnbp_projected_tail_search.py` added legal projections of future operands/outputs onto currently released atoms. A projection weight of 0.24 produced a 60-linear all-AND prefix, but its 7-gate exact tail was UNSAT.

### Single-deviation prefix frontier

`rnbp_prefix_variant_tail.py`, Run `41043180816`, changed one non-forced projected-RNBP choice to ranks 1..4 and exact-tested the remaining global 67-linear budget.

152 variants:

- 122 exact-UNSAT tails;
- 22 timeout/unknown;
- 8 prefix-incomplete;
- 0 SAT.

Prefix-linear histogram:

- 56: 2
- 58: 5
- 59: 16
- 60: 80
- 61: 40
- 62: 1
- 67: 8

The two best prefixes release all 33 AND atoms with only **56 linear helpers**:

- projection weight 0.24, deviation `d=1, rank=4`;
- projection weight 0.24, deviation `d=3, rank=2`.

A 56-linear prefix leaves 11 linear gates under a 67-linear / 100-total budget.

## Why the 56-linear prefixes are deceptive

Run `41043609832` measured their output geometry. Each prefix has 97 available affine signals = 8 inputs + 33 AND atoms + 56 helpers. None of the 8 AES output forms is present, one gate away, or two gates away.

`rnbp_support_distance.py`, corrected Run `41045178880`, measured Boyar–Peralta minimum-support distance through support size six:

- For both 56-linear prefixes, outputs 1 and 2 have minimum support 4 (BP distance 3).
- The other **six outputs have no representation using <=6 currently available signals**.
- d1/r4 prefix: 4,253 distinct pair XOR values and 109,919 triple XOR values.
- d3/r2 prefix: 4,288 pair values and 112,173 triple values.

Thus minimizing the number of helpers required to release all ANDs is badly misaligned with minimizing total circuit size. The relevant coupled objective is the AND-interface cost plus the support-distance geometry of future operands and outputs.

## Exact / bounded tail results for the 56-linear prefixes

`rnbp_tail_precondition_z3.py`, Run `41044055885`, first tested the restricted family with H anonymous helpers followed by 8 terminal output gates. Both prefixes are UNSAT for H=2 (99 total gates) and H=3 (100 total gates).

A stronger formulation is in `rnbp_tail_ordered_exact_z3.py`. Because every output is farther than two gates from either 56-prefix:

1. The first two tail gates cannot be AES outputs; they must be non-output helpers.
2. Eight distinct AES outputs require at least eight output-producing gates.
3. Therefore any <=11-gate tail has exactly two or three non-output helpers.
4. For the three-helper case, after fixing the first two helper slots, only the third helper position (2..10) remains to enumerate; every other slot produces a permutation of the exact eight AES outputs, and earlier outputs may feed later slots.

Run `41044306752` evaluated all 20 H=2/H=3 instances over the two known 56-prefixes. Artifact aggregation Run `41046041704` gives the authoritative solver-status count:

- **10 UNSAT**;
- **10 timeout/unknown**;
- **0 SAT**.

Each prefix contributes 5 UNSAT and 5 unknown instances. In particular, both H=2 / 10-slot tails (99 total gates) are exactly UNSAT: d1/r4 in 233.177s and d3/r2 in 283.038s. The H=3 / 100-gate schedule matrix is only partially resolved; timeout/unknown must not be treated as exclusion evidence.

Concrete H=3 UNSAT instances:

- d1/r4: third helper positions 6, 8, 9, 10;
- d3/r2: positions 3, 8, 9, 10.

Concrete H=3 timeout/unknown instances:

- d1/r4: positions 2, 3, 4, 5, 7;
- d3/r2: positions 2, 4, 5, 6, 7.

Therefore the two 56-linear prefixes are not yet exactly excluded from all 100-gate completions, but no SAT tail has been found and half of the full ordered H=3 schedule family is proved impossible.

## Current highest-value reformulation: true support-distance RNBP

The public Extended-BP RNBP implementation (`lemontrr/Extended-BP-Framework`, TCHES 2025) defines target distance as the minimum number of currently available signals whose XOR equals the target, minus one. It precomputes support sets up to four signals and recursively tests larger support. Its candidate pair selection minimizes the sum of target distances and then maximizes the Euclidean norm of the distance vector.

`released_rnbp_support_synth.py` ports that metric to the Few Shots affine/XNOR model with strict temporal legality:

- helpers may depend only on currently available signals;
- a future AND atom is unavailable until both exact affine operands have been synthesized;
- unreleased nonlinear coordinates are never used by a formal-vector shortcut;
- XOR and XNOR are both represented at unit gate cost, including the affine constant flip;
- finite support distances are updated incrementally exactly as a new pair helper can reduce distance by at most one;
- completed candidates are independently checked on all 256 AES inputs.

The public Extended-BP code also implies a useful exact acceleration: if a target has distance `d`, a new helper can reduce it only when `target XOR helper` is representable by `d-1` old signals. `released_rnbp_support_fast.py` uses the cached 0..4 support-XOR sets to generate such reducer helpers directly for low distances, falling back to recursive checks only at higher support. This removes the need to test every pair helper against every target without changing the represented search semantics.

Active constructive runs:

- FS101 (33 AND, <=67 linear target): original optimized support-distance Run `41045312828` and faster target-generated Run `41045875882`.
- NIST G103 (32 AND + 71 linear public seed; <=68 linear would give 100 total): Run `41045542990` and the fast G103 jobs inside `41045875882`.

These are currently the primary constructive search lines because they optimize the long-range basis geometry that the 56-linear-prefix experiments show is missing from shallow/local search. The 32-AND G103 skeleton is particularly important: it needs only three global linear savings relative to its 103-gate seed, and earlier local joint-factor failures do not exclude a globally re-synthesized 68-linear realization.
