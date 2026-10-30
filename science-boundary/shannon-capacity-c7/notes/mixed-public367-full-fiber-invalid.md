# Invalid homogeneous public-367 full-fiber formulation

Status: **do not reuse this formulation**. It is not a negative mathematical result about mixed public 367-point constructions; the simplifying ansatz itself is false.

An exploratory model (`code/bpz_mixed_public367_global.py`) attempted to keep the pinned `B x B` core and choose eight left and eight right zero-support endpoints `q in Q`, attaching an entire public 367-set to each chosen endpoint. The intended canonical reference was written as

`(PH x X) union (X x PV)`.

Two Actions exposed the issue:

1. run `40996092918` first failed because it incorrectly assumed different private-pair endpoints of `Q` never conflict; the concrete counterexample was `16046 ~ 13358`;
2. after encoding the true `Q` conflict graph, run `40996447445` made the hard model UNSAT.

The second failure is not a useful UNSAT theorem, because the claimed canonical reference is itself not independent. An independent replay using the pinned BPZ/Tan data and the exact `C7^5` conflict rule finds, for example,

- `(3716, 24)` in `PH x X`, and
- `(6466, 15075)` in `X x PV`

which are confusable in both coordinates and hence conflict in `C7^10`.

Therefore the real BPZ terminal construction cannot be represented as sixteen homogeneous full copies of the same `X` attached independently to `PH/PV` endpoints. Any future public-367 mixing model must reconstruct the actual endpoint-dependent terminal/fiber geometry from the source construction before optimizing assignments.

This does **not** affect the separate `public367_union_sat.py` search, which works purely in `C7^5` on the union of validated public 367-sets and makes no BPZ terminal-fiber assumption.
