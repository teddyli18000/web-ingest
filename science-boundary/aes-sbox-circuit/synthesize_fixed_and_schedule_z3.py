#!/usr/bin/env python3
"""Whole-circuit affine-interface synthesis for a fixed ordered AND skeleton.

This removes all named linear boundaries. The only fixed nonlinear structure is
an ordered list of AND atoms and their affine operand forms. Linear XOR/XNOR
slots may use any primary input, any already-released AND atom, or any earlier
linear helper. We ask whether one linear slot can be removed from the original
schedule while preserving every AND operand and final output.

UNSAT applies only to the tested release/schedule template, not to AES globally.
"""
from __future__ import annotations
import argparse, json, pathlib, time
import released_and_skeleton as ras

try:
    import z3
except ImportError as e:
    raise SystemExit('z3-solver is required') from e


def original_schedule(c):
    n=sum(g['op']=='AND' for g in c['gates'])
    counts=[0]*(n+1); ai=0
    for g in c['gates']:
        if g['op']=='AND': ai+=1
        else: counts[ai]+=1
    assert sum(counts)==len(c['gates'])-n
    return counts


def bv(v,D): return z3.BitVecVal(v,D)


def select_expr(sel, sources):
    e=sources[-1]
    for i in range(len(sources)-2,-1,-1):
        e=z3.If(sel==i,sources[i],e)
    return e


def build_problem(sk,schedule,timeout_ms):
    D=sk['const_bit']+1; C=1<<sk['const_bit']; n=sk['n_and']
    # Int selectors + BitVec signal values make this a mixed quantifier-free
    # problem; use the general solver rather than pretending it is pure QF_BV.
    s=z3.Solver(); s.set(timeout=timeout_ms)
    sources=[bv(1<<i,D) for i in range(8)]
    meta=[]; and_selectors=[]; lin_no=0
    for ai in range(n+1):
        for _ in range(schedule[ai]):
            p=z3.Int(f'p_{lin_no}'); q=z3.Int(f'q_{lin_no}'); neg=z3.Bool(f'n_{lin_no}')
            s.add(p>=0,q>=0,p<q,q<len(sources))
            v=z3.BitVec(f'L_{lin_no}',D)
            pv=select_expr(p,sources); qv=select_expr(q,sources)
            s.add(v == (pv ^ qv ^ z3.If(neg,bv(C,D),bv(0,D))))
            sources.append(v); meta.append(('linear',lin_no,p,q,neg,len(sources)-1)); lin_no+=1
        if ai<n:
            sels=[]
            for side in ('a','b'):
                t=sk['ands'][ai][side]
                q=z3.Int(f'and_{ai}_{side}')
                s.add(q>=0,q<len(sources),select_expr(q,sources)==bv(t,D))
                sels.append(q)
            and_selectors.append(tuple(sels))
            sources.append(bv(1<<(8+ai),D)); meta.append(('and',ai,len(sources)-1))
    out_selectors=[]
    for oi,t in enumerate(sk['outputs']):
        q=z3.Int(f'out_{oi}')
        s.add(q>=0,q<len(sources),select_expr(q,sources)==bv(t,D))
        out_selectors.append(q)
    return s,meta,and_selectors,out_selectors


def reconstruct(model,sk,schedule,meta,and_selectors,out_selectors):
    names=[f'x{i}' for i in range(8)]; gates=[]; mpos=0
    n=sk['n_and']
    for ai in range(n+1):
        for _ in range(schedule[ai]):
            rec=meta[mpos]; mpos+=1; assert rec[0]=='linear'
            _,_,p,q,neg,_=rec
            pi=model.eval(p,model_completion=True).as_long(); qi=model.eval(q,model_completion=True).as_long()
            nv=z3.is_true(model.eval(neg,model_completion=True))
            out=f'w{len(gates)}'
            gates.append({'op':'XNOR' if nv else 'XOR','a':names[pi],'b':names[qi],'out':out})
            names.append(out)
        if ai<n:
            rec=meta[mpos]; mpos+=1; assert rec[0]=='and'
            qa,qb=and_selectors[ai]
            ia=model.eval(qa,model_completion=True).as_long(); ib=model.eval(qb,model_completion=True).as_long()
            out=f'w{len(gates)}'; gates.append({'op':'AND','a':names[ia],'b':names[ib],'out':out}); names.append(out)
    outs=[names[model.eval(q,model_completion=True).as_long()] for q in out_selectors]
    return ras.prune({'gates':gates,'outputs':outs})


def solve(family,remove_interval,timeout_ms,outdir):
    base=ras.load_circuit(family); assert ras.independent_check(base)[0]
    sk=ras.extract_skeleton(base); sched0=original_schedule(base); sched=list(sched0)
    if remove_interval is not None:
        if remove_interval<0 or remove_interval>=len(sched) or sched[remove_interval]==0:
            return {'family':family,'remove_interval':remove_interval,'status':'skipped_empty_interval','schedule_original':sched0}
        sched[remove_interval]-=1
    target_linear=sum(sched); t0=time.time()
    solver,meta,ands,outs=build_problem(sk,sched,timeout_ms)
    r=solver.check(); elapsed=time.time()-t0
    res={'family':family,'remove_interval':remove_interval,'status':str(r),'elapsed_s':round(elapsed,3),
         'base_gates':len(base['gates']),'n_and':sk['n_and'],'base_linear':sum(sched0),'target_linear':target_linear,
         'schedule_original':sched0,'schedule_tested':sched}
    if r==z3.sat:
        c=reconstruct(solver.model(),sk,sched,meta,ands,outs)
        ok=ras.independent_check(c); assert ok[0],ok
        res['candidate_gates']=len(c['gates']); res['verified_all_256']=True
        pathlib.Path(outdir).mkdir(parents=True,exist_ok=True)
        pathlib.Path(outdir,'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
    elif r==z3.unknown:
        res['reason_unknown']=solver.reason_unknown()
    return res


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--family',choices=sorted(ras.SOURCES),default='fs-101')
    ap.add_argument('--remove-interval',type=int); ap.add_argument('--timeout-ms',type=int,default=240000)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    r=solve(args.family,args.remove_interval,args.timeout_ms,args.out)
    pathlib.Path(args.out).mkdir(parents=True,exist_ok=True)
    pathlib.Path(args.out,'summary.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r),flush=True)

if __name__=='__main__': main()
