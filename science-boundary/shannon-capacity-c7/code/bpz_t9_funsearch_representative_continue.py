#!/usr/bin/env python3
"""Root-shard/continue an exact repair in the unique FunSearch t=9 basin.

This is the same blocker-budget increasing-index DFS as
`bpz_t9_funsearch_representative_case.py`, but searches exactly the requested
first-candidate interval [root_start, root_end).  It is intended for radius-9+
cases where a whole 15k-candidate root range does not finish in one cutoff.

A completed interval is mathematical evidence only when the underlying solver
returns `exhausted`; a timeout reports `next_root` for a lossless continuation.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t9_aux_translation_fft as f
import bpz_t9_exchange_repair as ex
from bpz_t9_funsearch_fft import FUNSEARCH_COMMIT
from bpz_t9_funsearch_representative_case import IMAGE_INDEX, NEGMASK, PERM, TRANSLATION, cases


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('tan_root',type=Path);ap.add_argument('solver',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path)
    ap.add_argument('--case',type=int,required=True);ap.add_argument('--budget',type=int,required=True);ap.add_argument('--root-start',type=int,required=True);ap.add_argument('--root-end',type=int,default=None);ap.add_argument('--cutoff',type=int,default=540)
    args=ap.parse_args()
    if not 0<=args.case<20:raise SystemExit('case must be 0..19')
    if not 1<=args.budget<=9:raise SystemExit('budget must be 1..9')
    if args.root_start<0 or (args.root_end is not None and args.root_end<args.root_start):raise SystemExit('bad root interval')

    sys.path.insert(0,str(args.tan_root.resolve()));from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));ring=Ring(f.D);digits=tuple(ring.decode(v) for v in range(f.U));nb=[sum(1<<z for z in ring.NB[v]) for v in range(f.U)]
    c=cases(I0,ring,digits,nb)[args.case];S,bad,Dset=c['S'],c['bad'],c['D']
    with tempfile.TemporaryDirectory() as td:
        inp=Path(td)/'exchange.txt';retained,candidates,blockers=ex.export_input(inp,S,bad,Dset,ring,args.budget)
        end=len(candidates) if args.root_end is None else args.root_end
        if args.root_start>end or end>len(candidates):raise RuntimeError(f'root interval [{args.root_start},{end}) outside candidate count {len(candidates)}')
        cmd=[str(args.solver),str(args.cutoff),'--budget-bitsets','--root-start',str(args.root_start),'--root-prefix',str(end)]
        with inp.open('rb') as src:p=subprocess.run(cmd,stdin=src,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
    if p.returncode!=0:raise RuntimeError(f'exchange_dfs failed rc={p.returncode}: {p.stderr[-2000:]}')
    lines=[z for z in p.stdout.splitlines() if z.strip()]
    if not lines:raise RuntimeError('exchange_dfs produced no JSON')
    search=json.loads(lines[-1]);target=args.budget+1
    if int(search.get('root_start',-1))!=args.root_start or int(search.get('root_end',-1))!=end:raise RuntimeError(f'root interval replay drift: {search}')
    status={'method':'bpz-t9-funsearch-representative-root-sharded-exact-repair','candidate':search.get('status')=='witness','complete_interval':search.get('status') in ('witness','exhausted'),'score':134753,'image':IMAGE_INDEX,'perm':list(PERM),'negmask':NEGMASK,'translation':list(TRANSLATION),'case_index':args.case,'obstruction_index':c['obstruction_index'],'bad':bad,'budget':args.budget,'target_additions':target,'candidate_vertices':len(candidates),'requested_root_start':args.root_start,'requested_root_end':end,'search':search,'solver_stderr_tail':p.stderr[-2000:],'funsearch_source_commit':FUNSEARCH_COMMIT,'exchange_solver_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if not status['candidate']:
        args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(search.get('status','UNKNOWN').upper(),json.dumps(status,sort_keys=True),flush=True);return

    chosen=[int(i) for i in search.get('chosen',[])];
    if len(chosen)!=target or any(not 0<=i<len(candidates) for i in chosen):raise RuntimeError(f'bad witness {chosen}')
    add=[candidates[i] for i in chosen];owner_ids=set()
    for y in add:
        b=blockers[y]
        while b:
            q=b&-b;owner_ids.add(retained[q.bit_length()-1]);b^=q
    if len(owner_ids)>args.budget:raise RuntimeError('blocker budget replay failed')
    rem={bad}|owner_ids
    for q in retained:
        if len(rem)==target:break
        if q not in rem:rem.add(q)
    repaired=(S-rem)|set(add)
    if len(rem)!=target or len(repaired)!=f.N or repaired&Dset or not f.independent(repaired,digits):raise RuntimeError('repair replay failed')
    Ibits,pairs,orient,PH,PV=c['witness'];points,xp=f.build(Ibits,sum(1<<q for q in repaired),pairs,PH,PV,ring)
    if len(points)!=f.TARGET:raise RuntimeError(f'target score drift {len(points)}')
    status.update({'score':len(points),'removed_auxiliary_points':sorted(rem),'added_auxiliary_points':add,'private_pairs':[list(q) for q in pairs],'orientation':list(orient),'PH':PH,'PV':PV,'X_partition':{'X0':xp[0],'XH':xp[1],'XV':xp[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
