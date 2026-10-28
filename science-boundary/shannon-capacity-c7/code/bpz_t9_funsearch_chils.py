#!/usr/bin/env python3
"""Export/replay a seeded CHILS search on a FunSearch t=9 obstruction case.

For one exact one-hit state in the unique FunSearch basin, delete the unique bad
point.  This gives a known 366-point independent set in the full induced graph
C7^5 \ D.  CHILS is then started from that 366-point solution and is free to
make arbitrary nonlocal changes.  Any returned independent set of size >=367
is replayed exactly and a 367-point subset is materialized as the auxiliary set
of the 134770-point BPZ t=9 C7^10 construction.

Subcommands:
  export TAN_ROOT GRAPH INIT STATUS --case K
  replay TAN_ROOT SOLUTION OUTPUT STATUS --case K

The graph is written in CHILS/METIS weighted format with unit weights.  CHILS
solution vertices are 1-indexed positions in the sorted list of vertices outside
D, matching its documented output/initial-solution format.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_representative_case import cases

BASELINE = 134753
CHILS_COMMIT = "515952724cd3dcc6c4365a340ecf0f1da782119a"


def load_case(tan_root: Path, case_index: int):
    sys.path.insert(0, str(tan_root.resolve()))
    from shannon.certificates import Ring
    raw = json.loads((tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nbmask = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    cc = cases(I0, ring, digits, nbmask)
    if not 0 <= case_index < len(cc):
        raise RuntimeError("case index out of range")
    return ring, digits, cc[case_index]


def export_graph(tan_root: Path, graph: Path, init: Path, status: Path, case_index: int):
    ring, digits, c = load_case(tan_root, case_index)
    S, bad, Dset = set(c["S"]), int(c["bad"]), set(c["D"])
    if len(S) != f.N or S & Dset != {bad} or not f.independent(S, digits):
        raise RuntimeError("one-hit case replay failed")

    verts = [v for v in range(f.U) if v not in Dset]
    pos = {v: i + 1 for i, v in enumerate(verts)}
    seed = sorted(S - {bad})
    if len(seed) != 366 or any(v not in pos for v in seed) or not f.independent(seed, digits):
        raise RuntimeError("366-point initial core replay failed")

    # METIS stores every undirected edge in both endpoint adjacency lists while
    # the first-line edge count is the number of undirected edges.
    adj = []
    degree_sum = 0
    for v in verts:
        row = sorted(pos[u] for u in ring.NB[v] if u != v and u in pos)
        if len(row) != len(set(row)):
            raise RuntimeError("duplicate CHILS adjacency")
        adj.append(row)
        degree_sum += len(row)
    if degree_sum % 2:
        raise RuntimeError("odd degree sum")
    edges = degree_sum // 2

    graph.parent.mkdir(parents=True, exist_ok=True)
    with graph.open("w", encoding="ascii") as h:
        h.write(f"{len(verts)} {edges} 10\n")
        for row in adj:
            h.write("1")
            if row:
                h.write(" " + " ".join(map(str, row)))
            h.write("\n")
    init.parent.mkdir(parents=True, exist_ok=True)
    init.write_text("".join(f"{pos[v]}\n" for v in seed), encoding="ascii")

    st = {
        "method": "funsearch-t9-obstruction-seeded-chils-export",
        "case_index": case_index,
        "obstruction_index": c["obstruction_index"],
        "bad": bad,
        "obstruction_size": len(Dset),
        "graph_vertices": len(verts),
        "graph_edges": edges,
        "initial_solution_size": len(seed),
        "chils_source_commit": CHILS_COMMIT,
    }
    status.parent.mkdir(parents=True, exist_ok=True)
    status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    print(json.dumps(st, sort_keys=True), flush=True)


def replay_solution(tan_root: Path, solution: Path, output: Path, status: Path, case_index: int):
    ring, digits, c = load_case(tan_root, case_index)
    Dset = set(c["D"])
    verts = [v for v in range(f.U) if v not in Dset]
    raw = []
    for line in solution.read_text(encoding="ascii").splitlines():
        line = line.strip()
        if line:
            raw.append(int(line))
    if len(raw) != len(set(raw)) or any(i < 1 or i > len(verts) for i in raw):
        raise RuntimeError("bad CHILS solution indices")
    Xfull = [verts[i - 1] for i in raw]
    if not f.independent(Xfull, digits):
        raise RuntimeError("CHILS output is not independent")
    if set(Xfull) & Dset:
        raise RuntimeError("CHILS output hits obstruction")

    st = {
        "method": "funsearch-t9-obstruction-seeded-chils-replay",
        "candidate": len(Xfull) >= 367,
        "score": BASELINE,
        "case_index": case_index,
        "obstruction_index": c["obstruction_index"],
        "bad": c["bad"],
        "chils_solution_size": len(Xfull),
        "chils_source_commit": CHILS_COMMIT,
    }
    status.parent.mkdir(parents=True, exist_ok=True)
    if len(Xfull) < 367:
        status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(st, sort_keys=True), flush=True)
        return

    # Any 367-point subset remains independent and obstruction-free.
    X = set(sorted(Xfull)[:367])
    Ibits, pairs, orient, PH, PV = c["witness"]
    points, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"certificate score drift {len(points)}")
    st.update({
        "candidate": True,
        "score": len(points),
        "auxiliary_size_used": len(X),
        "private_pairs": [list(q) for q in pairs],
        "orientation": list(orient),
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(st, sort_keys=True), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ep = sub.add_parser("export")
    ep.add_argument("tan_root", type=Path); ep.add_argument("graph", type=Path); ep.add_argument("init", type=Path); ep.add_argument("status", type=Path); ep.add_argument("--case", type=int, required=True)
    rp = sub.add_parser("replay")
    rp.add_argument("tan_root", type=Path); rp.add_argument("solution", type=Path); rp.add_argument("output", type=Path); rp.add_argument("status", type=Path); rp.add_argument("--case", type=int, required=True)
    args = ap.parse_args()
    if args.cmd == "export":
        export_graph(args.tan_root, args.graph, args.init, args.status, args.case)
    else:
        replay_solution(args.tan_root, args.solution, args.output, args.status, args.case)

if __name__ == "__main__":
    main()
