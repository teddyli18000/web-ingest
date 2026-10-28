# C7^10 134753 record-set unrestricted net-+1 frontier

Status: active, 2026-10-28 (America/Los_Angeles).

This file tracks exact unrestricted exchange searches starting from verifier-accepted 134753-point independent sets in `C7^10`.  These statements are local to the named seeds/search radii and are not a proof that `alpha(C7^10)=134753`.

## Few Shots public baseline

The public baseline certificate is independently accepted by the Few Shots p004 verifier with score 134753 and canonical hash

`650b05567deb26a339a788674dce5a36cba3beaeafe2c6daae631bed481b0df8`.

### Complete net-+1 radius <= 4

Action run `40731638977` (fixed replay) first verified the baseline, applied the byte-asserted compile-only patch in `code/patch_search_net1_r4_compile.py`, and executed `search_net1_r4_complete.cpp`.

Exact result:

```json
{"kind":"none","method":"exact-unrestricted-net1-r4-complete","baseline_size":134753,"coverage0":0,"coverage1":5178,"coverage2":144861,"coverage3":999144,"coverage4":2131704,"support2_groups":136379,"support3_groups":966479,"support4_groups":2076092,"owner4_checked":10395299,"eligible_owner4":326642,"max_supported_pool":15}
```

Therefore the actual 134753 baseline has no unrestricted exchange of the forms add1, remove1/add2, remove2/add3, remove3/add4, or remove4/add5.  This complete owner-set formulation supersedes the older local radius-3/radius-4 searches whose group-generation completeness required additional care.

### Net-+1 radius 5

The complete radius-5 decomposition consists of exact support-size-5 owner sets plus connected lower-support owner sets, with target independent set size 6 inside a five-owner blocker union.  The fixed workflow is run `40732036984`.  At the time of this update:

- baseline verification: complete;
- complete radius <=4 replay: complete and negative;
- radius-5 direct coverage-5 stratum: complete;
- radius-5 connected lower-support stratum: still running.

Do not promote radius 5 to a negative result until the latter step finishes successfully and no candidate is emitted.

### Radius-6 direct support-size-6 stratum

Action run `40732621578`, job `122972665863`, independently verified the baseline and exactly checked every six-owner set occurring as an exact blocker support, reconstructing the full candidate pool from all nonempty support subsets.  Target size was seven additions, so any witness would give remove6/add7 and score 134754.

Exact result:

```json
{"kind":"none","method":"exact-unrestricted-net1-r6-direct-support","baseline_size":134753,"coverage0":0,"lower_candidates":5831591,"coverage6_candidates":3197204,"lower_support_groups":5663965,"coverage6_groups":3003919,"eligible_owner6":262690,"tested_owner6":262690,"max_supported_pool":26}
```

Thus the entire net-+1 radius-6 stratum containing at least one selected outside vertex with exact blocker-support size 6 is negative.  The Few Shots breakthrough verifier was skipped because no candidate was produced.

The remaining radius-6 lower-support strata must not be called complete yet.  Once radius 5 is fully negative, support-hypergraph connectivity can be used to close them without enumerating arbitrary owner six-tuples.

## Other verified 134753 basins

Two distinct boundary seeds are being tested with the same complete net-+1 radius-5 formulation:

- BPZ/Tan `J+`, workflow run `40732173031`; its fixed replay has already verified the 134753 seed and completed a negative radius<=4 search, while radius-5 lower-support search is active.
- neutral2 exact rank-3 MaxSAT tie, workflow run `40732339131`; the seed has been deterministically rebuilt with RC2 and independently Few Shots-verified, and its radius<=4/radius-5 chain is active.

A separate nonlocal experiment, workflow run `40732491924`, runs traced guided 1/2-swap plateau walks from both `J+` and the neutral2 rank-3 tie and then solves exact MaxSAT over all visited additions.  This changes basin rather than merely increasing a fixed exchange radius.
