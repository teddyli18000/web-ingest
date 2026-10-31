# AES S-box boundary log — 2026-10-31

## Objective

Break the current 101-gate AES S-box record under the Few Shots p008 verifier
(two-input AND/XOR/XNOR gates).  The current primary seed family is the public
NIST A32/G103 circuit because it uses only 32 AND gates; a 100-gate circuit may
therefore spend up to 68 gates on linear logic.

## G103 last-AND cut

For normalized `nist-g103`, cut immediately after the last AND:

- 32 AND gates total;
- 49 linear gates before/on the cut;
- 22-gate pure-linear suffix;
- 17 live boundary values;
- exactly three boundary values are non-atomic affine functions.

Hence the exact 100-gate budget frontiers are 49+19, 48+20, or 47+21 linear
(prefix+suffix).

A prior implementation bug hard-coded historical source names `t47/t48/t49`.
`released_and_skeleton.load_circuit()` normalizes wire names, so those names do
not survive.  The corrected scripts detect the three cut extras by affine
semantics: primary-input and AND-output basis vectors are atoms, and the three
crossing affine values that are not atoms are the extras.  In the current
normalized circuit they are `g77,g78,g72` at boundary indices `[1,7,11]`.
The failed pre-fix Action was infrastructure failure, not a scientific result.

## Complete GL(3,2) suffix-interface census

`g103_cut_basis_census.py` / `_shard.py` enumerate all 168 ordered bases of the
three-dimensional non-atomic cut space.  Run `41185126202` completed all eight
shards using the current true-support RNBP portfolio (6 seeds/basis, <=22 gates):

- 0/168 bases constructed a <=22-gate suffix;
- 108 bases ended at residual distance sum 2;
- 60 bases ended at residual distance sum 3;
- identity `[1,2,4]` is in the worse residual-3 group and has initial BP sum 52;
- some transformed bases reduce the initial BP sum to 48 and residual to 2.

This is only a heuristic miss.  It shows that cut basis materially changes the
suffix search geometry, but the current RNBP closure rule gets stuck near the
end and cannot support a lower-bound claim.

## Exact restricted prefix census

`g103_explicit_cut_basis.py` exploits a structural fact verified on the normalized
seed: the three non-atomic cut producers are terminal inside the nonlinear
prefix.  Delete those three producers and the fixed prefix contains 46 linear
gates.  For the <=49-linear fixed-prefix family, every missing transformed basis
output must itself be produced and there is room for at most three new gates, so
trying all generation orders of the three basis outputs is exact for this family.

Run `41185986966` completed all 168 bases:

- 18/168 ordered bases have a 49-linear transformed prefix;
- 0/168 have <=48 linear gates;
- the remaining 150 require >49 within this fixed-prefix/explicit-interface
  family.

The 18 are permutations of the row sets `{1,2,4}`, `{1,3,4}`, and `{2,3,4}`.
Therefore a 20-gate suffix cannot reach 100 while the original nonlinear prefix
is kept fixed; the 48+20 route requires a genuine prefix architecture change.
A prior hand guess that `[1,4,6]` was a 49-linear basis was wrong; the machine
census correctly reports that it needs >3 replacement gates.

## Direct exact suffix attempts

`g103_suffix_exact_z3.py` encodes the affine 17->8 suffix directly.  Run
`41185452014` tested identity-basis 19 and 20 gates with 480 s timeouts; both
returned `unknown`/timeout.  This is solver hardness only.

`g103_suffix_cadical.py` independently implements a bit-level affine CNF using
CaDiCaL/PySAT, motivated by the Fuhs--Schneider-Kamp shortest-SLP SAT encoding
and the 2026 `refutation-gap` implementation.  We do not reuse an UNSAT result as
a lower bound without proof certification.

`g103_suffix_cadical_control.py` validates the affine CNF semantics on the known
22-gate NIST suffix (Run `41186065183`):

- exact known topology/polarities fixed: SAT in ~0.326 s;
- same fixed topology with one live XNOR polarity flipped: UNSAT in ~0.308 s.

Thus slow unconstrained instances are search-space difficulty, not a truth-table
or affine-polarity encoding error.

## Affine-to-linear reduction

For this suffix the affine constant bit need not be part of the combinatorial
search.  Every synthesized non-input node may independently be XOR or XNOR.
After a linear XOR DAG is found, assign desired constant bits to target-producing
signals and derive each gate polarity recursively as

`xnor_bit = c_out xor c_left xor c_right`.

All eight suffix target linear forms have weight >1, so no target asks for a
complemented boundary input for free.  Therefore constructive suffix search may
be reduced to a standard 17-bit GF(2) SLP, with XNOR polarities recovered after
SAT and the assembled circuit still checked on all 256 AES inputs.

Implemented:

- `g103_suffix_linear_cadical.py`: pair-one-hot 17-bit CNF;
- `g103_suffix_linear_cadical_select.py`: more compact separate left/right
  selector CNF, following the standard shortest-SLP formulation;
- the compact encoder additionally enforces sound minimum-circuit liveness
  (every gate feeds a later gate or is a target) and one-hot target matches.

Live/most-recent compute at this log point:

- Run `41186220364`: pair-one-hot linear CNF, identity 19/20/22 and basis
  `[1,3,4]` at 19;
- Run `41186525750`: compact selector CNF before liveness strengthening;
- Run `41186850606`: compact selector CNF with liveness + one-hot matches;
- Run `41186870905`: 24-way joint prefix sweep at 48 linear gates over bases
  `[1,2,4]`, `[1,3,4]`, `[2,3,4]`, seeds 1..4, basis weights 1/3.

Any <=100 `full.json` produced by these workflows is automatically passed to the
Few Shots official p008 verifier before it is treated as a breakthrough.

## Search-space interpretation / next decisions

1. Do not scale the 168-basis RNBP census: it has already shown a systematic
   final-closure bottleneck rather than improving candidate quality.
2. A 19-gate suffix on any of the 18 explicit 49-linear bases is an immediate
   100-gate certificate.
3. A 20-gate suffix is useful only if a non-fixed prefix can be synthesized at
   48 linear gates; hence the separate joint prefix48 sweep.
4. If exact 19/20 SAT remains inconclusive, move to topology-guided/local SAT
   around a concrete 20/21/22-gate suffix rather than spending indefinitely on
   unconstrained CNF.
5. Every claimed candidate must pass both `released_and_skeleton.independent_check`
   on all 256 inputs and the Few Shots official verifier.
