#!/usr/bin/env python3
"""Joint factor-owner / product-cell injection SAT for the first support-3 family.

The support<=2 factor owner map is not frozen.  We jointly choose:
  1. for every regular factor z, one owner f(z) in its exact support S(z), with
     each owner fiber a confusability clique; and
  2. for every product point having at least one of the four support-3 exception
     coordinates, one core cell in its exact support rectangle.

For a variable product point p assigned cell (a,b), hard clauses forbid every
regular pair (u,v) that could simultaneously be assigned owners (a,b) while
remaining compatible with p.  Variable-variable compatible points are also
forbidden from sharing a cell.

SAT therefore gives a full 429x429 clique-fiber injection and proves raw core
gain <= 0 for this family.  UNSAT proves that no product injection of this
factorized-regular form exists, even after globally reorienting the regular
support<=2 owner map.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from pysat.solvers import Glucose4

import bpz_joint_row_defects_maxsat as J
from bpz_support3_first_mus_residual_prize import EXCEPTIONS


def product_conflict(ring, p, q):
    return q[0] in ring.NB[p[0]] and q[1] in ring.NB[p[1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tan_root', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    t0 = time.time()

    _base, ring, B, _fam = J.load_geometry(args.tan_root.resolve())
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

    # Owner-choice literals for every regular factor.
    own = {}
    eligible = defaultdict(list)
    for z in regular:
        lits = []
        for a in support[z]:
            v = nxt; nxt += 1; own[(z,a)] = v; lits.append(v); eligible[a].append((z,v))
        solver.add_clause(lits); clauses['factor_atleast1_owner'] += 1
        for i in range(len(lits)):
            for j in range(i+1, len(lits)):
                solver.add_clause([-lits[i], -lits[j]]); clauses['factor_atmost1_owner'] += 1

    # Owner fibers of regular factors must be cliques.
    owner_pair_checks = 0
    for a, es in eligible.items():
        for i in range(len(es)):
            z, vz = es[i]
            for j in range(i+1, len(es)):
                w, vw = es[j]; owner_pair_checks += 1
                if w not in ring.NB[z]:
                    solver.add_clause([-vz, -vw]); clauses['owner_nonclique'] += 1

    F = regular + list(exceptions)
    variable = [(x,y) for x in F for y in F if x in E or y in E]
    if len(variable) != 3416: raise RuntimeError(('variable census', len(variable)))

    # Product-cell choices use the entire exact support rectangle.
    pchoice = []; by_cell = defaultdict(list)
    for i, p in enumerate(variable):
        x,y = p; cm = {}; lits = []
        for a in support[x]:
            for b in support[y]:
                c=(a,b)
                if c in cm: continue
                v=nxt; nxt+=1; cm[c]=v; lits.append(v); by_cell[c].append((i,v))
        solver.add_clause(lits); clauses['product_atleast1_cell'] += 1
        for q in range(len(lits)):
            for r in range(q+1,len(lits)):
                solver.add_clause([-lits[q],-lits[r]]); clauses['product_atmost1_cell'] += 1
        pchoice.append(cm)

    # If p uses cell (a,b), no compatible regular pair may simultaneously own a,b.
    # This is the exact variable-vs-frozen-fiber condition, now with owner choices live.
    guard_checks = 0
    for i,p in enumerate(variable):
        for (a,b), xp in pchoice[i].items():
            Ea = eligible.get(a,())
            Eb = eligible.get(b,())
            for u,ua in Ea:
                for v,vb in Eb:
                    guard_checks += 1
                    if not product_conflict(ring,p,(u,v)):
                        solver.add_clause([-xp,-ua,-vb]); clauses['product_regular_guard'] += 1

    # Variable product points sharing a cell must themselves conflict.
    variable_pair_checks = 0
    for c, es in by_cell.items():
        for i in range(len(es)):
            pi, xi = es[i]; p=variable[pi]
            for j in range(i+1,len(es)):
                qj, xj = es[j]; q=variable[qj]; variable_pair_checks += 1
                if not product_conflict(ring,p,q):
                    solver.add_clause([-xi,-xj]); clauses['product_product_nonclique'] += 1

    ts=time.time(); sat=solver.solve(); solve_seconds=time.time()-ts
    out={
        'method':'joint-factor-owner-product-cell-injection-sat',
        'regular_factors':len(regular),'exceptions':list(exceptions),'factor_count':len(F),
        'variable_product_points':len(variable),'sat_variables':nxt-1,
        'sat_clauses':sum(clauses.values()),'clause_counts':dict(clauses),
        'owner_pair_checks':owner_pair_checks,'product_regular_guard_checks':guard_checks,
        'variable_pair_checks':variable_pair_checks,'status':'sat' if sat else 'unsat',
        'solve_seconds':solve_seconds,'wall_seconds':time.time()-t0,
    }
    if sat:
        model={z for z in solver.get_model() if z>0}
        fmap={}
        for z in regular:
            got=[a for a in support[z] if own[(z,a)] in model]
            if len(got)!=1: raise RuntimeError(('owner cardinality',z,got))
            fmap[z]=got[0]
        assign={}
        for i,p in enumerate(variable):
            got=[c for c,v in pchoice[i].items() if v in model]
            if len(got)!=1: raise RuntimeError(('product cardinality',p,got))
            assign[p]=got[0]
        # Full independent replay of all 429^2 fiber memberships.
        fibers=defaultdict(list)
        for u in regular:
            for v in regular: fibers[(fmap[u],fmap[v])].append((u,v))
        for p,c in assign.items(): fibers[c].append(p)
        checks=0
        for c,L in fibers.items():
            for i,p in enumerate(L):
                if c[0] not in support[p[0]] or c[1] not in support[p[1]]:
                    raise RuntimeError(('support replay',c,p))
                for q in L[i+1:]:
                    checks+=1
                    if not product_conflict(ring,p,q): raise RuntimeError(('nonclique replay',c,p,q))
        if sum(map(len,fibers.values())) != len(F)**2: raise RuntimeError('full point count drift')
        out.update(
            replay_ok=True,replay_same_cell_pairs=checks,used_core_cells=len(fibers),
            max_fiber_size=max(map(len,fibers.values())),
            regular_owner_assignment=[[z,fmap[z]] for z in regular],
            variable_product_assignment=[[p[0],p[1],assign[p][0],assign[p][1]] for p in variable],
            conclusion='full 429x429 family admits a replayed joint factor/product clique-fiber injection; raw core gain is nonpositive',
        )
    else:
        out['conclusion']='joint reorientation of every support<=2 factor owner is still insufficient for a full product-level injection'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('regular_owner_assignment','variable_product_assignment')},sort_keys=True))
    solver.delete()

if __name__=='__main__': main()
