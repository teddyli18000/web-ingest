# Support-3 iterated charge closure

Status: **the repaired charge-separation reduction expands to the entire support<=3 product family; it provides no useful compression. No score above 134,753 is claimed.**

This result follows the audit that invalidated the earlier one-shot residual charge-separation argument. The repair is mechanical: start from the original retained residual, track the exact core-cell support footprint of every retained outside-outside candidate, then repeatedly add every omitted regular product whose assigned support<=2 owner-clique charge cell lies inside the active footprint. Iterate to a fixed point before using the charge injection for anything omitted.

The durable implementation is `code/bpz_support3_iterated_charge_closure.py`. GitHub Actions run `41052051969`, job `124050285954`, completed successfully.

## Exact fixed-point result

Pinned geometry: BPZ/Tan source commit `c753408492dde92a239708986d16c15dbf6c3235`.

- regular support<=2 factors: **425**
- support-3 exceptions: **4** (`6712, 6721, 13936, 13937`)
- factor universe: **429**
- full ordered product candidates: **184,041**
- original exception footprint: **2,300** core cells
- original retained residual: **23,631** candidates

Closure history:

1. first iteration adds **160,852** regular products, reaching **184,039** retained candidates and **6,654** active core cells;
2. second iteration adds the final **2** regular products, reaching all **184,041** candidates;
3. the third iteration is stable.

At the fixed point:

- retained candidates: **184,041 / 184,041**
- retained regular pairs: **180,625**
- omitted regular pairs: **0**
- active core cells: **6,654**

Thus the corrected charge-overlap closure consumes the complete `(425 regular + 4 exceptional)^2` family. There is no nontrivial omitted family left to discharge by the previous owner-clique injection.

## Maximum-closure diagnostic

Ignoring all new-new conflicts, the exact maximum-closure upper problem selects all **184,041** candidates, activates **6,654** core cells, and has raw objective

`184,041 - 6,654 = +177,387`.

This huge positive value is **not** a construction. It shows that new-new compatibility, rather than blocker cost, is the dominant missing constraint once the full support-3 family is admitted.

## Consequence

Do not continue patching the one-shot charge-footprint reduction. Experimentally and exactly, its sound fixed-point repair has zero compression value. The useful next representation must be conflict-aware from the start, preferably exploiting the tensor/product structure of the 429-factor confusion relation rather than explicitly materializing every pairwise conflict clause among 184,041 product candidates.
