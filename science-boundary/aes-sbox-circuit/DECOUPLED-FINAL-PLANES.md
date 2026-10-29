# Decoupled final-product plane orientations

## Question

The merged 102-gate circuit uses the same basis choice for each of nine two-dimensional prelinear pairs in two places:

1. the first nine norm ANDs, and
2. the final eighteen ANDs, where each pair is multiplied by one common inversion-core factor.

The established plane-orientation search couples the two uses. This note asks whether the final-product basis can be changed independently while leaving the live first-product basis and its five middle injections fixed.

For one pair `(a,b)` the three bases are

```text
0: (a,b)
1: (a,a+b)
2: (a+b,b)
```

If the final choice differs from the first choice, the prelinear layer must expose the union of the required forms, potentially all of `{a,b,a+b}`. The final AND count remains two for that pair. Applying the corresponding dual transform to the pair of output-map columns preserves the same linear output function.

Thus this is a valid circuit family, not a heuristic rewrite.

## Exact accounting

Fix the merged-102 field transform and first-product orientation, i.e. local orientation `0^9` in the workspace convention. Keep the five merged-102 middle injection values unchanged.

For each independent final choice `f in {0,1,2}^9`:

- prelinear targets are the union of the fixed first-product operands, the fixed five middle-correction values, and the final-product operands selected by `f`;
- the output transpose target columns use the dual basis selected by `f`;
- both linear networks are synthesized exactly with the helper-closure algorithm from `search_plane_prelinear17.py` / `search_semilinear_outer.py`.

The nonlinear and transposition-overhead terms remain fixed, so

```text
size = 65 + prelinear + 5 + output_transpose
     = 70 + prelinear + output_transpose.
```

A 101-gate candidate therefore requires

```text
prelinear + output_transpose <= 31.
```

`search_decoupled_final_planes.py` implements this exact search in nine `3^7` shards and contains a regression assertion that `f=0^9` reproduces the merged record:

```text
prelinear = 18
output_transpose = 14
size = 102.
```

## Local exact result

A separate local reproduction of the same helper-closure calculation exhaustively scanned all `3^9 = 19,683` final choices.

At the 101 budget (`pre+out <= 31`):

```text
target-count pruned:       19,656
output exact infeasible:       26
prelinear exact infeasible:     1
hits:                           0
```

At the 102 budget (`pre+out <= 32`):

```text
target-count pruned:       19,512
output exact infeasible:      168
prelinear exact infeasible:     2
hits:                           1
```

The unique hit is exactly

```text
final orientations = [0,0,0,0,0,0,0,0,0]
prelinear = 18
output_transpose = 14
```

So within this decoupled-final-only family the merged 102 circuit is the unique optimum at <=102, and no 101 circuit exists.

The raw distinct-target lower-bound distribution for `prelinear targets + output targets` across all final choices is:

```text
30:    2
31:   25
32:  144
33:  514
34: 1286
35: 2403
36: 3468
37: 3930
38: 3510
39: 2449
40: 1304
41:  504
42:  128
43:   16
```

The two nominal target-count-30 choices still fail the exact helper-aware 101 budget, illustrating why target counts alone are insufficient.

## Verification status

The repository Action `.github/workflows/temp-aes-decoupled-final-planes.yml` independently shards the exact search and validates the merged-102 regression in every job. At the time this note was written its first run (`40797864596`) was queued under repository-wide runner pressure. Do not upgrade the Action result to an independent verification until all nine jobs complete and their `summary.json` files are inspected.

## Consequence

Do not spend more compute on changing only the final pair bases while the live first-product orientations and middle injections are fixed; that family is exactly exhausted.

The genuinely broader nearby family is **jointly decoupled front/final orientations**, where first-product choices may change the middle offsets while final-product choices independently change the output dual basis, and the prelinear network is synthesized for the union of both operand sets plus the chosen correction values. That family is `3^18` naively and needs decomposition / meet-in-the-middle rather than direct enumeration.
