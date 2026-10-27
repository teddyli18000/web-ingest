#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

DIM = 8
U = 3 ** DIM
POW3 = [3 ** i for i in range(DIM)]


def point_to_id(p):
    if not isinstance(p, list) or len(p) != DIM or any(type(x) is not int or x not in (0, 1, 2) for x in p):
        raise ValueError("invalid point")
    return sum(x * POW3[i] for i, x in enumerate(p))


def id_to_point(v):
    if not 0 <= v < U:
        raise ValueError("invalid id")
    out = []
    for _ in range(DIM):
        out.append(v % 3)
        v //= 3
    return out


def third(a, b):
    pa, pb = id_to_point(a), id_to_point(b)
    return sum((-(x + y) % 3) * POW3[i] for i, (x, y) in enumerate(zip(pa, pb)))


def load_ids(path):
    vals = [int(x) for x in Path(path).read_text().split()]
    if len(vals) != len(set(vals)) or any(x < 0 or x >= U for x in vals):
        raise ValueError("bad ids")
    return vals


def validate_ids(vals):
    s = set(vals)
    for i, a in enumerate(vals):
        for b in vals[i + 1:]:
            c = third(a, b)
            if c in s:
                raise ValueError(f"cap violation involving ids {a}, {b}, {c}")
    return len(vals)


def cmd_to_ids(args):
    obj = json.loads(Path(args.input).read_text())
    if not isinstance(obj, dict) or set(obj) != {"points"}:
        raise ValueError("expected certificate object with points")
    vals = [point_to_id(p) for p in obj["points"]]
    validate_ids(vals)
    Path(args.output).write_text("".join(f"{x}\n" for x in vals))
    print(len(vals))


def cmd_to_certificate(args):
    vals = load_ids(args.input)
    validate_ids(vals)
    obj = {"points": [id_to_point(x) for x in vals]}
    Path(args.output).write_text(json.dumps(obj, separators=(",", ":")) + "\n")
    print(len(vals))


def cmd_validate(args):
    vals = load_ids(args.input)
    print(validate_ids(vals))


def cmd_select(args):
    best_path = None
    best_vals = None
    for p in args.inputs:
        vals = load_ids(p)
        validate_ids(vals)
        if best_vals is None or len(vals) > len(best_vals):
            best_path, best_vals = p, vals
    if best_vals is None:
        raise ValueError("no candidates")
    Path(args.output).write_text("".join(f"{x}\n" for x in best_vals))
    print(json.dumps({"score": len(best_vals), "source": best_path}, separators=(",", ":")))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("to-ids")
    p.add_argument("input")
    p.add_argument("output")
    p.set_defaults(func=cmd_to_ids)
    p = sub.add_parser("to-certificate")
    p.add_argument("input")
    p.add_argument("output")
    p.set_defaults(func=cmd_to_certificate)
    p = sub.add_parser("validate")
    p.add_argument("input")
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser("select")
    p.add_argument("output")
    p.add_argument("inputs", nargs="+")
    p.set_defaults(func=cmd_select)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
