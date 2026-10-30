# AES architecture census after the 101-gate merge — 2026-10-29

## Purpose

The 101-gate breakthrough showed that a negative result around one decomposition is not evidence against another representation.  This note records a reproducible census of high-quality complete AES S-box circuits so future search can choose seeds by structural diversity rather than by gate count alone.

The scripts `seed_family_census.py` and `seed_family_census_extended.py`:

- parse Few Shots JSON certificates and NIST NCFF SLPs;
- normalize NIST bit order to the p008 convention;
- independently check every one of the 256 AES inputs against arithmetic inversion modulo `0x11b` plus the AES affine map;
- compute exact truth tables for every intermediate wire and every AND output;
- record an AND dependency-shape fingerprint; and
- compare exact intermediate/AND-function overlap.

Exact-function overlap is a descriptive fingerprint, **not** an equivalence test under arbitrary affine changes of variables.

## Validated seed families

### Few Shots transformed 101

`chunfeng11221/aes101-nist-interface-resub`

- 101 gates = 33 AND + 40 XOR + 28 XNOR;
- AND depth 8;
- zero exact AND-output functions shared with the NIST A32/G103 or A32/G104 circuits in the normalized p008 coordinates.

This is the current record representation and is structurally distinct from the NIST coordinates from which its successful 102 seed was derived.

### NIST main near-frontier family

The following circuits form one high-overlap family under exact AND truth functions:

- A32/G103;
- A32/G104;
- A32/G105;
- A32/G109;
- A33/G105;
- A33/G108.

Representative overlap:

- A32/G103 vs A32/G104: 30 shared AND functions, union 34, Jaccard `0.882353`;
- A32/G103 vs A32/G105: 27/37, Jaccard `0.729730`;
- A32/G104 vs A33/G105: 29/36, Jaccard `0.805556`;
- A32/G105 vs A32/G109: all 32 AND functions identical, same dependency-shape hash;
- A33/G105 vs A33/G108: all 33 AND functions identical, same dependency-shape hash.

Therefore these should not be counted as six independent nonlinear seed families.  A32/G103 is still useful because it is a differently interleaved sibling: 103 gates, 32 ANDs, AND depth 7, versus the G104 seed's AND depth 5.

### NIST A34/G110 — distinct nonlinear family

`aes-sbox-a34-ad4-g110-gd22-xx76-3`

- 110 gates = 34 AND + 73 XOR + 3 XNOR;
- AND depth 4, profile `9,3,4,18`;
- exact AND overlap with A32/G103: **0**;
- overlap with A32/G104: **1**;
- overlap with A32/G105 or A32/G109: **3**;
- overlap with A33/G105 or A33/G108: **3**;
- overlap with the merged 101: **0**.

It is nine gates above the current record, so naive local rewriting is not justified.  Its value is as a qualitatively different nonlinear skeleton to which a new whole-circuit linear/interface resynthesis may be applied.

## What the census changes

The working search space should now distinguish at least:

1. the NIST main near-frontier nonlinear family;
2. the field/plane transformed 101 family;
3. the A34/G110 nonlinear family;
4. future families obtained by changing the nonlinear skeleton or by semilinearly transporting an existing skeleton and jointly resynthesizing all affine interfaces.

The old Few Shots 102/103 pair is useful historical evidence but is no longer the primary seed family for 100.

## Next representation: released-AND affine skeleton

Any complete `{AND,XOR,XNOR}` circuit can be rewritten as:

- eight primary Boolean inputs;
- an ordered sequence of AND atoms `A_i`;
- two affine operand forms for each `A_i`, expressed over the primary inputs and already released `A_j`;
- eight final affine output forms.

Every XOR/XNOR-only wire is then an implementation choice for these affine forms, not an architectural boundary.  Linear helpers may persist across what a hand decomposition calls prelinear, middle, core, final multiplication, or output layers.

This representation is the next main search space.  For a semilinear field map `P`, substitute `P(x)` into **all** AND operand forms and derive the affine output compensation `Q` directly from the 256-entry permutation relation `Q(S(P(x))) = S(x)`.  Then jointly synthesize the released/deadline affine targets rather than optimizing each named layer separately.

The immediate falsifiable target is simple:

- reproduce the current linear cost of each seed under the released-AND representation;
- then find a 67-linear-gate realization of the 33-AND 101 skeleton, or a 68-linear-gate realization of a 32-AND transported NIST skeleton;
- any such realization gives a 100-gate circuit before any further ODC/resubstitution.

If the heuristic cannot reproduce the original cost, improve the linear synthesizer before drawing conclusions about a transported skeleton.

## Compute evidence

- initial five-seed census: GitHub Actions run `40991160742`, all 256-input checks passed;
- extended near-frontier census: run `40991496201`, all listed circuits verified and classified;
- the first extended run failed only because the A28 control circuit uses `U0..U7 / S0..S7` names while the first parser assumed NIST `x/y` names; no scientific inference was drawn from that parser failure.
