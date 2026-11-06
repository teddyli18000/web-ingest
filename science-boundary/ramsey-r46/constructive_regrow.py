#!/usr/bin/env python3
"""Construct a 36-vertex (4,6) Ramsey graph by jointly regenerating edges
incident to a selected vertex block, keeping a smaller known-valid core fixed.

Native libz3 via ctypes, stdlib only. A SAT result is independently verified
by bitset exhaustive K4 and independent-6 recount before saving a certificate.
"""
import argparse
import ctypes as C
import ctypes.util
import itertools
import json
import random
import time

p = argparse.ArgumentParser()
p.add_argument("--seed", required=True)
p.add_argument("--free", type=int, default=11)
p.add_argument("--rng", type=int, default=1)
p.add_argument("--timeout", type=int, default=40)
p.add_argument("--out", required=True)
a = p.parse_args()
rows = json.load(open(a.seed))["adjacency"]
n = len(rows)
if n == 35:
    rows = [r + "0" for r in rows] + ["0" * 36]
    n = 36
assert len(rows) == n and all(len(r) == n for r in rows)
assert all(rows[i][j] == rows[j][i] for i in range(n) for j in range(n))
rr = random.Random(a.rng)
near14 = a.seed.endswith("algorithm22-calibration-best-14.json")
# The 14-defect seed has a sole K4 not involving vertex 35 but involving 2.
mandatory = [35, 2] if near14 else ([35] if n == 36 else [])
free = set(mandatory)
free.update(rr.sample([v for v in range(n) if v not in free], a.free - len(free)))
free = sorted(free)
S = set(free)
pairs = list(itertools.combinations(range(n), 2))
variable = [e for e in pairs if e[0] in S or e[1] in S]
index = {e: i for i, e in enumerate(variable)}
fixed = {e: int(rows[e[0]][e[1]]) for e in pairs if e not in index}

L = C.CDLL(ctypes.util.find_library("z3") or "libz3.so.4")
P, U, I = C.c_void_p, C.c_uint, C.c_int
defs = [
    ("Z3_mk_config", P, []),
    ("Z3_mk_context", P, [P]),
    ("Z3_del_config", None, [P]),
    ("Z3_mk_bool_sort", P, [P]),
    ("Z3_mk_int_symbol", P, [P, I]),
    ("Z3_mk_string_symbol", P, [P, C.c_char_p]),
    ("Z3_mk_const", P, [P, P, P]),
    ("Z3_mk_not", P, [P, P]),
    ("Z3_mk_or", P, [P, U, C.POINTER(P)]),
    ("Z3_mk_solver", P, [P]),
    ("Z3_solver_inc_ref", None, [P, P]),
    ("Z3_solver_assert", None, [P, P, P]),
    ("Z3_solver_check", I, [P, P]),
    ("Z3_solver_get_model", P, [P, P]),
    ("Z3_model_eval", I, [P, P, P, I, C.POINTER(P)]),
    ("Z3_get_bool_value", I, [P, P]),
    ("Z3_mk_params", P, [P]),
    ("Z3_params_inc_ref", None, [P, P]),
    ("Z3_params_set_uint", None, [P, P, P, U]),
    ("Z3_solver_set_params", None, [P, P, P]),
]
for name, ret, types in defs:
    f = getattr(L, name)
    f.restype, f.argtypes = ret, types
conf = L.Z3_mk_config()
ctx = L.Z3_mk_context(conf)
L.Z3_del_config(conf)
solver = L.Z3_mk_solver(ctx)
L.Z3_solver_inc_ref(ctx, solver)
bs = L.Z3_mk_bool_sort(ctx)
v = [L.Z3_mk_const(ctx, L.Z3_mk_int_symbol(ctx, k + 1), bs)
     for k in range(len(variable))]
params = L.Z3_mk_params(ctx)
L.Z3_params_inc_ref(ctx, params)
L.Z3_params_set_uint(
    ctx, params, L.Z3_mk_string_symbol(ctx, b"timeout"), a.timeout * 1000)
L.Z3_solver_set_params(ctx, solver, params)

t0 = time.monotonic()
clauses = {4: 0, 6: 0}
for size in (4, 6):
    for subset in itertools.combinations(range(n), size):
        edges = list(itertools.combinations(subset, 2))
        must = (size == 4)
        if any(fixed[e] != must for e in edges if e in fixed):
            continue
        ix = [index[e] for e in edges if e in index]
        if not ix:
            print(json.dumps({"status": "FIXED_CORE_INVALID", "free": free}),
                  flush=True)
            raise SystemExit(1)
        lits = [L.Z3_mk_not(ctx, v[i]) if must else v[i] for i in ix]
        L.Z3_solver_assert(
            ctx, solver, L.Z3_mk_or(ctx, len(lits),
                                     (P * len(lits))(*lits)))
        clauses[size] += 1

status = L.Z3_solver_check(ctx, solver)
result = {
    "status": {1: "SAT", 0: "TIMEOUT_OR_UNKNOWN", -1: "UNSAT"}.get(
        status, str(status)),
    "seed": a.seed,
    "rng": a.rng,
    "free": free,
    "nvars": len(variable),
    "clauses": clauses,
    "wall_sec": round(time.monotonic() - t0, 3)
}
if status == 1:
    m = L.Z3_solver_get_model(ctx, solver)
    out = [list(r) for r in rows]
    for (i, j), z in zip(variable, v):
        obj = P()
        assert L.Z3_model_eval(ctx, m, z, 1, C.byref(obj)) == 1
        val = L.Z3_get_bool_value(ctx, obj)
        assert val in (-1, 1)
        out[i][j] = out[j][i] = "1" if val == 1 else "0"
    out = ["".join(r) for r in out]
    adj = [sum(1 << j for j, c in enumerate(r) if c == "1") for r in out]
    full = (1 << n) - 1

    def recount(k, mat, cand):
        if k == 0:
            return 1
        total = 0
        while cand.bit_count() >= k:
            b = cand & -cand
            i = b.bit_length() - 1
            cand -= b
            total += recount(k - 1, mat, cand & mat[i])
        return total

    k4 = recount(4, adj, full)
    comp = [full & ~mask & ~(1 << i) for i, mask in enumerate(adj)]
    i6 = recount(6, comp, full)
    assert k4 == 0 and i6 == 0, (k4, i6)
    with open(a.out, "w") as f:
        json.dump({"adjacency": out}, f, indent=1)
    result["certificate"] = a.out
    result["edges"] = sum(r.count("1") for r in out) // 2

print(json.dumps(result, sort_keys=True), flush=True)
