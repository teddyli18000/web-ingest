# Constructive p008 checkpoint — 2026-11-10

## Goal and official score
Few Shots p008 board checked November 10: **101 gates** (33 AND + 68 XOR/XNOR), merged PR #31. No verified <=100 witness yet. All reported candidate constructions are independently checked on the entire 256-byte AES S-box.

## Real nonlinear seed and parent diversity
- [make_and_shear_102.py](../make_and_shear_102.py) constructs a valid 102-gate, 33-AND AES S-box with one changed AND truth function (unordered AND truth-set symmetric difference 2) via a bilinear shear.
- [Action 42456579731](https://github.com/teddyli18000/web-ingest/actions/runs/42456579731): double shear yields 661 distinct normalized valid circuits, 38 archived/reverified 104-gate circuits with AND truth-set symmetric difference 4.
- [Action 42456112245](https://github.com/teddyli18000/web-ingest/actions/runs/42456112245): 11 alternate 102-gate factorizations, same shifted AND set.
- [Action 42852732598](https://github.com/teddyli18000/web-ingest/actions/runs/42852732598): four successful care-equivalent cone-evolution jobs, tens of thousands of legal 101/102 variants. Important: all 101-size solutions revert to the **original** AND truth-function set. Audit of every archived circuit: 38 shifted-AND 102, 6 old-AND 101, 4 old-AND 102. Do not confuse reordered AND hashes with novel nonlinear bases.

## Global semantic parent-plus-helper synthesis
- [Action 42456706490](https://github.com/teddyli18000/web-ingest/actions/runs/42456706490): warm-started shifted 102 seed; inherited graph OPTIMAL 102, adding 48/120 new helper candidates yields FEASIBLE 102 but no <=101.
- [Action 42456903568](https://github.com/teddyli18000/web-ingest/actions/runs/42456903568): preserve shifted 33-AND set and optimize complete linear DAG. Zero-helper graph OPTIMAL 102; with 100 helpers FEASIBLE 102, best bound 95 (not a proof).
- [Action 42854598394](https://github.com/teddyli18000/web-ingest/actions/runs/42854598394): recombine 38 verified altered-AND 102 parents and 11 other shifted 102 variants. 61 parents/1289 edges give OPTIMAL 102; +48 or +100 helpers gives FEASIBLE 102 (bounds 96,90). Not globally optimal; only limited inherited graph was certified.

## Constructive anchored large-neighborhood optimization
- [shear_lns_construct.py](../shear_lns_construct.py) and [frontier_lns_construct.py](../frontier_lns_construct.py) freeze most of the known complete 102/101 circuit and jointly optimize two separated cones with novel helpers.
- First [Action 42851818016](https://github.com/teddyli18000/web-ingest/actions/runs/42851818016) FAILED because of a stale-key Python witness reconstruction bug, not due to scientific infeasibility; fixed in commits 0e27a425 and 2329e087.
- Rerun [Action 42852408863](https://github.com/teddyli18000/web-ingest/actions/runs/42852408863): all 3 seeds reproduce valid known 102 SAT controls; tested 772 neighborhoods; 158 new valid 102 topologies; best remains 102.
- [Action 42852415878](https://github.com/teddyli18000/web-ingest/actions/runs/42852415878): all 3 seeds reproduce valid known 101 SAT controls; tested 662 neighborhoods; 132 new valid 101 topologies; best remains 101.
- These are productive full-circuit constructive search engines, but candidate **quality** stayed flat. Do not merely scale same neighborhoods.

## Two-site full-output-cofactor compensation
- [joint_two_retarget_construct.py](../joint_two_retarget_construct.py) allows the first AND/XOR/XNOR root to become arbitrary and temporarily make AES wrong; a different later gate must cooperatively restore all eight outputs. Internal two-site positive control validated.
- Initial [Action 42853442003](https://github.com/teddyli18000/web-ingest/actions/runs/42853442003), expanded [Action 42853790117](https://github.com/teddyli18000/web-ingest/actions/runs/42853790117): eight full jobs over 101/102 seeds, roughly 120k first root rewrites and millions of later repairs. Tens of distinct correct neutral networks but **no fewer gates**. No reason to extend this same two-site search again.

## Independent high-strength XAG optimizer
- The mature [mockturtle](https://github.com/lsils/mockturtle) library supports XAG logic resubstitution and XOR/AND linear extraction. The fresh [mockturtle_aes_probe.cpp](../mockturtle_aes_probe.cpp) feeds FS101, shifted 102 and NIST G103 to independent C++ XAG resynthesis; [mockturtle_xag_bridge.py](../mockturtle_xag_bridge.py) checks optimized XAG truth tables over all 256 input bytes.
- XAG complemented edges represent **free NOT operations**. They are NOT legal Few Shots gates! A phase-constraint legalizer only emits a certificate when all complemented AND fan-ins and outputs can be absorbed into XOR/XNOR choices and the final circuit checks all 256 bytes.
- [Action 42856582213](https://github.com/teddyli18000/web-ingest/actions/runs/42856582213) launched November 10. Inspect actual compiler logs and artifacts before asserting any optimization.

## Continue constructively, not by accumulating exclusions
1. If the independent XAG optimizer yields smaller network candidates, prioritize translating complemented edges to truly legal AND/XOR/XNOR with independent verification and official Few Shots checking.
2. Otherwise, return to the *successful upstream method* described in the merged 101 SHOT.md: joint semilinear input coordinate maps, nine independently oriented product planes, offset injections and total pre/middle/core/final synthesis. Freeing this global architecture coupling can expose structurally different candidate families.
3. Whenever a valid <=100 emerges: freeze full circuit JSON, separately compute the AES 256-byte scalar S-box, run the official p008 verifier, and submit the Few Shots shot/PR.

A successful GitHub Action only establishes an executed experiment; meaningful numerical claims are based on validated output/certificate.
