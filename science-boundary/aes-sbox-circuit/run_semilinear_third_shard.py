#!/usr/bin/env python3
"""Run an existing semilinear p008 search on one exact third-orientation shard.

The historical semilinear search programs partition 3^9 orientations by the
first two ternary choices (`--prefix`, 9 values), leaving 3^7=2187 orientations
per job.  A few scientifically important jobs were repeatedly lost to hosted
runner shutdowns before producing summaries.

This wrapper does not alter the search algorithm.  It fixes the first element of
the seven-choice tail to `--third` in {0,1,2}, leaving 3^6=729 orientations.
The three third-shards are disjoint and their union is exactly the original
prefix job.  The wrapped program's summary.json is annotated with the third
choice after successful completion.
"""
from __future__ import annotations

import argparse
import importlib
import itertools as real_itertools
import json
import pathlib
import sys


class ItertoolsProxy:
    def __init__(self, third: int):
        self.third = third

    def product(self, *args, **kwargs):
        repeat = kwargs.get("repeat")
        # The target search programs use exactly product(range(3), repeat=7)
        # for the orientation tail. Preserve every other product call exactly.
        if (
            repeat == 7
            and len(args) == 1
            and tuple(args[0]) == (0, 1, 2)
        ):
            for suffix in real_itertools.product(range(3), repeat=6):
                yield (self.third,) + suffix
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
    known, rest = ap.parse_known_args()

    allowed = {
        "search_semilinear_exactcorr",
        "search_semilinear_support5",
        "search_semilinear_support5_rank3",
    }
    if known.module not in allowed:
        raise SystemExit(f"unsupported module: {known.module}")

    module = importlib.import_module(known.module)
    module.itertools = ItertoolsProxy(known.third)

    old_argv = sys.argv
    try:
        sys.argv = [known.module] + rest
        module.main()
    finally:
        sys.argv = old_argv

    # Add shard identity to the scientific summary without changing any result.
    try:
        out_index = rest.index("--out") + 1
        out = pathlib.Path(rest[out_index])
    except (ValueError, IndexError):
        return
    summary_path = out / "summary.json"
    if summary_path.exists():
        data = json.loads(summary_path.read_text())
        data["third"] = known.third
        data["orientation_shard"] = {
            "prefix": data.get("prefix"),
            "third": known.third,
            "orientations_expected": 3**6,
        }
        assert data.get("counts", {}).get("orientations") == 3**6
        scope = data.get("proof_scope", "")
        data["proof_scope"] = (
            scope
            + "; exact third-orientation shard: three third values partition the original prefix"
        )
        summary_path.write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"SHARD_SUMMARY": data}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
