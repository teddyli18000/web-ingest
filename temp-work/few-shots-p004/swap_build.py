#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

Q = 7
D = 5
U = Q**D
N = 367
TARGET = 134_770


def dec5(v: int) -> tuple[int, ...]:
    out = [0] * D
    for i in range(D - 1, -1, -1):
        out[i] = v % Q
        v //= Q
    return tuple(out)


def enc5(w: tuple[int, ...]) -> int:
    v = 0
    for x in w:
        v = v * Q + x
    return v


def dec10(v: int) -> str:
    out = ["0"] * (2 * D)
    for i in range(2 * D - 1, -1, -1):
        out[i] = str(v % Q)
        v //= Q
    return "".join(out)


def conflict(a: int, b: int, digits: tuple[tuple[int, ...], ...]) -> bool:
    return all((x - y) % Q in (0, 1, Q - 1) for x, y in zip(digits[a], digits[b]))


def load_r(path: Path) -> list[int]:
    r = [enc5(tuple(map(int, line.split()))) for line in path.read_text().splitlines() if line.strip()]
    if len(r) != N or len(set(r)) != N:
        raise ValueError("bad R367")
    return r


def make_x(r: list[int], digits: tuple[tuple[int, ...], ...]) -> list[int]:
    x = []
    for rid in r:
        w = digits[rid]
        x.append(enc5(((2 - w[1]) % Q, w[3], w[0], (2 - w[2]) % Q, w[4])))
    x[267] = enc5((1, 5, 6, 3, 5))
    if len(set(x)) != N:
        raise ValueError("X duplicates")
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("search_result", type=Path)
    ap.add_argument("r367", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    result = json.loads(args.search_result.read_text())
    if result.get("kind") != "swap-ports-found":
        status = {"candidate": False, "search": result}
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print(json.dumps(status, sort_keys=True))
        return

    digits = tuple(dec5(v) for v in range(U))
    r0 = load_r(args.r367)
    xset = make_x(r0, digits)
    independent = [int(v) for v in result["independent_set"]]
    ports = result["ports"]

    if len(independent) != N or len(set(independent)) != N:
        raise ValueError("search result independent set has wrong size")
    for a, b in __import__("itertools").combinations(independent, 2):
        if conflict(a, b, digits):
            raise ValueError("search result independent set is not independent")

    in_set = set(independent)
    if len(ports) != 9:
        raise ValueError("expected nine ports")
    centers = [int(p["center"]) for p in ports]
    alts = [int(p["alt"]) for p in ports]
    if len(set(centers)) != 9 or len(set(alts)) != 9:
        raise ValueError("ports are not injective")
    for c, a in zip(centers, alts):
        if c not in in_set or a in in_set:
            raise ValueError("bad port membership")
        hits = [z for z in independent if conflict(a, z, digits)]
        if hits != [c]:
            raise ValueError("port alternative is not private")

    ph, pv = [], []
    for p in ports:
        c, a, side = int(p["center"]), int(p["alt"]), int(p["side"])
        if side not in (0, 1):
            raise ValueError("bad port side")
        ph.append((c, a)[side])
        pv.append((c, a)[1 - side])
    for name, trans in (("PH", ph), ("PV", pv)):
        for i, a in enumerate(trans):
            for b in trans[i + 1 :]:
                if conflict(a, b, digits):
                    raise ValueError(f"{name} is not independent")

    A = {xi for xi, x in enumerate(xset) if any(conflict(x, p, digits) for p in pv)}
    Dset = {xi for xi, x in enumerate(xset) if any(conflict(x, p, digits) for p in ph)}
    if A & Dset:
        raise ValueError("port footprints overlap on X")

    center_set = set(centers)
    bset = [z for z in independent if z not in center_set]
    if len(bset) != N - 9:
        raise ValueError("B size mismatch")

    candidate: set[int] = set(a * U + b for a in bset for b in bset)
    for xi, x in enumerate(xset):
        for p in ports:
            c, a, side = int(p["center"]), int(p["alt"]), int(p["side"])
            ep = (c, a)
            hidx = int((side == 0 and xi in A) or (side == 1 and xi in Dset))
            vidx = int((side == 0 and xi in Dset) or (side == 1 and xi in A))
            candidate.add(x * U + ep[hidx])
            candidate.add(ep[vidx] * U + x)

    if len(candidate) != TARGET:
        raise ValueError(f"candidate score {len(candidate)} != {TARGET}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"points": [dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
    )
    status = {
        "candidate": True,
        "score": len(candidate),
        "method": "5d-private-swap-walk",
        "steps": result.get("step"),
        "restart": result.get("restart"),
        "private_count": result.get("private_count"),
        "footprint_A": len(A),
        "footprint_D": len(Dset),
        "ports": ports,
    }
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    main()
