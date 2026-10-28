#!/usr/bin/env python3
"""Check whether merged 102 prefix already exposes alternate core-basis wires.

Evaluates gates 0..41 of the merged 102 certificate on all 256 AES inputs and
checks which existing wires lie in span(q34,q36,q39,q41).  The exact result is
that only q34,q36,q39,q41 themselves occur.  Thus a nontrivial GL(4,2) core
basis is not free; it must be paid for/resynthesized in the middle layer.
"""
import json
import urllib.request

URL = "https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p008-aes-sbox-circuit/shots/huangxin-design/aes102-field-plane-offsets/certificate.json"
MASK = (1 << 256) - 1


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        c = json.load(r)
    vals = {}
    for b in range(8):
        v = 0
        for x in range(256):
            if (x >> b) & 1:
                v |= 1 << x
        vals[f"x{b}"] = v
    for g in c["gates"][:42]:
        a, b = vals[g["a"]], vals[g["b"]]
        if g["op"] == "XOR":
            v = a ^ b
        elif g["op"] == "XNOR":
            v = (~(a ^ b)) & MASK
        elif g["op"] == "AND":
            v = a & b
        else:
            raise ValueError(g["op"])
        vals[g["out"]] = v

    basis_names = ["q34", "q36", "q39", "q41"]
    basis = [vals[w] for w in basis_names]
    comb = {}
    for m in range(16):
        v = 0
        for i, t in enumerate(basis):
            if (m >> i) & 1:
                v ^= t
        comb[v] = m

    hits = [(w, comb[t]) for w, t in vals.items() if t in comb]
    print(hits)
    assert hits == [("q34", 1), ("q36", 2), ("q39", 4), ("q41", 8)]


if __name__ == "__main__":
    main()
