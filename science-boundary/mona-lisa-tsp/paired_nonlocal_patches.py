#!/usr/bin/env python3
"""Exact nonlocal dual patches centered on pairs of public neutral 4-opt moves.

Moves are given as tiny edge differences from the canonical 5,757,191 tour.
The union of two nonlocal dual patches is optimized jointly with exact
degree and whole-tour connectivity constraints.
"""
import argparse,importlib.util,itertools,json,os,time
from pathlib import Path
import dual_patch_search as d

def key(a,b):return (a,b) if a<b else (b,a)

def main():
    p=argparse.ArgumentParser()
    for name in ['edges','baseline','neutral-moves','outdir','report']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--pair-start',type=int,default=0)
    p.add_argument('--max-pairs',type=int,default=3)
    p.add_argument('--radii',default='1,2,3')
    p.add_argument('--max-faces',type=int,default=420)
    p.add_argument('--seconds',type=int,default=30)
    args=p.parse_args()
    t0=time.monotonic()
    tour=[x-1 for x in json.loads(Path(args.baseline).read_text())['tour']]
    w,base,faces,dual,sides,positive=d.load(args.edges,tour)
    moves=json.loads(Path(args.neutral_moves).read_text())['neutral_moves']
    assert len(moves)==6
    assert len(base)==100000
    pair_list=list(itertools.combinations(range(len(moves)),2))
    spec=importlib.util.spec_from_file_location('verify',
        Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    verify=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
    assert verify.tour_length([v+1 for v in tour])==5757191
    outdir=Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    focus=[]
    for move in moves:
        f=set()
        for a,b in move['removed']+move['added']:
            k=key(a-1,b-1)
            assert k in sides
            for fid in sides[k]:
                # The 1231-edge outside face swallows all patches. We keep
                # it pinned in this *restricted* study; no global claim.
                if len(faces[fid])<=40:f.add(fid)
        assert f
        focus.append(f)
    print(json.dumps({'stage':'setup','pair_count':len(pair_list),
        'focus_faces_per_move':[len(x) for x in focus]}),flush=True)
    records=[]
    for i in range(args.pair_start,min(args.pair_start+args.max_pairs,len(pair_list))):
        a,b=pair_list[i]
        for radius in map(int,args.radii.split(',')):
            combined=set()
            skipped=None
            for seed in focus[a]|focus[b]:
                patch=d.patch(seed,radius,dual,args.max_faces)
                if patch is None:
                    skipped='BFS_LIMIT'
                    break
                combined.update(patch)
                if len(combined)>args.max_faces:
                    skipped='UNION_LIMIT'
                    break
            if skipped:
                rec={'pair_id':i,'sources':[moves[a]['artifact_seed'],
                    moves[b]['artifact_seed']],'radius':radius,'status':skipped}
            else:
                ans=d.solve(f'pair{i}',radius,combined,w,base,sides,tour,
                            verify,outdir,args.seconds,80)
                rec={'pair_id':i,'sources':[moves[a]['artifact_seed'],
                     moves[b]['artifact_seed']],**ans}
            records.append(rec)
            print(json.dumps({'stage':'patch',**rec}),flush=True)
            Path(args.report).write_text(json.dumps({'records':records},indent=2)+'\n')
            if rec['status']=='VERIFIED_IMPROVEMENT':break
    Path(args.report).write_text(json.dumps({'records':records,
        'seconds':round(time.monotonic()-t0,2)},indent=2)+'\n')

if __name__=='__main__':main()
