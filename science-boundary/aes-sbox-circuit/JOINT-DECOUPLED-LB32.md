# Joint-decoupled LB32 exact exclusion

Date: 2026-10-29 (+08:00)

## Scope

This note extends the retained-18-core joint-decoupled front/final product-plane search to all five exact semilinear orbit representatives whose original cheap lower bound is 32:

```text
D: (c,k) = (0x30,3)
E: (c,k) = (0x0d,0)
F: (c,k) = (0x5e,0)
G: (c,k) = (0x65,3)
H: (c,k) = (0x33,2)
```

The exact six-element semilinear orbit theorem already proved in this workspace transports any representative result to all 30 LB32 transforms.

The search is broader than the original same-orientation semilinear family: the nine norm-product orientations used before the inversion core and the nine final-product/output orientations are allowed to differ independently. The prelinear network must contain the union of both operand sets.

## Complete helper-aware frontiers

`screen_joint_decoupled_instance.cpp` was run locally on each transported instance. It exhausts the implicit `3^18` front/final orientation pairs after precomputing the `4^9` prelinear-union states and `3^9` output states, using exact zero-helper / one-helper closure lower bounds.

All five representatives have an especially narrow frontier: every surviving pair has score exactly 36 and **distance zero** (`front=final`). No strictly decoupled pair reaches the 36-gate variable budget after the helper-aware screen.

```text
D: pass0=45,708  helper_frontier=18
   score 36:18, middle support 3:18, distance 0:18

E: pass0=51,792  helper_frontier=27
   score 36:27, middle support 3:27, distance 0:27

F: pass0=58,476  helper_frontier=22
   score 36:22, middle support 3:20 / support 4:2, distance 0:22

G: pass0=66,070  helper_frontier=77
   score 36:77, middle support 3:77, distance 0:77

H: pass0=66,484  helper_frontier=62
   score 36:62, middle support 3:62, distance 0:62
```

Total exact frontier: **206 score-36 rows**.

## Exact final screen

`prove_joint_decoupled_score36_instance.cpp` consumes a transported instance plus its frontier CSV. For each score-36 row it independently restores the actual middle correction values and checks the only remaining possible budgets exactly:

1. decide whether the output target set really achieves the helper lower bound with at most two helper-only XOR/XNOR gates;
2. enumerate every minimum-support correction position set;
3. require a minimum-support set to have full column rank (otherwise a smaller support spans the same byte RHS, contradicting minimum support);
4. solve its correction bytes uniquely and add every non-input correction value to the prelinear target set;
5. decide the remaining prelinear budget exactly with at most two helper-only gates.

Local exact results:

```text
D: rows=18, systems=0
   output_killed=18, target_killed=0, pre_killed=0, candidates=0
   exact output cost 16 on all 18 rows

E: rows=27, systems=0
   output_killed=27, target_killed=0, pre_killed=0, candidates=0
   exact output cost 17 on all 27 rows

F: rows=22, systems=162
   output_killed=20, target_killed=162, pre_killed=0, candidates=0
   exact output costs: 14 on 2 rows, 16 on 20 rows
   supports: 3 on 20 rows, 4 on 2 rows

G: rows=77, systems=0
   output_killed=77, target_killed=0, pre_killed=0, candidates=0
   exact output cost 17 on all 77 rows

H: rows=62, systems=0
   output_killed=62, target_killed=0, pre_killed=0, candidates=0
   exact output cost 17 on all 62 rows
```

There were **zero** rank-deficient minimum-support systems, **zero** cases requiring more than two unresolved helpers, and **zero** candidate witnesses.

For D/E/G/H the one-helper lower bound on the output network is not physically attained within the 36-gate total budget; every row dies immediately after the exact output-cost check. F has two rows whose output network does attain cost 14, but all 162 exact minimum-support correction systems make the prelinear target count alone exceed the remaining budget.

## Independent local cross-check

A separately written Python implementation repeated the complete 206-row final screen without reusing the C++ checker. It independently implemented target closure, exact enumeration of up to two helper-only gates, middle-column rank/unique correction solving, and target accounting.

It reproduced every C++ statistic exactly:

```text
D: output_killed 18, systems 0, candidates 0
E: output_killed 27, systems 0, candidates 0
F: output_killed 20, systems 162, target_killed 162, candidates 0
G: output_killed 77, systems 0, candidates 0
H: output_killed 62, systems 0, candidates 0
```

The independent Python run completed in about 11 seconds locally.

## Consequence

All five LB32 exact orbit representatives are excluded from a 101-gate retained-18-core circuit even in the broader joint-decoupled front/final product-plane family. By the already proved exact six-element semilinear orbit equivalence, the result transports to **all 30 LB32 transforms**.

Therefore the retained-core semilinear frontier can move past LB32. The next cheap tier is LB33, containing 24 transforms / **4 exact six-element orbits**.

This does not exclude constructions that change the 18-gate inversion core or the middle/core interface. The direct fixed-interface six-independent-AND rank-six family remains a separate unresolved route.
