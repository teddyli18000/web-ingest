# First obstruction to the low-support owner-clique injection: support 3

Status: **structural frontier, not a score breakthrough**.

Pinned geometry: Tandon/BPZ commit `c753408492dde92a239708986d16c15dbf6c3235`, with the 359-point core factor `B`.

## Context

All outside factors with nonempty support `S(z)=N[z]∩B` of size at most two admit an owner assignment `f(z)∈S(z)` whose owner fibers are cliques.  The resulting product injection closes every outside×outside construction in which both factor supports have size at most two at nonpositive raw core gain; see `outside-outside-support2-closure.md`.

The natural next question is whether the same assignment exists for all factors with support size at most three.

## Exact list-SAT result

GitHub Actions run **`41046652519`**, job **`124032265004`**, completed successfully using `code/bpz_low_support3_owner_clique_sat.py` and Glucose4.

Exact factor census:

- support size 1: **50** factors;
- support size 2: **375** factors;
- support size 3: **1,581** factors;
- total: **2,006** factors.

SAT model:

- assignment variables: **5,543**;
- selector variables: **2,006**;
- clauses: **28,785**;
- owner-conflict clauses: **21,661**;
- owner-pair checks: **48,567**.

Result: **UNSAT** when all 2,006 factor selectors are assumed true.

The solver returned an assumption core of **64 factors**.

## Independently minimized obstruction

An independent exact finite-domain replay of the returned core removes one redundant factor, `z=13015` with singleton support `{12672}`.  The remaining **63 factors** are inclusion-minimal under single-factor deletion: deleting any one of them makes the owner-clique assignment feasible.

Composition of the 63-factor obstruction:

- 9 singleton-support factors;
- 18 support-two factors;
- 36 support-three factors;
- 59 distinct core owners occur in their supports.

The exact 63-factor list is frozen in `code/bpz_support3_core_product_prize.py`.

## Stronger diagnostic: no branching is needed

The 63-factor obstruction is not a difficult SAT artifact.  Unit propagation from the nine singleton-support factors forces assignments through the entire obstruction.  It assigns 62 factors and finally empties the domain of

- `z=1620`, support `{1577,2053,4014}`.

The final three exclusions are forced by the propagated assignments of factors `z=1528`, `z=2046`, and `z=3965` to owners `1577`, `2053`, and `4014`, respectively.  Thus support size three is the first layer where the simple product-injection mechanism genuinely fails.

## What this does and does not prove

UNSAT of the owner assignment does **not** imply a positive ten-dimensional construction.  It only proves that the support≤2 injection argument cannot extend globally to support≤3.

The immediate exact experiment is therefore the real prize problem on the obstruction itself: optimize all `63×63=3,969` outside×outside factor pairs against complete `B×B` and terminal-periphery deletion costs, including all new-new strong-product conflicts.  `code/bpz_support3_core_product_prize.py` implements this calculation over all 18 BPZ terminal scenarios; workflow `temp-science-boundary-c7-support3-core-product.yml` materializes and verifies any positive-gain result.
