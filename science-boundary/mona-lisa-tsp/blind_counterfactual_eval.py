#!/usr/bin/env python3
"""SEPARATE post-search evaluator: hidden Nagata may only be read here.

Reject reports for any candidate not fully scorer-verified, and measure edge
recovery vs the unseen 5,757,191 tour. Search jobs never import this module.
"""
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
N=100000
def E(u,v):return (u,v) if u<v else (v,u)
def edges(t):return {E(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def historical(path):
    text=Path(path).read_text().splitlines()
    q=text.index('TOUR_SECTION')
    a=[]
    for line in text[q+1:]:
        for z in line.split():
            if z in ('-1','EOF'):return a
            a.append(int(z))
    raise ValueError(path)
def main():
    p=argparse.ArgumentParser()
    for name in ('hidden','reference','reports','output'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    vpath=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('official',vpath)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    hidden=json.loads(Path(args.hidden).read_text())['tour']
    reference=historical(args.reference)
    assert len(hidden)==len(reference)==N and v.tour_length(hidden)==5757191
    assert v.tour_length(reference)==5757199
    Eb=edges(reference);Et=edges(hidden)
    missing=Et-Eb
    results=[]
    for report in sorted(Path(args.reports).rglob('report.json')):
        d=json.loads(report.read_text())
        if d.get('protocol')!='hidden-nagata-199':continue
        assert d['score_reference']==5757199
        source_path=report.parent/'certificate.json'
        row={k:d.get(k) for k in ('strategy','new_chord_budget','status','wall_seconds','parents','parent_union',
                                  'active_edges','contracted_vertices','improvement','score','branches','best_bound')}
        new_edges={E(*e) for e in d['selected_chords']}
        assert len(new_edges)==d['new_chord_budget']
        row['hidden_target_edges_in_new_chords']=len(missing&new_edges)
        if source_path.exists():
            route=json.loads(source_path.read_text())['tour']
            raw=source_path.read_bytes()
            verdict=v.verify_bytes(raw,v.load_config())
            assert verdict['valid'] and int(verdict['score'])==d['score']
            ec=edges(route)
            row.update({'valid':True,'hidden_target_edges_recovered':len((ec-Eb)&missing),
                        'hidden_target_edge_recall':round(len((ec-Eb)&missing)/len(missing),6),
                        'edges_different_from_incumbent':len(ec-Eb),
                        'edges_shared_with_hidden':len(ec&Et)})
        else:row.update({'valid':False,'hidden_target_edges_recovered':0})
        results.append(row)
    output={'hidden_score':5757191,'blind_incumbent_score':5757199,
      'reference_hidden_edge_difference':len(missing),
      'report_count':len(results),'results':results,
      'gate':'search script has no access to official baseline certificate or its edge set'}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output),flush=True)
if __name__=='__main__':main()
