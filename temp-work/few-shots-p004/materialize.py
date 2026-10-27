#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

N = 10
BASELINE_SCORE = 134_753


def encode(point: str) -> int:
    if len(point) != N or any(c not in "0123456" for c in point):
        raise ValueError("bad point")
    return int(point, 7)


def decode(value: int) -> str:
    if not 0 <= value < 7**N:
        raise ValueError("id out of range")
    out = ["0"] * N
    for i in range(N - 1, -1, -1):
        out[i] = str(value % 7)
        value //= 7
    return "".join(out)


def adjacent(a: str, b: str) -> bool:
    if a == b:
        return False
    for x, y in zip(a, b):
        d = (int(x) - int(y)) % 7
        if d not in (0, 1, 6):
            return False
    return True


def load_points(path: Path) -> list[str]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if set(obj) != {"points"} or not isinstance(obj["points"], list):
        raise ValueError("unexpected upstream certificate shape")
    points = obj["points"]
    if len(points) != BASELINE_SCORE:
        raise ValueError(f"expected {BASELINE_SCORE} baseline points, got {len(points)}")
    if len(set(points)) != len(points):
        raise ValueError("duplicate baseline point")
    return points


def cmd_extract(args: argparse.Namespace) -> None:
    points = load_points(args.certificate)
    args.output.write_text("".join(f"{encode(p)}\n" for p in points), encoding="ascii")
    print(json.dumps({"baseline_size": len(points), "output": str(args.output)}))


def validate_new_points(retained: list[str], additions: list[str]) -> None:
    if len(set(additions)) != len(additions):
        raise ValueError("duplicate additions")
    retained_set = set(retained)
    if any(p in retained_set for p in additions):
        raise ValueError("addition already in retained set")
    for i, p in enumerate(additions):
        for q in retained:
            if adjacent(p, q):
                raise ValueError("addition conflicts with retained baseline")
        for q in additions[:i]:
            if adjacent(p, q):
                raise ValueError("additions conflict with each other")


def cmd_build(args: argparse.Namespace) -> None:
    points = load_points(args.certificate)
    point_ids = [encode(p) for p in points]
    result = json.loads(args.search_result.read_text(encoding="utf-8"))
    kind = result.get("kind")

    status = {"search": result, "candidate": False, "score": BASELINE_SCORE}
    if kind == "none":
        args.status.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(status))
        return

    removed: list[str] = []
    full_python_validation = True

    if kind == "direct":
        additions = [decode(int(result["add"]))]
        retained = points[:]
    elif kind == "replace1":
        remove_index = int(result["remove_index"])
        if not 0 <= remove_index < len(points):
            raise ValueError("remove_index out of range")
        if point_ids[remove_index] != int(result["remove"]):
            raise ValueError("remove id does not match baseline ordering")
        removed = [points[remove_index]]
        retained = points[:remove_index] + points[remove_index + 1 :]
        additions = [decode(int(x)) for x in result["add"]]
        if len(additions) != 2:
            raise ValueError("replace1 must add two points")
    elif kind == "replace2":
        indices = [int(x) for x in result["remove_indices"]]
        remove_ids = [int(x) for x in result["remove"]]
        if len(indices) != 2 or len(set(indices)) != 2 or len(remove_ids) != 2:
            raise ValueError("replace2 must remove two distinct baseline points")
        if any(not 0 <= i < len(points) for i in indices):
            raise ValueError("replace2 remove index out of range")
        for i, rid in zip(indices, remove_ids):
            if point_ids[i] != rid:
                raise ValueError("replace2 remove id does not match baseline ordering")
        removed = [points[i] for i in indices]
        remove_set = set(indices)
        retained = [p for i, p in enumerate(points) if i not in remove_set]
        additions = [decode(int(x)) for x in result["add"]]
        if len(additions) != 3:
            raise ValueError("replace2 must add three points")
    elif kind == "bulk":
        remove_ids = [int(x) for x in result["remove"]]
        add_ids = [int(x) for x in result["add"]]
        if len(remove_ids) != len(set(remove_ids)):
            raise ValueError("bulk removal contains duplicates")
        if len(add_ids) != len(set(add_ids)):
            raise ValueError("bulk additions contain duplicates")
        baseline_id_set = set(point_ids)
        if not set(remove_ids) <= baseline_id_set:
            raise ValueError("bulk removal contains a non-baseline point")
        remove_set = set(remove_ids)
        retained = [p for p, pid in zip(points, point_ids) if pid not in remove_set]
        removed = [decode(x) for x in remove_ids]
        additions = [decode(x) for x in add_ids]
        if set(add_ids) & (baseline_id_set - remove_set):
            raise ValueError("bulk addition duplicates a retained baseline point")
        # The C++ structural search replays its exact coverage and 2-SAT constraints.
        # The authoritative upstream verifier immediately follows in the workflow;
        # avoid an O(|retained|*|additions|) Python duplicate verification here.
        full_python_validation = False
    else:
        raise ValueError(f"unknown search result kind: {kind!r}")

    if full_python_validation:
        validate_new_points(retained, additions)
    else:
        if len(set(additions)) != len(additions):
            raise ValueError("duplicate additions")
        if set(retained) & set(additions):
            raise ValueError("addition already in retained set")

    candidate = retained + additions
    if len(candidate) <= BASELINE_SCORE:
        raise ValueError("search result is not an improvement")
    if len(candidate) != len(set(candidate)):
        raise ValueError("candidate contains duplicate points")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"points": candidate}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    status.update(
        {
            "candidate": True,
            "score": len(candidate),
            "removed_count": len(removed),
            "additions_count": len(additions),
        }
    )
    if len(removed) <= 10:
        status["removed"] = removed
    if len(additions) <= 10:
        status["additions"] = additions
    args.status.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("extract")
    p.add_argument("certificate", type=Path)
    p.add_argument("output", type=Path)
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("build")
    p.add_argument("certificate", type=Path)
    p.add_argument("search_result", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("status", type=Path)
    p.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
