# 2026-10-27 neighboring-length transfer experiments

## Question

Can unusually low-energy public sequences at nearby lengths be converted into a better length-100 sequence by insertion/deletion, then serve as a promising basin for local refinement?

All energies below were recomputed from the resulting sequences with the same exact LABS objective used by `code/verify.py`.

## 2025 unrestricted N=99 record -> N=100

Zhang et al. (2025), arXiv:2504.00987, report a new unrestricted `N=99` sequence with energy `553`, encoded in their Table 2 as:

`0CF30C003783CBCC8DA92AAD4`

The last hexadecimal word contains one right-padding zero bit. After removing that pad, the source sequence independently rescored to `553`.

Exhaustively trying both signs in all 100 insertion positions gives best length-100 energy:

`606`

Best transferred sequence in Few Shots `+/-` notation:

`+++++--++----++--++++--++++++++++++--+----+++++----++-+----++--++-+++--+--+-+-++-++-+-+-+-+-+--+-+-+`

This transferred sequence is itself a one-bit local minimum. More strongly, exhaustive enumeration of every Hamming-distance 1 through 5 edit around it found no energy below `606`:

| radius | sequences |
| ---: | ---: |
| 1 | 100 |
| 2 | 4,950 |
| 3 | 161,700 |
| 4 | 3,921,225 |
| 5 | 75,287,520 |
| total | 79,375,495 |

So the excellent `N=99` record does not expose a shallow route to `E<578` after one insertion.

## 2025 unrestricted N=98 record -> N=100

The same paper reports `N=98`, energy `529`, encoded as:

`993A76393CDB4BCF78FF00AA8`

After removing two right-padding bits, it independently rescored to `529`.

Exhaustively inserting two signs over all position/sign choices gives best length-100 energy `642`, with inserted positions 80 and 88 in the enumeration used by `code/cross_length.py`. This is weaker than the N=99 transfer.

## Historical N=101 and N=102 records -> N=100

Knauer's historical table, mirrored in `borkob/git_labs`, gives:

- `N=101`, `E=578`, skew-symmetric. Deleting its best single position yields `E=578`, but the resulting sequence is a symmetry copy of the existing Few Shots incumbent, so it gives no new basin.
- `N=102`, `E=567`. Exhaustively deleting every pair of positions (`C(102,2)=5,151`) gives best length-100 energy only `710`.

For the N=102 source, the best deletion removes positions 0 and 100 (zero-based in `code/cross_length.py`) and gives:

`++-----++++++----++----+++---+-+--+--++-+-+-+++-+-++--++--+++--++-+--+---------+--+-+-++-+-+--+---+-`

## Historical N=103 record -> N=100

The public skew-symmetric `N=103`, `E=555` sequence was also tested. Exhaustive deletion of all three positions (`C(103,3)=176,851`) produced best length-100 energy `714` (deleting the first three positions), again far above the incumbent.

## Interpretation

Low energy at a neighboring length is not preserved well enough by raw insertion/deletion to challenge `E=578` at length 100. The strongest transfer found is `606` from the new 2025 N=99 record, and even that candidate has no better point within Hamming radius 5. Cross-length transfer should not be repeated in this simple form; any future use should combine structural recombination or a substantially stronger basin-crossing optimizer.

## Reproduction

`code/cross_length.py` reproduces the N=98, N=99 and N=102 scans. `code/sphere.cpp` or `code/sphere_shell.cpp` can reproduce exact Hamming-neighborhood checks.

## Sources

- Zhiwei Zhang, Jiayu Shen, Niraj Kumar, Marco Pistoia, *New Improvements in Solving Large LABS Instances Using Massively Parallelizable Memetic Tabu Search*, arXiv:2504.00987: <https://arxiv.org/abs/2504.00987>
- Historical Knauer record table mirrored by `borkob/git_labs`: <https://github.com/borkob/git_labs/blob/master/results-2016/2004-Knauer-original.txt>
