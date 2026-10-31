#!/usr/bin/env python3
"""Exact CaDiCaL synthesis of a late released-AND tail of NIST G103.

The pure 22-gate suffix is only one representation boundary.  Starting before a
chosen late AND atom, this encoder replaces the whole remaining tail while
keeping the ordered nonlinear functions of the G103 released-AND skeleton fixed.
Each local linear gate may be XOR or XNOR of any two currently available signals.
Before fixed AND atom i is released, both of its exact affine operands must be
materialized; the atom is then appended as a new independent basis vector.  At
the end, all eight exact AES output affine forms must be available.

The model is CNF over affine-vector bits plus one-hot source-pair selectors and is
solved with PySAT CaDiCaL.  For a fixed linear-slot schedule it is exact for the
represented fixed-prefix/fixed-ordered-AND family.  SAT is reconstructed into a
full circuit and independently checked on all 256 AES inputs.  Timeout is
inconclusive.  UNSAT is family-local; a publication-strength lower-bound claim
would additionally require a proof/certificate route.

For G103 start=28, the original local schedule is [0,0,2,0,22]: four AND atoms
and 24 linear gates.  The three total-linear-21 schedules [0,0,2,0,19],
[0,0,1,0,20], and [0,0,0,0,21] each directly target a 100-gate full circuit.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time
from dataclasses import dataclass

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Cadical153

import released_and_skeleton as ras
import temporal_window_resynth as tw


def parse_ints(s):
    return [int(x) for x in s.split(',') if x!='']


@dataclass
class Sig:
    name: str
    fixed: int | None = None
    bits: list[int] | None = None


def add_cond_xor(cnf: CNF, guard: int, out: int, terms: list[int], parity: int):
    """guard -> (out == XOR(terms) XOR parity), terms are positive vars."""
    vars_=[]
    for v in terms:
        if v not in vars_: vars_.append(v)
    # Enumerate at most 2 source-bit vars + optional polarity var + output.
    for assign in itertools.product((0,1), repeat=len(vars_)):
        val={v:b for v,b in zip(vars_,assign)}
        rhs=parity
        for v in terms: rhs^=val[v]
        for ob in (0,1):
            if ob==rhs: continue
            clause=[-guard]
            for v,b in zip(vars_,assign): clause.append(-v if b else v)
            clause.append(-out if ob else out)
            cnf.append(clause)


def bit_term(sig: Sig, k: int):
    if sig.fixed is not None:
        return None, (sig.fixed>>k)&1
    assert sig.bits is not None
    return sig.bits[k], 0


def match_target(cnf: CNF, vpool: IDPool, sources: list[Sig], target: int, D: int, label: str):
    # A fixed source may already satisfy the exact target, requiring no SAT vars.
    if any(s.fixed==target for s in sources if s.fixed is not None):
        return {'label':label,'target':target,'fixed':True,'choices':[]}
    choices=[]
    for si,s in enumerate(sources):
        if s.bits is None: continue
        m=vpool.id(f'match:{label}:{si}')
        choices.append((m,si))
        for k,b in enumerate(s.bits):
            cnf.append([-m, b if ((target>>k)&1) else -b])
    if not choices:
        # Force UNSAT cleanly rather than special-case caller logic.
        cnf.append([])
    else:
        cnf.append([m for m,_ in choices])
    return {'label':label,'target':target,'fixed':False,'choices':choices}


def live_sources(c, vals, lo):
    """Original tail live-ins, deduplicated by exact affine vector."""
    window=c['gates'][lo:]
    produced={g['out'] for g in window}
    names=[]; seen=set()
    for g in window:
        for w in (g['a'],g['b']):
            if w not in produced and w not in seen:
                seen.add(w); names.append(w)
    for w in c['outputs']:
        if w not in produced and w not in seen:
            seen.add(w); names.append(w)
    out=[]; seen_vec=set()
    for w in names:
        v=vals[w]
        if v in seen_vec: continue
        seen_vec.add(v); out.append((w,v))
    return out


def build(c, start, slots):
    sk=ras.extract_skeleton(c); n=sk['n_and']; D=sk['const_bit']+1; Cbit=sk['const_bit']
    sched=tw.original_schedule(c)
    if len(slots)!=n-start+1: raise ValueError((len(slots),n-start+1,slots))
    vals,_outs,_cb=tw.vectorize(c); lo=tw.interval_boundaries(c)[start]
    prefix=[dict(g) for g in c['gates'][:lo]]
    live=live_sources(c,vals,lo)
    sources=[Sig(name=w,fixed=v) for w,v in live]
    cnf=CNF(); pool=IDPool(); events=[]; lin=0; matches={}

    for stage in range(n-start+1):
        for _ in range(slots[stage]):
            pairs=[(a,b) for a in range(len(sources)) for b in range(a,len(sources))]
            rs=[pool.id(f'r:{lin}:{a}:{b}') for a,b in pairs]
            card=CardEnc.equals(lits=rs,bound=1,vpool=pool,encoding=EncType.seqcounter)
            cnf.extend(card.clauses)
            neg=pool.id(f'neg:{lin}')
            bits=[pool.id(f'v:{lin}:{k}') for k in range(D)]
            for r,(a,b) in zip(rs,pairs):
                sa,sb=sources[a],sources[b]
                for k,outv in enumerate(bits):
                    terms=[]; parity=0
                    va,ca=bit_term(sa,k); vb,cb=bit_term(sb,k)
                    parity^=ca^cb
                    if va is not None: terms.append(va)
                    if vb is not None: terms.append(vb)
                    if k==Cbit: terms.append(neg)
                    add_cond_xor(cnf,r,outv,terms,parity)
            sig=Sig(name=f'__tc_lin_{lin}',bits=bits)
            events.append({'kind':'linear','lin':lin,'pairs':pairs,'selectors':rs,'neg':neg})
            sources.append(sig); lin+=1
        if stage<n-start:
            ai=start+stage
            ma=match_target(cnf,pool,sources,sk['ands'][ai]['a'],D,f'and{ai}:a')
            mb=match_target(cnf,pool,sources,sk['ands'][ai]['b'],D,f'and{ai}:b')
            matches[ma['label']]=ma; matches[mb['label']]=mb
            atom=1<<(8+ai)
            events.append({'kind':'and','ai':ai,'ma':ma['label'],'mb':mb['label']})
            sources.append(Sig(name=f'__tc_and_{ai}',fixed=atom))

    out_match=[]
    for oi,t in enumerate(sk['outputs']):
        m=match_target(cnf,pool,sources,t,D,f'out{oi}')
        matches[m['label']]=m; out_match.append(m['label'])

    return {'cnf':cnf,'pool':pool,'events':events,'matches':matches,'out_match':out_match,
            'prefix':prefix,'live':live,'slots':slots,'start':start,'schedule':sched,
            'source_count':len(live),'D':D,'n_and':n,'linear':lin}


def true_choice(modelset, rec, sources):
    if rec['fixed']:
        for i,s in enumerate(sources):
            if s.fixed==rec['target']: return i
        raise AssertionError(('fixed match disappeared',rec))
    hits=[si for m,si in rec['choices'] if m in modelset]
    if not hits: raise AssertionError(('no match choice',rec['label']))
    return hits[0]


def reconstruct(c,data,model):
    ms={x for x in model if x>0}; sources=[Sig(name=w,fixed=v) for w,v in data['live']]
    gates=[dict(g) for g in data['prefix']]
    for ev in data['events']:
        if ev['kind']=='linear':
            hits=[(a,b) for r,(a,b) in zip(ev['selectors'],ev['pairs']) if r in ms]
            if len(hits)!=1: raise AssertionError(('pair selector',ev['lin'],hits))
            a,b=hits[0]; neg=ev['neg'] in ms; out=f'__tc_{len(gates)}'
            gates.append({'op':'XNOR' if neg else 'XOR','a':sources[a].name,'b':sources[b].name,'out':out})
            sources.append(Sig(name=out,bits=[]))
        else:
            ai=ev['ai']; ia=true_choice(ms,data['matches'][ev['ma']],sources); ib=true_choice(ms,data['matches'][ev['mb']],sources)
            out=f'__tc_{len(gates)}'; gates.append({'op':'AND','a':sources[ia].name,'b':sources[ib].name,'out':out})
            sources.append(Sig(name=out,fixed=1<<(8+ai)))
    outs=[]
    for lab in data['out_match']:
        idx=true_choice(ms,data['matches'][lab],sources); outs.append(sources[idx].name)
    full=ras.prune({'gates':gates,'outputs':outs})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('CaDiCaL tail candidate failed AES',ok))
    return full


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int,default=28)
    ap.add_argument('--slots',type=parse_ints,required=True); ap.add_argument('--conf-budget',type=int,default=3000000)
    ap.add_argument('--out',required=True); args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    data=build(c,args.start,args.slots); t0=time.time()
    with Cadical153(bootstrap_with=data['cnf'].clauses) as solver:
        if args.conf_budget>0: solver.conf_budget(args.conf_budget); sat=solver.solve_limited()
        else: sat=solver.solve()
        model=solver.get_model() if sat is True else None
    summary={'start':args.start,'slots':args.slots,'linear':data['linear'],'source_count':data['source_count'],
             'vars':data['pool'].top,'clauses':len(data['cnf'].clauses),'conf_budget':args.conf_budget,
             'sat':sat is True,'timed_out':sat is None,'unsat':sat is False,'seconds':round(time.time()-t0,3),
             'base_gates':len(c['gates']),'base_schedule':data['schedule'],
             'family_scope':'fixed prefix, live-in source interface, fixed ordered G103 AND atoms, fixed linear-slot schedule'}
    if model is not None:
        full=reconstruct(c,data,model); (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
        summary['candidate_gates']=len(full['gates']); summary['verified_all_256']=True
        summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__': main()
