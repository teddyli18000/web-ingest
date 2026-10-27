#!/usr/bin/env python3
"""Reproduce targeted neighboring-length transfers into length 100.

Sources:
- Zhang et al. (2025), arXiv:2504.00987, Table 2, for new N=98 and N=99 records.
- Knauer's historical record table mirrored by borkob/git_labs for the N=102 record.

The Zhang paper encodes sequences as hexadecimal and pads zero bits on the right
to a multiple of four. Bit complementation does not change LABS energy, so
mapping 0 -> +1 and 1 -> -1 is sufficient for exact energy checks.
"""

from itertools import combinations, product


def bits(hex_string: str) -> str:
    return "".join(f"{int(ch, 16):04b}" for ch in hex_string)


def from_runs(runs: list[int]) -> str:
    out = []
    bit = "0"
    for run in runs:
        out.extend(bit * run)
        bit = "1" if bit == "0" else "0"
    return "".join(out)


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


def best_delete_two(source: str):
    assert len(source) == 102
    best = None
    for p, q in combinations(range(102), 2):
        candidate = "".join(ch for i, ch in enumerate(source) if i not in (p, q))
        item = (energy(candidate), p, q, candidate)
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

    runs102 = [
        3, 5, 6, 4, 2, 4, 3, 3, 1, 1, 1, 2, 1, 2, 2, 1, 1, 1, 1, 1,
        3, 1, 1, 1, 2, 2, 2, 2, 3, 2, 2, 1, 1, 2, 1, 9, 1, 2, 1, 1,
        1, 1, 2, 1, 1, 1, 1, 2, 1, 3, 1, 2,
    ]
    seq102 = from_runs(runs102)
    assert len(seq102) == 102
    assert energy(seq102) == 567
    e102, p, q, candidate102 = best_delete_two(seq102)
    print("N102 source energy=567")
    print(f"N102->100 best energy={e102} deleted_positions={p},{q}")
    print(to_pm(candidate102))


if __name__ == "__main__":
    main()
