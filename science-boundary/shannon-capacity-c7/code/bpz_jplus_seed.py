#!/usr/bin/env python3
"""Materialize the BPZ/Tan eight-exchange J+ seed as a Few Shots p004 certificate.

The construction itself is imported from a pinned checkout of
C7-Shannon-Capacity-Heterogeneous-Recursion so the public implementation remains
the source of truth for the five-dimensional gadget, automorphism, and eight
simultaneous exchanges.
"""

import argparse
import json
import sys
from pathlib import Path

EXPECTED_SCORE = 134_753
EXPECTED_EXCHANGES = 8


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import build, load_base  # type: ignore

    base, transform, exchanges, axioms = load_base(root / "data" / "base_c7.json")
    if not all(axioms.values()):
        bad = [name for name, ok in axioms.items() if not ok]
        raise RuntimeError(f"upstream base-gadget axioms failed: {bad}")
    if len(exchanges) != EXPECTED_EXCHANGES:
        raise RuntimeError(f"exchange count drift: {len(exchanges)}")

    graph_data, _, extras = build(base, transform, exchanges, verbose=False)
    jps = []
    for blocks in graph_data.values():
        for block in blocks:
            for atom in block:
                if getattr(atom, "name", None) == "Jp":
                    jps.append(atom)
    if not jps:
        raise RuntimeError("Jp atom not found in upstream construction")
    jp = jps[0]
    if any(atom.pairs != jp.pairs for atom in jps[1:]):
        raise RuntimeError("inconsistent Jp atoms")
    if len(jp.pairs) != EXPECTED_SCORE:
        raise RuntimeError(f"Jp score drift: {len(jp.pairs)}")

    def point(pair: tuple[int, int]) -> str:
        a, b = pair
        digits = base.ring.decode(a) + base.ring.decode(b)
        if len(digits) != 10 or any(not 0 <= x < 7 for x in digits):
            raise RuntimeError("bad decoded Jp point")
        return "".join(str(x) for x in digits)

    points = sorted(point(p) for p in jp.pairs)
    if len(points) != len(set(points)):
        raise RuntimeError("duplicate Jp points after conversion")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    status = {
        "candidate": True,
        "score": len(points),
        "exchange_count": len(exchanges),
        "c1_pre_exchange": extras.get("C1_pre_exchange"),
        "source": "tandonravi/C7-Shannon-Capacity-Heterogeneous-Recursion",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
