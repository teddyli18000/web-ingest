# U2 radius<=2 private-pair orientability frontier

Exact local result around `results/u2-t11-parent.json`.

The frozen U2-derived 367-point parent and every distinct neutral 1-for-1 and 2-for-2 neighbor were reconstructed directly in `C7^5`. The enumeration matches the existing independent radius-2 run exactly:

- 59 distinct independent states total;
- 11 support-1 owner groups;
- 216 support-2 owner pairs;
- 270 owner pairs generated;
- 85 candidate add-pairs tested;
- maximum radius-2 candidate pool size 3.

For every one of the 59 states, all private-neighbour pairs were recomputed and an exact branch-and-bound search maximized the number of private pairs that can be simultaneously oriented so that both endpoint sets are independent.

## Result

Maximum orientable private-pair subset size over the entire radius<=2 neighborhood: **8**.

Histogram:

- orientable 6: 12 states;
- orientable 7: 33 states;
- orientable 8: 14 states;
- orientable 9 or more: **0 states**.

The private-pair/private-owner counts themselves are much larger:

- 6: 7 states;
- 7: 7 states;
- 8: 25 states;
- 9: 8 states;
- 10: 4 states;
- 11: 7 states;
- 12: 1 state.

Thus even the unique 12-private-pair state is not a valid `t=9` parent. The obstruction is orientability, not lack of private pairs.

This closes the possible `t=9`, `t=10`, and `t=11` Gao/BPZ constructions throughout this exact neutral radius<=2 neighborhood. A useful next parent search must leave this neighborhood (radius>=3 or a nonlocal exchange) and should optimize maximum orientable subset directly rather than private-owner count.

Reproducible code paths:

- `code/u2_t11_orientation_neighborhood.py` (exact 59-state neighborhood and direct t=11 witness search);
- `code/u2_r2_orientable_t10_t9_scan.py` (t=10/t=9 orientability and obstruction scanner);
- frozen parent: `results/u2-t11-parent.json`.
