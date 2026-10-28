#!/usr/bin/env python3
"""Retarget the complete r5 owner-set solvers from net+2 to net+1.

The durable r5 direct/lower solvers were written for a 134752 seed and search
remove-5/add-7. Their owner-support enumeration is independent of target set
size. After a separate complete net+1 r4 proof on a 134753 baseline, every
remove-5/add-6 witness has connected support hypergraph, so the same two r5
strata are complete after changing only the independent-set target 7->6 and the
result label.

This patch is intentionally tiny and byte-asserted. It changes no support
recovery, owner-set generation, conflict test, or exact DFS logic.
"""
import argparse
from pathlib import Path


def exact(s: str, old: str, new: str, name: str, want: int = 1) -> str:
    n = s.count(old)
    if n != want:
        raise SystemExit(f"{name}: expected exactly {want} occurrences of {old!r}, found {n}")
    return s.replace(old, new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["direct", "lower"])
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    s = args.source.read_text()
    if args.mode == "direct":
        s = exact(s, "p.size()>=7", "p.size()>=6", "direct pool threshold")
        s = exact(s, "find_k(p,7,chosen)", "find_k(p,6,chosen)", "direct target")
        s = exact(s, 'replace5add7', 'replace5add6', "direct result kind")
        s = exact(s, 'exact-unrestricted-r5-direct-c5', 'exact-unrestricted-net1-r5-direct-c5', "direct method", 2)
    else:
        s = exact(s, "p.size()<7", "p.size()<6", "lower pool threshold")
        s = exact(s, "find_k(p,7,chosen)", "find_k(p,6,chosen)", "lower target")
        s = exact(s, 'replace5add7', 'replace5add6', "lower result kind")
        s = exact(s, 'exact-unrestricted-r5-connected-lower-support', 'exact-unrestricted-net1-r5-connected-lower-support', "lower method", 2)
    args.output.write_text(s)


if __name__ == "__main__":
    main()
