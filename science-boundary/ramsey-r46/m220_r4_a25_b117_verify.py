#!/usr/bin/env python3
"""Exact relaxed-row-CSP verification for the m=220 r=4 A25/B117 layer.

For a degree-11 anchor v with r(v)=132-S(v)=4 we have S(v)=128.  If
(e(A),e(B))=(25,117), then the total number of A-B cross edges is
128-11-2*25=67.  The already-certified m220_r2_row_csp.cpp solver is more
 general than its filename: for any fixed 11-vertex A and 24-vertex B it
searches all row subsets satisfying every mixed K4/I6 constraint, allows each
A vertex any global degree 11..17, and imposes only that same total of 67
cross edges.  Thus running it on the complete authenticated A25 and B117
catalogues proves UNSAT for a superfamily of the actual r=4 configurations.

This driver compiles that exact C++ core and exhausts all 6*90=540 pairs in
parallel.  Any SAT or timeout is treated as failure; a successful run is a
complete exact exclusion of the (25,117) local edge layer.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, os, pathlib, subprocess, tempfile

HERE = pathlib.Path(__file__).resolve().parent
A = HERE / "data/m219-r34-A25.g6"
B = HERE / "data/m219-r34-B117.g6"
CORE = HERE / "m220_r2_row_csp.cpp"
EXPECTED_A = 6
EXPECTED_B = 90
EXPECTED_A_SHA = "11b69f5bc2a945abe0cc1e93b17a674c153201a3"
EXPECTED_B_SHA = "8ea75f78c0c8c0f77a3d1987413069ab52be0aee"


def blob_sha(path: pathlib.Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def run_one(exe: pathlib.Path, ai: int, bi: int, seconds: float) -> dict:
    p = subprocess.run(
        [str(exe), str(A), str(B), str(ai), str(bi), str(seconds), str(1 + ai * 1000 + bi)],
        text=True, capture_output=True,
    )
    if not p.stdout.strip():
        raise RuntimeError((ai, bi, p.returncode, p.stderr[-1000:]))
    d = json.loads(p.stdout.strip().splitlines()[-1])
    # Core convention: 20=UNSAT, 10=SAT, 0=TIMEOUT.
    if d["status"] == "UNSAT" and p.returncode != 20:
        raise RuntimeError((ai, bi, "bad UNSAT rc", p.returncode, d))
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--jobs", type=int, default=max(1, os.cpu_count() or 1))
    ap.add_argument("--output", type=pathlib.Path)
    args = ap.parse_args()

    assert blob_sha(A) == EXPECTED_A_SHA, blob_sha(A)
    assert blob_sha(B) == EXPECTED_B_SHA, blob_sha(B)
    assert len([x for x in A.read_text().splitlines() if x]) == EXPECTED_A
    assert len([x for x in B.read_text().splitlines() if x]) == EXPECTED_B

    with tempfile.TemporaryDirectory(prefix="r46-m220-r4-") as td:
        exe = pathlib.Path(td) / "row_csp"
        subprocess.run(
            ["g++", "-O3", "-march=native", "-std=c++17", str(CORE), "-o", str(exe)],
            check=True,
        )
        todo = [(a, b) for a in range(EXPECTED_A) for b in range(EXPECTED_B)]
        rows = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            fut = {pool.submit(run_one, exe, a, b, args.seconds): (a, b) for a, b in todo}
            for f in concurrent.futures.as_completed(fut):
                rows.append(f.result())

    rows.sort(key=lambda d: (d["a"], d["b"]))
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    raw = "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n"
    out = {
        "campaign": "m220-r4-A25-B117-relaxed-row-csp",
        "logical_scope": "all 6 complete A25 x 90 complete B117 local pairs for a degree-11 r=4 anchor at m=220",
        "pair_count": len(rows),
        "status_counts": counts,
        "all_unsat": len(rows) == 540 and counts == {"UNSAT": 540},
        "aggregate_cross_edges": 67,
        "max_nodes": max(r["nodes"] for r in rows),
        "max_depth": max(r["maxDepth"] for r in rows),
        "max_seconds": max(r["seconds"] for r in rows),
        "raw_rows_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "data_blob_sha": {"A25": EXPECTED_A_SHA, "B117": EXPECTED_B_SHA},
        "relaxation": "global degree labels are dropped; each A row only respects global degree range 11..17, exact row-size bounds from deg_A, aggregate cross total 67, and all mixed K4/I6 constraints",
        "reproducer_core": str(CORE.relative_to(HERE.parent.parent.parent)),
        "conclusion": "No m=220 degree-11 r=4 anchor can have local edge pair (e(A),e(B))=(25,117).",
    }
    assert out["all_unsat"], out
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
