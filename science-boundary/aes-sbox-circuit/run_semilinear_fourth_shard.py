#!/usr/bin/env python3
"""Run an existing semilinear p008 search on one exact fourth-orientation shard.

The wrapped search programs enumerate the seven ternary orientation choices after
`--prefix` with `itertools.product(range(3), repeat=7)`.  This wrapper fixes the
first two of those seven choices (`--third`, `--fourth`), leaving exactly 3^5=243
orientations.  The nine (third,fourth) shards are disjoint and their union is the
original 3^7 prefix job.  No search logic is changed.
"""
from __future__ import annotations

import argparse
import importlib
import itertools as real_itertools
import json
import pathlib
import sys


class ItertoolsProxy:
    def __init__(self, third: int, fourth: int):
        self.third = third
        self.fourth = fourth

    def product(self, *args, **kwargs):
        repeat = kwargs.get("repeat")
        if repeat == 7 and len(args) == 1 and tuple(args[0]) == (0, 1, 2):
            for suffix in real_itertools.product(range(3), repeat=5):
                yield (self.third, self.fourth) + suffix
            return
        yield from real_itertools.product(*args, **kwargs)

    def combinations(self, *args, **kwargs):
        return real_itertools.combinations(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(real_itertools, name)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--module", required=True)
    ap.add_argument("--third", type=int, required=True, choices=range(3))
    ap.add_argument("--fourth", type=int, required=True, choices=range(3))
    known, rest = ap.parse_known_args()

    allowed = {
        "search_semilinear_exactcorr",
        "search_semilinear_support5",
        "search_semilinear_support5_rank3",
    }
    if known.module not in allowed:
        raise SystemExit(f"unsupported module: {known.module}")
    if rest and rest[0] == "--":
        rest = rest[1:]

    module = importlib.import_module(known.module)
    module.itertools = ItertoolsProxy(known.third, known.fourth)
    old_argv = sys.argv
    try:
        sys.argv = [known.module] + rest
        module.main()
    finally:
        sys.argv = old_argv

    try:
        out_index = rest.index("--out") + 1
        out = pathlib.Path(rest[out_index])
    except (ValueError, IndexError):
        return
    summary_path = out / "summary.json"
    if summary_path.exists():
        data = json.loads(summary_path.read_text())
        data["third"] = known.third
        data["fourth"] = known.fourth
        data["orientation_shard"] = {
            "prefix": data.get("prefix"),
            "third": known.third,
            "fourth": known.fourth,
            "orientations_expected": 3**5,
        }
        assert data.get("counts", {}).get("orientations") == 3**5
        data["proof_scope"] = (
            data.get("proof_scope", "")
            + "; exact fourth-orientation shard: nine (third,fourth) values partition the original prefix"
        )
        summary_path.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"SHARD_SUMMARY": data}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
