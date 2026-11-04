#!/usr/bin/env python3
"""Post-audit exact necessary class-matrix screening for m=220, n11=6, seq1/seq2.

This is NOT a complete exclusion of these degree sequences. It relies on the
certified six-low-vertex boundary and complete three-type B88 packing census.
No old withdrawn row-CSP predicate is used.
"""
import json

SEQUENCES = {
    1: {11: 6, 12: 16, 13: 14},
    2: {11: 6, 12: 17, 13: 12, 14: 1},
}


def class_matrices(seq):
    n12, n13, n14 = seq[12], seq[13], seq.get(14, 0)
    result = []
    for R in (22, 24):
        for z in range(n14 * (n14 - 1) // 2 + 1):
            for y in range(n13 * n14 + 1):
                for x in range(n13 * (n13 - 1) // 2 + 1):
                    c = 66 - R
                    a = 13 * n13 - 2 * x - y
                    b = 14 * n14 - y - 2 * z
                    two_p = 12 * n12 - c - a - b
                    if min(a, b, two_p) < 0 or two_p % 2:
                        continue
                    p = two_p // 2
                    S12 = 11 * c + 24 * p + 13 * a + 14 * b
                    S13 = 12 * a + 26 * x + 14 * y
                    S14 = 12 * b + 13 * y + 28 * z
                    if not 132 * n12 <= S12 <= 147 * n12:
                        continue
                    if not 143 * n13 <= S13 <= 164 * n13:
                        continue
                    if n14 and not 154 * n14 <= S14 <= 178 * n14:
                        continue
                    result.append({
                        "R": R, "x": x, "y": y, "z": z,
                        "S12": S12, "S13": S13, "S14": S14,
                        "D13": 164 * n13 - S13,
                        "D12": 147 * n12 - S12,
                    })
    return result


def main():
    out = {
        "campaign": "m220-n11-6-seq12-post-audit-prefilter",
        "edges": 220,
        "soundness": (
            "Certified low-class R=22/24 boundary, exact degree-class handshakes, "
            "S caps, complete B88 six-low anticomplete profile maximum 3, "
            "R(3,4)=9; no withdrawn row-domain predicate."
        ),
        "logical_scope": "Necessary conditions only; seq1 and seq2 remain open.",
        "B88_anticomplete_maximum": 3,
        "proof": (
            "An S=164 degree-13 vertex forces (A32,B88). "
            "With no low-high edges, its number of high nonneighbors is "
            "5 (seq1) or 4+k (seq2, k degree-14 neighbors); B88 permits <=3, "
            "so all degree-13 vertices have S<=163. "
            "An S=163 degree-13 vertex permits only (A31,B88) or (A32,B89); "
            "the former is ruled out by 6 (seq1) or 5+k (seq2) high "
            "nonneighbors, so every S=163 vertex has the unique A32. "
            "For seq2 the degree-14 vertex has at most 8 high neighbors "
            "by R(3,4)=9 and alpha(high)<=3."
        ),
    }
    for idx, seq in SEQUENCES.items():
        rows = class_matrices(seq)
        # If every degree-13 vertex has S<=163, summed deficit D13>=n13.
        nonextreme = [v for v in rows if v["D13"] >= seq[13]]
        survivors = [
            v for v in nonextreme
            if idx == 1 or v["y"] <= 8
        ]
        for v in survivors:
            v["min_S147_degree12"] = max(0, seq[12] - v["D12"])
            v["min_S163_degree13"] = max(
                0, 2 * seq[13] - v["D13"]
            )
        out[f"seq{idx}"] = {
            "degree_sequence": {str(k): v for k, v in seq.items()},
            "before_B88": len(rows),
            "after_S164_exclusion": len(nonextreme),
            "after_high_degree_cap": len(survivors),
            "min_S147_degree12": min(v["min_S147_degree12"] for v in survivors),
            "min_S163_degree13": min(v["min_S163_degree13"] for v in survivors),
            "surviving_class_matrices": survivors,
        }
    assert [out["seq1"][k] for k in (
        "before_B88", "after_S164_exclusion", "after_high_degree_cap",
        "min_S147_degree12", "min_S163_degree13"
    )] == [23, 9, 9, 8, 6]
    assert [out["seq2"][k] for k in (
        "before_B88", "after_S164_exclusion", "after_high_degree_cap",
        "min_S147_degree12", "min_S163_degree13"
    )] == [137, 18, 8, 14, 10]
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
