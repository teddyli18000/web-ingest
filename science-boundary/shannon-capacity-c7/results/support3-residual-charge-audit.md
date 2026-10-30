# Audit of the first support-3 residual charge reduction

Status: **the current disjoint-charge justification is invalid as stated**. This is a proof audit, not a score result.

The script `code/bpz_support3_first_mus_residual_prize.py` uses a certified owner-clique assignment `f` on all 425 support-≤2 factors and four support-3 exceptions

`E = {1012, 1025, 1285, 3722}`.

It defines `K` as the set of core cells that can be touched by an exception-containing candidate. A regular×regular candidate `q=(u,v)` is omitted from the explicit residual when its assigned cell

`m(q)=(f(u),f(v))`

lies outside `K`; the intended argument is that such omitted selected candidates can be charged injectively to distinct core cells disjoint from the residual footprint.

## Explicit counterexample to charge separation

An independent local replay of the pinned BPZ geometry and the exact support-≤2 2-SAT assignment finds the following pair immediately.

Omitted regular candidate:

- `q = (222, 278)`;
- `S(222) = {215,229}`, `f(222)=229`;
- `S(278) = {229,3079}`, `f(278)=3079`;
- assigned charge cell `m(q)=(229,3079)`;
- `(229,3079) ∉ K`, so `q` is omitted by the residual rule.

Retained regular candidate:

- `r = (222,3421)`;
- `S(3421) = {3079,3420}`, `f(3421)=3420`;
- assigned cell `m(r)=(229,3420) ∈ K`, so `r` is retained;
- but `r`'s exact core support rectangle is
  `{215,229} × {3079,3420}`,
  which contains the omitted candidate's charge cell `(229,3079)`.

The two 10D candidates are mutually compatible:

- first coordinates are equal (`222`), hence conflict there;
- second coordinates `278` and `3421` are **nonconfusable** in `C7^5`;
- therefore `(222,278)` and `(222,3421)` are independent in the strong product.

Pinned base-7 coordinates (least-significant coordinate first, matching the source encoding):

- `222 = (5,3,4,0,0)`;
- `278 = (5,4,5,0,0)`;
- `3421 = (5,5,6,2,1)`;
- `229 = (5,4,4,0,0)`;
- `3079 = (6,5,6,1,1)`;
- `3420 = (4,5,6,2,1)`.

Thus a retained residual point can activate a core cell used as the assigned charge of a compatible omitted regular point. The omitted charge is therefore **not guaranteed disjoint from residual deletion costs**.

## Consequence

A negative optimum from `bpz_support3_first_mus_residual_prize.py` is still a valid exact optimum of the residual instance it explicitly builds, but it does **not**, by the current argument, close the full `(425+4)×(425+4)` factor family.

Do not promote that residual result to a full-family exclusion unless one of the following is supplied:

1. a stronger charging theorem that handles overlap with retained regular rectangles;
2. an enlarged residual that retains every regular candidate capable of touching an omitted charge cell (iterated to closure if necessary);
3. a direct exact optimization of the complete family.

`code/audit_support3_residual_charge.py` implements the replay/search and is intended for independent Action confirmation.
