#!/usr/bin/env python3
"""Exact audit of every one-BB-hole unlocked layer in the pinned BPZ profile.

For B=I0\R and W_b={z:N[z] intersect B={b}}, deleting core point (b,c)
from BB unlocks T_(b,c)=(W_b x W_c)\{(b,c)} beyond the complete fixed-BB
safe universe U0=(Q x V5) union (V5 x Q), where Q is the zero-support set.

The script exhaustively computes all W_b and the exact independence number of
every T_(b,c).  In the pinned data every singleton class has size 1 or 2.  The
only nontrivial case is 2x2, giving three unlocked points; all 2,500 such
triples are checked pairwise under the real C7^10 confusability relation.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore

    data_path = root / "data" / "base_c7.json"
    raw = json.loads(data_path.read_text())
    base, _transform, _exchanges, axioms = load_base(data_path)
    if not all(axioms.values()):
        raise RuntimeError({k: v for k, v in axioms.items() if not v})
    ring = base.ring

    I = set(map(int, raw["I0"]))
    pairs = [tuple(map(int, p)) for p in raw["private_pairs"]]
    owners = {a for a, _ in pairs}
    B = I - owners
    if len(B) != 359:
        raise RuntimeError(("B size drift", len(B)))

    singleton = defaultdict(list)
    zero = set()
    for z in range(ring.n):
        S = ring.NB[z] & B
        if not S:
            zero.add(z)
        elif len(S) == 1:
            singleton[next(iter(S))].append(z)
    if set(singleton) != B:
        raise RuntimeError(("singleton owner coverage", len(singleton), len(B)))
    size_hist = Counter(len(singleton[b]) for b in B)

    def conflict10(a, b):
        return b[0] in ring.NB[a[0]] and b[1] in ring.NB[a[1]]

    hole_hist = Counter()
    alpha_hist = Counter()
    nontrivial = 0
    pair_tests = 0
    independent_pairs = 0
    examples = []

    for b in sorted(B):
        for c in sorted(B):
            T = [(u, v) for u in singleton[b] for v in singleton[c]
                 if not (u in B and v in B)]
            hole_hist[len(T)] += 1
            if not T:
                alpha = 0
            elif len(T) == 1:
                alpha = 1
            else:
                # In the pinned profile this can only be the 2x2 case, so
                # |T|=3.  Check every pair exactly; any nonconflicting pair
                # would make alpha(T)>=2.
                nontrivial += 1
                alpha = 1
                for i in range(len(T)):
                    for j in range(i + 1, len(T)):
                        pair_tests += 1
                        if not conflict10(T[i], T[j]):
                            independent_pairs += 1
                            alpha = 2
                            if len(examples) < 20:
                                examples.append({
                                    "core": [b, c],
                                    "pair": [list(T[i]), list(T[j])],
                                })
                if alpha > 1:
                    # No larger exact search is needed for the intended pinned
                    # data; keep this explicit rather than silently assuming.
                    raise RuntimeError(("one-hole unlocked alpha exceeds 1", b, c, T))
            alpha_hist[alpha] += 1

    status = {
        "method": "exact-pinned-bpz-one-core-hole-unlocked-layer-audit",
        "B_size": len(B),
        "zero_support_size": len(zero),
        "singleton_class_size_histogram": {str(k): v for k, v in sorted(size_hist.items())},
        "hole_unlocked_size_histogram": {str(k): v for k, v in sorted(hole_hist.items())},
        "hole_alpha_histogram": {str(k): v for k, v in sorted(alpha_hist.items())},
        "nontrivial_three_vertex_holes": nontrivial,
        "pair_tests_in_three_vertex_holes": pair_tests,
        "independent_unlocked_pairs": independent_pairs,
        "max_unlocked_alpha": max(alpha_hist) if alpha_hist else 0,
        "counterexamples": examples,
        "conclusion": "Every one-core-hole unlocked layer T_(b,c) has independence number at most 1.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
