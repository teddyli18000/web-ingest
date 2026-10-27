#!/usr/bin/env python3
"""Reproduce targeted neighboring-length transfers into length 100.

Public source sequences are from Table 2 of Zhang et al. (2025), arXiv:2504.00987.
The paper encodes sequences as hexadecimal and pads zero bits on the right to a
multiple of four. Bit complementation does not change LABS energy, so mapping
0 -> +1 and 1 -> -1 is sufficient for exact energy checks.
"""

from itertools import combinations, product


def bits(hex_string: str) -> str:
    return "".join(f"{int(ch, 16):04b}" for ch in hex_string)


def energy(bit_string: str) -> int:
    s = [1 if ch == "0" else -1 for ch in bit_string]
    n = len(s)
    return sum(
        sum(s[i] * s[i + k] for i in range(n - k)) ** 2
        for k in range(1, n)
    )


def to_pm(bit_string: str) -> str:
    return "".join("+" if ch == "0" else "-" for ch in bit_string)


def best_insert_one(source: str):
    best = None
    for pos in range(100):
        for value in "01":
            candidate = source[:pos] + value + source[pos:]
            item = (energy(candidate), pos, value, candidate)
            if best is None or item < best:
                best = item
    return best


def best_insert_two(source: str):
    best = None
    for p, q in combinations(range(100), 2):
        for a, b in product("01", repeat=2):
            out = []
            j = 0
            for i in range(100):
                if i == p:
                    out.append(a)
                elif i == q:
                    out.append(b)
                else:
                    out.append(source[j])
                    j += 1
            candidate = "".join(out)
            item = (energy(candidate), p, q, a, b, candidate)
            if best is None or item < best:
                best = item
    return best


def main() -> None:
    seq99 = bits("0CF30C003783CBCC8DA92AAD4")[:99]
    seq98 = bits("993A76393CDB4BCF78FF00AA8")[:98]
    assert energy(seq99) == 553
    assert energy(seq98) == 529

    e99, pos, value, candidate99 = best_insert_one(seq99)
    print("N99 source energy=553")
    print(f"N99->100 best energy={e99} inserted_pos={pos} inserted_bit={value}")
    print(to_pm(candidate99))

    e98, p, q, a, b, candidate98 = best_insert_two(seq98)
    print("N98 source energy=529")
    print(f"N98->100 best energy={e98} inserted_positions={p},{q} inserted_bits={a},{b}")
    print(to_pm(candidate98))


if __name__ == "__main__":
    main()
