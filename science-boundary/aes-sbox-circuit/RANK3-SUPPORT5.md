# Rank-3 five-injection correction search

## Why this exists

The retained-18-gate-core semilinear/plane family has fixed nonlinear cost 65 gates. A 101-gate construction therefore needs

```text
prelinear + middle_support + output_transpose <= 36.
```

`search_semilinear_exactcorr.py` covers full-column-rank correction supports through size four. `search_semilinear_support5.py` covers all 117 five-position supports whose fixed middle columns have rank four. Exactly nine five-position supports have rank three and were the remaining explicit five-injection gap:

```text
(0,1,2,6,7)
(0,1,3,4,7)
(0,1,5,7,8)
(0,2,3,4,5)
(0,3,4,6,8)
(1,2,3,6,8)
(1,2,4,5,6)
(2,4,5,7,8)
(3,5,6,7,8)
```

## Exact parameterization

For any consistent rank-3 support, the five correction byte masks form an affine two-byte family

```text
f_i(z,w) = base_i XOR alpha_i*z XOR beta_i*w.
```

The two free bytes encode the two-dimensional kernel independently in each of the eight AES input-bit coefficients. Naively this is 65,536 assignments for every support and orientation.

## Complete event reduction

With support fixed at five, a 101 candidate must satisfy

```text
prelinear + output_transpose <= 31.
```

After exact output synthesis, let `R` be the number of additional distinct non-input target masks that the remaining prelinear gate budget could possibly accommodate beyond the base plane-operand target set. If the five correction values use at most `R` new masks, then unless the number of distinct symbolic `f_i` expressions is already at most `R`, at least one of these events must occur:

1. some `f_i` equals an already-free mask (an AES input or existing base operand target), or
2. two non-identical `f_i,f_j` are equal.

Every such event is one byte equation of the form

```text
z = K,
w = K,
or z XOR w = K.
```

`search_semilinear_support5_rank3.py` enumerates the union of these one-equation families, each with only 256 points, deduplicates them, applies the exact distinct-new-target test, and finally calls the same exact XOR/XNOR synthesis used by the other semilinear searches. In the rare case where symbolic duplicates alone make every assignment target-count-admissible, it explicitly falls back to all 65,536 pairs.

Therefore the reduction is complete for rank-3 five-position correction supports; it is not a heuristic sample of `(z,w)`.

## Independent completeness check

Before launching the Action, the event generator was reimplemented independently and checked against brute-force enumeration of all 65,536 `(z,w)` pairs on random synthetic instances:

- all 9 physical rank-3 supports;
- 3 random base/free-mask instances per support;
- `max_new = 0,1,2,3,4`;
- 135 cases total.

For every case, every brute-force target-count-feasible pair was present in the event-generated candidate set. No misses occurred.

## Running campaign

Workflow: `.github/workflows/temp-aes-semilinear-support5-rank3.yml`

Action run: `40639348464`

The matrix covers four important representations, each split over the nine first-two-plane prefixes:

```text
identity: c=0x01, k=0
live 102: c=0x1b, k=4
class B:  c=0x9d, k=3
class C:  c=0x5b, k=3
```

Each positive component candidate still needs to be materialized into a full certificate and pass independent 256-byte AES arithmetic verification plus the unchanged Few Shots verifier before it can count as a result.
