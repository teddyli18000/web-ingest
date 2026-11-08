# Constructive p003 handoff — rooted interface and exact defect search (2026-11-08)

## Objective and verified status

The only success criterion for a new Few Shots result is a **36-vertex graph with zero K4 and zero independent 6-sets**, independently recounted and then accepted by Few Shots' official verifier. No such witness has been found in this campaign. The current retained 36-vertex near miss remains \`results/algorithm22-calibration-best-14.json\`, with exactly **10 K4 + 4 I6 = 14** violations.

Public bound remains \`36 <= R(4,6) <= 40\`. Source: Radziszowski (2026), Exoo (2012), McKay (37 public 35-vertex graph6 examples). The objective is construction, not another class exclusion.

## Why previous "mutable halves" did not generate an improvement

Corrected Glucose4 2026-11-08 job [42457396915](https://github.com/teddyli18000/web-ingest/actions/runs/42457396915): five shards returned UNKNOWN after controlled budgets. Four 36-point tests generated around 28–31 SAT models and ~10,500–11,000 lazy Ramsey clauses, but none produced an UNSAT assumption core and **all 306 originally frozen internal edges remained fixed**. The hidden-answer 35-point control also failed to reconstruct the known graph in that budget.

A genuinely proactive update [42499813332](https://github.com/teddyli18000/web-ingest/actions/runs/42499813332) then **released** 35–60 internal edges based on the active K4/I6 witnesses, demonstrating that the intended mutation mechanism now runs. Its hidden 35-point control improved its imperfect score from 209 to 139 violations, and the 36-point arms did not improve the incumbent 14 (all are still UNKNOWN). This is a failure of its *ability to construct high-quality graphs* within the budget, not a mathematical exclusion.

## New first-principles rooted interface

For a vertex v of a (4,6,n) graph, \`A=N(v)\` must be triangle-free with no independent 6-set; \`B=V\(N[v]\` must have no K4 and no independent 5-set. Therefore choose valid A and B **as coherent root-neighborhood pieces**, rather than arbitrary disjoint 18-vertex cores, and jointly synthesize the A–B edges.

An exact exhaustive recount of the 14-defect elite reveals an unusually favorable root:

- **Root v=3 (zero-indexed)** has degree 13, with |A|=13 and |B|=22.
- Neither A nor B contains a forbidden K4 or I6. A has no triangle, B has no independent 5-set. No forbidden subset contains v.
- **All 14 existing forbidden subsets cross the A/B partition**. Thus changing the 13×22=286 cross edges *alone* could, if a compatible solution exists, fix the near miss without disturbing either valid interior.
- Other roots with useful small conflict incidence: v=6,7,15,17,30,33. Their rooted interiors require occasional coupled changes, so treating v=3 as the only possible decomposition would unduly restrict search.

### Implementations and experiments

1. \`rooted_fusion35_36.py\` generates root-aware A/B pairs from published Exoo 35-point graphs (\`control35\` and \`fusion36\`) or the 14-defect elite (\`near14\`), encodes every potentially forbidden mixed configuration statically, and imposes proven degree bounds. The initial \`CardEnc\` implementation mistakenly *reset* its auxiliary-variable high-water mark when a trivial cardinality encoding returned no auxiliary variables, making its "UNSAT" outputs invalid. Fixed in commit \`db5c53d\` via \`top=max(top,cnf.nv)\`. A separate known-answer assumption test now uses original actual 35-point cross edges, and **both degree-14 and degree-15 positive controls passed SAT** in [42501506877](https://github.com/teddyli18000/web-ingest/actions/runs/42501506877). This validates the CNF; hidden-answer reconstruction remains a harder performance check.
2. A direct fixed-root v=3 full 286-edge SAT solve [42501027390](https://github.com/teddyli18000/web-ingest/actions/runs/42501027390) ended UNKNOWN after 392 seconds. This is not UNSAT. Fixed-root independent-parent sweep: [42500747324](https://github.com/teddyli18000/web-ingest/actions/runs/42500747324); note the hidden 35-point controls did not finish in their 170-second budget.
3. \`rooted_mutable_static.py\` keeps v's incidence fixed and jointly changes **all cross edges plus 0,12,22,35, or 54 selected A/B internal edges**, with *all* 4/6-set constraints materialized up front and the entire 36-vertex degree limits. Unlike the lazy half solver, this SAT formulation can correct both interiors simultaneously. Six-way run [42501283478](https://github.com/teddyli18000/web-ingest/actions/runs/42501283478); as of this note, the first four configurations (0,12,22,35 released interior edges) ended UNKNOWN after ~300 seconds each, with no witness.
4. \`rooted_mutable_static.py\` supports other root partitions (6,7,15,17,30,33). Multi-root, partially mutable search [42501739284](https://github.com/teddyli18000/web-ingest/actions/runs/42501739284), for distinct high-quality search basins rather than repeatedly scaling root=3.
5. \`rooted_maxsat.py\` uses **weighted partial MaxSAT** to minimize the *exact total number of forbidden K4/I6 subsets*, instead of demanding a zero-defect SAT witness immediately. Its unchanged near miss has cost **14** by an independent clause-based recount, so any candidate of cost below 14 is a genuine measurable improvement if independent full-bitset recount agrees. Run [42502080443](https://github.com/teddyli18000/web-ingest/actions/runs/42502080443). Cases with 0,12,22 interior edges released; all A/B cross edges are variables. Unlike exclusion-oriented attempts, prioritize improving candidate quality over proving a nonexistence range.

## Integrity

- \`CardEnc\` auxiliary IDs must be globally monotone across both substantive and trivial encodings.
- Never treat a green workflow, an SAT solver timeout, an UNSAT result for one fixed-parent pair, or a valid **35-point** positive control as a new Ramsey record.
- Independent construction candidate verification: regenerate all adjacency rows; assert 36x36 symmetric loop-free; bitset recursively count all K4 and I6 (both zero is required); then use \`few-shots/problems/p003-ramsey-r46/verify/verify.py\` and submit per Few Shots instructions.
- If the current rooted families produce only UNKNOWN or cost >= 14, **reassess representation**, especially whether the fixed root incidence and exact inner structure prevent qualitative candidates. Do not mechanically scale the same masks.

## References

- Exoo (2012), *On the Ramsey Number R(4,6)*, https://doi.org/10.37236/2102
- McKay, 37 published R(4,6,35) graph6 graphs: https://users.cecs.anu.edu.au/~bdm/data/r46_35some.g6
- Radziszowski (2026), *Small Ramsey Numbers*: https://www.cs.rit.edu/~spr/ElJC/sur.pdf
