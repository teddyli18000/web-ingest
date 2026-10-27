#!/usr/bin/env python3
import argparse
import json


def energy(seq: str) -> int:
    if len(seq) != 100 or set(seq) - {"+", "-"}:
        raise ValueError("sequence must be exactly 100 signs")
    s = [1 if c == "+" else -1 for c in seq]
    return sum(sum(s[i] * s[i + k] for i in range(100 - k)) ** 2 for k in range(1, 100))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence", nargs="?")
    ap.add_argument("--json")
    args = ap.parse_args()
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            seq = json.load(f)["sequence"]
    else:
        seq = args.sequence
    print(energy(seq))


if __name__ == "__main__":
    main()
