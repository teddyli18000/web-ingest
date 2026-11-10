#!/usr/bin/env python3
"""Bridge independently optimized mockturtle XAG and Few Shots p008 certificate.

All 256 Boolean input assignments are checked against independently implemented
AES inversion. The raw XAG has free complemented edges, which are *not* legal
Few Shots NOT gates. A phase-exact translation emits only AND, XOR, XNOR when
all required signal polarities are compatible; otherwise report the gap rather
than claiming an invalid gate count.
"""
from __future__ import annotations
import argparse, collections, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census
import make_and_shear_102 as shear

MASK=(1<<256)-1
INPUTS=census.input_tables(False)

def source(name):
    return shear.build()[1] if name=="shear-102" else ras.load_circuit(name)

def export(c,p):
    d={f'x{i}':i for i in range(8)}
    lines=[str(len(c['gates']))]
    for j,g in enumerate(c['gates']):
        lines.append(f"{dict(AND='A',XOR='X',XNOR='N')[g['op']]} {d[g['a']]} {d[g['b']]}")
        d[g['out']]=8+j
    lines.append(" ".join(str(d[w]) for w in c['outputs']))
    pathlib.Path(p).write_text("\n".join(lines)+"\n")

def load_xag(p):
    gates=[]; pis=[]; outputs=[]; count=None;before=None
    for line in pathlib.Path(p).read_text().splitlines():
        fields=line.split()
        if fields[0]=='C':
            count,before=map(int,fields[1:])
        elif fields[0]=='I': pis.append(int(fields[1]))
        elif fields[0]=='G':
            _,n,op,a,ca,b,cb=fields
            gates.append((int(n),op,int(a),int(ca),int(b),int(cb)))
        elif fields[0]=='O':
            outputs.append((int(fields[1]),int(fields[2])))
    assert len(gates)==count and len(pis)==len(INPUTS)==8 and len(outputs)==8
    return {'gates':gates,'pis':pis,'outputs':outputs,'count':count,'initial':before}

def trace_xag(net):
    v={0:0}
    for i,n in enumerate(net['pis']): v[n]=INPUTS[f'x{i}']
    for n,op,a,ca,b,cb in net['gates']:
        A=v[a]^(MASK if ca else 0); B=v[b]^(MASK if cb else 0)
        v[n]=(A&B) if op=='A' else (A^B)
    out=[v[n]^(MASK if c else 0) for n,c in net['outputs']]
    for x in range(256):
        actual=sum(((bit>>x)&1)<<i for i,bit in enumerate(out))
        assert actual==census.aes_sbox(x),('optimized XAG invalid',x,actual,census.aes_sbox(x))
    return v

def legalized(net):
    # For XNOR/XOR nodes an arbitrary output polarity is free. However, AND
    # outputs and primary inputs cannot be freely inverted in this basis.
    requests=collections.defaultdict(set)
    inputs={n:f'x{i}' for i,n in enumerate(net['pis'])}
    for n in inputs: requests[n].add(0)
    for n,op,a,ca,b,cb in net['gates']:
        if op=='A':
            requests[n].add(0)
            requests[a].add(ca)
            requests[b].add(cb)
    for n,c in net['outputs']:requests[n].add(c)
    conflict={n:sorted(x) for n,x in requests.items() if len(x)>1}
    if 0 in requests:
        conflict[0]=sorted(requests[0])
    stats={'forced_phase_nodes':len(requests),
           'phase_conflicts':len(conflict),
           'phase_conflict_detail':list(conflict.items())[:25],
           'complemented_AND_fanins':sum(ca+cb for _,op,_,ca,_,cb in net['gates'] if op=='A'),
           'complemented_outputs':sum(c for _,c in net['outputs']),
           'contains_constant_reference':any(0 in (a,b) for _,_,a,_,b,_ in net['gates']) or any(n==0 for n,_ in net['outputs'])}
    if conflict:return None,stats
    phase={n:next(iter(p)) if p else 0 for n,p in requests.items()}
    wires=dict(inputs);gs=[]
    for n,op,a,ca,b,cb in net['gates']:
        if a not in wires or b not in wires:return None,{**stats,'topology_failure':n}
        if wires[a]==wires[b]:return None,{**stats,'identical_operands':n}
        if op=='A':
            assert (phase.get(a,0)^ca)==(phase.get(b,0)^cb)==0
            operation='AND'
            assert phase.get(n,0)==0
        else:
            flip=phase.get(a,0)^ca^phase.get(b,0)^cb^phase.get(n,0)
            operation='XNOR' if flip else 'XOR'
        out='w'+str(len(gs))
        gs.append({'op':operation,'a':wires[a],'b':wires[b],'out':out})
        wires[n]=out
    outs=[]
    for n,c in net['outputs']:
        if n not in wires:return None,{**stats,'missing_output_node':n}
        assert phase.get(n,0)==c
        outs.append(wires[n])
    c=ras.prune({'gates':gs,'outputs':outs})
    assert ras.independent_check(c)[0], 'illegal phase lowering despite XAG proof'
    stats['legal_gates']=len(c['gates'])
    stats['verified_all_256']=True
    return c,stats

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',choices=['fs-101','shear-102','nist-g103'],default='fs-101')
    ap.add_argument('--export')
    ap.add_argument('--inspect')
    ap.add_argument('--out')
    args=ap.parse_args()
    if args.export:
        c=source(args.seed)
        assert ras.independent_check(c)[0]
        export(c,args.export)
        print(json.dumps({'seed':args.seed,'baseline_gates':len(c['gates']),'export':args.export,'all_256':True}))
    else:
        net=load_xag(args.inspect);trace_xag(net)
        circuit,stats=legalized(net)
        report={'seed':args.seed,'raw_xag_gates':net['count'],'raw_xag_before':net['initial'],
                'raw_xag_all_256':True,'legal_translation_found':circuit is not None,**stats}
        if circuit is not None:
            pathlib.Path(args.out).mkdir(parents=True,exist_ok=True)
            (pathlib.Path(args.out)/'legal.json').write_text(json.dumps(circuit,indent=2)+'\n')
        print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
