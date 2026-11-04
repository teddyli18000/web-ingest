#!/usr/bin/env python3
"""Free-label 5D slice recombination with all 2401 4D relative translations.

Unlike the previous layer-stitching program, 4D templates extracted from any
of the seven original symbol layers may now be placed in ANY destination
symbol layer. This releases the original 'which symbol owns this 4D slice'
choice and turns candidate selection into a max-weight 7-cycle walk on one
common template-compatibility graph.

The relaxed graph allows an edge if some relative 4D phase is compatible,
discarding the requirement that 7 edge phases sum to zero. Its score is an
exact upper bound for the translated-template family. The zero-phase graph
is a valid constructive subfamily; any >=368 witness is replayed and squared.
"""
from __future__ import annotations
import argparse,json,time,collections
from pathlib import Path
from c7p5_full_shift_compatibility import allow_mask,base_templates
from c7p5_slice_stitch_dp import gather
from c7p5_two_layer_repair import lift,independent,dump_certificate

def cycle(nodes,edges):
    m=len(nodes);best=(-1,None)
    for first in range(m):
        dp={first:(nodes[first]['size'],(first,))}
        for _ in range(6):
            nd={}
            for i,(v,p) in dp.items():
                for j in edges[i]:
                    z=v+nodes[j]['size']
                    if j not in nd or z>nd[j][0]:nd[j]=(z,p+(j,))
            dp=nd
            if not dp:break
        for j,(value,path) in dp.items():
            if first in edges[j] and value>best[0]:best=(value,path)
    return best

def search(seeds,axis,certificate):
    T=base_templates(seeds,axis)
    unique={}
    for layer,L in enumerate(T):
        for x in L:
            unique.setdefault(x['q'],{'q':x['q'],'size':len(x['q']),
                         'source':x['source'],'original_layer':layer})
    nodes=list(unique.values());n=len(nodes)
    anyedges=[[] for _ in nodes];zeroedges=[[] for _ in nodes]
    hist=collections.Counter()
    nonzero=0
    for i,A in enumerate(nodes):
        for j,B in enumerate(nodes):
            mask=allow_mask(A['q'],B['q'])
            k=mask.bit_count();hist[k]+=1
            if k:
                anyedges[i].append(j)
                if mask & 1:zeroedges[i].append(j)
                if mask & ~1:nonzero+=1
    (upper,upath)=cycle(nodes,anyedges)
    (actual,zpath)=cycle(nodes,zeroedges)
    if zpath is None:raise RuntimeError(('missing original 367 family',axis))
    words=set()
    for s,j in enumerate(zpath):
        for q in nodes[j]['q']:words.add(lift(q,axis,s))
    assert len(words)==actual and independent(words)
    have=dump_certificate(words,certificate) if actual>=368 else False
    def pathinfo(path):
        return [{'label':s,'size':nodes[j]['size'],'source':nodes[j]['source'],
                 'source_layer':nodes[j]['original_layer']} for s,j in enumerate(path)]
    return {'axis':axis,'source_sets':len(seeds),'distinct_freelabel_templates':n,
            'compatible_anyshift_edges':sum(map(len,anyedges)),
            'compatible_zeroshift_edges':sum(map(len,zeroedges)),
            'nonzero_shift_edges':nonzero,
            'phase_count_histogram':{str(k):v for k,v in sorted(hist.items())},
            'phase_relaxed_cycle_upper':upper,
            'exact_zero_phase_cycle_score':actual,
            'candidate_368':have,'zero_phase_path':pathinfo(zpath),
            'relaxed_path':pathinfo(upath)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('bpz',type=Path);p.add_argument('family',type=Path)
    p.add_argument('result',type=Path);p.add_argument('certificate',type=Path)
    p.add_argument('--axis',type=int,required=True);a=p.parse_args()
    t=time.monotonic()
    seeds=gather(json.loads(a.bpz.read_text()),json.loads(a.family.read_text()))
    out=search(seeds,a.axis,a.certificate);out['seconds']=time.monotonic()-t
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True),flush=True)

if __name__=='__main__':main()
