# U2 private-pair orientability bound

Status as of 2026-10-27 (America/Los_Angeles).

The frozen U2-derived `C7^5` independent set in `results/u2-t11-parent.json` has 367 points and 11 distinct genuine private owner/neighbor pairs.  However, the BPZ/Gao construction needs more than distinct private owners: after choosing one endpoint of every selected pair for `P^H` and the opposite endpoint for `P^V`, both endpoint sets must themselves be independent in `C7^5`.

An exact enumeration over every subset of the 11 frozen private pairs and every binary orientation gives:

- size 11: 0 valid orientations across 0 orientable subsets;
- size 10: 0 valid orientations across 0 orientable subsets;
- size 9: 0 valid orientations across 0 orientable subsets;
- size 8: 384 valid orientations across 15 orientable subsets.

Therefore the maximum simultaneously orientable subset of these 11 private pairs has size exactly 8.  In particular this frozen U2 state cannot instantiate a new `t=9`, `t=10`, or `t=11` BPZ/Gao witness, despite having 11 distinct private owners.

This explains the earlier `u2_t11_translation_scan.py` run: it failed before any FFT work because all `2^11=2048` full orientations violate independence of `P^H` or `P^V`.  That workflow failure was an implementation-visible manifestation of a genuine structural obstruction, not evidence about auxiliary-set intersections.

For any future private-owner search, the objective should therefore track **maximum orientable private-pair subset size**, not only the count of private owners.
