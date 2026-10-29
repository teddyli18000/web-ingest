# Core-release support/product frontier for the pinned C7 construction

Status: no verified score above 134,753. This note records exact structural exclusions and the first support-defect families that reached the local `+1` boundary before peripheral compatibility was imposed.

All five-dimensional supports are measured against the pinned `B` of size 359 from Tandon/BPZ commit `c753408492dde92a239708986d16c15dbf6c3235`.

## Two core holes

A one-core-hole unlocked layer has independence number at most one; see `results/one-core-hole-closure.md` and `code/bpz_one_core_hole_alpha_audit.py`.

For two deleted core points:

- if the holes are in different rows and columns, the newly unlocked layer is contained in the union of two one-hole layers, so its independence number is at most two;
- the only genuinely new footprint is an aligned row/column pair, where an exact support-2 five-dimensional class can appear.

There are 322 exact support-2 owner-pair groups against `B`. All `359 x 322 = 115,598` aligned row cases were enumerated; column cases are symmetric. Unlocked layer sizes ranged from 1 through 10. Exact `C7^10` MIS on every layer gave maximum independence number 2. Hence, conditional on `alpha(C7^5)<=367`, deleting two core points gives at most

`128879 + 5872 + 2 = 134753`.

So two core holes also cannot create an independent route around the unresolved five-dimensional 368 problem.

## Row-aligned k-hole support defects

For `C subseteq B`, define

`Y_C = { z in C7^5 : empty != (N[z] intersect B) subseteq C }`.

Deleting the same column-owner set `C` in one `BB` row makes a new layer whose second-coordinate projection lies in `Y_C`. Connected support-hypergraph enumeration with complete pool reconstruction gives:

| k | exact result |
|---:|---|
| 2 | no `alpha(Y_C)>=3` |
| 3 | no `alpha(Y_C)>=4` |
| 4 | no `alpha(Y_C)>=5` |
| 5 | exactly one owner set reaches 6 |
| 6 | exactly four genuine outside-only owner sets reach 7 |

The unique `k=5` defect is

- owners: `1644,13347,13600,13692,14040`
- unique independent 6-set: `3709,13684,14335,15959,16045,16050`.

The four genuine `k=6` defects are:

1. owners `8888,10960,13347,13600,13692,14040`; additions `6494,10659,13649,13684,14335,15959,16045`;
2. owners `1644,11305,13347,13600,13692,14040`; additions `3709,11298,13684,14335,15959,16045,16050`;
3. owners `1644,13248,13347,13600,13692,14040`; additions `3709,13297,13684,14335,15959,16045,16050`;
4. owners `1644,1741,13347,13600,13692,14040`; additions `3709,13684,14335,15959,16045,16050,16147`.

Each listed replacement set is unique within its complete support pool.

## Private-pair killer obstruction

Let the eight `Q` private pairs be the pinned BPZ pairs. A five-dimensional replacement `y` is a *killer* of private pair `p` when `y` conflicts with both endpoints of that pair.

Among all non-`B`, nonzero-support five-dimensional candidates, killer masks have popcount only zero or one:

- 15,584 killer-free candidates;
- 848 killers, exactly 106 for each of the eight private-pair colors.

If a row-aligned replacement set `Y` contains a killer of a private pair, then retaining a full 367-point safe block for that private pair would require a 367-word independent set in `C7^5` wholly nonconfusable with the row coordinate. Adding the row coordinate itself would give a 368-word set. Thus, conditional on `alpha(C7^5)<=367`, every distinct killed private pair forces at least one peripheral loss.

A useful necessary score bound for a row defect is therefore

`Delta <= |Y| - |C| - h(Y)`,

where `h(Y)` is the number of distinct killed private-pair colors.

The raw `k=5` and `k=6` `+1` core defects above all contain multiple killers, so they do not yield a ten-dimensional improvement without simultaneously resolving the five-dimensional 368 problem.

Killer-free exact searches gave:

- `k=5`: 83,374 connected finals, 8,006 sufficiently large pools, maximum pool 12, no remove-5/add-6 defect;
- `k=6`: 669,735 connected finals, 84,133 sufficiently large pools, maximum pool 16, no remove-6/add-7 defect;
- `k=7`, max-support 7: 2,495 anchors, 650 tested pools, max pool 21, no 8-set;
- `k=7`, max-support 6: 684,501 owner sets, 59,217 tested pools, max pool 20, no 8-set;
- `k=7`, max-support 5: 3,568 anchors, 529,848 owner sets, 104,769 tested pools, max pool 20, no 8-set.

The remaining lower-support `k=7` strata were deliberately not extended mechanically after candidate quality stayed flat; the search representation was changed instead.

## Rectangular core deletion as a support-graph product

For a core rectangle `D=A x C`, the complete new layer beyond the fixed-`BB` safe universe is

`T_D = (Y_A strong-product Y_C) minus (A x C)`

under the inherited `C7^5` conflict relation. This turns core release into exact MIS on small rooted support graphs.

### Pair and triple support graphs

All `C(359,2)=64,261` rooted pair support graphs compress to only 18 adjacency patterns; every pair graph is perfect.

Four-owner/triple precursor facts:

- all 115,018 rich three-owner sets compress to 1,566 rooted patterns;
- all 7,532,041 poor three-owner sets compress to 18 rooted patterns;
- every pair and every rich/poor triple support graph is perfect by exact perfect-graph recognition.

Consequences checked exactly:

- every `2 x 2` rectangle has unlocked-layer independence number at most 4;
- every `2 x 3` rectangle has unlocked-layer independence number at most 6.

Thus neither can give delete-4/add-5 or delete-6/add-7.

### First nonperfect support graphs occur at four owners

Among 16,166 connected four-owner sets, 9,750 rooted support-graph patterns occur. Exactly 68 of these patterns are nonperfect; each such pattern occurs once.

The first nonperfect example is

- owners `314,1741,2380,14040`;
- `Y_C = {314,1741,2380,14040,321,2379,14335,14727,14734,16147,16785}`;
- `|Y_C|=11`, `alpha(Y_C)=4`;
- it contains an induced `C5`, e.g. on `2379,14040,14335,14727,16147`.

This is the first genuinely Shannon-active support graph found: pair/triple support graphs were all perfect.

All `68*69/2 = 2,346` unordered products of the 68 connected nonperfect four-owner types were solved exactly as binary MIS instances after deleting the 16 core cells. Four local worker processes were used. Every solver returned an optimal integer solution with zero MIP gap.

Exact optimum histogram:

| product alpha | unordered type pairs |
|---:|---:|
| 11 | 225 |
| 12 | 282 |
| 13 | 863 |
| 14 | 682 |
| 15 | 159 |
| 16 | 135 |

There is **no alpha-17 product**. The best products only tie the 16 deleted core cells.

One best pair is

- `C1 = {314,1741,2380,14040}`;
- `C2 = {1644,9177,13600,13692}`;
- product graph: 138 unlocked vertices, 2,891 conflict edges;
- exact MIS optimum: 16.

This closes nonperfect-connected-type `4 x 4` products only. It does not by itself classify every disconnected four-owner support graph or every higher-order nonrectangular core deletion.

## Current search principle

Pure replacement count is no longer the right objective. The ten-dimensional score directly pays for

1. deleted core owners/cells, and
2. peripheral losses forced by private-pair killers.

The active formulation is therefore prize-collecting: maximize effective replacement value after owner and killer costs, and promote only positive-net candidates to the full ten-dimensional peripheral compatibility stage. This avoids spending compute merely enlarging an excluded radius or product family whose raw local alpha never translates into a better final score.
