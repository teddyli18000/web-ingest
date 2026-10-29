#!/usr/bin/env python3
"""Exact blocker profile for BPZ product blocks omitted by the record terminal code.

The BPZ 5D gadget has seven labelled families (B,N,A,D,O,H,V).  The public
134753-point 10D construction is the union of the seven product blocks

    BB, NO, AH, DV, ON, HD, VA.

The binary terminal-code abstraction discards the other 42 label words because
they are not *guaranteed* separated from all selected words.  This script drops
the abstraction and inspects every actual vertex in those omitted Cartesian
blocks.  For each external vertex it computes the exact number of blockers in
the 134753-point record set, using the disjoint seven-block factorization.

This is a diagnostic for deeper structured exchange search: a low blocker count
identifies the first radius at which an omitted terminal block can participate.
It does not by itself prove that a net-positive exchange exists.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

LABELS = ("B", "N", "A", "D", "O", "H", "V")
RECORD_CODE = (
    ("B", "B"),
    ("N", "O"),
    ("A", "H"),
    ("D", "V"),
    ("O", "N"),
    ("H", "D"),
    ("V", "A"),
)
EXPECTED_SCORE = 134_753


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--detail-cap", type=int, default=16,
                    help="retain candidate summaries through this blocker count")
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore

    base, _transform, _exchanges, axioms = load_base(root / "data" / "base_c7.json")
    if not all(axioms.values()):
        raise RuntimeError({k: v for k, v in axioms.items() if not v})
    ring = base.ring

    fam = {
        "B": set(base.B.elements),
        "N": set(base.X0.elements),
        "A": set(base.XV.elements),
        "D": set(base.XH.elements),
        "O": set(base.R.elements),
        "H": set(base.PH.elements),
        "V": set(base.PV.elements),
    }
    sizes = {k: len(v) for k, v in fam.items()}
    if sizes != {"B": 359, "N": 322, "A": 19, "D": 26,
                 "O": 8, "H": 8, "V": 8}:
        raise RuntimeError(("family-size drift", sizes))

    blocks = []
    baseline = set()
    block_sizes = {}
    for w in RECORD_CODE:
        blk = {(a, b) for a in fam[w[0]] for b in fam[w[1]]}
        blocks.append((w, blk))
        block_sizes["".join(w)] = len(blk)
        before = len(baseline)
        baseline |= blk
        if len(baseline) != before + len(blk):
            raise RuntimeError(("record blocks overlap", w, before, len(blk), len(baseline)))
    if len(baseline) != EXPECTED_SCORE:
        raise RuntimeError(("record score drift", len(baseline), block_sizes))

    # For every 5D vertex x and family F, count |N[x] intersect F| exactly.
    nb_count = {lab: [0] * ring.n for lab in LABELS}
    for lab in LABELS:
        F = fam[lab]
        for x in range(ring.n):
            nb_count[lab][x] = sum(1 for y in ring.NB[x] if y in F)

    def blocker_count(a: int, b: int) -> int:
        # The seven baseline blocks are pairwise disjoint, so these products sum
        # to the exact number of baseline neighbours of (a,b).
        return sum(nb_count[c][a] * nb_count[d][b] for c, d in RECORD_CODE)

    per_word = []
    global_hist = Counter()
    detail = []
    scanned = 0
    external = 0
    for u in LABELS:
        for v in LABELS:
            w = (u, v)
            if w in RECORD_CODE:
                continue
            hist = Counter()
            min_b = None
            min_examples = []
            overlap = 0
            for a in fam[u]:
                for b in fam[v]:
                    scanned += 1
                    if (a, b) in baseline:
                        overlap += 1
                        continue
                    external += 1
                    k = blocker_count(a, b)
                    if k <= 0:
                        raise RuntimeError(("unexpected add-1 candidate", w, a, b, k))
                    hist[k] += 1
                    global_hist[k] += 1
                    if min_b is None or k < min_b:
                        min_b = k
                        min_examples = [[a, b]]
                    elif k == min_b and len(min_examples) < 8:
                        min_examples.append([a, b])
                    if k <= args.detail_cap:
                        detail.append({"word": "".join(w), "a": a, "b": b, "blockers": k})
            per_word.append({
                "word": "".join(w),
                "cartesian_size": len(fam[u]) * len(fam[v]),
                "baseline_overlap": overlap,
                "external": sum(hist.values()),
                "min_blockers": min_b,
                "min_examples": min_examples,
                "histogram": {str(k): hist[k] for k in sorted(hist)},
            })

    per_word.sort(key=lambda r: (10**9 if r["min_blockers"] is None else r["min_blockers"],
                                 r["word"]))
    detail.sort(key=lambda r: (r["blockers"], r["word"], r["a"], r["b"]))
    status = {
        "method": "exact-bpz-omitted-terminal-blocker-profile",
        "record_score": len(baseline),
        "record_code": ["".join(w) for w in RECORD_CODE],
        "family_sizes": sizes,
        "omitted_words": 49 - len(RECORD_CODE),
        "scanned_cartesian_vertices": scanned,
        "external_vertices_with_multiplicity": external,
        "global_min_blockers": min(global_hist) if global_hist else None,
        "global_histogram": {str(k): global_hist[k] for k in sorted(global_hist)},
        "detail_cap": args.detail_cap,
        "detail_count": len(detail),
        "low_blocker_candidates": detail,
        "per_word": per_word,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    summary = dict(status)
    summary.pop("low_blocker_candidates")
    summary["top_words"] = per_word[:12]
    summary.pop("per_word")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
