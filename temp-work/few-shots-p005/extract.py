#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

D = 8
Q = 3
BASELINE = 512


def encode(point: list[int]) -> int:
    if len(point) != D or any(x not in (0, 1, 2) for x in point):
        raise ValueError("bad point")
    v = 0
    for x in point:
        v = Q * v + x
    return v


def decode(v: int) -> list[int]:
    if not 0 <= v < Q**D:
        raise ValueError("id out of range")
    out = [0] * D
    for i in range(D - 1, -1, -1):
        out[i] = v % Q
        v //= Q
    return out


def extract(src: Path, dst: Path) -> None:
    obj = json.loads(src.read_text(encoding="utf-8"))
    pts = obj["points"]
    if len(pts) != BASELINE or len({tuple(p) for p in pts}) != BASELINE:
        raise ValueError("unexpected baseline")
    ids = [encode(p) for p in pts]
    dst.write_text("".join(f"{v}\n" for v in ids), encoding="ascii")
    print(json.dumps({"baseline": len(ids)}))


def build(result: Path, output: Path, status: Path) -> None:
    obj = json.loads(result.read_text(encoding="utf-8"))
    if obj.get("kind") != "found":
        s = {"candidate": False, "search": obj}
        status.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(s))
        return
    ids = [int(x) for x in obj["points"]]
    if len(ids) < 513 or len(ids) != len(set(ids)):
        raise ValueError("bad candidate size/duplicates")
    pts = [decode(v) for v in ids]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n", encoding="utf-8")
    s = {"candidate": True, "score": len(ids), "moves": obj.get("moves"), "restart": obj.get("restart"), "seed": obj.get("seed")}
    status.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(s))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract")
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)
    p = sub.add_parser("build")
    p.add_argument("result", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("status", type=Path)
    a = ap.parse_args()
    if a.cmd == "extract":
        extract(a.src, a.dst)
    else:
        build(a.result, a.output, a.status)


if __name__ == "__main__":
    main()
