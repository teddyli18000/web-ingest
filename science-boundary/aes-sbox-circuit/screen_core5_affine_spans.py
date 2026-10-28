#!/usr/bin/env python3
"""Exact nonlinear-span screen for the 16 rank-4 zero-state completions.

`prove_core5_rank5_completions.py` excludes the other 496 completion patterns from
five-AND circuits.  For one of the remaining rank-4 patterns T, any five-AND
circuit must have five independent nonlinear quotient classes whose 5D span N
contains T.  The first AND is a product of affine input functions; there are 35
possible nonzero first-AND classes.  Each class outside T defines one candidate
N = span(T,r0).

For every such N this script exactly checks whether there is a five-step chain of
independent AND classes r0,...,r4 spanning N, where at step d each new class is the
nonlinear residue of a product of two affine functions in the span of the four
inputs and the previously generated classes.  This is a multiplicative-complexity
screen only: a reachable N may still require too many XOR/XNOR gates.
"""
from __future__ import annotations

import argparse
import functools
import json
import pathlib
import time


def mobius16(x: int) -> int:
    x ^= (x & 0x5555) << 1
    x ^= (x & 0x3333) << 2
    x ^= (x & 0x0F0F) << 4
    x ^= (x & 0x00FF) << 8
    return x & 0xFFFF


def strip_affine_slow(x: int) -> int:
    anf = mobius16(x)
    anf &= ~0x0117 & 0xFFFF
    return mobius16(anf)


STRIP = [strip_affine_slow(x) for x in range(1 << 16)]
ONES = 0xFFFF


def var(i: int) -> int:
    return sum((((x >> i) & 1) << x) for x in range(16))


INPUTS = tuple(var(i) for i in range(4))


def canonical_basis(vectors):
    rows = [0] * 16
    for x in vectors:
        y = x
        for p in range(15, -1, -1):
            if not ((y >> p) & 1):
                continue
            if rows[p]:
                y ^= rows[p]
                continue
            for q in range(p - 1, -1, -1):
                if rows[q] and ((y >> q) & 1):
                    y ^= rows[q]
            p = y.bit_length() - 1
            for q in range(p + 1, 16):
                if rows[q] and ((rows[q] >> p) & 1):
                    rows[q] ^= y
            rows[p] = y
            break
    return tuple(x for x in rows if x)


def reduce_by_basis(x, basis):
    y = x
    for v in reversed(basis):
        if (y >> (v.bit_length() - 1)) & 1:
            y ^= v
    return y


def span_values(basis):
    values = [0]
    for v in basis:
        values += [x ^ v for x in values]
    return values


def source_targets():
    a, b, c, d = INPUTS
    q42 = a & b
    q43 = q42 ^ c
    q44 = q43 & d
    q45 = b ^ q44
    q46 = q42 & c
    q47 = d ^ q46
    q48 = a & q47
    q49 = q43 ^ q48
    q50 = q48 ^ b
    q51 = q49 & q50
    q52 = q51 ^ a
    q53 = q52 ^ q49
    q54 = q45 & q53
    q55 = q54 ^ q47
    q56 = q55 ^ q49
    q57 = q53 ^ q45
    q58 = q56 ^ q57
    q59 = q55 ^ q45
    return (q45, q59, q52, q57, q53, q49, q58, q55, q56)


TARGETS = source_targets()
CARE_NONZERO = 0xFFFE


def rank4_cases():
    cases = []
    for pattern in range(1 << 9):
        residues = [
            STRIP[TARGETS[i] ^ (CARE_NONZERO if ((pattern >> i) & 1) else 0)]
            for i in range(9)
        ]
        basis = canonical_basis(residues)
        if len(basis) == 4:
            cases.append((pattern, basis))
    assert len(cases) == 16
    return cases


def first_and_classes():
    funcs = span_values(canonical_basis(INPUTS + (ONES,)))
    out = set()
    for i, left in enumerate(funcs):
        for right in funcs[: i + 1]:
            residue = STRIP[left & right]
            if residue:
                out.add(residue)
    assert len(out) == 35
    return frozenset(out)


@functools.lru_cache(maxsize=None)
def product_residues(nonlinear_basis):
    """Every independent next AND class reachable from this nonlinear span."""
    funcs = span_values(canonical_basis(INPUTS + nonlinear_basis + (ONES,)))
    out = set()
    for i, left in enumerate(funcs):
        for right in funcs[: i + 1]:
            residue = STRIP[left & right]
            if residue and reduce_by_basis(residue, nonlinear_basis):
                out.add(residue)
    return frozenset(out)


def chain_to_space(target5, first):
    allowed = set(span_values(target5))
    states = {canonical_basis((first,))}
    for _new_dim in range(2, 6):
        next_states = set()
        for basis in states:
            for residue in product_residues(basis):
                if residue not in allowed:
                    continue
                if not reduce_by_basis(residue, basis):
                    continue
                next_states.add(canonical_basis(basis + (residue,)))
        states = next_states
        if not states:
            return False
    return target5 in states


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int, required=True, choices=range(16))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    started = time.time()
    pattern, target4 = rank4_cases()[args.case]
    firsts = first_and_classes()
    candidates = []
    reachable = []
    for first in sorted(firsts):
        assert reduce_by_basis(first, target4) != 0  # true for all 16 cases
        target5 = canonical_basis(target4 + (first,))
        item = {
            "first_and_class": f"0x{first:04x}",
            "target5_basis": [f"0x{x:04x}" for x in target5],
        }
        candidates.append(item)
        if chain_to_space(target5, first):
            reachable.append(item)

    summary = {
        "case": args.case,
        "completion_pattern": pattern,
        "completion_pattern_binary": f"{pattern:09b}",
        "rank": len(target4),
        "first_and_classes": len(firsts),
        "candidate_five_dimensional_spaces": len(candidates),
        "reachable_five_dimensional_spaces": len(reachable),
        "excluded_five_dimensional_spaces": len(candidates) - len(reachable),
        "product_residue_cache": {
            "hits": product_residues.cache_info().hits,
            "misses": product_residues.cache_info().misses,
            "size": product_residues.cache_info().currsize,
        },
        "elapsed_seconds": round(time.time() - started, 3),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "reachable.json").write_text(json.dumps(reachable, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
