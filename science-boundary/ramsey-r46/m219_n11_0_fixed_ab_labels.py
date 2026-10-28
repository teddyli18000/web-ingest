#!/usr/bin/env python3
"""Exact fixed-A/B cover for the remaining m=219, degree sequence 12^30 13^6.

Choose a degree-12 vertex v having exactly two degree-13 neighbours; such a
vertex exists because the six degree-13 vertices send at least 54 edges to the
30 degree-12 vertices, while every degree-12 vertex sees at most two of them.
Then S(v)=146, so for A=N(v), B=V\(A union {v}),

    e(B)-e(A)=219-146=73.

Exact endpoint extrema therefore leave only

    (e(A),e(B)) = (28,101) or (29,102).

The complete R(3,6,12) catalogue has 8 A28 graphs and 1 A29 graph; the complete
extreme R(4,5,23) strata have 1 B101 graph and 76 B102 graphs.  Thus there are
84 fixed graph pairs.

For a fixed pair we do NOT branch over placements of the six degree-13
vertices.  Boolean labels h choose exactly two vertices of A and four of B.
For each vertex the A--B cross degree is constrained to make its full degree
exactly 12+h.  All mixed K4 and independent-6 obstructions are then encoded.
Only 276 A--B edge variables plus label/cardinality auxiliaries remain.

SAT yields a genuine (4,6,36) certificate; UNSAT excludes the whole graph pair,
including every placement of the six high vertices.
"""
from __future__ import annotations

import argparse
import itertools
import json
import tarfile
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import d12_fixed_ab_sat as base

NA, NB = 12, 23


def add_formula(s: Solver, cnf, guard: int | None = None) -> int:
    """Add CNF, optionally guarded by a literal that disables each clause."""
    for cl in cnf.clauses:
        s.add_clause(list(cl) + ([] if guard is None else [guard]))
    return len(cnf.clauses)


def add_exact(s: Solver, lits: list[int], value: int, pool: IDPool, guard: int | None = None) -> int:
    if not 0 <= value <= len(lits):
        if guard is None:
            s.add_clause([])
        else:
            s.add_clause([guard])
        return 1
    cnf = CardEnc.equals(lits=lits, bound=value, vpool=pool, encoding=EncType.seqcounter)
    return add_formula(s, cnf, guard)


def extract_extreme(archive: Path, n: int, wanted: set[int], outdir: Path) -> dict[int, Path]:
    rows = {e: [] for e in wanted}
    with tarfile.open(archive, "r:gz") as tf:
        for info in tf.getmembers():
            if not info.isfile():
                continue
            # The archive is large; the member names encode n and edge count.
            name = info.name.rsplit("/", 1)[-1]
            if not name.startswith(f"r45{n}.") or not name.endswith(".g6"):
                continue
            try:
                e = int(name.split(".")[-2])
            except ValueError:
                continue
            if e not in wanted:
                continue
            f = tf.extractfile(info)
            if f is None:
                continue
            for raw in f:
                line = raw.decode("ascii").strip()
                if not line or line.startswith(">>"):
                    continue
                adj, ee = base.decode_graph6(line)
                if len(adj) == n and ee == e:
                    rows[e].append(line)
    out = {}
    outdir.mkdir(parents=True, exist_ok=True)
    for e in sorted(wanted):
        p = outdir / f"B{e}.g6"
        p.write_text("\n".join(rows[e]) + ("\n" if rows[e] else ""), encoding="ascii")
        out[e] = p
    return out


def prepare(r36_12: Path, r45extreme: Path, outdir: Path, manifest: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    a28 = outdir / "A28.g6"
    a29 = outdir / "A29.g6"
    c28 = base.extract_g6_stratum(r36_12, 12, 28, a28)
    c29 = base.extract_g6_stratum(r36_12, 12, 29, a29)
    bs = extract_extreme(r45extreme, 23, {101, 102}, outdir)
    c101 = sum(1 for _ in base.iter_g6(bs[101]))
    c102 = sum(1 for _ in base.iter_g6(bs[102]))
    assert (c28, c29, c101, c102) == (8, 1, 1, 76), (c28, c29, c101, c102)
    branches = []
    for ao in range(c28):
        branches.append({"case": 0, "a_edges": 28, "b_edges": 101, "a_ordinal": ao, "b_ordinal": 0})
    for bo in range(c102):
        branches.append({"case": 1, "a_edges": 29, "b_edges": 102, "a_ordinal": 0, "b_ordinal": bo})
    assert len(branches) == 84
    d = {
        "campaign": "m219-n11-0-fixedAB-labelled",
        "logical_scope": "remaining degree sequence 12^30 13^6",
        "counts": {"A28": c28, "A29": c29, "B101": c101, "B102": c102, "branches": len(branches)},
        "branches": branches,
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return d


def target_catalog(catalog_dir: Path, case: int) -> tuple[Path, Path, int, int]:
    if case == 0:
        return catalog_dir / "A28.g6", catalog_dir / "B101.g6", 28, 101
    if case == 1:
        return catalog_dir / "A29.g6", catalog_dir / "B102.g6", 29, 102
    raise ValueError(case)


def solve(catalog_dir: Path, case: int, a_ordinal: int, b_ordinal: int, solver_name: str, summary: Path, output: Path) -> int:
    ap, bp, expected_ae, expected_be = target_catalog(catalog_dir, case)
    ag6, A, ae = base.select_record(ap, a_ordinal, NA)
    bg6, B, be = base.select_record(bp, b_ordinal, NB)
    base.validate_A(A); base.validate_B(B)
    assert (ae, be) == (expected_ae, expected_be)
    da, db = base.degrees(A), base.degrees(B)

    # Cross edge variables 1..276; high-vertex labels follow.
    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    hA = [NA * NB + 1 + a for a in range(NA)]
    hB = [NA * NB + 1 + NA + b for b in range(NB)]
    pool = IDPool(start_from=NA * NB + NA + NB + 1)
    counts = {"label_cardinality": 0, "conditional_degree": 0, "k4_1a3b": 0, "k4_2a2b": 0,
              "i6_5a1b": 0, "i6_4a2b": 0, "i6_3a3b": 0, "i6_2a4b": 0}

    with Solver(name=solver_name) as s:
        counts["label_cardinality"] += add_exact(s, hA, 2, pool)
        counts["label_cardinality"] += add_exact(s, hB, 4, pool)

        # A vertex full degree = 1(anchor) + deg_A + cross = 12 + h.
        for a in range(NA):
            row = x[a]
            k0 = 11 - da[a]
            # h=0 => exact k0: clauses guarded by h. h=1 => exact k0+1: guarded by -h.
            counts["conditional_degree"] += add_exact(s, row, k0, pool, guard=hA[a])
            counts["conditional_degree"] += add_exact(s, row, k0 + 1, pool, guard=-hA[a])
        # B vertex full degree = deg_B + cross = 12 + h.
        for b in range(NB):
            col = [x[a][b] for a in range(NA)]
            k0 = 12 - db[b]
            counts["conditional_degree"] += add_exact(s, col, k0, pool, guard=hB[b])
            counts["conditional_degree"] += add_exact(s, col, k0 + 1, pool, guard=-hB[b])

        b_tri = base.subsets(B, 3, True)
        a_edges = base.subsets(A, 2, True)
        b_edges = base.subsets(B, 2, True)
        a_i5 = base.subsets(A, 5, False)
        a_i4 = base.subsets(A, 4, False)
        b_non = base.subsets(B, 2, False)
        a_i3 = base.subsets(A, 3, False)
        b_i3 = base.subsets(B, 3, False)
        a_non = base.subsets(A, 2, False)
        b_i4 = base.subsets(B, 4, False)
        for a in range(NA):
            for bs in b_tri:
                s.add_clause([-x[a][b] for b in bs]); counts["k4_1a3b"] += 1
        for aa in a_edges:
            for bb in b_edges:
                s.add_clause([-x[a][b] for a in aa for b in bb]); counts["k4_2a2b"] += 1
        for aa in a_i5:
            for b in range(NB):
                s.add_clause([x[a][b] for a in aa]); counts["i6_5a1b"] += 1
        for aa in a_i4:
            for bb in b_non:
                s.add_clause([x[a][b] for a in aa for b in bb]); counts["i6_4a2b"] += 1
        for aa in a_i3:
            for bb in b_i3:
                s.add_clause([x[a][b] for a in aa for b in bb]); counts["i6_3a3b"] += 1
        for aa in a_non:
            for bb in b_i4:
                s.add_clause([x[a][b] for a in aa for b in bb]); counts["i6_2a4b"] += 1

        sat = s.solve()
        model = set(l for l in (s.get_model() or []) if l > 0)

    result = {
        "campaign": "m219-n11-0-fixedAB-labelled", "case": case,
        "a_ordinal": a_ordinal, "b_ordinal": b_ordinal,
        "a_graph6": ag6, "b_graph6": bg6, "a_edges": ae, "b_edges": be,
        "solver": solver_name, "clauses_by_kind": counts,
        "max_var": pool.top, "status": "SAT" if sat else "UNSAT",
    }
    summary.parent.mkdir(parents=True, exist_ok=True)

    if not sat:
        summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 20

    rows = [["0"] * 36 for _ in range(36)]
    for a in range(NA):
        u = 1 + a; rows[0][u] = rows[u][0] = "1"
    for i in range(NA):
        for j in range(i + 1, NA):
            if (A[i] >> j) & 1:
                rows[1+i][1+j] = rows[1+j][1+i] = "1"
    for i in range(NB):
        for j in range(i + 1, NB):
            if (B[i] >> j) & 1:
                rows[13+i][13+j] = rows[13+j][13+i] = "1"
    for a in range(NA):
        for b in range(NB):
            if x[a][b] in model:
                rows[1+a][13+b] = rows[13+b][1+a] = "1"
    srows = ["".join(r) for r in rows]
    base.verify_full(srows, 12, 13)
    ds = sorted(r.count("1") for r in srows)
    assert ds == [12] * 30 + [13] * 6, ds
    chosen_A = [i for i,h in enumerate(hA) if h in model]
    chosen_B = [i for i,h in enumerate(hB) if h in model]
    assert len(chosen_A) == 2 and len(chosen_B) == 4
    result.update(degree_sequence=ds, high_A=chosen_A, high_B=chosen_B)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"adjacency": srows}, indent=2) + "\n", encoding="utf-8")
    summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


def self_test() -> None:
    # Guard semantics: guard=true disables an exact-cardinality formula.
    pool = IDPool(start_from=5)
    with Solver(name="cadical195") as s:
        xs = [1,2,3]; h=4
        add_exact(s, xs, 1, pool, guard=h)
        add_exact(s, xs, 2, pool, guard=-h)
        assert s.solve(assumptions=[-h,1,-2,-3])
        assert not s.solve(assumptions=[-h,1,2,-3])
        assert s.solve(assumptions=[h,1,2,-3])
        assert not s.solve(assumptions=[h,1,-2,-3])
    print("fixed-AB labelled conditional-cardinality self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare"); p.add_argument("--r36-12",type=Path,required=True);p.add_argument("--r45extreme",type=Path,required=True);p.add_argument("--outdir",type=Path,required=True);p.add_argument("--manifest",type=Path,required=True)
    q=sub.add_parser("solve");q.add_argument("--catalog-dir",type=Path,required=True);q.add_argument("--case",type=int,choices=(0,1),required=True);q.add_argument("--a-ordinal",type=int,required=True);q.add_argument("--b-ordinal",type=int,required=True);q.add_argument("--solver",default="cadical195");q.add_argument("--summary",type=Path,required=True);q.add_argument("--output",type=Path,required=True)
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="prepare":
        d=prepare(a.r36_12,a.r45extreme,a.outdir,a.manifest);print(json.dumps(d["counts"],sort_keys=True));return 0
    if a.cmd=="solve":return solve(a.catalog_dir,a.case,a.a_ordinal,a.b_ordinal,a.solver,a.summary,a.output)
    self_test();return 0

if __name__=="__main__":raise SystemExit(main())
