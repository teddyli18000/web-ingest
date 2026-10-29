# Hall exchange below the BPZ terminal-code abstraction

Status: active research formulation. No verified score above 134,753 is claimed here.

## Motivation

The exact binary BPZ terminal-code sweep reaches 134,753 and no more. That sweep works only with the seven family cardinalities `(B,N,A,D,O,H,V)` and therefore treats an omitted terminal word as an all-or-nothing product block.

At the actual ten-dimensional vertex level, an omitted product block can conflict with only part of the 134,753-point record. This suggests optimizing the real blocker incidence rather than the terminal separation abstraction.

For the BPZ base gadget the seven families have sizes

- `B=359`, `N=322`, `A=19`, `D=26`, `O=H=V=8`,

and the 134,753-point record is the disjoint union

`BB, NO, AH, DV, ON, HD, VA`.

The reusable implementation is `code/bpz_terminal_single_block_hall.py`.

## Single omitted block: an arbitrary-radius exact theorem

Fix one omitted terminal word `uv`. Let

- `C_uv = (F_u x F_v) \ I` be the product-block vertices outside the current record `I`;
- `B = I` be the record vertices;
- connect `c in C_uv` to `b in B` exactly when `c` conflicts with `b` in `C7^10`.

The script explicitly checks that every five-dimensional family `F_u` is independent. Therefore every product block `F_u x F_v` is independent as well.

For any selected `A subseteq C_uv`, the cheapest possible repair is to delete exactly its blocker neighborhood `N(A) subseteq B`. The score change is

`Delta(A) = |A| - |N(A)|`.

By Hall's deficiency theorem,

`max_A (|A|-|N(A)|) = |C_uv| - nu(H_uv)`,

where `nu(H_uv)` is the size of a maximum matching in the candidate-to-blocker bipartite graph.

Consequences:

1. If the matching fails to saturate `C_uv`, one maximum-matching computation produces an arbitrary-radius positive exchange. Alternating reachability from unmatched candidate vertices gives an explicit Hall-deficient witness and therefore a materializable Few Shots certificate.
2. If the matching saturates `C_uv`, then **no exchange of any deletion radius using additions only from this omitted product block can improve the record**. This is much stronger than testing radii 1,2,... separately.

The current workflow `temp-science-boundary-c7-terminal-single-block-hall.yml` applies this test to all 42 omitted terminal words and invokes the upstream Few Shots verifier if any deficiency is positive.

## Tight sets when a block is Hall-saturated

Suppose a block has a matching `M` saturating all candidate vertices. A nonempty set `A` is *tight* when

`|A| = |N(A)|`.

Such a set gives an equal-score exchange by replacing `N(A)` with `A`.

For a fixed saturating matching, form a directed graph on candidate vertices plus a sink:

- for candidate `x` and every blocker `b in N(x)` that is matched to candidate `y=M^{-1}(b)`, add `x -> y`;
- if `b` is unmatched, add `x -> sink`.

Then a candidate set `A` is tight iff it is forward-closed in this directed graph and cannot reach the sink. Indeed, `M(A) subseteq N(A)` always; forward closure and absence of an unmatched blocker force `N(A) subseteq M(A)`, hence equality.

This gives a compact representation of neutral boundary moves. Terminal strongly connected components that do not point toward the sink are minimal tight pieces; forward closures of vertices in the sink-free region give larger tight pieces containing prescribed matched blockers.

## Two omitted blocks: the first recombination target

Let `A1` and `A2` be tight sets from two different omitted blocks, and suppose the selected ten-dimensional vertices in `A1 union A2` are pairwise compatible across the two blocks. Their combined score change is

`|A1| + |A2| - |N(A1) union N(A2)|`

`= |N(A1) intersect N(A2)|`.

Therefore:

> Two cross-compatible neutral Hall exchanges that share even one deleted baseline blocker give an immediate net `+1` breakthrough.

This is the natural next search if all 42 single-block matchings saturate. It exploits information that neither local radius search nor the aggregate terminal-code profile sees.

A practical first pass should:

1. compute one left-saturating matching for every Hall-saturated omitted block;
2. extract sink-free SCCs / forward closures and their exact blocker sets;
3. index tight pieces by matched baseline blocker;
4. for pieces from distinct product blocks sharing a blocker, test exact cross-confusability;
5. materialize and upstream-verify any compatible pair.

This neutral-tight recombination is not a complete two-block optimization. In general two-block gain is

`delta_1 + delta_2 + |N(A1) intersect N(A2)|`,

where `delta_i = |A_i|-|N(A_i)| <= 0`; a positive exchange could therefore use individually negative pieces whose blocker overlap overcompensates the deficits. If the neutral-tight slice is negative, the next exact formulation should admit small individual deficits and optimize overlap directly rather than returning to radius-by-radius ambient search.

## Relation to the 2026 heterogeneous recursion

Tandon's heterogeneous Gao theorem changes auxiliary parameters `(s,o,h,v)` but leaves the main-code size `a` equal to the ordinary Gao product formula. Thus applying the theorem once to the same five-dimensional BPZ inputs does not by itself raise the ten-dimensional main code above 134,753. Its value here is conceptual: auxiliary structure matters beyond equal cardinality profiles, which is exactly why the real blocker incidence below the terminal abstraction is worth searching.
