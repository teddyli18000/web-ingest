# Six-AND rank-four completions: four raw target factors are excluded

## Scope

The merged 102-gate AES S-box would fall to 101 if its fixed four-input / nine-factor 18-gate core could be replaced by a 17-gate circuit. Earlier exact work in this workspace already excludes:

- every five-AND / twelve-linear fixed-interface core;
- every quotient-rank-five six-AND / eleven-linear core;
- every quotient-rank-six six-AND core for the 496 rank-five zero-state completions.

The remaining fixed-interface family consists of one of the 16 rank-four zero-state completions, six independent AND gates with final nonlinear quotient rank six, and at most eleven XOR/XNOR gates.

This note closes the most favorable subfamily: **four of the six raw AND outputs are themselves required tail factors**.

## Structural reduction

For any rank-four completion the nine required factors span a four-dimensional nonlinear quotient space `T`. Since the six raw AND quotient classes are independent, at most four raw AND outputs can be target factors. If the maximum four is attained, exactly two AND gates are non-target helpers.

The first AND must be a helper: before any nonlinear source exists, an AND of affine input functions has algebraic degree at most two, whereas each required factor has degree three. The second helper must supply the second quotient dimension outside `T`; otherwise four target classes plus the two helpers cannot form a six-dimensional raw-AND span containing `T`.

This gives a very constrained exact search:

```text
2 non-target helper ANDs + 4 exact target-factor ANDs = 6 independent ANDs.
```

## Exact optimistic physical screen

`screen_core6_rank4_raw4.cpp` exhausts this family separately for all 16 rank-four zero-state completions.

The search uses exact 16-state truth tables and is deliberately **more permissive** than a physical `{AND,XOR,XNOR}` circuit:

- every affine function of the currently available primitive inputs/raw-AND outputs, with either constant phase, may be used as an AND operand;
- every distinct non-source affine operand form is charged only one linear gate, even when realizing that form would itself require helper XOR/XNOR gates;
- after six ANDs, each remaining non-raw required factor is likewise charged only one linear gate, with no requirement that the collected forms admit a realizable linear schedule.

Therefore `mandatory_count <= 11` is only a necessary condition for a 17-gate circuit. If this optimistic search has no hit, the corresponding physical circuit is impossible.

## Result

A complete local run of all 16 rank-four completion cases found **zero hits in every case**. No search path reached a complete six-AND sequence while staying within the optimistic eleven-form linear budget.

Representative search sizes were:

```text
case 0 (000000000): 737,701 nodes, 0 hits
nonzero cases:       about 756k--763k nodes each, 0 hits
```

The nonzero cases had either 13,824 or 20,736 target-AND transition attempts, but all branches were eliminated before a complete <=11-mandatory-form sequence.

GitHub Actions run `40797432231` was launched as an independent 16-way reproduction using `.github/workflows/temp-aes-core6-rank4-raw4.yml`; at the time this note was written it was queued behind other project workloads. The local result is reproducible directly from the checked-in C++ source; the Action result should be recorded separately once all jobs complete.

## Consequence

Any remaining fixed-interface 17-gate candidate must have **at most three raw AND outputs equal to required factors**.

Thus at least six of the nine required factors must be materialized by XOR/XNOR gates. With only eleven linear gates available in total, at most five linear gates remain for all other distinct operand/helper forms unless required-factor forms are themselves reused as AND operands.

This is the next exact-search leverage point: classify the `r <= 3` branches by which required-factor linear forms can simultaneously serve as future AND operands, instead of enumerating all 23,970 nonlinear envelopes uniformly.
