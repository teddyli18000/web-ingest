#!/usr/bin/env python3
"""Exact static SAT for a fixed lucky degree-16 neighbourhood in R(4,6,36).

Fix vertex 0 to degree 16 and A={1,...,16} to one complete R(3,6,16)
catalogue graph.  B={17,...,35} has 19 vertices and remains fully variable,
as do all A--B edges.  The encoding contains every K4 / independent-6 clause,
exact global degree bounds 11..17, a sound lex ordering of the unlabeled B
vertices by their 16-bit cross rows, and the lucky-vertex edge window

    57 <= e(B) <= e(A)+32.

Thus SAT is a genuine 36-vertex certificate and UNSAT eliminates the fixed A
from the lucky-d=16 branch.  The first 630 DIMACS variables are the graph
edges in sat_r46.py order, so SAT models can be decoded by the existing
independent verifier.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import degree17_static_sat_v2 as card

N = 36
A = tuple(range(1, 17))
B = tuple(range(17, 36))
MIN_DEG, MAX_DEG = 11, 17
B_EDGE_MIN = 57  # exact minimum for R(4,5,19)


def decode_graph6(line: str) -> list[str]:
    s = line.strip()
    if not s or s.startswith(">>"):
        raise ValueError("expected one short graph6 record")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 records are supported")
    bits: list[int] = []
    for ch in s[1:]:
        v = ord(ch) - 63
        if not 0 <= v < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((v >> shift) & 1 for shift in range(5, -1, -1))
    need = n * (n - 1) // 2
    if len(bits) < need:
        raise ValueError("truncated graph6 record")
    rows = [["0"] * n for _ in range(n)]
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]: rows[i][j] = rows[j][i] = "1"
            p += 1
    return ["".join(r) for r in rows]


def edge_count(rows: list[str]) -> int:
    return sum(r.count("1") for r in rows) // 2


def valid_r36(rows: list[str]) -> bool:
    n = len(rows)
    for vs in itertools.combinations(range(n), 3):
        if all(rows[u][v] == "1" for u, v in itertools.combinations(vs, 2)):
            return False
    for vs in itertools.combinations(range(n), 6):
        if all(rows[u][v] == "0" for u, v in itertools.combinations(vs, 2)):
            return False
    return True


def load_edge_stratum(path: Path, wanted_edges: int) -> list[list[str]]:
    out = []
    for line in path.read_text(encoding="ascii").splitlines():
        if not line.strip(): continue
        rows = decode_graph6(line)
        if len(rows) != 16: continue
        if edge_count(rows) == wanted_edges:
            if not valid_r36(rows):
                raise ValueError("catalogue record failed R(3,6,16) validation")
            out.append(rows)
    return out


def edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt; nxt += 1
    return edge, nxt - 1


def fixed_edges(edge: list[list[int]], neighborhood: list[str]) -> dict[int, bool]:
    fixed: dict[int, bool] = {}
    for v in range(1, N): fixed[edge[0][v]] = v <= 16
    for i in range(16):
        for j in range(i + 1, 16):
            fixed[edge[i + 1][j + 1]] = neighborhood[i][j] == "1"
    return fixed


def simplified_ramsey_clause(vertices, edge, fixed, positive: bool):
    out = []
    for u, v in itertools.combinations(vertices, 2):
        var = edge[u][v]; value = fixed.get(var)
        if value is None:
            out.append(var if positive else -var); continue
        if value if positive else not value:
            return None
    if not out:
        raise ValueError("fixed branch violates Ramsey constraint")
    return out


def emit(out, clause: list[int]) -> None:
    out.write(" ".join(map(str, clause)) + " 0\n")


def add_b_lex(out, edge, next_var: int) -> tuple[int, int]:
    clauses = 0
    for b, c in zip(B, B[1:]):
        pref = list(range(next_var, next_var + len(A))); next_var += len(A)
        emit(out, [pref[0]]); clauses += 1
        for i, a in enumerate(A):
            p, x, y = pref[i], edge[a][b], edge[a][c]
            emit(out, [-p, -x, y]); clauses += 1
            if i + 1 == len(A): continue
            q = pref[i + 1]
            for cl in ([-q,p],[-q,-x,y],[-q,x,-y],[-p,-x,-y,q],[-p,x,y,q]):
                emit(out, list(cl)); clauses += 1
    return next_var, clauses


def degree_clauses(edge, fixed, next_var: int) -> tuple[list[list[int]], int]:
    clauses = []
    for v in range(N):
        free=[]; fixed_true=0
        for u in range(N):
            if u == v: continue
            var=edge[v][u]; val=fixed.get(var)
            if val is None: free.append(var)
            elif val: fixed_true += 1
        lo=max(0, MIN_DEG-fixed_true); hi=min(len(free), MAX_DEG-fixed_true)
        if lo > hi: return [[]], next_var
        upper,next_var=card.atmost_seq(free,hi,next_var)
        lower,next_var=card.atmost_seq([-x for x in free],len(free)-lo,next_var)
        clauses.extend(upper); clauses.extend(lower)
    return clauses,next_var


def generate(path: Path, neighborhood: list[str], stratum_ordinal: int) -> dict:
    ae=edge_count(neighborhood); bmax=ae+32
    if bmax < B_EDGE_MIN: raise ValueError("lucky window empty")
    edge, edge_vars = edge_variables(); fixed=fixed_edges(edge,neighborhood)
    header_fmt="p cnf {vars:10d} {clauses:12d}\n"
    header=header_fmt.format(vars=edge_vars,clauses=0)
    counts={"fixed_units":0,"b_lex":0,"k4":0,"ind6":0,"degree":0,"lucky_b_edges":0}
    next_var=edge_vars+1
    with path.open("w+",encoding="ascii",buffering=1024*1024) as out:
        out.write(header)
        for var,val in sorted(fixed.items()): emit(out,[var if val else -var]); counts["fixed_units"]+=1
        next_var,counts["b_lex"]=add_b_lex(out,edge,next_var)
        for vs in itertools.combinations(range(N),4):
            cl=simplified_ramsey_clause(vs,edge,fixed,False)
            if cl is not None: emit(out,cl); counts["k4"]+=1
        for vs in itertools.combinations(range(N),6):
            cl=simplified_ramsey_clause(vs,edge,fixed,True)
            if cl is not None: emit(out,cl); counts["ind6"]+=1
        dcls,next_var=degree_clauses(edge,fixed,next_var)
        for cl in dcls: emit(out,cl)
        counts["degree"]=len(dcls)
        bedges=[edge[u][v] for u,v in itertools.combinations(B,2)]
        up,next_var=card.atmost_seq(bedges,bmax,next_var)
        lo,next_var=card.atmost_seq([-x for x in bedges],len(bedges)-B_EDGE_MIN,next_var)
        for cl in up+lo: emit(out,cl)
        counts["lucky_b_edges"]=len(up)+len(lo)
        nvars=next_var-1; nclauses=sum(counts.values())
        final=header_fmt.format(vars=nvars,clauses=nclauses)
        if len(final)!=len(header): raise RuntimeError("DIMACS header width changed")
        out.seek(0); out.write(final)
    return {"a_edges":ae,"b_edge_min":B_EDGE_MIN,"b_edge_max":bmax,
            "stratum_ordinal":stratum_ordinal,"variables":nvars,"edge_variables":edge_vars,
            "clauses":nclauses,**counts,"path":str(path)}


def self_test() -> None:
    card.self_test()
    # The lex ordering has one adjacent-pair block per B pair and preserves the
    # first 630 graph-edge variables; cardinality counters are separately tested.
    e,last=edge_variables(); assert last==630 and len(B)==19 and len(A)==16
    assert len([e[u][v] for u,v in itertools.combinations(B,2)])==171
    print("degree16 lucky static SAT self-test ok")


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--catalog",type=Path); ap.add_argument("--edge-count",type=int,default=32)
    ap.add_argument("--ordinal",type=int); ap.add_argument("--output",type=Path); ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test: self_test(); return 0
    if args.catalog is None or args.ordinal is None or args.output is None: ap.error("catalog, ordinal, output required")
    graphs=load_edge_stratum(args.catalog,args.edge_count)
    if not 0<=args.ordinal<len(graphs): ap.error(f"ordinal must be 0..{len(graphs)-1}")
    result=generate(args.output,graphs[args.ordinal],args.ordinal)
    result["edge_stratum_count"]=len(graphs)
    print(json.dumps(result,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
