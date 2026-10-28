# Semilinear lower-bound frontier for p008

## Full 2040-transform scan

For every semilinear AES input transform

```text
P(x) = c * x^(2^k),   c != 0,   k in {0,...,7},
```

`scan_semilinear_frontier.py` exhaustively evaluates all `3^9 = 19,683` product-plane orientations. This is all `255*8 = 2040` semilinear transforms in the searched retained-18-core family.

For each orientation it computes the rigorous lower bound

```text
prelinear non-input target count
+ unrestricted minimum middle correction support
+ output-transpose non-input target count.
```

Action run `40638593824` completed all 32 shards. Aggregation run `40640996806` loaded all 2040 transform records and obtained:

```text
best outer-variable lower bound | transforms | exact six-orbits
31                              | 18         | 3
32                              | 30         | 5
33                              | 24         | 4
34                              | 78         | 13
35                              | 150        | 25
36                              | 234        | 39
37                              | 336        | 56
38                              | 594        | 99
39                              | 576        | 96
--------------------------------+------------+-----------------
total                           | 2040       | 340
```

A retained-18-gate-core 101 construction needs actual outer-variable cost at most 36. Therefore **1506 / 2040 transforms are rigorously excluded** by the cheap lower bound alone; 534 transforms survive, but after the exact symmetry reduction below they represent only **89 independent orbits**.

## Global exact six-element automorphism orbits

The six-member grouping is not merely equality of cheap lower-bound distributions.

`prove_all_semilinear_orbits.py` enumerates the complete automorphism group compatible with both:

- the nine fixed middle columns, and
- the nine factors exposed by the retained 18-gate core.

The group has exactly six elements. Grouping all 2040 semilinear transforms by their transported input/output product-plane sets gives exactly **340 groups of size six**. For every one of the 1700 representative-to-nonrepresentative maps the script verifies:

1. one permutation `sigma` maps all nine input product planes;
2. the same `sigma` maps all nine output product planes;
3. the ternary product-plane orientation choices are bijectively relabeled;
4. an invertible four-bit map `M` sends the nine middle columns according to `sigma`;
5. the live core satisfies `F_{sigma(i)}(M y)=F_i(y)` for all nine factors and all 16 core states;
6. the complete middle correction equation is transported by the same map.

Because the selected prelinear and output target sets are literally preserved under relabeling, arbitrary helper choices and exact XOR/XNOR network costs transport unchanged. Thus one representative is sufficient for every exact retained-core outer search within an orbit.

Independent GitHub Actions run **`40745501728`** completed successfully and reproduced the full `2040 -> 340 x 6` result.

This is specific to the retained-18-core semilinear outer family; it is not a global equivalence statement about arbitrary AES circuits.

## LB=31: three exact orbits

The 18 global-best transforms form three exact six-member orbits.

### Orbit A

```text
(0x01,0), (0xbc,0), (0xbd,0),
(0x1b,4), (0x66,4), (0x7d,4)
```

Representative: identity `(0x01,0)`. This orbit includes the live-102 transform `(0x1b,4)`.

### Orbit B

```text
(0x6b,3), (0x9d,3), (0xf6,3),
(0x13,7), (0xea,7), (0xf9,7)
```

Representative: `(0x9d,3)`.

### Orbit C

```text
(0x5b,3), (0xa9,3), (0xf2,3),
(0x7e,7), (0xb9,7), (0xc7,7)
```

Representative: `(0x5b,3)`.

The earlier dedicated proof `prove_semilinear_class_automorphisms.py` checked all 15 nonrepresentatives against all 19,683 orientations per member; Action run **`40743531094`** independently reproduced it.

## Complete exclusion of middle support >= 6 for LB=31

A retained-core 101 construction with middle support at least six would require

```text
prelinear + output_transpose <= 30.
```

`prove_semilinear_support6_impossible.py` exhausts all 19,683 orientations of the three LB=31 representatives. It uses exact 0-helper and 1-helper linear-network closure; when a target set cannot be synthesized with at most one helper, it has the rigorous lower bound of at least two helpers.

Independent Action run **`40744953469`** completed successfully. It proved:

```text
representative A: min rigorous pre+out lower bound = 31
representative B: min rigorous pre+out lower bound = 32
representative C: min rigorous pre+out lower bound = 32
```

All three have zero orientations with lower bound <=30. Exact orbit equivalence transports this to all 18 LB=31 transforms. Therefore **middle support >=6 is completely excluded from 101 in the LB=31 tier**.

## Support <=5 exact campaigns

For representatives A/B/C the complementary exact middle-correction searches are:

- `search_semilinear_exactcorr.py`: full-column-rank correction supports of size <=4;
- `search_semilinear_support5.py`: all 117 five-position supports whose middle columns have rank four;
- `search_semilinear_support5_rank3.py`: the remaining nine rank-three support-5 sets, with complete two-free-byte event enumeration under the 101 budget.

The rank-3 event reduction was independently checked against full `2^16` `(z,w)` brute force on 135 random synthetic cases with no misses; see `RANK3-SUPPORT5.md`.

Class A/B rank-four support-5 evidence is fully aggregated: Action `40742805378` loaded all 18 historical shard summaries, covering 39,366 prefix orientations, and verified `candidates_101=0` and zero saved witnesses.

Historical runner cancellations left exact-correction gaps in A/B/C and one Class-C rank-three-support-5 shard. Dedicated low-parallel gap workflows are filling exactly those missing pieces. Cancelled jobs are never counted as negative evidence.

Once all support<=5 representative summaries are present and zero-candidate, combining them with the support>=6 theorem and the exact six-orbit equivalence will close the **entire LB=31 retained-core semilinear tier**.

## Next outer tier if LB=31 closes

The LB=32 transforms form exactly **five** six-member exact orbits, not 30 independent searches. Convenient representatives are:

```text
(0x30,3)
(0x0d,0)
(0x5e,0)
(0x65,3)
(0x33,2)
```

Thus the next retained-core frontier after LB=31 is five representative problems.

## Search policy

Do not search all 2040 transforms independently. Work by exact orbit representatives. The 534 cheap-LB survivors are 89 representative orbits; transforms with cheap lower bound >=37 are already excluded from 101 unless the nonlinear core/interface changes.
