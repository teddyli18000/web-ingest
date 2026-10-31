#!/usr/bin/env python3
"""Extract a small assumption core for the joint factor/product injection failure.

Both regular support<=2 factors and exception-containing product points are made
optional with selector assumptions.  With every selector enabled this is the
same factorized product-injection question as bpz_joint_factor_product_injection_sat.py.
An UNSAT core therefore identifies a finite subset of regular factors and product
points that already defeats every factor-owner / product-cell clique-fiber injection.

The returned core is greedily deletion-minimized by exact SAT calls.  This is a
proof-localization tool, not a score result.  The output also computes the exact
raw BxB prize of the core product points alone (selected new points minus distinct
core cells deleted, with exact new-new conflicts) to distinguish proof failure
from an actual positive construction.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from pysat.solvers import Glucose4

import bpz_joint_row_defects_maxsat as J
from bpz_support3_first_mus_residual_prize import EXCEPTIONS


def product_conflict(ring, p, q):
    return q[0] in ring.NB[p[0]] and q[1] in ring.NB[p[1]]


def build(root: Path):
    _base, ring, B, _fam = J.load_geometry(root)
    B = set(B)
    exceptions = tuple(map(int, EXCEPTIONS)); E = set(exceptions)
    support = {}
    regular = []
    for z in range(ring.n):
        if z in B: continue
        S = tuple(sorted(ring.NB[z] & B))
        if 1 <= len(S) <= 2:
            regular.append(z); support[z] = S
    for z in exceptions:
        S = tuple(sorted(ring.NB[z] & B)); support[z] = S
        if len(S) != 3: raise RuntimeError(('exception support', z, S))
    if len(regular) != 425: raise RuntimeError(('regular census', len(regular)))

    solver = Glucose4(with_proof=False)
    nxt = 1; clauses = Counter()

    # Optional regular factors.  When active, choose exactly one owner.
    fsel = {}; own = {}; eligible = defaultdict(list)
    for z in regular:
        s = nxt; nxt += 1; fsel[z] = s
        lits = []
        for a in support[z]:
            v = nxt; nxt += 1; own[(z,a)] = v; lits.append(v); eligible[a].append((z,v))
            solver.add_clause([-v, s]); clauses['owner_implies_factor'] += 1
        solver.add_clause([-s, *lits]); clauses['factor_requires_owner'] += 1
        for i in range(len(lits)):
            for j in range(i+1,len(lits)):
                solver.add_clause([-lits[i],-lits[j]]); clauses['factor_atmost1_owner'] += 1

    owner_pair_checks=0
    for a,es in eligible.items():
        for i in range(len(es)):
            z,vz=es[i]
            for j in range(i+1,len(es)):
                w,vw=es[j]; owner_pair_checks+=1
                if w not in ring.NB[z]:
                    solver.add_clause([-vz,-vw]); clauses['owner_nonclique'] += 1

    F=regular+list(exceptions)
    variable=[(x,y) for x in F for y in F if x in E or y in E]
    if len(variable)!=3416: raise RuntimeError(('variable census',len(variable)))

    # Optional exception-containing product points.
    psel=[]; pchoice=[]; by_cell=defaultdict(list)
    for i,p in enumerate(variable):
        s=nxt; nxt+=1; psel.append(s)
        x,y=p; cm={}; lits=[]
        for a in support[x]:
            for b in support[y]:
                c=(a,b)
                if c in cm: continue
                v=nxt; nxt+=1; cm[c]=v; lits.append(v); by_cell[c].append((i,v))
                solver.add_clause([-v,s]); clauses['cell_implies_product'] += 1
        solver.add_clause([-s,*lits]); clauses['product_requires_cell'] += 1
        for q in range(len(lits)):
            for r in range(q+1,len(lits)):
                solver.add_clause([-lits[q],-lits[r]]); clauses['product_atmost1_cell'] += 1
        pchoice.append(cm)

    guard_checks=0
    for i,p in enumerate(variable):
        for (a,b),xp in pchoice[i].items():
            for u,ua in eligible.get(a,()):
                for v,vb in eligible.get(b,()):
                    guard_checks+=1
                    if not product_conflict(ring,p,(u,v)):
                        solver.add_clause([-xp,-ua,-vb]); clauses['product_regular_guard'] += 1

    variable_pair_checks=0
    for c,es in by_cell.items():
        for i in range(len(es)):
            pi,xi=es[i]; p=variable[pi]
            for j in range(i+1,len(es)):
                qj,xj=es[j]; q=variable[qj]; variable_pair_checks+=1
                if not product_conflict(ring,p,q):
                    solver.add_clause([-xi,-xj]); clauses['product_product_nonclique'] += 1

    return solver,ring,B,regular,exceptions,support,variable,fsel,psel,clauses,owner_pair_checks,guard_checks,variable_pair_checks


def shrink_core(solver, core, max_passes=10):
    core=list(dict.fromkeys(core)); calls=0; changed=True; passes=0
    while changed and passes<max_passes:
        changed=False; passes+=1; i=0
        while i<len(core):
            trial=core[:i]+core[i+1:]; calls+=1
            if not solver.solve(assumptions=trial):
                c=solver.get_core() or trial
                cs=set(c)
                new=[x for x in trial if x in cs]
                if len(new)<len(core):
                    core=new; changed=True; i=0; continue
                core=trial; changed=True; i=0; continue
            i+=1
    return core,calls,passes


def exact_raw_prize(ring,support,points):
    points=list(points); n=len(points)
    cells=sorted({(a,b) for x,y in points for a in support[x] for b in support[y]})
    ci={c:i for i,c in enumerate(cells)}
    w=WCNF(); y0=n+1; conflicts=0; impl=0
    for i,p in enumerate(points):
        for a in support[p[0]]:
            for b in support[p[1]]:
                w.append([-(i+1),y0+ci[(a,b)]]); impl+=1
    for i,p in enumerate(points):
        for j in range(i+1,n):
            if product_conflict(ring,p,points[j]):
                w.append([-(i+1),-(j+1)]); conflicts+=1
    for i in range(n): w.append([i+1],weight=1)
    for j in range(len(cells)): w.append([-(y0+j)],weight=1)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute(); cost=rc2.cost
    if model is None: raise RuntimeError('RC2 no model')
    pos={z for z in model if z>0}; sel=[points[i] for i in range(n) if i+1 in pos]
    lost={(a,b) for p in sel for a in support[p[0]] for b in support[p[1]]}
    gain=len(sel)-len(lost)
    if gain!=n-cost: raise RuntimeError(('prize drift',gain,n-cost))
    return {'candidate_count':n,'core_cell_count':len(cells),'conflict_clauses':conflicts,'support_implications':impl,'selected_count':len(sel),'deleted_core_cells':len(lost),'exact_raw_gain':gain,'selected_points':[list(p) for p in sel],'deleted_cells':[list(c) for c in sorted(lost)]}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); a=ap.parse_args(); t0=time.time()
    solver,ring,B,regular,exceptions,support,variable,fsel,psel,clauses,opc,gc,vpc=build(a.tan_root.resolve())
    assumptions=[fsel[z] for z in regular]+psel
    if solver.solve(assumptions=assumptions): raise RuntimeError('expected full model UNSAT')
    initial=solver.get_core() or assumptions
    shrunk,calls,passes=shrink_core(solver,initial)
    f_of={v:z for z,v in fsel.items()}; p_of={v:i for i,v in enumerate(psel)}
    cf=[f_of[x] for x in shrunk if x in f_of]; cp=[variable[p_of[x]] for x in shrunk if x in p_of]
    # Verify deletion-minimality explicitly.
    minimal=True; witness_sat=[]
    for i,x in enumerate(shrunk):
        sat=solver.solve(assumptions=shrunk[:i]+shrunk[i+1:])
        witness_sat.append(bool(sat)); minimal &= bool(sat)
    prize=exact_raw_prize(ring,support,cp) if cp else None
    out={'method':'joint-factor-product-injection-assumption-core','full_regular_factors':len(regular),'full_variable_products':len(variable),'initial_core_size':len(initial),'shrunk_core_size':len(shrunk),'core_regular_factor_count':len(cf),'core_product_point_count':len(cp),'core_regular_factors':cf,'core_product_points':[list(p) for p in cp],'deletion_minimal':minimal,'remove_one_sat':witness_sat,'shrink_sat_calls':calls,'shrink_passes':passes,'sat_clauses':sum(clauses.values()),'clause_counts':dict(clauses),'owner_pair_checks':opc,'guard_checks':gc,'variable_pair_checks':vpc,'core_product_raw_prize':prize,'wall_seconds':time.time()-t0}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('core_regular_factors','core_product_points','remove_one_sat','core_product_raw_prize')},sort_keys=True))
    print('core_regular_factors',cf); print('core_product_points',cp); print('raw_prize',json.dumps(prize,sort_keys=True))
    solver.delete()

if __name__=='__main__': main()
