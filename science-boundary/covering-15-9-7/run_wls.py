#!/usr/bin/env python3
"""Run the external MIT-licensed WLS2 from the public baseline, verify independently."""
import argparse
import itertools
import json
import subprocess
from pathlib import Path

SUBSETS = list(itertools.combinations(range(15), 7))
INDEX = {s: i for i, s in enumerate(SUBSETS)}

def valid(blocks):
    covered = bytearray(len(SUBSETS))
    for block in blocks:
        assert len(block) == len(set(block)) == 9
        assert all(0 <= x < 15 for x in block)
        for seven in itertools.combinations(sorted(block), 7):
            covered[INDEX[seven]] = 1
    return 0 not in covered

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--binary", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--seconds", type=int, default=900)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tenure", type=int, default=7)
    args = ap.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    blocks = json.loads(Path(args.input).read_text())["blocks"]
    assert valid(blocks)
    initial = output / "initial.txt"
    initial.write_text("".join(" ".join(str(p + 1) for p in block) + "\n" for block in blocks))
    command = [str(Path(args.binary).resolve()), "15", "9", "7", str(len(blocks)),
               str(args.seconds), str(args.seed), str(initial), str(args.tenure), "0.05", "269"]
    result = subprocess.run(command, cwd=output, text=True, capture_output=True, check=True)
    (output / "run.log").write_text(result.stdout + "\nSTDERR:\n" + result.stderr)
    best = blocks
    for path in output.glob("shrink_cover_15_9_7_*.txt"):
        candidate = [[int(x) - 1 for x in line.split()]
                     for line in path.read_text().splitlines() if line.strip()]
        if len(candidate) < len(best) and valid(candidate):
            best = candidate
    (output / "certificate.json").write_text(json.dumps({"blocks": best}, separators=(",", ":")))
    (output / "result.json").write_text(
        json.dumps({"score": len(best), "verified": valid(best), "seed": args.seed}, indent=2))
    print((output / "result.json").read_text())

if __name__ == "__main__":
    main()
