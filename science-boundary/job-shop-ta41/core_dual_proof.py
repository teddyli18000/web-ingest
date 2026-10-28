#!/usr/bin/env python3
"""Produce an independently checkable rational dual certificate for ta41.

Primal: min sum x_i, x_i binary, sum_{i in core} x_i >=1 for every
CP-SAT certified infeasible assumption core.
Dual fractional packing: max sum y_core, sum_{core containing i} y_core<=1.

We solve with a floating LP, then SCALE DOWN to conservative integer
coefficients and check EVERY inequality using exact Python integer
arithmetic. Any feasible dual weight sum L proves min #violated baseline
adjacent precedences >= ceil(L), independently of the floating solver.
"""
import argparse
import json
import math
from pathlib import Path
from ortools.linear_solver import pywraplp

SCALE=1000000000
def main(inp,out):
    data=json.loads(inp.read_text())
    assert data['target']==2005 and data['baseline']==2006
    cores=[sorted(set(c)) for c in data['core_sets']]
    solver=pywraplp.Solver.CreateSolver('GLOP')
    assert solver is not None
    y=[solver.NumVar(0,solver.infinity(),'y_%d'%j) for j in range(len(cores))]
    caps=[solver.RowConstraint(0,1,'arc_%d'%i) for i in range(580)]
    for j,c in enumerate(cores):
        for i in c:caps[i].SetCoefficient(y[j],1)
    solver.Maximize(solver.Sum(y))
    status=solver.Solve()
    assert status==pywraplp.Solver.OPTIMAL,status
    # Intentionally weaken and floor the solution to absorb LP tolerance;
    # all surviving exact rational arithmetic is checked independently.
    def verify(nums):
        used=[0]*580
        for j,c in enumerate(cores):
            if nums[j]:
                for i in c: used[i]+=nums[j]
        return max(used), sum(nums), used
    factor=0.99999
    for attempt in range(12):
        numerators=[max(0,int(math.floor(max(0,y[j].solution_value())*SCALE*factor)))
                    for j in range(len(cores))]
        maxload,score,used=verify(numerators)
        if maxload<=SCALE:break
        factor*=0.99
    assert maxload<=SCALE
    degree=max(used)
    positive={str(i):n for i,n in enumerate(numerators) if n}
    report={
       'problem':'rational fractional core packing of proven UNSAT subproblems',
       'target':2005,'incumbent':2006,
       'cores':len(cores),'machine_arc_variables':580,
       'floating_lp_objective':solver.Objective().Value(),
       'rational_denominator':SCALE,
       'rational_total_numerator':score,
       'max_arc_capacity_numerator':degree,
       'exact_integer_inequalities_verified':True,
       'portable_lower_bound':(score+SCALE-1)//SCALE,
       'nonzero_core_weights':positive,
       'certificate_semantics':'Every viable <=2005 schedule must violate at least ceil(sum y) baseline adjacent precedences; y satisfies sum_{cores containing any arc} y <= 1 by exact integer checks.',
       'source_core_file':str(inp)
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='nonzero_core_weights'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path(__file__).parent/'results'/'core-seed4107'/'core-analysis.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'core-dual.json')
    a=p.parse_args();main(a.input,a.out)
