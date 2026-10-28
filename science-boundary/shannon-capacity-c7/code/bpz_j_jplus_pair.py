#!/usr/bin/env python3
"""Materialize the public pre-exchange J and eight-exchange J+ C7^10 seeds.

Both objects come from the same pinned Tan/BPZ construction.  Calling build()
with no exchanges yields J=(T x T)(I_10); calling it with the eight public
exchanges yields J+.  This makes the 8-for-8 relation explicit and lets a
separate exact recombination step inspect the bipartite conflict graph on their
difference sets.
"""
import argparse
import json
import sys
from pathlib import Path

EXPECTED_SCORE = 134_753
EXPECTED_EXCHANGES = 8


def extract_jp(graph_data):
    atoms = []
    for blocks in graph_data.values():
        for block in blocks:
            for atom in block:
                if getattr(atom, "name", None) == "Jp":
                    atoms.append(atom)
    if not atoms:
        raise RuntimeError("Jp atom not found")
    p = atoms[0].pairs
    if any(a.pairs != p for a in atoms[1:]):
        raise RuntimeError("inconsistent Jp atoms")
    return set(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("j_cert", type=Path)
    ap.add_argument("jp_cert", type=Path)
    ap.add_argument("j_ids", type=Path)
    ap.add_argument("jp_ids", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import build, load_base  # type: ignore

    base, transform, exchanges, axioms = load_base(root / "data" / "base_c7.json")
    if not all(axioms.values()):
        raise RuntimeError(f"base axioms failed: {[k for k,v in axioms.items() if not v]}")
    if len(exchanges) != EXPECTED_EXCHANGES:
        raise RuntimeError(f"exchange count drift: {len(exchanges)}")

    gj, _, _ = build(base, transform, (), verbose=False)
    gjp, _, _ = build(base, transform, exchanges, verbose=False)
    J = extract_jp(gj)
    Jp = extract_jp(gjp)
    if len(J) != EXPECTED_SCORE or len(Jp) != EXPECTED_SCORE:
        raise RuntimeError(f"score drift J={len(J)} Jp={len(Jp)}")

    left = sorted(J - Jp)
    right = sorted(Jp - J)
    common = J & Jp
    if len(left) != EXPECTED_EXCHANGES or len(right) != EXPECTED_EXCHANGES:
        raise RuntimeError(f"difference drift left={len(left)} right={len(right)}")

    def point(pair):
        a, b = pair
        d = base.ring.decode(a) + base.ring.decode(b)
        if len(d) != 10 or any(not 0 <= x < 7 for x in d):
            raise RuntimeError("bad decoded point")
        return "".join(map(str, d))

    def enc(pair):
        # Few-Shots strings are most-significant digit first; base-7 integer IDs
        # are used only by auxiliary code and preserve equality.
        return int(point(pair), 7)

    Jpts = sorted(point(p) for p in J)
    Jppts = sorted(point(p) for p in Jp)
    for p, pts, ids in ((args.j_cert, Jpts, args.j_ids), (args.jp_cert, Jppts, args.jp_ids)):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
        ids.parent.mkdir(parents=True, exist_ok=True)
        ids.write_text("".join(f"{int(x,7)}\n" for x in pts))

    st = {
        "method": "bpz-preexchange-j-and-jplus",
        "score_j": len(J),
        "score_jplus": len(Jp),
        "common": len(common),
        "left_only": len(left),
        "right_only": len(right),
        "exchange_count": len(exchanges),
        "left_pairs": [list(p) for p in left],
        "right_pairs": [list(p) for p in right],
        "left_ids": [enc(p) for p in left],
        "right_ids": [enc(p) for p in right],
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    print(json.dumps(st, sort_keys=True))


if __name__ == "__main__":
    main()
