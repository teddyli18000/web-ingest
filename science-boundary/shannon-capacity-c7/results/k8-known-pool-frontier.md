# Known-pool k=8 support-defect frontier

Status: **116 exact 8-owner / 9-addition defects are known inside the completed k6/k7 support-pool union, but none of these has fewer than four BPZ private-pair killer colors. This is not a complete k8 census and is not a 10D breakthrough.**

The reproducible audit is `code/bpz_k8_known_pool_extensions.py`. It consumes the pinned BPZ `base_c7.json`, the completed k6/k7 cover-gap census JSON, and the k7 irreducibility audit.

## Exact scope and support recovery

The completed k6/k7 cover-gap artifacts expose complete five-dimensional support pools. Their union contains 296 distinct outside points relevant to this audit. For every such point the script recomputes the full support

`S(z) = N[z] ∩ B`

against all 359 pinned core owners `B`, using the exact `C7^5` conflict rule. It does not infer a support merely from one containing pool.

Each of the 12 previously audited irreducible k7 witnesses has eight pairwise nonconfusable outside points with support union exactly seven. Testing every known-pool outside point as a ninth addition yields exactly **116** extensions with full support union exactly **eight**. Hence these are genuine `8 -> 9` positive support defects.

This gives a useful regression fact for the corrected global k8 SAT model: unrestricted exact-k8 must be SAT. It does **not** imply that all k8 defects are contained in this known-pool union.

## Private-pair killer audit

For a selected five-dimensional replacement set, a private-pair color is killed when at least one selected point conflicts with both endpoints of that BPZ private pair. Across the 116 exact known-pool k8 defects:

| distinct killer colors | defects |
|---:|---:|
| 4 | 7 |
| 5 | 38 |
| 6 | 61 |
| 7 | 10 |

The minimum observed killer count is therefore **4**. No known-pool k8 defect is killer-free or has only one, two, or three killed colors.

All seven minimum-killer witnesses kill the same colors `{0,4,5,6}` (mask `113`). Representative exact witnesses include:

1. owners `{1741,8888,10960,13248,13347,13600,13692,14040}`; additions `{6494,10659,13297,13649,13684,14335,15959,16045,16147}`;
2. owners `{1741,8888,10861,10960,13347,13600,13692,14040}`; additions `{6494,10659,10910,13649,13684,14335,15959,16045,16147}`;
3. owners `{1741,2433,8888,10960,13347,13600,13692,14040}`; additions `{4492,6494,10659,13649,13684,14335,15959,16045,16147}`;
4. owners `{8888,10861,10960,13248,13347,13600,13692,14040}`; additions `{6494,10659,10910,13297,13649,13684,14335,15959,16045}`.

Every listed addition set is independently replayed by the audit script under the exact `C7^5` conflict relation, and its support union is recomputed against all of `B`.

## Consequence

A raw `8 -> 9` row defect has local gain `+1`, but the known examples all kill at least four private-pair colors. Under the existing conditional killer bound (`alpha(C7^5) <= 367`), these examples therefore cannot by themselves improve the 10D record.

The high-value exact question is now stronger than simple k8 existence:

> Does any exact 8-owner / at-least-9-addition defect use at most three private-pair killer colors?

A corrected global SAT formulation with exact support-union variables is active. Proving UNSAT with a `<=3` killer-color constraint would certify that the minimum global killer count for a positive k8 support defect is exactly four, because the explicit witnesses above supply the matching upper bound.

## Provenance

The k6/k7 census inputs came from the successful census stages of GitHub Actions run `40998510720`; its downstream combined prize optimization was cancelled and is not used as a mathematical conclusion here. The underlying BPZ/Tan geometry is pinned at `c753408492dde92a239708986d16c15dbf6c3235`.
