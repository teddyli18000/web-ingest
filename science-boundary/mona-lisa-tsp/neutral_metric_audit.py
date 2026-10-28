#!/usr/bin/env python3
"""Measure exact integer ties versus the hidden Euclidean metric on neutral moves."""
import argparse,importlib.util,json,math,os
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--moves',required=True)
    p.add_argument('--report',required=True)
    z=p.parse_args()
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    def dist(a,b):
        a-=1;b-=1
        return math.hypot(xs[a]-xs[b],ys[a]-ys[b])
    moves=json.loads(Path(z.moves).read_text())['neutral_moves']
    reports=[]
    for move in moves:
        removed=move['removed'];added=move['added']
        rounded_delta=sum(v.euc_2d(xs[a-1]-xs[b-1],ys[a-1]-ys[b-1])
                          for a,b in added)-sum(v.euc_2d(xs[a-1]-xs[b-1],ys[a-1]-ys[b-1])
                          for a,b in removed)
        real_delta=math.fsum(dist(a,b) for a,b in added)-math.fsum(dist(a,b) for a,b in removed)
        assert rounded_delta==0
        reports.append({'seed':move['artifact_seed'],'changed_edges':len(added),
            'tsplib_delta':rounded_delta,'euclidean_delta':real_delta,
            'rounding_residual_delta':-real_delta})
    out={'note':'Negative Euclidean delta on zero integer delta is a strictly descending secondary objective, not a new p010 record.',
         'moves':reports}
    dest=Path(z.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out),flush=True)
if __name__=='__main__':main()
