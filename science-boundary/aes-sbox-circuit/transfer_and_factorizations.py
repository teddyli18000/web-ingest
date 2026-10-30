#!/usr/bin/env python3
"""Transfer AND factorizations between NIST G103/G104 sibling circuits.

The two circuits share 30/32 exact AND-output functions but may realize a shared
atom with different operand functions.  For each shared atom, replace the target
AND operands by the source circuit's factor functions when those factors are
already available earlier in the target, or can be built with <=2 new XOR/XNOR
helpers.  Prune afterwards and keep only non-worsening exact AES circuits.

This is cross-seed architecture transfer, not an ODC rewrite: the alternate
factorization comes from a different complete high-quality circuit.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1


def eval_trace(c):
    vals=census.input_tables(False); ands=[]
    for idx,g in enumerate(c['gates']):
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']])
        if g['op']=='AND':
            ands.append({'gate_index':idx,'out_func':vals[g['out']],
                         'a_func':vals[g['a']],'b_func':vals[g['b']],
                         'a':g['a'],'b':g['b']})
    return vals,ands


def sig(c):return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def synth_one(target, earlier, vals):
    """Return (existing_wire,None) or ((a,b,op), truth) for one-gate synthesis."""
    by={vals[w]:w for w in earlier}
    if target in by:return ('wire',by[target])
    for i,a in enumerate(earlier):
        va=vals[a]
        for b in earlier[i+1:]:
            x=va^vals[b]
            if x==target:return ('gate',a,b,'XOR')
            if (x^MASK)==target:return ('gate',a,b,'XNOR')
    return None


def splice(c,idx,factors,vals):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    earlier=[f'x{i}' for i in range(8)]+[g['out'] for g in c['gates'][:idx]]
    specs=[synth_one(t,earlier,vals) for t in factors]
    if any(x is None for x in specs):return None,None
    helpers=[];wires=[]
    for j,s in enumerate(specs):
        if s[0]=='wire':wires.append(s[1])
        else:
            _,a,b,op=s;h=f'__factor_helper_{j}__';helpers.append({'op':op,'a':a,'b':b,'out':h});wires.append(h)
    # If both requested factors synthesize to the same new helper function, share it.
    if len(helpers)==2 and factors[0]==factors[1]:
        helpers=helpers[:1];wires[1]=wires[0]
    nc['gates'][idx:idx]=helpers
    ai=idx+len(helpers); assert nc['gates'][ai]['op']=='AND'
    nc['gates'][ai]['a']=wires[0];nc['gates'][ai]['b']=wires[1]
    nc=ras.prune(nc)
    return nc,specs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--target',choices=['nist-g103','nist-g104'],required=True)
    ap.add_argument('--source',choices=['nist-g103','nist-g104'],required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();assert args.target!=args.source
    tc=ras.load_circuit(args.target);sc=ras.load_circuit(args.source)
    assert ras.independent_check(tc)[0] and ras.independent_check(sc)[0]
    tv,ta=eval_trace(tc);sv,sa=eval_trace(sc);source_by={x['out_func']:x for x in sa}
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True);rows=[];seen={sig(tc)};shared=0;alternate=0
    for t in ta:
        s=source_by.get(t['out_func'])
        if not s:continue
        shared+=1
        target_pair={t['a_func'],t['b_func']};source_pair={s['a_func'],s['b_func']}
        if target_pair==source_pair:continue
        alternate+=1
        nc,specs=splice(tc,t['gate_index'],(s['a_func'],s['b_func']),tv)
        if nc is None or len(nc['gates'])>len(tc['gates']):continue
        h=sig(nc)
        if h in seen:continue
        seen.add(h);ok=ras.independent_check(nc);assert ok[0],ok
        rec={'target_and_gate_index':t['gate_index'],'target_local_factors':[t['a'],t['b']],
             'source_factor_gate_index':s['gate_index'],'helper_specs':specs,'gates':len(nc['gates']),'sha256':h}
        rows.append((rec,nc))
    rows.sort(key=lambda z:(z[0]['gates'],z[0]['target_and_gate_index']))
    for i,(r,c) in enumerate(rows):pathlib.Path(out,f'candidate-{i:03d}-{r["gates"]}.json').write_text(json.dumps(c,indent=2)+'\n')
    summary={'target':args.target,'source':args.source,'base_gates':len(tc['gates']),'shared_and_atoms':shared,
             'shared_atoms_with_alternate_factorization':alternate,'nonworsening_transfers':len(rows),
             'strict_reductions':sum(r['gates']<len(tc['gates']) for r,_ in rows),'candidates':[r for r,_ in rows]}
    pathlib.Path(out,'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
