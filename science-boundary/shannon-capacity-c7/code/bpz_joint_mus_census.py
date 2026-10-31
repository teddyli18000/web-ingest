#!/usr/bin/env python3
"""Census multiple deletion-minimal MUSes of the joint factor/product injection SAT.

The first MUS has only 10 assumptions, but a proof obstruction need not be unique.
We explore a bounded hitting-set tree: each UNSAT node is shrunk to a deletion-
minimal core, then children disable one core assumption.  This exposes the basin
of small, structurally distinct injection frustrations without enumerating the
184k-point product prize directly.

Output is diagnostic/search state, not a score theorem.  Its union of factors and
product coordinates is intended as the next exact real-prize candidate basin.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, deque
from pathlib import Path

from bpz_joint_factor_product_core import build, shrink_core


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--max-cores',type=int,default=200); ap.add_argument('--max-states',type=int,default=2000); ap.add_argument('--max-disabled',type=int,default=3); a=ap.parse_args(); t0=time.time()
    solver,ring,B,regular,exceptions,support,variable,fsel,psel,clauses,opc,gc,vpc=build(a.tan_root.resolve())
    all_ass=[fsel[z] for z in regular]+psel; aset=set(all_ass)
    f_of={v:z for z,v in fsel.items()}; p_of={v:i for i,v in enumerate(psel)}
    def label(s):
        if s in f_of: return ('f',f_of[s])
        i=p_of[s]; return ('p',variable[i][0],variable[i][1])
    # BFS over disabled-selector sets. Product selectors first in branching order to
    # expose alternative product obstructions before globally deleting factors.
    q=deque([frozenset()]); seen_disabled={frozenset()}; seen_cores=set(); cores=[]; states=0; sat_nodes=0; unsat_nodes=0; shrink_calls=0
    while q and len(cores)<a.max_cores and states<a.max_states:
        disabled=q.popleft(); states+=1
        assumptions=[s for s in all_ass if s not in disabled]
        if solver.solve(assumptions=assumptions): sat_nodes+=1; continue
        unsat_nodes+=1
        core=solver.get_core() or assumptions
        core,calls,_passes=shrink_core(solver,core); shrink_calls+=calls
        sig=tuple(sorted(core))
        if sig not in seen_cores:
            seen_cores.add(sig)
            cf=sorted(f_of[s] for s in core if s in f_of)
            cp=sorted(variable[p_of[s]] for s in core if s in p_of)
            rec={'size':len(core),'regular_factors':cf,'product_points':[list(p) for p in cp],'disabled_depth':len(disabled)}
            cores.append(rec); print(json.dumps({'core_index':len(cores)-1,**rec},sort_keys=True),flush=True)
        if len(disabled)<a.max_disabled:
            branch=sorted(core,key=lambda s:(0 if s in p_of else 1,label(s)))
            for s in branch:
                nd=frozenset((*disabled,s))
                if nd not in seen_disabled:
                    seen_disabled.add(nd); q.append(nd)
    fcnt=Counter(); pcnt=Counter(); pfirst=Counter(); psecond=Counter(); sizes=Counter()
    for c in cores:
        sizes[c['size']]+=1
        fcnt.update(c['regular_factors'])
        for p in c['product_points']:
            t=tuple(p); pcnt[t]+=1; pfirst[p[0]]+=1; psecond[p[1]]+=1
    union_f=sorted(fcnt); union_p=sorted(pcnt)
    out={'method':'bounded-joint-injection-mus-census','max_cores':a.max_cores,'max_states':a.max_states,'max_disabled':a.max_disabled,'states_visited':states,'sat_nodes':sat_nodes,'unsat_nodes':unsat_nodes,'queue_remaining':len(q),'core_count':len(cores),'core_size_histogram':{str(k):v for k,v in sorted(sizes.items())},'union_regular_factor_count':len(union_f),'union_regular_factors':union_f,'union_product_point_count':len(union_p),'union_product_points':[list(p) for p in union_p],'top_regular_factors':[[z,n] for z,n in fcnt.most_common(50)],'top_product_points':[[list(p),n] for p,n in pcnt.most_common(50)],'top_product_first':[[z,n] for z,n in pfirst.most_common(50)],'top_product_second':[[z,n] for z,n in psecond.most_common(50)],'shrink_sat_calls':shrink_calls,'cores':cores,'wall_seconds':time.time()-t0}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('cores','union_regular_factors','union_product_points','top_regular_factors','top_product_points','top_product_first','top_product_second')},sort_keys=True))
    print('top_regular',out['top_regular_factors'][:20]); print('top_second',out['top_product_second'][:20])
    solver.delete()

if __name__=='__main__': main()
