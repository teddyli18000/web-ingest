#!/usr/bin/env python3
"""Track one CvS ground source as the archimedean cutoff T increases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from source_escape_diagnostic import diagnose_cutoff


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c", type=int, default=100)
    parser.add_argument("--N", type=int, default=16)
    parser.add_argument("--Ts", default="120,240,480")
    parser.add_argument("--dps", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    t_values = [int(x) for x in args.Ts.split(",") if x.strip()]
    payload = {
        "status": "research_probe_only",
        "warning": "Finite-T signs require independent tail certification.",
        "c": args.c,
        "N": args.N,
        "runs": [
            diagnose_cutoff(args.c, [args.N], T, args.dps)
            for T in t_values
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
