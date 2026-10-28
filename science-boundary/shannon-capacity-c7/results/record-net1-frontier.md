# C7^10 134753 record-set unrestricted net-+1 frontier

Status: active, 2026-10-28 (America/Los_Angeles).

This file tracks exact unrestricted exchange searches starting from verifier-accepted 134753-point independent sets in `C7^10`. These statements are local to the named seeds/search radii and are not a proof that `alpha(C7^10)=134753`.

## Few Shots public baseline

The public baseline certificate is independently accepted by the Few Shots p004 verifier with score 134753 and canonical hash

`650b05567deb26a339a788674dce5a36cba3beaeafe2c6daae631bed481b0df8`.

### Complete net-+1 radius <= 4

Action run `40731638977` (fixed replay) first verified the baseline, applied the byte-asserted compile-only patch in `code/patch_search_net1_r4_compile.py`, and executed `search_net1_r4_complete.cpp`.

Exact result:

```json
{"kind":"none","method":"exact-unrestricted-net1-r4-complete","baseline_size":134753,"coverage0":0,"coverage1":5178,"coverage2":144861,"coverage3":999144,"coverage4":2131704,"support2_groups":136379,"support3_groups":966479,"support4_groups":2076092,"owner4_checked":10395299,"eligible_owner4":326642,"max_supported_pool":15}
```

Therefore the actual 134753 baseline has no unrestricted exchange of the forms add1, remove1/add2, remove2/add3, remove3/add4, or remove4/add5. This complete owner-set formulation supersedes the older local radius-3/radius-4 searches whose group-generation completeness required additional care.

### Complete net-+1 radius 5

Action run `40732036984`, job `122970615870`, independently replayed the verified baseline and the complete radius<=4 negative result, then exactly decomposed all five-owner blocker unions into direct support-size-5 and connected lower-support strata. Both stages returned `kind=none`; no candidate was emitted and the Few Shots breakthrough verifier was skipped.

Direct support-size-5 result:

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-direct-c5","baseline_size":134753,"coverage0":0,"coverage1":5178,"coverage2":144861,"coverage3":999144,"coverage4":2131704,"coverage5":2550704,"coverage2_groups":136379,"coverage3_groups":966479,"coverage4_groups":2076092,"coverage5_groups_checked":2479863,"eligible_groups":142936,"max_supported_pool":20}
```

Connected lower-support result:

```json
{"kind":"none","method":"exact-unrestricted-net1-r5-connected-lower-support","baseline_size":134753,"coverage0":0,"coverage1":5178,"coverage2":144861,"coverage3":999144,"coverage4":2131704,"coverage2_groups":136379,"coverage3_groups":966479,"coverage4_groups":2076092,"generated_calls":223560050,"unique_owner5_checked":102738766,"eligible_owner5":3518156,"max_supported_pool":20}
```

Hence the public 134753 record has no unrestricted remove5/add6 net-+1 exchange.

### Radius-6 consequences and direct support-size-6 stratum

The complete radius<=5 negative results imply, for every owner subset `U` of size at most five, `alpha(P(U)) <= |U|`, where `P(U)` is the complete outside-vertex pool whose blocker support is contained in `U`. Therefore any seven-addition/six-owner improving witness must have a connected selected-support hypergraph. Its Hall-type necessary incidence bounds are:

- every owner is hit by at least 2 of the 7 additions (`7-alpha(P(5 owners)) >= 2`);
- every owner pair is hit by at least 3 additions (`7-alpha(P(4 owners)) >= 3`);
- every owner triple is hit by at least 4 additions (`7-alpha(P(3 owners)) >= 4`).

These thresholds differ from the older 134752 net-+2 radius-6 thresholds; lower-support solvers must be retargeted with these exact bounds rather than mechanically changing the target size.

Action run `40732621578`, job `122972665863`, independently verified the baseline and exactly checked every six-owner set occurring as an exact blocker support, reconstructing the full candidate pool from all nonempty support subsets. Target size was seven additions, so any witness would give remove6/add7 and score 134754.

Exact result:

```json
{"kind":"none","method":"exact-unrestricted-net1-r6-direct-support","baseline_size":134753,"coverage0":0,"lower_candidates":5831591,"coverage6_candidates":3197204,"lower_support_groups":5663965,"coverage6_groups":3003919,"eligible_owner6":262690,"tested_owner6":262690,"max_supported_pool":26}
```

Thus the entire radius-6 stratum containing at least one selected outside vertex with exact blocker-support size 6 is negative. The Few Shots breakthrough verifier was skipped because no candidate was produced.

Because radius 5 is now completely negative, a radius-6 witness containing a selected support-size-5 addition can be generated completely by anchoring that five-owner support and attaching the sixth owner through a real co-owner support: if the sixth owner occurred in only one selected addition, the remaining six additions would contradict radius-5 negativity; two singleton occurrences are impossible because one-owner pools have independence number at most one. Workflow run `40733537920` tests this c5-anchor stratum with target seven. It is active at the time of this update.

A separate support-size-7 direct search for radius 7 is also active in run `40733405252`. It is independent of the unfinished lower-support radius-6 closure.

## Other verified 134753 basins

Two distinct boundary seeds are being tested with the same complete net-+1 radius-5 formulation:

- BPZ/Tan `J+`, workflow run `40732173031`; its fixed replay has verified the 134753 seed and completed a negative radius<=4 search, while radius-5 lower-support search is active.
- neutral2 exact rank-3 MaxSAT tie, workflow run `40732339131`; the seed has been deterministically rebuilt with RC2 and independently Few Shots-verified, and its radius<=4/radius-5 chain is active.

A separate nonlocal experiment, workflow run `40732491924`, runs traced guided 1/2-swap plateau walks from both `J+` and the neutral2 rank-3 tie and then solves exact MaxSAT over all visited additions. This changes basin rather than merely increasing a fixed exchange radius.
